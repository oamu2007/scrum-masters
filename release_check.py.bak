"""Final check of a submission file, and the record to paste into module1/RUNNER.md.

    python release_check.py evaluation/results/candidate.csv
    python release_check.py candidate.csv --expect-sha256 CF1844BF...   (reproduction check)

It runs the official validation (the same function the scorer uses), then the byte-level things
the official validator does not look at: exact header, no BOM, LF line endings, final newline,
and X only outside the two halves. Exit code 0 = everything passed, 1 = something failed.
"""

import argparse
import hashlib
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
for path in (os.path.join(ROOT, "evaluation"), ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

import possession_metrics as pm  # noqa: E402
from games import GAME, GAMES, half_video_blocks  # noqa: E402


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def check_file(path, n_rows=None, blocks=None, expect_sha256=None, require_x_outside=True):
    """Return (problems, info). problems is a list of one-line strings; empty means all good."""
    n_rows = n_rows if n_rows is not None else GAMES[GAME]["n_video_frames"]
    problems, info = [], {}
    if not os.path.isfile(path):
        return ["no such file: {}".format(path)], info

    info["sha256"] = sha256_of(path)
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append("file starts with a UTF-8 BOM")
    if b"\r" in raw:
        problems.append("file has CR characters (CRLF line endings)")
    if not raw.endswith(b"\n"):
        problems.append("file does not end with a newline")
    first_line = raw.lstrip(b"\xef\xbb\xbf").split(b"\n", 1)[0].rstrip(b"\r")
    if first_line != b"frame,label":
        problems.append("header is {!r}, expected b'frame,label'".format(first_line))

    try:
        table = pm.read_label_csv(path)
    except Exception as error:
        return problems + ["could not read: {}".format(error)], info
    reason = pm.validate_submission(table, n_rows)
    if reason:
        return problems + ["official validation: {}".format(reason)], info

    labels = pm.label_codes(table)
    info["rows"] = len(labels)
    info["counts"] = {name: int(np.sum(labels == k)) for k, name in enumerate(pm.LABELS)}

    blocks = blocks if blocks is not None else half_video_blocks(GAME)
    inside = np.zeros(len(labels), dtype=bool)
    for _, first, last in blocks:
        inside[first:last + 1] = True
    if require_x_outside:
        bad = int(np.sum(labels[~inside] != pm.X))
        if bad:
            problems.append("{} frames outside the halves are not X".format(bad))

    if expect_sha256 is not None and info["sha256"] != expect_sha256.strip().upper():
        problems.append("SHA-256 {} != expected {}".format(
            info["sha256"], expect_sha256.strip().upper()))
    return problems, info


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("submission")
    parser.add_argument("--rows", type=int, default=None)
    parser.add_argument("--expect-sha256", default=None)
    args = parser.parse_args(argv)

    problems, info = check_file(args.submission, n_rows=args.rows,
                                expect_sha256=args.expect_sha256)
    if "sha256" in info:
        print("SHA-256  {}".format(info["sha256"]))
    if "counts" in info:
        print("rows     {}".format(info["rows"]))
        print("labels   " + "  ".join("{} {}".format(k, v) for k, v in info["counts"].items()))
    if problems:
        print("\nFAIL")
        for problem in problems:
            print("  - " + problem)
        return 1
    print("\nOK" + ("  (hash matches)" if args.expect_sha256 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
