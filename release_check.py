"""Final check of a submission file, and the record to paste into module1/RUNNER.md.

    python release_check.py evaluation/results/candidate.csv              (CSV validity only)
    python release_check.py candidate.csv --expect-sha256 CF1844BF...     (reproduction check)
    python release_check.py candidate.csv --release                       (is it approved to ship?)

Two different questions, never mixed:

  1. CSV VALID     check_file(): the official validation (the same function the scorer uses),
                   then the byte-level things the official validator does not look at: exact
                   header, no BOM, LF line endings, final newline, and X outside the two
                   halves. Says nothing about whether the labels come from a finished pipeline.
  2. RELEASE OK    approve_release(): CSV valid AND every gate in release_gates.json is
                   'passed' with written evidence AND the file belongs to a run that
                   run_release.py recorded (fresh folder, tests green, generation green, same
                   SHA-256). A valid CSV with a blocked gate is "VALID BUT NOT APPROVED".

Exit codes: 0 = ok for what was asked, 1 = CSV invalid or release check failed,
2 = CSV valid but release blocked (only with --release).
"""

import argparse
import hashlib
import json
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


# -- release approval (separate from CSV validity) ---------------------------------------------

GATES_FILE = os.path.join(ROOT, "release_gates.json")
EVIDENCE_NAME = "evidence.json"
REQUIRED_GATES = {"M2_integrated", "M4_integrated", "scenarios_with_real_M2_M4",
                  "M1_carries_data", "candidate_frozen", "independent_reproduction",
                  "pinned_environment", "same_machine_repeatability", "submission_approval",
                  "published_kickoff_diagnostic"}


def load_gates(path=None):
    """Gates from release_gates.json. A missing or unreadable file is itself a blocker."""
    path = path or GATES_FILE
    try:
        with open(path, encoding="utf-8") as handle:
            gates = json.load(handle)["gates"]
        if not isinstance(gates, list) or any(not isinstance(g, dict) for g in gates):
            raise ValueError("gates must be a list of records")
        return gates, None
    except Exception as error:
        return [], "cannot read gates file {}: {}".format(path, error)


def gate_blockers(gates):
    """One line per gate that is not genuinely passed. 'passed' without evidence is blocked."""
    out = []
    for gate in gates:
        status = str(gate.get("status", "")).strip().lower()
        if status != "passed":
            out.append("{}: {}".format(gate.get("id", "?"), gate.get("reason") or status or "no status"))
        elif not str(gate.get("evidence", "")).strip():
            out.append("{}: marked passed but has no evidence".format(gate.get("id", "?")))
    return out


def run_blockers(path, info, evidence_path=None):
    """Blockers about *this file*: was it produced by a recorded, green, fresh run?

    The evidence file is written by run_release.py only after tests and generation succeeded,
    and it names the exact SHA-256 and folder. A file approved from an old folder, copied from
    elsewhere, or edited afterwards cannot match it.
    """
    evidence_path = evidence_path or os.path.join(os.path.dirname(os.path.abspath(path)), EVIDENCE_NAME)
    if not os.path.isfile(evidence_path):
        return ["no {} next to the file: it was not produced by run_release.py".format(EVIDENCE_NAME)]
    try:
        with open(evidence_path, encoding="utf-8") as handle:
            evidence = json.load(handle)
    except Exception as error:
        return ["cannot read {}: {}".format(evidence_path, error)]

    out = []
    if not isinstance(evidence, dict):
        return ["run evidence must be an object"]
    if evidence.get("schema_version") != 1 or evidence.get("mode") != "integrated":
        out.append("run is not a recorded integrated pipeline (fallback/fixture/legacy cannot pass)")
    if info.get("rows") != GAMES[GAME]["n_video_frames"] or evidence.get("rows") != GAMES[GAME]["n_video_frames"]:
        out.append("integrated release requires 199319 rows; short fixtures cannot approve release")
    if os.path.normcase(os.path.abspath(evidence.get("run_dir", ""))) != os.path.normcase(os.path.dirname(os.path.abspath(path))):
        out.append("candidate is outside its recorded run directory")
    source = evidence.get("source", {})
    if not isinstance(source, dict) or source.get("clean") is not True or len(str(source.get("sha", ""))) != 40:
        out.append("missing clean source commit identity")
    inputs = evidence.get("inputs", {})
    if not isinstance(inputs, dict) or set(inputs) != {"atd_meta", "atd_raw", "smart_tagging"}:
        out.append("missing exact input identities")
    elif any(not isinstance(v, dict) or len(str(v.get("sha256", ""))) != 64 for v in inputs.values()):
        out.append("invalid input hashes")
    for key in ("environment", "configuration", "pipeline_report"):
        if not isinstance(evidence.get(key), dict) or not evidence[key]:
            out.append("missing " + key)
    if evidence.get("official_validation_ok") is not True:
        out.append("official validation was not recorded as successful")
    commands = evidence.get("commands", [])
    if (not isinstance(commands, list) or len(commands) != 3
            or any(not isinstance(c, dict) or c.get("returncode") != 0 for c in commands)
            or [c.get("step") for c in commands] != ["tests", "generation", "official_validator"]):
        out.append("missing successful required commands")
    report_path = os.path.join(os.path.dirname(os.path.abspath(path)), "pipeline.json")
    if not os.path.isfile(report_path) or sha256_of(report_path) != evidence.get("pipeline_report_sha256"):
        out.append("pipeline report missing or changed")
    if evidence.get("tests_ok") is not True:
        out.append("evidence says the test suite did not pass")
    if evidence.get("generation_ok") is not True:
        out.append("evidence says generation did not succeed")
    if evidence.get("candidate_sha256", "").upper() != info.get("sha256", "").upper():
        out.append("file SHA-256 differs from the one recorded at generation (edited or replaced)")
    if os.path.basename(path) != evidence.get("candidate_name"):
        out.append("file name {!r} is not the generated candidate {!r}".format(
            os.path.basename(path), evidence.get("candidate_name")))
    started = evidence.get("started_at_epoch")
    if not isinstance(started, (float, int)) or isinstance(started, bool) or not np.isfinite(started):
        out.append("missing valid generation start time")
    elif os.path.getmtime(path) < started - 1.0:
        out.append("file is older than the run that supposedly generated it (stale file)")
    return out


