"""Release procedure for the candidate CSV. Stops at the first failure.

    python run_release.py --gen-cmd "python module1/run.py --out {out}"
    python run_release.py --gen-cmd "..." --expect-sha256 CF1844BF...   (independent reproduction)

Steps, in order. Any failure stops everything and nothing later runs:

  1. make a NEW folder  release/runs/<UTC timestamp>/   (refuses to reuse an existing one, so an
                        old candidate can never be picked up and approved by mistake)
  2. run the full test suite            python -m unittest discover -s tests
  3. run generation (Module 1's command) -- {out} is replaced by the new candidate path
  4. check the file exists, is new, and is non-empty
  5. official validator                 evaluation/validate_submission.py
  6. write evidence.json beside the candidate (tests_ok, generation_ok, SHA-256, start time)
  7. approve_release(): CSV validity AND the gates in release_gates.json

Exit codes: 0 approved, 1 a step failed, 2 everything ran but the release is blocked by gates.
Blocked is not a pass: the file may be valid and still must not be delivered.
"""

import argparse
import datetime
import json
import os
import shlex
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import release_check  # noqa: E402

RUNS_DIR = os.path.join(ROOT, "release", "runs")
CANDIDATE_NAME = "candidate.csv"


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def new_run_dir(runs_dir=RUNS_DIR):
    """Create a folder that did not exist before. exist_ok is False on purpose."""
    path = os.path.join(runs_dir, stamp())
    os.makedirs(path, exist_ok=False)
    return path


def quote(path):
    """Quote one path for the shell, on POSIX and on Windows."""
    return '"{}"'.format(path) if os.name == "nt" else shlex.quote(path)


def run_step(name, command, cwd=ROOT):
    """Run a shell command string. Shell, so the same text works in bash, zsh and cmd."""
    print("\n== {} ==\n$ {}".format(name, command), flush=True)
    return subprocess.run(command, cwd=cwd, shell=True).returncode


def stop(message):
    print("\nSTOP: {}".format(message))
    return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--gen-cmd", required=True,
                        help="Module 1's generation command; {out} = where it must write the CSV")
    parser.add_argument("--runs-dir", default=RUNS_DIR)
    parser.add_argument("--test-cmd", default=None,
                        help="override the test command (used by this tool's own tests)")
    parser.add_argument("--validator", default=os.path.join(ROOT, "evaluation",
                                                            "validate_submission.py"))
    parser.add_argument("--rows", type=int, default=None)
    parser.add_argument("--gates", default=None)
    parser.add_argument("--expect-sha256", default=None)
    args = parser.parse_args(argv)

    started = time.time()
    run_dir = new_run_dir(args.runs_dir)
    out = os.path.join(run_dir, CANDIDATE_NAME)
    print("run folder: {}".format(run_dir))

    if "{out}" not in args.gen_cmd:
        return stop("--gen-cmd must contain {out} so the candidate lands in the fresh folder")

    test_cmd = args.test_cmd or "{} -m unittest discover -s tests".format(quote(sys.executable))
    if run_step("1/4 tests", test_cmd) != 0:
        return stop("tests failed; generation was NOT run and nothing was approved")

    gen_cmd = args.gen_cmd.replace("{out}", quote(out))
    if run_step("2/4 generation", gen_cmd) != 0:
        return stop("generation failed; no candidate to approve")
    if not os.path.isfile(out) or os.path.getsize(out) == 0:
        return stop("generation exited 0 but did not write {}".format(out))
    if os.path.getmtime(out) < started - 1.0:
        return stop("candidate is older than this run (stale file)")

    validate = "{} {} {}".format(quote(sys.executable), quote(args.validator), quote(out))
    if args.rows:
        validate += " --rows {}".format(args.rows)
    if run_step("3/4 official validator", validate) != 0:
        return stop("official validator rejected the candidate")

    problems, info = release_check.check_file(out, n_rows=args.rows,
                                              expect_sha256=args.expect_sha256)
    if problems:
        print("\n== 4/4 release_check ==")
        for problem in problems:
            print("  - " + problem)
        return stop("byte-level / hash check failed")

    evidence = {"tests_ok": True, "generation_ok": True, "candidate_name": CANDIDATE_NAME,
                "candidate_sha256": info["sha256"], "started_at_epoch": started,
                "gen_cmd": args.gen_cmd, "run_dir": run_dir}
    with open(os.path.join(run_dir, release_check.EVIDENCE_NAME), "w", encoding="utf-8") as h:
        json.dump(evidence, h, indent=2, sort_keys=True)

    result = release_check.approve_release(out, gates_path=args.gates, n_rows=args.rows)
    print("\n== release decision ==\nSHA-256  {}".format(info["sha256"]))
    if result["status"] == "APPROVED":
        print("RELEASE APPROVED")
        return 0
    print("CSV VALID, RELEASE NOT APPROVED -- {} blocker(s):".format(len(result["blockers"])))
    for blocker in result["blockers"]:
        print("  - " + blocker)
    return 2


if __name__ == "__main__":
    sys.exit(main())
