"""Release runner: tracking -> per-frame evidence -> possession labels -> submission CSV.

    python run_possession.py --data-dir C:\\path\\to\\bundle --out data/release/<team_name>.csv

The bundle directory contains tactical/. MTAH_DATA_DIR (set before Python starts) also works.

Pipeline
--------
1. M3 streams the tactical tracking ONCE (iter_tracking_frames).
2. Each unchanged observation goes to every evidence producer in PRODUCERS. Today that is M1
   (score_frame). M4 plugs in here later without touching the loop.
3. The decoder turns the full-precision evidence arrays into one label per frame.
4. Every frame is written: H / A / D inside the graded halves, X outside them.

The decoder below (decode_half) is a deliberately simple FALLBACK so that a valid candidate
exists today. It uses only M1 evidence. When M2's tested decoder is ready, replace the call in
decode_match() with it and keep everything else.

No ground-truth labels are read. Thresholds are fixed constants, not tuned on public labels.
The file is written to a temporary name and renamed only after the full run succeeds, so a
failed run never leaves a partial file that looks like a submission.
"""

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from games import GAME, half_video_blocks, source_frames  # noqa: E402
from module1.control_scores import score_frame  # noqa: E402
from starter.tactical_tracking import iter_tracking_frames  # noqa: E402

# Fallback decoder configuration (frames at 25 fps). Fixed, documented, not tuned on labels.
MIN_SCORE = 0.10      # the leading side must be at least this close (exp(-d/tau)); ~7 m at tau=3
MARGIN = 0.05         # leading side must beat the other by at least this much
CONFIRM_FRAMES = 12   # about 0.5 s of consecutive credible opposing control before switching

PRODUCERS = []  # extra per-frame evidence producers (M4 goes here); each takes an observation

FLOAT_FIELDS = ("d_home", "d_away", "score_home", "score_away")
BOOL_FIELDS = ("ball_visible", "home_available", "away_available")


def validate_evidence(evidence, n_frames):
    """Fail loudly if the evidence is not what the decoder assumes. Run before decoding.

    Checks: all seven arrays exist with length n_frames; flags are boolean dtype; scores are
    finite and inside [0, 1]; distances are NaN or finite and >= 0; availability never occurs
    without a visible ball; an unavailable side has score 0 and no distance.
    """
    expected = set(FLOAT_FIELDS) | set(BOOL_FIELDS)
    missing = expected - set(evidence)
    if missing:
        raise ValueError("evidence is missing fields: {}".format(sorted(missing)))

    for name in sorted(expected):
        array = np.asarray(evidence[name])
        if array.shape != (n_frames,):
            raise ValueError("evidence[{!r}] has shape {}, expected ({},)".format(
                name, array.shape, n_frames))

    for name in BOOL_FIELDS:
        if np.asarray(evidence[name]).dtype != np.bool_:
            raise ValueError("evidence[{!r}] must be boolean, got {}".format(
                name, np.asarray(evidence[name]).dtype))

    for name in ("score_home", "score_away"):
        score = np.asarray(evidence[name], dtype=float)
        if not np.isfinite(score).all():
            raise ValueError("evidence[{!r}] has non-finite scores".format(name))
        if score.min() < 0.0 or score.max() > 1.0:
            raise ValueError("evidence[{!r}] has scores outside [0, 1]: min {}, max {}".format(
                name, score.min(), score.max()))

    for name in ("d_home", "d_away"):
        distance = np.asarray(evidence[name], dtype=float)
        seen = ~np.isnan(distance)
        if not np.isfinite(distance[seen]).all() or (distance[seen] < 0).any():
            raise ValueError("evidence[{!r}] has negative or infinite distances".format(name))

    visible = np.asarray(evidence["ball_visible"])
    for side in ("home", "away"):
        available = np.asarray(evidence[side + "_available"])
        if (available & ~visible).any():
            raise ValueError("{}_available is true on frames without a visible ball".format(side))
        if (np.asarray(evidence["score_" + side])[~available] != 0.0).any():
            raise ValueError("score_{} is nonzero where {} evidence is unavailable".format(
                side, side))


