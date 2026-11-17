import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import release_check  # noqa: E402

BLOCKS = [(1, 2, 5), (2, 8, 11)]   # 14 frames; X outside


def write(folder, data, name="s.csv"):
    path = os.path.join(folder, name)
    with open(path, "wb") as handle:
        handle.write(data)
    return path


def good(labels="XXHHAAXXDDHHXX"):
    return ("frame,label\n" + "".join("{},{}\n".format(i, c) for i, c in enumerate(labels))).encode()


class ReleaseCheckTests(unittest.TestCase):
    def check(self, data, **kw):
        with tempfile.TemporaryDirectory() as folder:
            return release_check.check_file(write(folder, data), n_rows=14, blocks=BLOCKS, **kw)

    def test_good_file_has_no_problems(self):
        problems, info = self.check(good())
        self.assertEqual(problems, [])
        self.assertEqual(info["rows"], 14)
        self.assertEqual(len(info["sha256"]), 64)

    def test_same_bytes_same_hash_and_expect_works(self):
        _, info = self.check(good())
        self.assertEqual(self.check(good(), expect_sha256=info["sha256"].lower())[0], [])
        self.assertTrue(self.check(good(), expect_sha256="0" * 64)[0])

    def test_one_changed_label_changes_the_hash(self):
        self.assertNotEqual(self.check(good())[1]["sha256"],
                            self.check(good("XXHHAAXXDDHAXX"))[1]["sha256"])

    def test_crlf_bom_and_missing_newline(self):
        self.assertTrue(self.check(good().replace(b"\n", b"\r\n"))[0])
        self.assertTrue(self.check(b"\xef\xbb\xbf" + good())[0])
        self.assertTrue(self.check(good().rstrip(b"\n"))[0])

    def test_wrong_header(self):
        self.assertTrue(self.check(good().replace(b"frame,label", b"Frame,Label"))[0])

    def test_label_outside_halves_must_be_x(self):
        problems, _ = self.check(good("HXHHAAXXDDHHXX"))
        self.assertTrue(any("outside the halves" in p for p in problems))

    def test_wrong_row_count_is_reported(self):
        problems, _ = self.check(good("XXHHAAXXDDHHX"))
        self.assertTrue(any("row count" in p for p in problems))

    def test_missing_file(self):
        self.assertTrue(release_check.check_file("no_such.csv")[0])


if __name__ == "__main__":
    unittest.main()
