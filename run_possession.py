"""Release runner: tracking -> per-frame evidence -> possession labels -> submission CSV.

    python run_possession.py --data-dir C:\\path\\to\\bundle --out data/release/<team_name>.csv

The bundle directory contains tactical/. MTAH_DATA_DIR (set before Python starts) also works.

Pipeline
--------
1. M3 streams the tactical tracking ONCE (iter_tracking_frames).
2. Actual M1 and M4 receive the same recursively read-only observation.
3. Actual M2 receives ten full-precision arrays, M4's initial-dead prior and native half triples.
4. Every frame is written: H / A / D / X inside the graded halves, X outside them.

Integrated mode is the default. The historical M1-only decoder requires --mode fallback;
it is not eligible for integrated release gates. See module1/RUNNER.md.

No ground-truth labels are read. Thresholds are fixed constants, not tuned on public labels.
The file is written to a temporary name and renamed only after the full run succeeds, so a
failed run never leaves a partial file that looks like a submission.
"""

import argparse
from collections.abc import Mapping
from dataclasses import asdict
import json
import math
from numbers import Real
import os
import sys
from types import MappingProxyType

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

PRODUCERS = []  # legacy fallback-only diagnostic hooks; not the integrated evidence interface

FLOAT_FIELDS = ("d_home", "d_away", "score_home", "score_away")
BOOL_FIELDS = ("ball_visible", "home_available", "away_available")
M1_FIELDS = ("score_home", "score_away") + BOOL_FIELDS
M4_FLOAT_FIELDS = ("dead_score", "restart_score")
M4_BOOL_FIELDS = ("dead_available", "restart_available")
M4_FIELDS = M4_FLOAT_FIELDS + M4_BOOL_FIELDS + ("restart_side",)


def integrated_modules():
    """Required imports fail closed; never silently replace M2 or M4."""
    try:
        from modulos import modulo2 as m2
        from module4 import evidence as m4
    except ImportError as error:
        raise RuntimeError("Integrated mode requires corrected M2 and M4") from error
    return m2, m4


