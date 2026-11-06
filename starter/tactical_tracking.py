"""Stream validated tactical ATD observations using only the standard library.

See TACTICAL_TRACKING.md for the dictionary fields and consumer examples.
Full-length validation finishes only when the iterator is exhausted.
"""

import argparse
import math
import os
import sys
import xml.etree.ElementTree as ET

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from games import GAME, GAMES, require, source_frames


class TrackingDataError(ValueError):
    """Invalid metadata or tracking, reported without including source rows."""


def _read_slot_teams(meta_path):
    """Team for each raw column, in XML Player document order (as in baseline.py)."""
    try:
        root = ET.parse(meta_path).getroot()
    except ET.ParseError as error:
        raise TrackingDataError(
            "{}: malformed XML at line {}, column {}".format(meta_path, *error.position)
        ) from None

    team_ids = [team.get("id") for team in root.iter("Team")]
    if len(team_ids) != 2 or any(not team_id for team_id in team_ids):
        raise TrackingDataError("{}: expected two Team entries with nonempty IDs".format(meta_path))
    if len(set(team_ids)) != 2:
        raise TrackingDataError("{}: duplicate Team IDs".format(meta_path))
    # The first Team is home, the second away, following the supplied EPTS convention.
    sides = dict(zip(team_ids, ("H", "A")))
    slot_teams = []
    for slot, player in enumerate(root.iter("Player"), start=1):
        team_id = player.get("teamId")
        if team_id not in sides:
            raise TrackingDataError(
                "{}: Player slot {} has a missing or unknown teamId".format(meta_path, slot)
            )
        slot_teams.append(sides[team_id])
    if not slot_teams:
        raise TrackingDataError("{}: no Player track slots".format(meta_path))
    return slot_teams


def _parse_observation(group, pitch, context):
    fields = group.split(",")
    if len(fields) != 3:
        raise TrackingDataError("{}: expected x,y,speed (three fields)".format(context))
    try:
        x, y, speed = (float(field) for field in fields)
    except ValueError:
        raise TrackingDataError("{}: invalid numeric field".format(context)) from None

    observed = math.isfinite(x) and math.isfinite(y)
    if not observed:
        x = y = None
    return {
        "x_norm": x,
        "y_norm": y,
        "x_m": x * pitch[0] if observed else None,
        "y_m": y * pitch[1] if observed else None,
        "speed_mps": speed if math.isfinite(speed) else None,
        "observed": observed,
    }


def _iter_frames(meta_path, raw_path, expected_count, fps, pitch):
    """Internal entry point allowing small invented files in tests."""
    slot_teams = _read_slot_teams(meta_path)
    record = 0
    # Decode per record so even encoding errors identify the offending line safely.
    with open(raw_path, "rb") as handle:
        for record, raw_line in enumerate(handle, start=1):
            context = "{}: record {}".format(raw_path, record)
            if record > expected_count:
                raise TrackingDataError("{}: extra record, expected {} total".format(
                    context, expected_count))
            try:
                line = raw_line.decode("utf-8-sig")
            except UnicodeDecodeError:
                raise TrackingDataError("{}: invalid UTF-8 encoding".format(context)) from None
            parts = line.strip().split(":")
            if len(parts) != 3:
                raise TrackingDataError("{}: expected frame:players:ball".format(context))
            id_text = parts[0].strip()
            if not id_text.isascii() or not id_text.isdecimal():
                raise TrackingDataError("{}: frame ID must be a positive integer".format(context))
            try:
                frame_id = int(id_text)
            except ValueError:
                raise TrackingDataError("{}: frame ID is too large".format(context)) from None
            if frame_id != record:
                raise TrackingDataError("{}: expected tracking frame ID {} in sequence".format(
                    context, record))

            groups = parts[1].split(";")
            if len(groups) != len(slot_teams):
                raise TrackingDataError("{}: found {} player slots, metadata requires {}".format(
                    context, len(groups), len(slot_teams)))
            players = []
            for slot, (team, group) in enumerate(zip(slot_teams, groups), start=1):
                player = _parse_observation(group, pitch, "{}: player slot {}".format(context, slot))
                player.update(track_slot=slot, team=team)
                players.append(player)
            ball = _parse_observation(parts[2], pitch, "{}: ball".format(context))
            if ball["observed"]:
                ball = {key: ball[key] for key in ("x_norm", "y_norm", "x_m", "y_m")}
            else:
                ball = None
            yield {"frame": record - 1, "time_s": (record - 1) / fps,
                   "players": players, "ball": ball}

    if record != expected_count:
        raise TrackingDataError("{}: record {} (end of file): found {} records, expected {}".format(
            raw_path, record + 1, record, expected_count))


def iter_tracking_frames(game=GAME, data_dir=None):
    """Yield fresh dictionaries for every tactical frame, including non-playing periods.

    track_slot is the one-based position in XML Player order, stable within this export.
    Missing positions have all four coordinates None. Speed is independently nullable.
    ball is None when either coordinate is nonfinite. Finite coordinates are not clamped.
    Errors are raised during iteration. Exhaust the iterator to verify the final count.
    """
    meta_path, raw_path = require(["atd_meta", "atd_raw"], game, data_dir, source="tactical")
    config = GAMES[game]
    yield from _iter_frames(meta_path, raw_path, source_frames("tactical", game),
                            config["fps"], config["pitch"])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate tactical tracking and print aggregates.")
    parser.add_argument("--game", default=GAME, choices=sorted(GAMES))
    parser.add_argument("--data-dir", help="bundle root containing tactical/ (default from games.py)")
    args = parser.parse_args(argv)
    count = ball_count = observed_players = slots = 0
    try:
        for frame in iter_tracking_frames(args.game, args.data_dir):
            count += 1
            ball_count += frame["ball"] is not None
            slots = len(frame["players"])
            observed_players += sum(player["observed"] for player in frame["players"])
    except (TrackingDataError, OSError) as error:
        print("FAIL  {}".format(error), file=sys.stderr)
        return 1
    print("OK  {} tactical: {} frames, indices 0..{}, {} slots per frame".format(
        args.game, count, count - 1, slots))
    print("Ball observed: {} / {} ({:.1f}%)".format(ball_count, count, 100 * ball_count / count))
    print("Mean observed players per frame: {:.2f}".format(observed_players / count))
    print("Frame rate: {} fps; pitch: {} x {} m".format(
        GAMES[args.game]["fps"], *GAMES[args.game]["pitch"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
