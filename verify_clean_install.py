"""Prove the project installs and its tests pass in a brand-new virtualenv.

    python verify_clean_install.py            # requirements-release.txt, Python 3.12.10
    python verify_clean_install.py --starter  # also requirements-starter.txt (kloppy, notebook)

1. refuses any requirement that is not pinned with ==
2. builds a fresh venv in a NEW temporary folder (never reuses one)
3. pip install -r requirements.txt  (no cache, so a stale wheel cannot hide a problem)
4. runs the whole test suite with that venv's python, not yours

Exit 0 only if every step passed. Needs network access to PyPI.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
PIN = re.compile(r"^[A-Za-z0-9_.\-]+(\[[^\]]+\])?==[^\s=]+$")


def unpinned(path):
    """Requirement lines in `path` (following -r includes) that are not name==version."""
    bad = []
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("-r "):
                bad += unpinned(os.path.join(os.path.dirname(path), line[3:].strip()))
            elif not PIN.match(line):
                bad.append("{}: {}".format(os.path.basename(path), line))
    return bad


def run(command, **kwargs):
    print("$ " + " ".join(command), flush=True)
    return subprocess.run(command, **kwargs).returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--starter", action="store_true")
    args = parser.parse_args(argv)

    if sys.version_info[:3] != (3, 12, 10):
        print("FAIL  pinned release runtime is Python 3.12.10")
        return 1
    req = os.path.join(ROOT, "requirements-starter.txt" if args.starter else "requirements-release.txt")
    bad = unpinned(req)
    if bad:
        print("FAIL  unpinned requirements (use name==version):")
        for line in bad:
            print("  - " + line)
        return 1

    local = os.path.join(ROOT, "data", "environment-checks")
    os.makedirs(local, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="m5_clean_", dir=local) as folder:
        venv = os.path.join(folder, "venv")
        if run([sys.executable, "-m", "venv", venv]) != 0:
            print("FAIL  could not create the virtualenv")
            return 1
        python = os.path.join(venv, "Scripts" if os.name == "nt" else "bin",
                              "python.exe" if os.name == "nt" else "python")
        if run([python, "-m", "pip", "install", "--no-cache-dir", "-r", req]) != 0:
            print("FAIL  pip install failed with the pinned versions")
            return 1
        run([python, "-m", "pip", "freeze"])
        if run([python, "-m", "unittest", "discover", "-s", "tests"], cwd=ROOT) != 0:
            print("FAIL  tests failed in the clean environment")
            return 1
    print("\nOK    clean install with pinned versions; tests pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