def readonly(value):
    if isinstance(value, Mapping):
        return MappingProxyType({k: readonly(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(readonly(v) for v in value)
    return value


def validate_row(row, fields, index):
    """Check scalar types before NumPy assignment can silently coerce bad evidence."""
    if not isinstance(row, Mapping) or set(row) != set(fields):
        raise ValueError("producer frame {} must return exactly {}".format(index, sorted(fields)))
    for name, value in row.items():
        if name in BOOL_FIELDS + M4_BOOL_FIELDS:
            valid = isinstance(value, (bool, np.bool_))
        elif name == "restart_side":
            valid = value is None or (isinstance(value, str) and value in ("H", "A"))
        else:
            valid = isinstance(value, Real) and not isinstance(value, (bool, np.bool_))
            if valid:
                valid = (math.isnan(value) or math.isfinite(value) and value >= 0) if name.startswith("d_") else math.isfinite(value) and 0 <= value <= 1
        if not valid:
            raise ValueError("invalid {} at frame {}".format(name, index))


def validate_evidence(evidence, n_frames, *, mode="integrated"):
    """Fail loudly if the evidence is not what the decoder assumes. Run before decoding.

    Checks: all required M1/M4 arrays exist with length n_frames; flags are boolean dtype; scores are
    finite and inside [0, 1]; distances are NaN or finite and >= 0; availability never occurs
    without a visible ball; an unavailable side has score 0 and no distance.
    """
    expected = set(FLOAT_FIELDS) | set(BOOL_FIELDS)
    if mode not in ("integrated", "fallback"):
        raise ValueError("unknown pipeline mode: " + str(mode))
    if mode == "integrated":
        expected.update(M4_FIELDS)
        expected.add("initial_dead")
    missing = expected - set(evidence)
    if missing:
        raise ValueError("evidence is missing fields: {}".format(sorted(missing)))

    for name in sorted(expected):
        array = np.asarray(evidence[name])
        if array.shape != (n_frames,):
            raise ValueError("evidence[{!r}] has shape {}, expected ({},)".format(
                name, array.shape, n_frames))

    for name in BOOL_FIELDS + (M4_BOOL_FIELDS + ("initial_dead",) if mode == "integrated" else ()):
        if np.asarray(evidence[name]).dtype != np.bool_:
            raise ValueError("evidence[{!r}] must be boolean, got {}".format(
                name, np.asarray(evidence[name]).dtype))

    for name in ("score_home", "score_away") + (M4_FLOAT_FIELDS if mode == "integrated" else ()):
        score = np.asarray(evidence[name])
        if score.dtype.kind not in "iuf":
            raise ValueError(name + " must contain real numeric scores")
        if not np.isfinite(score).all():
            raise ValueError("evidence[{!r}] has non-finite scores".format(name))
        if np.any(score < 0.0) or np.any(score > 1.0):
            raise ValueError("evidence[{!r}] has scores outside [0, 1]: min {}, max {}".format(
                name, score.min(), score.max()))

    for name in ("d_home", "d_away"):
        distance = np.asarray(evidence[name])
        if distance.dtype.kind not in "iuf":
            raise ValueError(name + " must contain real numeric distances")
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
        distance = np.asarray(evidence["d_" + side])
        if not np.isfinite(distance[available]).all() or not np.isnan(distance[~available]).all():
            raise ValueError("d_{} must be finite when available and NaN when unavailable".format(side))
    if mode == "integrated":
        for prefix in ("dead", "restart"):
            if np.any(np.asarray(evidence[prefix + "_score"])[~np.asarray(evidence[prefix + "_available"])] != 0):
                raise ValueError(prefix + " score must be zero when unavailable")
        if any(side is not None and (not isinstance(side, str) or side not in ("H", "A"))
               for side in evidence["restart_side"]):
            raise ValueError("restart_side must be H/A/None")


def collect_evidence(tau, game, data_dir, *, mode="integrated", windows=None):
    """One M3 pass, compact aligned M1/M4 arrays. None windows loads automatic tags."""
    if not math.isfinite(tau) or tau <= 0:
        raise ValueError("tau must be finite and positive")
    if mode not in ("integrated", "fallback"):
        raise ValueError("unknown pipeline mode")
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
    if mode == "integrated":
        _, m4 = integrated_modules()
        if windows is None:
            windows = m4.restart_windows(m4.load(game=game, data_dir=data_dir))
        producer = m4.StoppageEvidence(windows, game=game)
        fields.update({name: np.zeros(n_frames) for name in M4_FLOAT_FIELDS})
        fields.update({name: np.zeros(n_frames, dtype=bool) for name in M4_BOOL_FIELDS})
        fields["restart_side"] = np.full(n_frames, None, dtype=object)
        initial_dead = np.zeros(n_frames, dtype=bool)
        initial_dead[list(producer.initial_dead_frames)] = True

    count = 0
    source = iter_tracking_frames(game=game, data_dir=data_dir)
    try:
        for index, observation in enumerate(source):
            if index >= n_frames:
                raise RuntimeError("tracking has more frames than the video ({})".format(n_frames))
            frame = observation.get("frame") if hasattr(observation, "get") else None
            if frame is None:
                raise RuntimeError("observation {} has no 'frame' field".format(index))
            if isinstance(frame, (bool, np.bool_)) or not isinstance(frame, (int, np.integer)) or frame != index:
                raise RuntimeError("tracking out of order: observation {} carries frame {}".format(
                    index, frame))
            shared = readonly(observation)
            evidence = score_frame(shared, tau=tau)
            validate_row(evidence, FLOAT_FIELDS + BOOL_FIELDS, index)
            if mode == "integrated":
                stopped = producer(index, shared)
                validate_row(stopped, M4_FIELDS, index)
                evidence = dict(evidence, **stopped)
            for name, array in fields.items():
                array[index] = evidence[name]
            if mode == "fallback":
                for hook in PRODUCERS:
                    hook(index, shared)
            count += 1
    finally:
        close = getattr(source, "close", None)
        if close:
            close()  # exhausting the iterator completes M3's final count validation

    if count != n_frames:
        raise RuntimeError("expected {} tracking frames, read {}".format(n_frames, count))
    if mode == "integrated":
        fields["initial_dead"] = initial_dead
    validate_evidence(fields, n_frames, mode=mode)
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


def decode_match(evidence, n_frames, game, *, mode="integrated"):
    """One legal label for every frame. X outside the graded halves."""
    validate_evidence(evidence, n_frames, mode=mode)
    blocks = half_video_blocks(game)
    if mode == "integrated":
        m2, _ = integrated_modules()
        labels = m2.modulo2(**{k: evidence[k] for k in M1_FIELDS + M4_FIELDS},
                            half_blocks=blocks, initial_dead=evidence["initial_dead"])
    else:
        labels = ["X"] * n_frames
        for _half, first, last in blocks:
            labels[first:last + 1] = decode_half(evidence, first, last)
    if len(labels) != n_frames or any(l not in ("H", "A", "D", "X") for l in labels):
        raise RuntimeError("decoder produced an illegal label sequence")
    inside = np.zeros(n_frames, dtype=bool)
    for _, first, last in blocks:
        inside[first:last + 1] = True
    if any(label != "X" for label, graded in zip(labels, inside) if not graded):
        raise RuntimeError("decoder produced non-X outside graded halves")
    return labels


def write_submission(path, labels):
    """frame,label CSV. Written to a temp file and renamed so a failure leaves nothing partial."""
    path = os.fspath(path)
    labels = list(labels)
    if any(label not in ("H", "A", "D", "X") for label in labels):
        raise ValueError("illegal submission label")
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
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
    parser.add_argument("--mode", choices=("integrated", "fallback"), default="integrated")
    parser.add_argument("--report", help="optional aggregate-only JSON report")
    args = parser.parse_args(argv)

    n_frames = source_frames("tactical", args.game)
    print("mode: {}{}".format(args.mode, " (NOT integrated release eligible)" if args.mode == "fallback" else ""))
    print("reading tracking ...")
    evidence = collect_evidence(args.tau, args.game, args.data_dir, mode=args.mode)
    print("  ball visible on {} of {} frames".format(int(evidence["ball_visible"].sum()), n_frames))

    labels = decode_match(evidence, n_frames, args.game, mode=args.mode)
    if len(labels) != n_frames or any(l not in ("H", "A", "D", "X") for l in labels):
        raise RuntimeError("decoder produced an illegal label sequence")

    write_submission(args.out, labels)
    counts = {k: labels.count(k) for k in ("H", "A", "D", "X")}
    if args.report:
        report = dict(mode=args.mode, game=args.game, tau=args.tau, rows=n_frames, counts=counts,
                      half_blocks=half_video_blocks(args.game))
        if args.mode == "integrated":
            m2, m4 = integrated_modules()
            report.update(m2_config=asdict(m2.CONFIG_M2), m4_config=asdict(m4.EvidenceConfig()))
            report["initial_dead_halves"] = [h for h, first, _ in half_video_blocks(args.game)
                                              if evidence["initial_dead"][first]]
            report["evidence"] = {prefix: dict(available=int(evidence[prefix + "_available"].sum()),
                positive=int((evidence[prefix + "_score"] > 0).sum()),
                strong=int((evidence[prefix + "_score"] >= .5).sum())) for prefix in ("dead", "restart")}
        with open(args.report, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
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
