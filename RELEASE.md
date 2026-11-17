# Reproduce the integrated candidate

File validity, behavioral acceptance, fresh generation, same-machine repeatability,
independent teammate reproduction and submission approval are separate claims.
A valid file never establishes possession accuracy or authorizes submission.

## Pinned environment

Use Python **3.12.10** in a project-local virtual environment:

```powershell
python -m venv data/release-env
$python = (Resolve-Path data/release-env/Scripts/python.exe).Path
& $python -m pip install -r requirements-release.txt
if ($LASTEXITCODE -ne 0) { throw 'Pinned install failed' }
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $python -B -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
```

The authoritative pins are NumPy 2.5.4, pandas 3.1.1, python-dateutil 4.0.0 and
tzdata 2026.6. `requirements.txt` includes that same set. Optional notebook
requirements are not needed for inference/validation. `verify_clean_install.py`
checks the exact interpreter and creates a fresh temporary environment under
ignored `data/environment-checks/`. Actual install/test limitations and results
are in `docs/INTEGRATION_STATUS.md`; no global package changes are required.

## Freeze and generate

Commit intended source/configuration and start with a clean checkout. From its root:

```powershell
& $python -B run_release.py --data-dir C:/path/to/licensed-bundle
$generationExit = $LASTEXITCODE
if ($generationExit -eq 1) { throw 'Required step failed; do not reuse any old CSV' }
if ($generationExit -notin @(0, 2)) { throw 'Unexpected release failure' }
```

Exit **2** means generation and file validation succeeded but approval remains
blocked. It is not permission to submit. Exit 0 additionally requires every named
external gate to pass with evidence. Submission is a separate authorized action.

Each run creates `data/release/runs/<UTC-stamp>/` without reusing an existing path.
It runs the full maintained suite, the actual runner with `--mode integrated`,
the official validator, and exact byte/hash checks. Every command must succeed;
logs remain in that run directory. It hashes the three permitted tactical inputs
(metadata, raw ATD, automatic Smart Tagging), records a clean source SHA, full
configuration, interpreter/packages/thread settings, command statuses, aggregate
pipeline report and output hash. Source and inputs are checked again at the end.
No public-label inference, training, tuning or possession-count matching occurs.

The old `--gen-cmd`, test/validator overrides and shortened `--rows` are restricted
to explicit `--fixture-mode`. A fixture, fallback or legacy record cannot pass an
integrated release gate, even with a valid CSV and all textual gates marked passed.
`input_checks.py` is a retained legacy proposed-schema utility; the authoritative
boundary is `run_possession.validate_evidence`, tested through real producers.

## Repeat, then reproduce independently

```powershell
& $python -B run_release.py --data-dir C:/path/to/licensed-bundle --expect-sha256 FIRST_OUTPUT_HASH
if ($LASTEXITCODE -notin @(0, 2)) { throw 'Fresh regeneration or hash comparison failed' }
```

This starts a fresh process/run directory and reruns all required steps. Matching
hashes on the same machine establish same-machine repeatability only. M5 must
have a second teammate start from the recorded source commit in a clean checkout,
install the pinned environment, use identical licensed inputs and regenerate.
Record operator, machine, environment, exact command and matching hash. Do not
copy the original CSV and call that reproduction.

`release_check.py candidate.csv` checks the file only. `--rows` labels it a fixture.
`--release` additionally checks required named gates and the adjacent run record.
The record is an auditable local manifest, not a cryptographic attestation of
who ran it. External gates remain blocked until their evidence exists. Current
candidate paths, hashes, gate results and remaining owners are recorded in
`docs/INTEGRATION_STATUS.md`. Generated assets and records stay ignored under data/.
