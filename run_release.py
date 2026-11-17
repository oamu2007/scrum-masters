"""Fresh integrated generation, official validation and provenance; separate approval gates.

Canonical: python run_release.py --data-dir <licensed-bundle>
Repeat: add --expect-sha256 <first-output-hash>, in a fresh process.
Exit 0: approved; 1: required step failed; 2: generated/valid but approval blocked.
Custom commands and short rows require --fixture-mode and can NEVER approve a release.
"""

import argparse
from dataclasses import asdict
import datetime
import importlib.metadata
import json
import os
import platform
import shlex
import subprocess
import sys
import time

import release_check
from games import GAME, asset_paths, half_video_blocks, source_frames
from run_possession import integrated_modules

ROOT = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.join(ROOT, "data", "release", "runs")
CANDIDATE_NAME = "candidate.csv"


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def new_run_dir(runs_dir=RUNS_DIR):
    path = os.path.abspath(os.path.join(runs_dir, stamp()))
    os.makedirs(path, exist_ok=False)
    return path


def quote(path):
    return '"{}"'.format(path) if os.name == "nt" else shlex.quote(path)


def run_step(name, command, cwd=ROOT, log_path=None):
    """Real release commands are argv lists, using this interpreter without a shell."""
    print("\n{}: {}".format(name, command), flush=True)
    if log_path:
        with open(log_path, "w", encoding="utf-8") as log:
            return subprocess.run(command, cwd=cwd, shell=isinstance(command, str),
                                  stdout=log, stderr=subprocess.STDOUT).returncode
    return subprocess.run(command, cwd=cwd, shell=isinstance(command, str)).returncode


def stop(message):
    print("STOP: " + message)
    return 1


def source_identity():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    if git("status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("Commit intended source/configuration first; release requires a clean checkout")
    return dict(sha=git("rev-parse", "HEAD"), branch=git("branch", "--show-current"), clean=True)


def input_identity(game, data_dir):
    paths = asset_paths(game=game, data_dir=data_dir)
    return {key: dict(path=os.path.abspath(paths[key]), bytes=os.path.getsize(paths[key]),
                      sha256=release_check.sha256_of(paths[key]))
            for key in ("atd_meta", "atd_raw", "smart_tagging")}


def environment_identity():
    return dict(python=platform.python_version(), executable=sys.executable,
                platform=platform.platform(), packages={name: importlib.metadata.version(name)
                    for name in ("numpy", "pandas", "python-dateutil", "tzdata")},
                threads={name: os.environ.get(name) for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--game", default=GAME)
    parser.add_argument("--tau", type=float, default=3.)
    parser.add_argument("--runs-dir", default=RUNS_DIR)
    parser.add_argument("--expect-sha256", default=None)
    parser.add_argument("--gates", default=None)
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--gen-cmd", help="fixture-only command with {out}")
    parser.add_argument("--test-cmd", default=None, help="fixture-only override")
    parser.add_argument("--validator", default=None, help="fixture-only override")
    parser.add_argument("--rows", type=int, default=None, help="fixture-only length")
    args = parser.parse_args(argv)
    overrides = (args.gen_cmd, args.test_cmd, args.validator, args.rows)
    if not args.fixture_mode and any(value is not None for value in overrides):
        return stop("custom commands/rows require --fixture-mode; fixtures cannot pass integrated gates")
    if args.fixture_mode and (not args.gen_cmd or "{out}" not in args.gen_cmd):
        return stop("fixture --gen-cmd must contain {out}")
    started = time.time()
    run_dir = new_run_dir(args.runs_dir)
    out = os.path.join(run_dir, CANDIDATE_NAME)
    report_path = os.path.join(run_dir, "pipeline.json")
    print("run folder: " + run_dir, flush=True)
    commands = []
    try:
        if not args.fixture_mode:
            m2, m4 = integrated_modules()
            source = source_identity()
            inputs = input_identity(args.game, args.data_dir)
            environment = environment_identity()
            config = dict(game=args.game, tau=args.tau, half_blocks=half_video_blocks(args.game),
                          m2=asdict(m2.CONFIG_M2), m4=asdict(m4.EvidenceConfig()))
        test_cmd = args.test_cmd or [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]
        gen_cmd = (args.gen_cmd.replace("{out}", quote(out)) if args.fixture_mode else
                   [sys.executable, "-B", os.path.join(ROOT, "run_possession.py"), "--mode", "integrated",
                    "--out", out, "--report", report_path, "--game", args.game, "--tau", str(args.tau)])
        if not args.fixture_mode and args.data_dir is not None:
            gen_cmd += ["--data-dir", os.path.abspath(args.data_dir)]
        validator = args.validator or os.path.join(ROOT, "evaluation", "validate_submission.py")
        validate_cmd = [sys.executable, "-B", validator, out]
        if args.rows is not None:
            validate_cmd += ["--rows", str(args.rows)]
        for name, command in (("tests", test_cmd), ("generation", gen_cmd), ("official_validator", validate_cmd)):
            log_path = os.path.join(run_dir, name + ".log")
            code = run_step(name, command, log_path=log_path)
            commands.append(dict(step=name, argv=command, returncode=code, log=log_path))
            if code != 0:
                return stop(name + " failed; no successful run evidence written (see " + log_path + ")")
            if name == "generation" and (not os.path.isfile(out) or os.path.getsize(out) == 0
                                            or os.path.getmtime(out) < started - 1.):
                return stop("generation did not create a fresh nonempty candidate")
        problems, info = release_check.check_file(out, n_rows=args.rows, expect_sha256=args.expect_sha256)
        if problems:
            return stop("; ".join(problems))
        record = dict(schema_version=1, tests_ok=True, generation_ok=True, official_validation_ok=True,
                      candidate_name=CANDIDATE_NAME, candidate_sha256=info["sha256"],
                      started_at_epoch=started, run_dir=run_dir, rows=info["rows"], commands=commands,
                      mode="fixture" if args.fixture_mode else "integrated")
        if not args.fixture_mode:
            if source_identity() != source or input_identity(args.game, args.data_dir) != inputs:
                return stop("source or inputs changed during generation")
            with open(report_path, encoding="utf-8") as handle:
                report = json.load(handle)
            if (report["mode"] != "integrated" or report["rows"] != source_frames("tactical", args.game)
                    or report["m2_config"] != config["m2"] or report["m4_config"] != config["m4"]
                    or report["game"] != args.game or report["tau"] != args.tau
                    or report["half_blocks"] != [list(b) for b in config["half_blocks"]]
                    or report["counts"] != info["counts"]):
                return stop("runner report does not match integrated configuration")
            record.update(source=source, inputs=inputs, environment=environment, configuration=config,
                          pipeline_report=report, pipeline_report_sha256=release_check.sha256_of(report_path),
                          same_machine_expected_hash=args.expect_sha256)
        with open(os.path.join(run_dir, release_check.EVIDENCE_NAME), "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
        result = release_check.approve_release(out, gates_path=args.gates, n_rows=args.rows)
        print("CSV VALID; fresh generation succeeded; SHA-256 " + info["sha256"])
        if result["status"] == "APPROVED":
            print("RELEASE APPROVED")
            return 0
        print("RELEASE NOT APPROVED:")
        for blocker in result["blockers"]:
            print("  - " + blocker)
        return 2
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        return stop(str(error))


if __name__ == "__main__":
    sys.exit(main())
