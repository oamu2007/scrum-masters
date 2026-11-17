"""Conservative tracking evidence, not possession labels. See EVIDENCE.md.

Run ``python -m module4.evidence --data-dir <bundle>`` for an aggregate-only scan.
"""

import argparse
from collections import deque
from dataclasses import asdict, dataclass
import json
import math

from games import GAME, GAMES, half_video_blocks, source_frames
from module4.stoppages import restart_windows
from starter.load_smart_tagging import load
from starter.tactical_tracking import iter_tracking_frames


@dataclass(frozen=True)
class EvidenceConfig:
    boundary_margin_m: float = 1.5
    nearby_radius_m: float = 20.0
    min_nearby_players: int = 3
    motion_window_s: float = 0.20
    min_motion_s: float = 0.08
    max_ball_gap_s: float = 0.20
    ball_slow_mps: float = 0.7
    player_slow_mps: float = 1.5
    player_active_mps: float = 2.0
    collective_fraction: float = 2 / 3
    pause_s: float = 0.40
    restart_memory_s: float = 3.0
    restart_ball_mps: float = 2.0
    restart_displacement_m: float = 0.8
    boundary_dead_weight: float = 0.65
    tag_dead_weight: float = 0.15
    pause_anchor_score: float = 0.50
    movement_restart_weight: float = 0.80
    tag_restart_weight: float = 0.10

    def __post_init__(self):
        for name, value in asdict(self).items():
            if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                raise ValueError(name + " must be finite and positive")
        if not isinstance(self.min_nearby_players, int):
            raise ValueError("min_nearby_players must be an integer")
        for name in ("collective_fraction", "pause_anchor_score"):
            if getattr(self, name) > 1:
                raise ValueError(name + " must be <= 1")
        if self.min_motion_s > self.motion_window_s:
            raise ValueError("min_motion_s must be <= motion_window_s")
        if self.player_slow_mps >= self.player_active_mps:
            raise ValueError("slow player threshold must be below active threshold")
        if self.ball_slow_mps >= self.restart_ball_mps:
            raise ValueError("slow ball threshold must be below restart threshold")
        for names in (("boundary_dead_weight", "tag_dead_weight"),
                      ("movement_restart_weight", "tag_restart_weight")):
            if sum(getattr(self, name) for name in names) > 1:
                raise ValueError("feature weights must sum to <= 1")


def _position(point):
    if point is None:
        return None
    x, y = point.get("x_m"), point.get("y_m")
    if x is None or y is None or not math.isfinite(x) or not math.isfinite(y):
        return None
    return x, y


def _empty():
    return dict(dead_score=0.0, dead_available=False,
                restart_score=0.0, restart_available=False, restart_side=None)


class StoppageEvidence:
    """Instance-owned bounded history; call ``producer(index, observation)``.

    Calls must be contiguous and agree with observation['frame'] and ['time_s'].
    The first call may start partway through a match with fresh history. Observations
    and windows are read-only; returned mappings are independent. No global store.
    """

    def __init__(self, windows=(), *, game=GAME, config=None):
        self.config = config if config is not None else EvidenceConfig()
        self.fps = GAMES[game]["fps"]
        self.pitch = GAMES[game]["pitch"]
        self.n_frames = source_frames("tactical", game)
        self.halves = tuple(half_video_blocks(game))  # inclusive games.py blocks
        self.windows = []
        for window in windows:
            start, end, side = (window[k] for k in ("start_frame", "end_frame", "side"))
            if (type(start) is not int or type(end) is not int or end < start
                    or side not in ("H", "A", None)):
                raise ValueError("invalid half-open restart window")
            self.windows.append((start, end, side))
        self.windows = tuple(self.windows)
        self.history = deque(maxlen=math.ceil(self.config.motion_window_s * self.fps) + 2)
        self.reset()

    def reset(self):
        """Start an independent sequence (also resets order validation)."""
        self.last_index = None
        self.half = None
        self._clear_motion()

    def _clear_motion(self):
        self.history.clear()
        self.pause_since = None
        self.anchor = None  # (time_s, x_m, y_m); evidence memory, not a D state

    def __call__(self, index, observation):
        if (type(index) is not int or not 0 <= index < self.n_frames
                or type(observation.get("frame")) is not int
                or observation["frame"] != index):
            raise ValueError("index must match the tactical observation frame")
        if self.last_index is not None and index != self.last_index + 1:
            raise ValueError("M4 requires contiguous ordered frames")
        t = observation.get("time_s")
        if (t is None or not math.isfinite(t)
                or not math.isclose(t, index / self.fps, abs_tol=1e-8, rel_tol=0)):
            raise ValueError("time_s must equal frame / configured fps")
        self.last_index = index
        half = next((h for h, first, last in self.halves if first <= index <= last), None)
        if half != self.half or half is None:
            self._clear_motion()
            self.half = half
        result = _empty()
        if half is None:
            return result

        active_sides = [side for start, end, side in self.windows if start <= index < end]
        tagged = bool(active_sides)
        # Unknown or conflicting simultaneous tags do not become a known side.
        sides = set(active_sides)
        if len(sides) == 1 and None not in sides:
            result["restart_side"] = active_sides[0]
        c = self.config
        if self.anchor is not None and t - self.anchor[0] > c.restart_memory_s:
            self.anchor = None

        ball = _position(observation.get("ball"))
        if ball is None:
            self.pause_since = None
            return result  # no positive evidence from disappearance or tag alone
        if self.history and t - self.history[-1][0] > c.max_ball_gap_s + 1e-9:
            self.history.clear()
            self.pause_since = None
        self.history.append((t, *ball))
        while self.history and t - self.history[0][0] > c.motion_window_s + 1e-9:
            self.history.popleft()
        dt = t - self.history[0][0]
        ball_speed = None
        if len(self.history) >= 2 and dt + 1e-9 >= c.min_motion_s:
            # Observed path length / elapsed seconds, including short missing gaps.
            # No invented sample, and a long gap starts a new motion history.
            ball_speed = sum(math.hypot(b[1] - a[1], b[2] - a[2])
                             for a, b in zip(self.history, list(self.history)[1:])) / dt

        speeds = []
        for player in observation.get("players", ()):
            pos = _position(player)
            speed = player.get("speed_mps")
            if (player.get("observed") is True and pos is not None
                    and speed is not None and math.isfinite(speed) and speed >= 0
                    and math.dist(ball, pos) <= c.nearby_radius_m):
                speeds.append(speed)  # already m/s; no slot trajectories
        if ball_speed is None or len(speeds) < c.min_nearby_players:
            self.pause_since = None
            return result

        result["dead_available"] = True
        slow = sum(speed <= c.player_slow_mps for speed in speeds) / len(speeds)
        active = sum(speed >= c.player_active_mps for speed in speeds) / len(speeds)
        x, y = ball
        edge = min(x, self.pitch[0] - x, y, self.pitch[1] - y)
        boundary = max(0.0, min(1.0, (c.boundary_margin_m - edge) / c.boundary_margin_m))
        pause = (ball_speed <= c.ball_slow_mps and slow >= c.collective_fraction
                 and (boundary > 0 or tagged))
        if pause:
            if self.pause_since is None:
                self.pause_since = t
            if t - self.pause_since + 1e-9 >= c.pause_s:
                result["dead_score"] = (c.boundary_dead_weight * boundary
                                        + c.tag_dead_weight * tagged) * slow
                if result["dead_score"] >= c.pause_anchor_score:
                    self.anchor = (t, x, y)
        else:
            self.pause_since = None

        # Availability needs an observed supported pause in recent same-half history.
        result["restart_available"] = self.anchor is not None
        if (self.anchor is not None and edge >= 0 and ball_speed >= c.restart_ball_mps
                and math.dist(ball, self.anchor[1:]) >= c.restart_displacement_m
                and active >= c.collective_fraction):
            result["restart_score"] = (c.movement_restart_weight * active
                                       + c.tag_restart_weight * tagged)
        return result


