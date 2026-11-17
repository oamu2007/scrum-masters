"""CSV valid is not release approved, and the release procedure stops when it should."""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import release_check  # noqa: E402
import run_release  # noqa: E402

BLOCKS = [(1, 2, 5), (2, 8, 11)]
LABELS = "XXHHAAXXDDHHXX"
PY = '"{}"'.format(sys.executable) if os.name == "nt" else sys.executable


def csv_bytes(labels=LABELS):
    return ("frame,label\n" + "".join("{},{}\n".format(i, c) for i, c in enumerate(labels))).encode()


def gates_file(folder, statuses=("blocked",), evidence="ran X on 2026-11-16"):
    gates = [{"id": "g{}".format(i), "description": "d", "status": s, "reason": "pending {}".format(i),
              "evidence": evidence if s == "passed" else ""} for i, s in enumerate(statuses)]
    path = os.path.join(folder, "gates.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"gates": gates}, handle)
    return path


def make_candidate(folder, data=None, evidence=True, **evidence_overrides):
    """A candidate plus the evidence run_release.py would have written."""
    path = os.path.join(folder, "candidate.csv")
    with open(path, "wb") as handle:
        handle.write(data or csv_bytes())
    if evidence:
        sha = release_check.sha256_of(path)
        record = {"tests_ok": True, "generation_ok": True, "candidate_name": "candidate.csv",
                  "candidate_sha256": sha, "started_at_epoch": time.time() - 5}
        record.update(evidence_overrides)
        with open(os.path.join(folder, release_check.EVIDENCE_NAME), "w", encoding="utf-8") as h:
            json.dump(record, h)
    return path


class ValidIsNotApprovedTests(unittest.TestCase):
    def approve(self, folder, path, gates):
        return release_check.approve_release(path, gates_path=gates, n_rows=14, blocks=BLOCKS)

    def test_valid_csv_with_a_blocked_gate_is_not_approved(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.approve(folder, make_candidate(folder), gates_file(folder, ("blocked",)))
        self.assertEqual(result["status"], "VALID_NOT_APPROVED")
        self.assertTrue(any("pending 0" in b for b in result["blockers"]))

    def test_one_blocked_gate_among_passed_still_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.approve(folder, make_candidate(folder),
                                  gates_file(folder, ("passed", "blocked", "passed")))
        self.assertEqual(result["status"], "VALID_NOT_APPROVED")
        self.assertEqual(sum("pending 1" in b for b in result["blockers"]), 1)

    def test_passed_without_evidence_is_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.approve(folder, make_candidate(folder),
                                  gates_file(folder, ("passed",), evidence=""))
        self.assertEqual(result["status"], "VALID_NOT_APPROVED")
        self.assertTrue(any("no evidence" in b for b in result["blockers"]))

    def test_passed_gate_text_cannot_approve_a_short_legacy_fixture(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.approve(folder, make_candidate(folder),
                                  gates_file(folder, ("passed", "passed")))
        self.assertEqual(result["status"], "VALID_NOT_APPROVED")
        self.assertTrue(any("short fixtures" in b for b in result["blockers"]))

    def test_invalid_csv_is_invalid_not_merely_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            path = make_candidate(folder, data=csv_bytes("XXHHAAXXDDHHX"))
            result = self.approve(folder, path, gates_file(folder, ("passed",)))
        self.assertEqual(result["status"], "INVALID")

    def test_missing_gates_file_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.approve(folder, make_candidate(folder), os.path.join(folder, "nope.json"))
        self.assertEqual(result["status"], "VALID_NOT_APPROVED")
        self.assertTrue(any("cannot read gates" in b for b in result["blockers"]))

    def test_shipped_gates_file_blocks_until_m2_m4_land(self):
        gates, error = release_check.load_gates()
        self.assertIsNone(error)
        ids = {g["id"] for g in gates}
        for needed in ("M2_integrated", "M4_integrated", "scenarios_with_real_M2_M4",
                       "M1_carries_data", "candidate_frozen", "independent_reproduction"):
            self.assertIn(needed, ids)
        self.assertTrue(release_check.gate_blockers(gates),
                        "the repo ships with pending dependencies; none may read as passed")


class RunEvidenceTests(unittest.TestCase):
    def approve(self, path, folder):
        return release_check.approve_release(path, gates_path=gates_file(folder, ("passed",)),
                                             n_rows=14, blocks=BLOCKS)

    def test_file_without_evidence_is_not_approved(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.approve(make_candidate(folder, evidence=False), folder)
        self.assertEqual(result["status"], "VALID_NOT_APPROVED")
        self.assertTrue(any("not produced by run_release" in b for b in result["blockers"]))

    def test_edited_after_generation_is_not_approved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = make_candidate(folder)
            with open(path, "wb") as handle:
                handle.write(csv_bytes("XXHHAAXXDDHAXX"))     # still valid, but not what was recorded
            result = self.approve(path, folder)
        self.assertEqual(result["status"], "VALID_NOT_APPROVED")
        self.assertTrue(any("SHA-256 differs" in b for b in result["blockers"]))

    def test_failed_tests_in_evidence_block(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.approve(make_candidate(folder, tests_ok=False), folder)
        self.assertTrue(any("test suite" in b for b in result["blockers"]))

    def test_failed_generation_in_evidence_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.approve(make_candidate(folder, generation_ok=False), folder)
        self.assertTrue(any("generation" in b for b in result["blockers"]))

    def test_stale_file_older_than_the_run_is_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            path = make_candidate(folder, started_at_epoch=time.time() + 3600)
            result = self.approve(path, folder)
        self.assertTrue(any("stale" in b for b in result["blockers"]))

    def test_wrong_file_name_is_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            path = make_candidate(folder)
            other = os.path.join(folder, "old_submission.csv")
            os.replace(path, other)
            result = self.approve(other, folder)
        self.assertTrue(any("not the generated candidate" in b for b in result["blockers"]))


class ReleaseCommandExitCodeTests(unittest.TestCase):
    def test_plain_check_is_ok_but_release_flag_is_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "all_x.csv")
            with open(path, "wb") as handle:
                handle.write(csv_bytes("X" * 14))
            gates = gates_file(folder, ("blocked",))
            plain = release_check.main([path, "--rows", "14"])
            blocked = release_check.main([path, "--rows", "14", "--release", "--gates", gates])
            invalid = release_check.main([path, "--rows", "15", "--release", "--gates", gates])
        self.assertEqual((plain, blocked, invalid), (0, 2, 1))


class RunReleaseStopsTests(unittest.TestCase):
    """run_release.py must stop at the first failure and never leave an approvable file."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runs = os.path.join(self.tmp.name, "runs")
        self.marker = os.path.join(self.tmp.name, "generation_ran")
        self.gen_ok = os.path.join(self.tmp.name, "gen_ok.py")
        with open(self.gen_ok, "w", encoding="utf-8") as handle:
            handle.write("import sys\nopen(sys.argv[1], 'w', newline='\\n').write("
                         "'frame,label\\n' + ''.join('%d,X\\n' % i for i in range(14)))\n"
                         "open(sys.argv[2], 'w').write('ran')\n")
        self.gen_noop = os.path.join(self.tmp.name, "gen_noop.py")
        with open(self.gen_noop, "w", encoding="utf-8") as handle:
            handle.write("pass\n")

    def run_release(self, gen_script, tests_pass=True, gates=("blocked",)):
        gates_path = gates_file(self.tmp.name, gates)
        test_cmd = "{} -c \"import sys; sys.exit({})\"".format(PY, 0 if tests_pass else 1)
        gen_cmd = "{} {} {{out}} {}".format(PY, gen_script, self.marker)
        return run_release.main(["--fixture-mode", "--gen-cmd", gen_cmd, "--runs-dir", self.runs, "--rows", "14",
                                 "--test-cmd", test_cmd, "--gates", gates_path])

    def candidates(self):
        found = []
        for folder, _, names in os.walk(self.runs):
            found += [os.path.join(folder, n) for n in names if n == "candidate.csv"]
        return found

    def test_failing_tests_stop_before_generation(self):
        code = self.run_release(self.gen_ok, tests_pass=False)
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(self.marker), "generation ran despite failing tests")
        self.assertEqual(self.candidates(), [])

    def test_generation_that_writes_nothing_stops(self):
        self.assertEqual(self.run_release(self.gen_noop), 1)

    def test_generation_command_without_out_placeholder_stops(self):
        code = run_release.main(["--gen-cmd", "{} {}".format(PY, self.gen_ok),
                                 "--runs-dir", self.runs, "--test-cmd", "{} -c pass".format(PY)])
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(self.marker))

    def test_valid_candidate_with_blocked_gates_exits_two(self):
        code = self.run_release(self.gen_ok, gates=("blocked",))
        self.assertEqual(code, 2)
        self.assertEqual(len(self.candidates()), 1)

    def test_green_fixture_never_approves_integrated_release(self):
        self.assertEqual(self.run_release(self.gen_ok, gates=("passed",)), 2)

    def test_each_run_uses_a_new_folder(self):
        self.run_release(self.gen_ok)
        self.run_release(self.gen_ok)
        folders = {os.path.dirname(c) for c in self.candidates()}
        self.assertEqual(len(folders), 2)

    def test_run_folder_is_never_reused(self):
        first = run_release.new_run_dir(self.runs)
        with self.assertRaises(FileExistsError):
            os.makedirs(first, exist_ok=False)


if __name__ == "__main__":
    unittest.main()
