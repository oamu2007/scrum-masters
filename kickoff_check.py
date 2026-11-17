"""Published FAQ semantics diagnostic, never imported by prediction code.

python kickoff_check.py <candidate.csv>
Exit 0: this published interval matches; 2: discrepancy; 1: malformed input.
This is not public-window scoring or a claim of full-match football accuracy.
"""
import argparse
from collections import Counter
import csv
import json
import sys

from games import GAME, half_video_blocks, source_frames

# Explicit FAQ diagnostic reference only. games.py's burned-in clock anchor
# converts to 113741, one frame earlier; do not silently substitute that anchor.
PUBLISHED_SECOND_KICKOFF = 113742


def check(path):
    first = half_video_blocks(GAME)[1][1]
    stop = PUBLISHED_SECOND_KICKOFF
    counts = Counter({k: 0 for k in "HADX"})
    count = 0
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["frame", "label"]:
            raise ValueError("expected frame,label header")
        for index, row in enumerate(reader):
            if row["frame"] != str(index) or row["label"] not in "HADX" or len(row["label"]) != 1:
                raise ValueError("unordered frame or illegal label")
            if first <= index < stop:
                counts[row["label"]] += 1
            count += 1
    if count != source_frames():
        raise ValueError("wrong total frame count")
    return dict(diagnostic="FAQ graded interval before second kickoff", first=first, last=stop-1,
                frames=stop-first, expected_label="D", counts=dict(counts),
                matches_published_semantics=counts["D"] == stop-first,
                scope="Published alignment/semantics diagnostic only; not full-match accuracy")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("candidate")
    args = parser.parse_args()
    try:
        result = check(args.candidate)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["matches_published_semantics"] else 2


if __name__ == "__main__":
    sys.exit(main())
