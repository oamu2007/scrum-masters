"""Load M2 from this combined checkout; no external clone or Git HEAD pin."""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


M2_SHA = "d1500582493069cbd9a7b74c86cd217fb279772c"


def load_m2():
    root = Path(__file__).resolve().parents[1]
    source = root / "modulos" / "modulo2.py"
    if not source.is_file():
        raise RuntimeError("Integrated checkout has no modulos/modulo2.py")
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
    print(json.dumps(dict(accepted_m2_ancestor=M2_SHA, actual_m2_source=str(source),
                          decoder_sha256=hashlib.sha256(source.read_bytes()).hexdigest()), sort_keys=True))
    return module
