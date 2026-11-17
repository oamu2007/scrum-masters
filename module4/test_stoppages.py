from stoppages import side_from_team_tag, restart_windows

# --- side_from_team_tag ---
assert side_from_team_tag("Barcelona") == "H"
assert side_from_team_tag("Atletic Club") == "A"
assert side_from_team_tag("N/A") is None
assert side_from_team_tag(None) is None

# --- restart_windows, with invented tags ---
fake_events = [
    {"code": "BUILD UP", "start_frame": 100, "end_frame": 400,
     "tags": {"Team": "Barcelona"}},
    {"code": "SET PIECES", "start_frame": 500, "end_frame": 625,
     "tags": {"Team": "N/A", "Type": "Throw-in"}},
    {"code": "SET PIECES", "start_frame": 900, "end_frame": 1025,
     "tags": {"Team": "Atletic Club", "Type": "Corner Kick"}},
]
windows = restart_windows(fake_events)
assert len(windows) == 2                      # the BUILD UP is ignored
assert windows[0]["type"] == "Throw-in"
assert windows[0]["side"] is None             # unknown team stays unknown
assert windows[1]["side"] == "A"

print("all tests passed")