# Release procedure (M5)

A **valid CSV is not an approved release.** `release_check.py` answers two different questions:

| Question | Command | Exit |
|---|---|---|
| Is the file well-formed? | `python release_check.py file.csv` | 0 valid, 1 invalid |
| May it be delivered? | `python release_check.py file.csv --release` | 0 approved, 1 invalid, **2 valid but blocked** |

Approval needs every gate in `release_gates.json` to be `passed` **with written evidence**, and the
file must come from a run recorded by `run_release.py` (same SHA-256, fresh folder, tests and
generation green). Nothing here implements M2's or M4's algorithms; it only stops delivery while
their work is missing.

## Run it

```bash
python verify_clean_install.py                      # clean venv, pinned versions, full tests
python run_release.py --gen-cmd "<Module 1 command> {out}"
```

`{out}` is mandatory: the candidate is written to a **new** `release/runs/<UTC-stamp>/candidate.csv`
every time, so an old file can never be approved by accident. The procedure stops at the first
failure: tests -> generation -> official validator -> byte checks -> gates. Exit 0 approved,
1 a step failed, 2 everything ran but gates are blocked.

Independent reproduction (another teammate, same commit, fresh clone):

```bash
python run_release.py --gen-cmd "<Module 1 command> {out}" --expect-sha256 <FROZEN_SHA256>
```

## Current blockers (documented, not hidden)

| Gate | Waiting for |
|---|---|
| `M2_integrated`, `M4_integrated` | M2 / M4 to push their final changes |
| `scenarios_with_real_M2_M4` | Pass/deflection, persistent D, late restart / unknown side, half-time reset run with the real M2 and M4 (today only synthetic sequences run: `tests/test_scenarios.py`) |
| `M1_carries_data` | Check that M1 transports M2/M4 data into the CSV |
| `candidate_frozen` | Freeze commit + SHA-256 after the above are tested |
| `independent_reproduction` | A second person reproduces the identical SHA-256 |

To unblock a gate: run the real check, then edit that gate in `release_gates.json` to
`"status": "passed"` and put the command, date, person and hash in `"evidence"`. A `passed` gate
with empty evidence still blocks.

## Rejection cases (`input_checks.py`, `tests/test_input_rejections.py`)

Contradictory availability/distance (unavailable but with distance or side; available but with
empty, negative, infinite or absurd distance) and missing fields are rejected. **The field names
are an assumption**: update the constants at the top of `input_checks.py` when M2/M4 publish theirs.

## Environment

`requirements.txt` is pinned (`numpy==2.5.3`, `pandas==3.0.5`), tested on Python 3.13; these
versions need Python >= 3.11. If the team runs an older Python, pin versions that support it,
rerun `python verify_clean_install.py`, and commit the result.