def approve_release(path, gates_path=None, evidence_path=None, **check_kwargs):
    """Return dict(status, problems, blockers, info).

    status is one of:
      INVALID               the CSV itself fails check_file()
      VALID_NOT_APPROVED    CSV is fine, but at least one gate or run-evidence blocker remains
      APPROVED              CSV fine, every gate passed with evidence, run evidence matches
    """
    problems, info = check_file(path, **check_kwargs)
    if problems:
        return {"status": "INVALID", "problems": problems, "blockers": [], "info": info}

    gates, gates_error = load_gates(gates_path)
    blockers = [gates_error] if gates_error else gate_blockers(gates)
    blockers += ["missing required gate: " + name for name in sorted(REQUIRED_GATES - {g.get("id") for g in gates})]
    blockers += run_blockers(path, info, evidence_path)
    status = "VALID_NOT_APPROVED" if blockers else "APPROVED"
    return {"status": status, "problems": [], "blockers": blockers, "info": info}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("submission")
    parser.add_argument("--rows", type=int, default=None)
    parser.add_argument("--expect-sha256", default=None)
    parser.add_argument("--release", action="store_true",
                        help="also require every release gate and the run evidence")
    parser.add_argument("--gates", default=None, help="gates JSON (default: release_gates.json)")
    args = parser.parse_args(argv)

    if not args.release:
        problems, info = check_file(args.submission, n_rows=args.rows,
                                    expect_sha256=args.expect_sha256)
        report_info(info)
        if problems:
            print("\nFAIL (CSV invalid)")
            for problem in problems:
                print("  - " + problem)
            return 1
        scope = "FIXTURE CSV VALID" if args.rows is not None else "CSV VALID"
        print("\n" + scope + ("  (hash matches)" if args.expect_sha256 else ""))
        print("(this is NOT release approval; run with --release for that)")
        return 0

    result = approve_release(args.submission, gates_path=args.gates, n_rows=args.rows,
                             expect_sha256=args.expect_sha256)
    report_info(result["info"])
    if result["status"] == "INVALID":
        print("\nFAIL (CSV invalid)")
        for problem in result["problems"]:
            print("  - " + problem)
        return 1
    print("\nCSV VALID")
    if result["status"] == "VALID_NOT_APPROVED":
        print("RELEASE NOT APPROVED -- {} blocker(s):".format(len(result["blockers"])))
        for blocker in result["blockers"]:
            print("  - " + blocker)
        return 2
    print("RELEASE APPROVED")
    return 0


def report_info(info):
    if "sha256" in info:
        print("SHA-256  {}".format(info["sha256"]))
    if "counts" in info:
        print("rows     {}".format(info["rows"]))
        print("labels   " + "  ".join("{} {}".format(k, v) for k, v in info["counts"].items()))


if __name__ == "__main__":
    sys.exit(main())
