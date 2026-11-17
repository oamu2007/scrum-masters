"""Fail-closed release orchestration, including real failed subprocesses."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import release_check as rc
import run_release as rr
from test_release_gates import make_candidate, gates_file


class IntegratedReleaseTests(unittest.TestCase):
    def test_failed_regeneration_cannot_adopt_an_old_or_new_stale_CSV(self):
        with tempfile.TemporaryDirectory() as folder:
            old = make_candidate(folder)
            before = Path(old).read_bytes()
            failed = Path(folder) / "fails.py"
            failed.write_text("import sys\nfrom pathlib import Path\nPath(sys.argv[1]).write_text('frame,label\\n0,X\\n')\nsys.exit(7)\n")
            runs = Path(folder) / "runs"
            code = rr.main(["--fixture-mode", "--runs-dir", str(runs), "--rows", "1",
                            "--test-cmd", rr.quote(rr.sys.executable) + " -c pass",
                            "--gen-cmd", rr.quote(rr.sys.executable) + " " + rr.quote(str(failed)) + " {out}"])
            self.assertEqual(code, 1)
            self.assertEqual(Path(old).read_bytes(), before)
            self.assertEqual(list(runs.rglob("evidence.json")), [])
            generated = next(runs.rglob("candidate.csv"))
            self.assertTrue(rc.run_blockers(str(generated), {"sha256": rc.sha256_of(generated), "rows": 1}))
            self.assertTrue((generated.parent / "generation.log").is_file())

    def test_fallback_custom_test_validator_or_short_rows_cannot_be_release_commands(self):
        for override in (["--gen-cmd", "python run_possession.py --mode fallback --out {out}"],
                         ["--test-cmd", "echo success"], ["--validator", "fake.py"], ["--rows", "1"]):
            with self.subTest(override=override), patch.object(rr, "new_run_dir") as create:
                self.assertEqual(rr.main(override), 1)
                create.assert_not_called()

    def test_empty_gate_list_cannot_approve(self):
        with tempfile.TemporaryDirectory() as folder:
            path = make_candidate(folder)
            gates = gates_file(folder, statuses=())
            result = rc.approve_release(path, gates_path=gates, n_rows=14, blocks=[(1, 2, 11)])
            self.assertEqual(result["status"], "VALID_NOT_APPROVED")
            self.assertTrue(any("independent_reproduction" in b for b in result["blockers"]))

    def test_full_manifest_is_bound_to_mode_input_config_environment_and_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "candidate.csv"
            path.write_text("frame,label\n" + "".join(f"{i},X\n" for i in range(199319)), encoding="utf-8", newline="\n")
            report = Path(folder) / "pipeline.json"
            report.write_text('{"mode": "integrated", "rows": 199319}')
            record = dict(schema_version=1, mode="integrated", rows=199319, tests_ok=True,
                          generation_ok=True, official_validation_ok=True, candidate_name=path.name,
                          candidate_sha256=rc.sha256_of(path), started_at_epoch=path.stat().st_mtime - 1,
                          run_dir=folder, source=dict(sha="a" * 40, clean=True),
                          inputs={k: dict(sha256="b" * 64) for k in ("atd_meta", "atd_raw", "smart_tagging")},
                          environment=dict(python="fixture"), configuration=dict(tau=3),
                          pipeline_report=dict(mode="integrated", rows=199319),
                          pipeline_report_sha256=rc.sha256_of(report),
                          commands=[dict(step=k, returncode=0) for k in ("tests", "generation", "official_validator")])
            evidence_path = Path(folder) / rc.EVIDENCE_NAME
            info = dict(rows=199319, sha256=rc.sha256_of(path))
            evidence_path.write_text(json.dumps(record))
            self.assertEqual(rc.run_blockers(str(path), info), [])
            # Written synthetic provenance exercises structure, not a claim of execution.
            for key, value in (("mode", "fallback"), ("mode", "fixture"), ("source", {}),
                               ("configuration", {}), ("environment", {}), ("inputs", {}),
                               ("run_dir", str(Path(folder).parent)), ("generation_ok", False),
                               ("commands", []), ("pipeline_report_sha256", "wrong")):
                with self.subTest(key=key, value=value):
                    evidence_path.write_text(json.dumps(dict(record, **{key: value})))
                    self.assertTrue(rc.run_blockers(str(path), info))

    def test_dirty_source_stops_before_tests_or_generation(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(rr, "source_identity", side_effect=RuntimeError("clean checkout required")), patch.object(rr, "run_step") as run:
            self.assertEqual(rr.main(["--runs-dir", folder]), 1)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
