"""Module 1 - current proximity evidence with explicit per-team availability.

Consume corrected Module 3 observations; distances and tau are in metres.
Use score_frame, iter_control_scores or build_evidence for inference. The rounded
CLI CSV is diagnostic only. See CONTROL_SCORES.md for the handoff contract.
"""

import argparse
import math
import os
import sys

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from games import GAME, GAMES, source_frames  # noqa: E402
from starter.tactical_tracking import iter_tracking_frames  # noqa: E402

HOME, AWAY = 0, 1


def _validate_tau(tau):
    try:
        valid = math.isfinite(tau) and tau > 0
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError("tau must be finite and strictly positive (metres)")


def min_dist_per_team(ball, players, team_of_slot):
    """Shortest ball-player distance per team. players: list of (slot, x, y).

    Returns (d_home, d_away); math.inf where a team has no visible player.
    """
    best = [math.inf, math.inf]
    bx, by = ball
    for slot, x, y in players:
        d = math.hypot(x - bx, y - by)
        t = team_of_slot[slot]
        if d < best[t]:
            best[t] = d
    return best[HOME], best[AWAY]


def distance_to_score(d, tau):
    """d = inf (no ball / no players) -> 0."""
    _validate_tau(tau)
    return 0.0 if math.isinf(d) else math.exp(-d / tau)


def _metre_position(point):
    if point is None:
        return None
    x, y = point.get("x_m"), point.get("y_m")
    if x is None or y is None or not (math.isfinite(x) and math.isfinite(y)):
        return None
    return x, y


def score_frame(observation, tau=3.0):
    """Return seven named evidence fields without modifying an M3 observation.

    Availability requires a finite ball position and at least one observed finite
    player position on that side. Speed and persistent identities are not needed.
    Unavailable distances are NaN; scores are zero with availability False.
    """
    _validate_tau(tau)
    ball = _metre_position(observation["ball"])
    result = dict(ball_visible=ball is not None, d_home=math.nan, d_away=math.nan,
                  score_home=0.0, score_away=0.0,
                  home_available=False, away_available=False)
    if ball is None:
        return result

    players, team_of_slot = [], []
    available = [False, False]
    for player in observation["players"]:
        position = _metre_position(player) if player["observed"] else None
        if position is None:
            continue
        if player["team"] not in ("H", "A"):
            raise ValueError("observed player team must be H or A")
        team = HOME if player["team"] == "H" else AWAY
        # Local tuple indices adapt the existing helper; they do not identify people.
        players.append((len(team_of_slot), *position))
        team_of_slot.append(team)
        available[team] = True

    distances = min_dist_per_team(ball, players, team_of_slot)
    for team, side in enumerate(("home", "away")):
        if available[team]:
            result[side + "_available"] = True
            result["d_" + side] = distances[team]
            result["score_" + side] = distance_to_score(distances[team], tau)
    return result


def iter_control_scores(tau=3.0, game=GAME, data_dir=None):
    """Yield frame plus the seven evidence fields, retaining no frame history.

    Exhaust this iterator to complete M3's final record-count validation.
    """
    _validate_tau(tau)
    observations = iter_tracking_frames(game=game, data_dir=data_dir)
    try:
        for observation in observations:
            yield dict(frame=observation["frame"], **score_frame(observation, tau))
    finally:
        observations.close()


def build_evidence(tau=3.0, game=GAME, data_dir=None):
    """Build named full-precision arrays indexed by tactical frame, including availability."""
    _validate_tau(tau)
    n_frames = source_frames("tactical", game)
    arrays = {name: np.full(n_frames, np.nan) for name in ("d_home", "d_away")}
    arrays.update({name: np.zeros(n_frames) for name in ("score_home", "score_away")})
    arrays.update({name: np.zeros(n_frames, dtype=bool) for name in (
        "ball_visible", "home_available", "away_available")})
    count = 0
    for count, evidence in enumerate(iter_control_scores(tau, game, data_dir), start=1):
        frame = evidence["frame"]
        if frame != count - 1 or frame >= n_frames:
            raise ValueError("control evidence must have sequential tactical frame indices")
        for name, array in arrays.items():
            array[frame] = evidence[name]
    if count != n_frames:
        raise ValueError("control evidence count does not match tactical frame count")
    return arrays


def build(tau=3.0, game=GAME, data_dir=None):
    """Compatibility five-array tuple; use build_evidence to retain availability."""
    evidence = build_evidence(tau, game, data_dir)
    return (evidence["ball_visible"].astype(np.int8), evidence["d_home"], evidence["d_away"],
            evidence["score_home"], evidence["score_away"])


def write_csv(path, visible, d_home, d_away, s_home, s_away, *,
              home_available=None, away_available=None):
    """Write rounded diagnostics, never canonical inference input.

    Legacy calls retain six columns. Supplying both availability arrays appends two.
    """
    if (home_available is None) != (away_available is None):
        raise ValueError("supply both availability arrays or neither")
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)

    def fmt(v):
        return "" if np.isnan(v) else "{:.3f}".format(v)

    with open(path, "w") as out:
        extra = home_available is not None
        out.write("frame,ball_visible,d_home,d_away,score_home,score_away" +
                  (",home_available,away_available" if extra else "") + "\n")
        for i in range(len(visible)):
            row = "{},{},{},{},{:.4f},{:.4f}".format(
                i, int(visible[i]), fmt(d_home[i]), fmt(d_away[i]), s_home[i], s_away[i])
            if extra:
                row += ",{},{}".format(int(home_available[i]), int(away_available[i]))
            out.write(row + "\n")


def _self_test():
    """The paper example from the task, plus the two 'Done when' properties."""
    ball = (10.0, 10.0)
    players = [(0, 13.0, 14.0), (1, 10.0, 11.0)]
    team = np.array([HOME, AWAY])
    assert min_dist_per_team(ball, players, team) == (5.0, 1.0)
    # swapping the teams swaps the scores
    dh, da = min_dist_per_team(ball, players, team)
    dh2, da2 = min_dist_per_team(ball, players, 1 - team)
    assert (dh2, da2) == (da, dh)
    assert distance_to_score(dh2, 3.0) == distance_to_score(da, 3.0)
    # a missing ball gives neither team an advantage
    assert distance_to_score(math.inf, 3.0) == 0.0
    print("self-test OK")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="control_scores.csv")
    parser.add_argument("--tau", type=float, default=3.0,
                        help="metres at which a score falls to 1/e (default 3)")
    parser.add_argument("--test", action="store_true", help="run the self-test and exit")
    parser.add_argument("--game", choices=sorted(GAMES), default=GAME)
    parser.add_argument("--data-dir", help="bundle root containing tactical/")
    args = parser.parse_args(argv)

    if args.test:
        _self_test()
        return 0

    try:
        evidence = build_evidence(tau=args.tau, game=args.game, data_dir=args.data_dir)
        write_csv(args.out, evidence["ball_visible"], evidence["d_home"], evidence["d_away"],
                  evidence["score_home"], evidence["score_away"],
                  home_available=evidence["home_available"], away_available=evidence["away_available"])
    except (OSError, ValueError) as error:
        print("FAIL  {}".format(error), file=sys.stderr)
        return 1
    print("wrote diagnostic CSV {} ({} frames, ball visible on {})".format(
        args.out, len(evidence["ball_visible"]), int(evidence["ball_visible"].sum())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