def iter_stoppage_evidence(*, game=GAME, data_dir=None, config=None, windows=None):
    """Stream ``frame`` plus the five fields, retaining every tactical frame.

    None windows loads automatic tags; () disables them. Exhaust for count validation.
    Closing this generator closes M3. Only compact M4 history is retained.
    """
    if windows is None:
        windows = restart_windows(load(game=game, data_dir=data_dir))
    producer = StoppageEvidence(windows, game=game, config=config)
    source = iter_tracking_frames(game=game, data_dir=data_dir)
    count = 0
    try:
        for index, observation in enumerate(source):
            yield dict(frame=index, **producer(index, observation))
            count += 1
        if count != producer.n_frames:
            raise ValueError("expected {} tactical frames, read {}".format(producer.n_frames, count))
    finally:
        close = getattr(source, "close", None)
        if close:
            close()


def build_evidence(*, game=GAME, data_dir=None, config=None, windows=None):
    """Five aligned NumPy arrays; float64 scores, bool flags, object H/A/None sides."""
    import numpy as np

    n = source_frames("tactical", game)
    fields = {"dead_score": np.zeros(n), "dead_available": np.zeros(n, dtype=bool),
              "restart_score": np.zeros(n), "restart_available": np.zeros(n, dtype=bool),
              "restart_side": np.full(n, None, dtype=object)}
    for row in iter_stoppage_evidence(game=game, data_dir=data_dir, config=config, windows=windows):
        for name, array in fields.items():
            array[row["frame"]] = row[name]
    return fields


def check_stream(*, game=GAME, data_dir=None):
    """Exhaust real M3 -> M4, assert the contract, return only aggregate diagnostics."""
    counts = {"frames": 0, "dead_available": 0, "restart_available": 0,
              "dead_positive": 0, "restart_positive": 0,
              "side_H": 0, "side_A": 0, "side_unknown": 0}
    ranges = {name: [1.0, 0.0] for name in ("dead_score", "restart_score")}
    for index, row in enumerate(iter_stoppage_evidence(game=game, data_dir=data_dir)):
        if row["frame"] != index:
            raise ValueError("unordered evidence")
        for prefix in ("dead", "restart"):
            score, available = row[prefix + "_score"], row[prefix + "_available"]
            if (type(available) is not bool or not math.isfinite(score) or not 0 <= score <= 1
                    or (not available and score != 0)):
                raise ValueError("invalid score/availability")
            counts[prefix + "_available"] += available
            counts[prefix + "_positive"] += score > 0
            ranges[prefix + "_score"][0] = min(ranges[prefix + "_score"][0], score)
            ranges[prefix + "_score"][1] = max(ranges[prefix + "_score"][1], score)
        side = row["restart_side"]
        if side not in ("H", "A", None):
            raise ValueError("illegal restart side")
        counts["side_" + (side or "unknown")] += 1
        counts["frames"] += 1
    if counts["frames"] != source_frames("tactical", game):
        raise ValueError("wrong evidence count")
    return dict(counts, score_ranges=ranges, config=asdict(EvidenceConfig()))


def main():
    parser = argparse.ArgumentParser(description="M4 aggregate-only full-stream contract check")
    parser.add_argument("--data-dir", default=None, help="bundle root containing tactical/")
    parser.add_argument("--game", default=GAME)
    args = parser.parse_args()
    print(json.dumps(check_stream(game=args.game, data_dir=args.data_dir), sort_keys=True))


if __name__ == "__main__":
    main()