def collect_evidence(tau, game, data_dir):
    """One pass over the tracking. Returns M1's seven full-precision arrays."""
    n_frames = source_frames("tactical", game)
    fields = {
        "ball_visible": np.zeros(n_frames, dtype=bool),
        "d_home": np.full(n_frames, np.nan),
        "d_away": np.full(n_frames, np.nan),
        "score_home": np.zeros(n_frames),
        "score_away": np.zeros(n_frames),
        "home_available": np.zeros(n_frames, dtype=bool),
        "away_available": np.zeros(n_frames, dtype=bool),
    }

    count = 0
    source = iter_tracking_frames(game=game, data_dir=data_dir)
    try:
        for index, observation in enumerate(source):
            if index >= n_frames:
                raise RuntimeError("tracking has more frames than the video ({})".format(n_frames))
            frame = observation.get("frame") if hasattr(observation, "get") else None
            if frame is None:
                raise RuntimeError("observation {} has no 'frame' field".format(index))
            if frame != index:
                raise RuntimeError("tracking out of order: observation {} carries frame {}".format(
                    index, frame))
            evidence = score_frame(observation, tau=tau)
            for name, array in fields.items():
                array[index] = evidence[name]
            for producer in PRODUCERS:
                producer(index, observation)
            count += 1
    finally:
        close = getattr(source, "close", None)
        if close:
            close()  # exhausting the iterator completes M3's final count validation

    if count != n_frames:
        raise RuntimeError("expected {} tracking frames, read {}".format(n_frames, count))
    return fields


def decode_half(evidence, first, last):
    """Fallback labels for one half, inclusive frames first..last. State starts fresh here.

    - Both availability flags are required before a score comparison can change anything.
    - A switch needs the other side to lead by MARGIN, with at least MIN_SCORE, for
      CONFIRM_FRAMES consecutive frames. One nearest-player flip is not enough.
    - Missing or weak evidence keeps the current side (a pass or occlusion does not end it).
    - Before the first confirmed side the label is X (no guess).
    - D is not produced: stoppage evidence is M4's job and is not connected yet.
    """
    labels = []
    current = None   # "H", "A" or None
    pending = None   # side currently trying to take over
    streak = 0

    for frame in range(first, last + 1):
        leader = None
        if evidence["home_available"][frame] and evidence["away_available"][frame]:
            home = evidence["score_home"][frame]
            away = evidence["score_away"][frame]
            if home - away >= MARGIN and home >= MIN_SCORE:
                leader = "H"
            elif away - home >= MARGIN and away >= MIN_SCORE:
                leader = "A"

        if leader is None:
            pending, streak = None, 0       # inconclusive: keep the current side
        elif leader == current:
            pending, streak = None, 0       # confirms the side we already have
        else:
            streak = streak + 1 if leader == pending else 1
            pending = leader
            if current is None or streak >= CONFIRM_FRAMES:
                current, pending, streak = leader, None, 0

        labels.append(current if current is not None else "X")
    return labels


def decode_match(evidence, n_frames, game):
    """One legal label for every frame. X outside the graded halves."""
    validate_evidence(evidence, n_frames)  # before any decoder (fallback or M2) touches it
    labels = ["X"] * n_frames
    for _half, first, last in half_video_blocks(game):
        labels[first:last + 1] = decode_half(evidence, first, last)
    return labels


def write_submission(path, labels):
    """frame,label CSV. Written to a temp file and renamed so a failure leaves nothing partial."""
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", newline="\n") as handle:
            handle.write("frame,label\n")
            handle.writelines("{},{}\n".format(i, label) for i, label in enumerate(labels))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", default=None, help="bundle root containing tactical/")
    parser.add_argument("--out", required=True, help="submission CSV to write")
    parser.add_argument("--game", default=GAME)
    parser.add_argument("--tau", type=float, default=3.0, help="metres for exp(-d/tau)")
    args = parser.parse_args(argv)

    n_frames = source_frames("tactical", args.game)
    print("reading tracking ...")
    evidence = collect_evidence(args.tau, args.game, args.data_dir)
    print("  ball visible on {} of {} frames".format(int(evidence["ball_visible"].sum()), n_frames))

    labels = decode_match(evidence, n_frames, args.game)
    if len(labels) != n_frames or any(l not in ("H", "A", "D", "X") for l in labels):
        raise RuntimeError("decoder produced an illegal label sequence")

    write_submission(args.out, labels)
    counts = {k: labels.count(k) for k in ("H", "A", "D", "X")}
    print("wrote {} ({} rows)  H {}  A {}  D {}  X {}".format(
        args.out, len(labels), counts["H"], counts["A"], counts["D"], counts["X"]))
    print("now validate:  python evaluation/validate_submission.py \"{}\"".format(args.out))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # clear failure, no partial submission
        print("ERROR: {}".format(error), file=sys.stderr)
        sys.exit(1)
