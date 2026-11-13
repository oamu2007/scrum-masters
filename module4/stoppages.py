"""Module 4 - evidence for stoppages and restarts (first piece: restart windows from Smart Tagging)."""

# The XML names clubs, but the submission wants a side: H = home (Barcelona), A = away (Athletic).
# "Atletic Club" (one h) is how the file spells it, so we keep both spellings to be safe.
TEAM_TO_SIDE = {
    "barcelona": "H",
    "atletic club": "A",
    "athletic club": "A",
}


def side_from_team_tag(team_tag):
    """'Barcelona' -> 'H', 'Atletic Club' -> 'A', anything else ('N/A', missing...) -> None."""
    if team_tag is None:
        return None
    return TEAM_TO_SIDE.get(team_tag.strip().lower())


def restart_windows(events):
    """Keep only the set pieces (restarts) and describe each one in a simple dictionary.

    `events` is the list that starter/load_smart_tagging.load() returns.
    """
    windows = []
    for event in events:
        code = (event["code"] or "").strip().lower()
        if code != "set pieces":
            continue
        tags = event["tags"]
        windows.append({
            "type": tags.get("Type"),
            "start_frame": event["start_frame"],
            "end_frame": event["end_frame"],
            "side": side_from_team_tag(tags.get("Team")),
        })
    return windows

if __name__ == "__main__":
    import os
    import sys
    # __file__ is this file; two dirname() calls climb up to the repo root
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from starter.load_smart_tagging import load

    windows = restart_windows(load())
    print("restart windows:", len(windows))

    counts = {}
    for w in windows:
        counts[w["type"]] = counts.get(w["type"], 0) + 1
    for restart_type, n in counts.items():
        print("  ", restart_type, n)

    print("first three:")
    for w in windows[:3]:
        print("  ", w)