"""Module 1 - which team looks in control.

For every video frame, writes two scores in [0, 1]: one for Barcelona (home) and one for
Athletic (away). The score of a team is exp(-d / tau), where d is the distance in metres from the
ball to that team's nearest tracked player. No ball -> both scores 0 (nobody gets an advantage).

Place this file at <repo>/module1/control_scores.py and run from the repo root:

    python module1/control_scores.py --out control_scores.csv

Output columns:  frame, ball_visible, d_home, d_away, score_home, score_away
  - frame is the video frame / submission row (0-based), as everywhere else in the project.
  - d_* are in metres, empty when there is no ball or no tracked player for that team.
  - ball_visible (0/1) lets Module 2 tell "no ball" apart from "ball far from everyone".
"""

import argparse
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE if os.path.exists(os.path.join(HERE, "games.py")) else os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "starter"))

from games import GAME, GAMES, require, source_frames  # noqa: E402
from baseline import team_of_each_track  # noqa: E402  (0 = home slot, 1 = away slot)

FIELD_SEP = ":"
GROUP_SEP = ";"
MISSING = "N"  # first letter of "NaN"
HOME, AWAY = 0, 1


def parse_xy(group, length, width):
    """'x,y,speed' (normalised) -> (x_m, y_m), or None if missing."""
    if group[0] == MISSING:
        return None
    c1 = group.index(",")
    c2 = group.index(",", c1 + 1)
    return float(group[:c1]) * length, float(group[c1 + 1:c2]) * width


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
    return 0.0 if math.isinf(d) else math.exp(-d / tau)


def build(tau=3.0, game=GAME, data_dir=None):
    meta_path, raw_path = require(["atd_meta", "atd_raw"], game, data_dir)
    n_frames = source_frames("tactical", game)
    length, width = GAMES[game]["pitch"]
    team_of_slot = team_of_each_track(meta_path)

    d_home = np.full(n_frames, np.nan)
    d_away = np.full(n_frames, np.nan)
    visible = np.zeros(n_frames, dtype=np.int8)
    s_home = np.zeros(n_frames)
    s_away = np.zeros(n_frames)

    with open(raw_path) as handle:
        for line in handle:
            parts = line.split(FIELD_SEP)
            if len(parts) != 3:
                continue
            frame = int(parts[0]) - 1  # frame_id counts from 1, submission from 0
            ball = parse_xy(parts[2], length, width)
            if ball is None:
                continue  # no ball: scores stay 0/0, distances NaN

            players = []
            for slot, group in enumerate(parts[1].split(GROUP_SEP)):
                xy = parse_xy(group, length, width)
                if xy is not None:
                    players.append((slot, xy[0], xy[1]))

            dh, da = min_dist_per_team(ball, players, team_of_slot)
            visible[frame] = 1
            if not math.isinf(dh):
                d_home[frame] = dh
            if not math.isinf(da):
                d_away[frame] = da
            s_home[frame] = distance_to_score(dh, tau)
            s_away[frame] = distance_to_score(da, tau)

    return visible, d_home, d_away, s_home, s_away


def write_csv(path, visible, d_home, d_away, s_home, s_away):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)

    def fmt(v):
        return "" if np.isnan(v) else "{:.3f}".format(v)

    with open(path, "w") as out:
        out.write("frame,ball_visible,d_home,d_away,score_home,score_away\n")
        for i in range(len(visible)):
            out.write("{},{},{},{},{:.4f},{:.4f}\n".format(
                i, visible[i], fmt(d_home[i]), fmt(d_away[i]), s_home[i], s_away[i]))


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="control_scores.csv")
    parser.add_argument("--tau", type=float, default=3.0,
                        help="metres at which a score falls to 1/e (default 3)")
    parser.add_argument("--test", action="store_true", help="run the self-test and exit")
    args = parser.parse_args()

    if args.test:
        _self_test()
        sys.exit(0)

    arrays = build(tau=args.tau)
    write_csv(args.out, *arrays)
    seen = int(arrays[0].sum())
    print("wrote {} ({} frames, ball visible on {})".format(args.out, len(arrays[0]), seen))
