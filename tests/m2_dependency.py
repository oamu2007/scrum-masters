"""Load the explicitly selected real M2 dependency; never substitute or skip it."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


M2_SHA = "d1500582493069cbd9a7b74c86cd217fb279772c"


def load_m2():
    selected = os.environ.get("MTAH_M2_ROOT")
    if not selected:
        raise RuntimeError("Actual-M2 gate requires MTAH_M2_ROOT pointing to the corrected M2 checkout; see module4/EVIDENCE.md")
    root = Path(selected).resolve()
    source = root / "modulos" / "modulo2.py"
    if not source.is_file():
        raise RuntimeError("MTAH_M2_ROOT has no modulos/modulo2.py")
    try:
        head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        changed = subprocess.check_output(["git", "-C", str(root), "diff", "HEAD", "--", "modulos/modulo2.py"])
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Cannot verify selected actual M2 Git dependency") from error
    if head != M2_SHA or changed:
        raise RuntimeError("Actual-M2 gate requires clean decoder at " + M2_SHA)
    name = "m4_acceptance_actual_m2"
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses resolves its defining module here
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True  # read-only dependency, including when caller omits -B
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    print(json.dumps(dict(actual_m2_head=head, actual_m2_source=str(source),
                          decoder_sha256=hashlib.sha256(source.read_bytes()).hexdigest()), sort_keys=True))
    return module
