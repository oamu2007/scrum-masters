# Integration status — November 17, 2026

**Current work: kickoff-state follow-up.** The original freeze/result below is
preserved as historical execution evidence, including its limited 283-test gate.
It does not cover the subsequently demonstrated FAQ kickoff discrepancy. See
the appended kickoff follow-up for the new rule, candidate and remaining limits.

This is execution evidence for the combined checkout, separate from the preserved
historical component reviews. No possession-accuracy claim, independent teammate
sign-off, publication or submission is implied.

## Starting workspace and accepted versions

Original repository: `C:/Users/oamu2/more-than-a-hack-2027`, branch
`module-3-tracking-reader`, HEAD `ef2fea667ad774d1ece1dfb825d376adbee6723a`.
Integration clone: `data/integration-attempt`, branch `integration-attempt`, clean
index/worktree at `b4f2d70816f1d9f79819d0e534c353c27bbf362a`. No existing work was
reset or overwritten. VS Code was opened on this clone. The original and both
module checkouts are preserved; only the integration clone is being changed.

Remote fetch initially failed under restricted execution; the approved retry
succeeded. The refreshed remote contains the accepted local M2/M4 commits.
No newer M1/M2/M4 tip was silently discarded. Latest M5 is the newer requested tip.

| Work | Verified full component SHA | Local ordinary merge commit | Post-merge checks |
|---|---|---|---|
| M1 runner foundation | `33c135385862c5f597ed846e64207ae49be6eea2` | `be37fb120a9eb49f010907d27f4d866bd633dd14` | 66 tests pass |
| Accepted M4 | `325e073fb8f90cb7bf38e139c85ea1e4c8200e3e` | `4f202d17cc7e667d048569b8641534b77e2506c6` | 132 tests + tag assertions pass |
| Accepted M2 | `d1500582493069cbd9a7b74c86cd217fb279772c` | `25051b063c981ffa8238336da6edcd3bfb67ec80` | 166 tests + 13 standalone M2 tests pass |
| Latest M5 | `ed6880f0f7ba3d1abdb088314ff72f8b100a5b62` | `e33a4d3345cb37e914ed79c375554e0b502d57f7` | 266 tests pass before wiring changes |

Ancestry and changed paths were inspected before merging, without replaying inherited
M1/M3 commits. Conflicts were confined to `.gitignore`: preserve both historical
review/HANDOFF exclusions, and split M5's accidentally concatenated
`MODULE_REVIEW.mdrelease/runs/` into two correct entries. No restricted outputs
were staged. M4's accepted producer hash is
`616f0be6cdb9376a2c9f43d141f4978cee1db0a2a09b1532d5b9ab2582d356f7`;
M2's accepted decoder hash is
`6976c1f65e87b3e8e6088d1e9905162430abd5eb937e9dd156bfc68a7b53eda4`.
Their source files are unchanged by integration, as are M1 scoring and M3 reading.
The post-M4 merge check temporarily selected the verified local M2 dependency;
the final tests import M2 from the combined checkout without that selection.

## Wiring and scoped fixes

`run_possession.py --mode integrated` (also the default) exhausts one M3 stream.
Actual M1 and M4 receive the same recursively read-only frame. All seven M1 and
five M4 returns are retained in compact aligned arrays. Scalar type/schema checks
precede NumPy coercion; final array checks enforce dimensions/count, Boolean flags,
finite bounded scores, visibility/availability, finite nonnegative available
distances, NaN unavailable distances, unavailable zero scores and H/A/None sides.
Actual M2 receives the selected five M1 fields, all five M4 fields and native
inclusive half triples. No rounded CSV, alternate tracking reader or new decoder
is inserted. Missing dependencies/dropped fields fail clearly.

The old fallback is explicit `--mode fallback` and cannot satisfy release gates.
Its API and meaningful regression tests remain. Available zero evidence is legal;
restart availability need not imply visible players; side context alone is not a
restart. X remains legal inside halves and required outside. Accepted defaults,
confirmation timing and M4's restricted envelope are unchanged.

M5 `ed6880f` was reassessed against its historical review: it adds 100 tests beyond
M1 plus file/gate/run tools, but its scenarios test constructed labels, and its
input utility assumes a different schema. Those tests/utilities remain explicitly
scoped; new maintained tests exercise actual production composition. Its old
custom generation/test commands, short-row overrides and unbound provenance could
not establish integrated generation. The corrected procedure uses fixed required
commands, unique ignored directories, checked statuses, clean source and input
hashes before/after, full configuration/environment, pipeline report and exact
output hash. Fixtures never approve release. Missing named gates also block.
The legacy input utility is not the production boundary. Requirements now share
the authoritative release pins; historical `.bak` files are not active code.

## Maintained verification

Combined pinned suite before source freeze: **283 tests passed, no skips**.
The 17 added methods include actual transport/behavior, real invented EPTS through
serialization, and release negative controls. Existing 266 regressions remain
(including historical fallback, M2, M4, M3/M1, official metrics and file checks).
Old tests that approved short fixtures now require rejection; failure and stopping
assertions are preserved. The component loader no longer depends on another clone,
a personal path, a matching checkout HEAD or `MTAH_M2_ROOT`.

Coverage includes pass/occlusion/brief deflection, exact 12-sample turnover, weak
scores/unavailable teams, supported stop/persistent D, 32/60/120-second supported
recovery, known/unknown/conflicting sides, independent restart availability, live
boundary drift/holds, reacquired jitter, native half endpoints and fresh half state.
Existing actual-M2 regressions retain simultaneous dead/restart conflict, interrupted
confirmation, consumption, tag endpoints and accepted fast-retrieval ambiguity.
Negative controls reject dropped M4 returns, missing required modules, input index
shift, malformed types/arrays/distances/sides, fallback substitution, fixture release
substitution, stale files, modified outputs, failed tests and failed regeneration.
A real subprocess writes a CSV then exits 7; no success manifest is created and
it cannot pass the integrated gate. Official file regressions reject output-index shifts.

Standalone M1 self-test, 13 M2 sequence tests, M4 tag assertions, dependency
compatibility check and whitespace checks pass. Tests involving supplied public
labels only retain existing shape/metric checks; no public scores are used to train,
tune, select versions or match desired possession counts.

## Environment and exact reproduction commands

Downloaded Python **3.12.10** to ignored `data/python/` and created a fresh local
`data/release-env/`. Installed NumPy **2.5.4**, pandas **3.1.1**,
python-dateutil **4.0.0**, tzdata **2026.6**. Global installations were preserved.
Initial installer/OpenBLAS resource failures were resolved by reduced concurrency
and single-thread numerical-library settings. A default uv cache write failed;
using the project-local ignored cache succeeded. These are recorded installation
issues, not silent substitution of older dependency pins. `uv pip check` passes.

Commands run from the integration root (PowerShell):

```powershell
$env:UV_PYTHON_INSTALL_DIR = "$PWD/data/python"
$env:UV_CACHE_DIR = "$PWD/data/uv-cache"
uv python install 3.12.10
uv venv --python data/python/cpython-3.12.10-windows-x86_64-none/python.exe data/release-env
$env:UV_CONCURRENT_DOWNLOADS = '1'
$env:UV_CONCURRENT_BUILDS = '1'
$env:UV_CONCURRENT_INSTALLS = '1'
uv pip install --python data/release-env/Scripts/python.exe -r requirements-release.txt
$python = (Resolve-Path data/release-env/Scripts/python.exe).Path
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $python -B -m unittest discover -s tests -q
& $python -B module1/control_scores.py --test
& $python -B modulos/test_modulo2.py -q
& $python -B module4/test_stoppages.py
uv pip check --python $python
```

Check every required exit code when reproducing. Logs of merge and combined
checks/install attempts are under ignored `data/integration-20261117/`.
Canonical full generation/repeat commands are in [RELEASE.md](../RELEASE.md).

## Candidate and remaining gates

**Actual M3 -> M1/M4 -> M2 runs successfully. Behavioral acceptance, official
format validation, fresh generation and same-machine repeatability pass.**
Independent teammate reproduction and submission approval remain blocked.

The source/configuration freeze is local commit
**`90d1f4efa969f21b0b932d770e1011d23a7ed14d`** (runner/boundary/release fixes,
tests and documentation). Both full runs used that clean SHA and the pinned
environment above. Subsequent result-record changes affect only this status
document and `release_gates.json`; reproduce inference from the frozen source SHA.

| Execution | Ignored run directory relative to integration root | Required step results |
|---|---|---|
| First candidate | `data/release/runs/20261117T102236151903Z/` | 283 tests pass, generation 0, official validator 0, file/hash check passes |
| Fresh repeat | `data/release/runs/20261117T102424208440Z/` | 283 tests pass, generation 0, official validator 0, expected hash matches |

Each directory contains `candidate.csv`, `pipeline.json`, `evidence.json`,
`tests.log`, `generation.log` and `official_validator.log`. Both CSVs have
**199,319 ordered rows, frames 0..199318**, 1,682,773 bytes, and SHA-256:

```text
BE262BB468B3610289F94F4A45CB8D8A1D8879F675C2668E6267F68E62FCE62D
```

Primary candidate absolute path:
`C:/Users/oamu2/more-than-a-hack-2027/data/integration-attempt/data/release/runs/20261117T102236151903Z/candidate.csv`.
The second is a separate process, fresh output directory and full reread, not a
copy. Both run records agree exactly on source, configuration, input identities,
environment, output hash and aggregate report. Local verification is recorded in
`data/integration-20261117/repeat-verification.json`.

| Aggregate | Full match | Half 1 | Half 2 |
|---|---:|---:|---:|
| H | 83,202 | 43,145 | 40,057 |
| A | 74,894 | 36,218 | 38,676 |
| D | 641 | 55 | 586 |
| X inside graded halves | 120 | 49 | 71 |
| Entries to D / exits from D | 6 / 6 | 1 / 1 | 5 / 5 |

All **40,462** outside-half frames are X; total X is **40,582**. Inside-half
abstentions are legal, not a failed gate. Native blocks are exactly
`(1,11185,90651)` and `(2,110808,190197)`. M4 dead available/positive/strong:
**88,292 / 1,488 / 368**; restart available/positive/strong:
**791 / 129 / 129**, matching the accepted component aggregate record. The official
validator reports 716 possessions, mean 8.8 s, with its documented X-gap convention.
These are descriptive diagnostics, not accuracy, a desired count or a selection metric.
No public-window evaluation was run.

Exact full-run commands, using `$python`, thread settings and working directory above:

```powershell
& $python -B run_release.py --data-dir C:/Users/oamu2/more-than-a-hack-2027/data
& $python -B run_release.py --data-dir C:/Users/oamu2/more-than-a-hack-2027/data --expect-sha256 BE262BB468B3610289F94F4A45CB8D8A1D8879F675C2668E6267F68E62FCE62D
```

Both orchestration commands exit **2**, deliberately: every required execution
step passed but external approval gates remained blocked. This is not a failed
inference and is not submission approval. The manifests record the exact child
argv for tests, canonical runner (`--mode integrated --game BAR-ATH --tau 3.0
--out <fresh>/candidate.csv --report <fresh>/pipeline.json --data-dir <bundle>`)
and official validator on that exact output. Their statuses are all 0.
The first run's `candidate_frozen`/repeat gates were still pending at execution;
the result record now passes those gates with both runs as evidence. It does not
retroactively claim an independent review or teammate sign-off.

Input identities (no restricted inputs are committed):

| Input | Bytes | SHA-256 |
|---|---:|---|
| tactical ATD metadata | 59,057 | `327E35E32E46A647389B88F883D4F9A2AB931E3E6148AEF2FCF8F22B1E93C43A` |
| tactical raw ATD | 195,714,285 | `F130E350D2BFDF734B7E32F072931FCCC6D015C1E837D082064875FE0A700431` |
| automatic Smart Tagging | 261,055 | `0594D35E3DF01B9C5002372D8615E2E8EF5379AC8F4E84C5EF7A53F4304C9019` |

An additional **clean source export** of the frozen commit passed all **283 tests,
no skips**, using the project-local pinned interpreter with `MTAH_M2_ROOT` unset.
Its M2 import path resolves inside the export, not another clone; it has no Git
metadata or personal dependency paths. Export/test commands:

```powershell
git archive --format=zip --output=data/integration-20261117/clean-source.zip 90d1f4efa969f21b0b932d770e1011d23a7ed14d
Expand-Archive -LiteralPath data/integration-20261117/clean-source.zip -DestinationPath data/integration-20261117/clean-checkout
# From that fresh export, using the same absolute $python:
& $python -B -m unittest discover -s tests -v
```

This is local clean-source verification, not an independent operator/machine.
Actual Python/platform: 3.12.10, Windows 11 (`Windows-11-10.0.26300-SP0`).
Full source-freeze and clean-export logs remain ignored under
`data/integration-20261117/`; no frame-level outputs or environment files are tracked.

Accepted limitations: fast in-pitch retrieval may be indistinguishable from a
ball-only restart; unreported eligibility can last the half; interior fouls/offside
are weakly covered; noise, curved/reversing motion and sparse samples can fail the
heuristics. Synthetic behavior and valid/reproducible output do not prove match
possession accuracy. No component thresholds were tuned.

Owners/actions still outside local execution: **M5 + a second teammate** regenerate
from the frozen source/pins/licensed input identities and record operator, machine,
commands and matching hash. **M5 + team lead** verify registered name, technical
package, exact team-named CSV/hash, submitter/backup, access and official cutoff/timezone,
and obtain submission approval. No external action is authorized here.

## Final preservation and result record

Rechecking both exact candidates with the updated gates yields `VALID_NOT_APPROVED`
with **only two blockers**: independent reproduction and submission approval. File,
fresh-run provenance and all locally executable gates pass. The result is stored
locally in `data/integration-20261117/final-gates.json`.

The final result-record commit changes only this document and `release_gates.json`;
the candidate's source/configuration remains the frozen `90d1f4e` commit above.
Integration stays on `integration-attempt` with intended local commits and a clean
index/worktree after recording. Original checkout remains clean at `ef2fea6`, M2
at `d150058`, M4 at `325e073`, on their original branches. Their working files and
checkouts are preserved. `git ls-files data` lists only `data/README.md`; candidate
CSV, evidence, environments and local logs are ignored. Historical reviews were
not rewritten. Nothing was pushed, merged into main, sent externally or submitted.

## Kickoff-state follow-up — November 17, 2026

Starting checkout verified clean on `integration-attempt` at
`3dec1799e6878f118fc367fde17669c916d88703`. The prior frozen source remains
`90d1f4efa969f21b0b932d770e1011d23a7ed14d`. Both prior run directories and every
file in them are hash-recorded in ignored
`data/kickoff-fix-20261117/previous-artifacts.json` and are preserved unchanged.

### Root cause and executed baseline diagnosis

The FAQ explicitly distinguishes graded-half start from kickoff. M2 previously
initialized X, then treated twelve credible M1 proximity samples as sufficient
for H/A, implicitly assuming live play. M1 supplies distance evidence, not live
status. M4 discarded kickoff type while keeping only generic set-piece context;
its interior pause support could not establish D, and restart evidence required
an earlier supported boundary pause. Thus no component represented waiting for
a half-start kickoff. The same initial-live assumption affects the first half
and any untagged interior stop; established D already correctly requires a restart.

A fresh baseline M3 -> M1/M4 -> M2 scan reproduced every frozen label exactly.
For FAQ frames 110808..113741: **H 2,235; A 688; X 11; D 0**. Of 2,934 frames,
2,370 have observed ball and 1,716 meet M2's proximity credibility gates;
there are zero strong dead or restart samples (maximum dead score 0).
Automatic supplied tags contain one nonempty Kick Off (Start) window per half,
each 125 frames; the first overlaps graded start, the second is still upcoming.
Both have unknown side. These are aggregate diagnostics, not human annotations.
No public-window scoring, video annotation, external match annotations or tuning
was performed. Baseline evidence arrays stay ignored locally.

`games.py`'s burned-in second kickoff clock anchor converts to 113741, whereas
FAQ and the existing tagging alignment constant specify 113742. The new isolated
`kickoff_check.py` explicitly uses the FAQ reference, checking all 2,934 frames
inclusively; it does not silently substitute the clock anchor. This diagnostic
constant is never imported or consulted by inference. Native graded halves and
all existing tracking/frame alignment remain unchanged.

### General correction and ownership

M4 recognizes a unique nonempty automatic **Kick Off (Start)** window intersecting
a graded half and exposes that half start as an initial-D prior. Missing or
multiple matches supply no prior. This uses type and supplied approximate timing,
not published kickoff anchors, half-number special cases or label masks.
The runner retains all existing full-precision arrays and transports an additional
strict Boolean `initial_dead` array. It is true only at supported half starts.
M2 validates that constraint and initializes persistent D there, resetting every
counter; close players cannot release D. The new M2 keyword is optional for
existing component callers, preserving their previous X initialization.

M4 suspends ordinary boundary eligibility while the initial kickoff is pending.
Before the approximate phase starts, warm-up movement is not restart support.
At/after its start, the first observed ball seeds a fresh origin. Existing A/B
motion, displacement, progress, availability and three-sample report rules then
apply without threshold changes. Neither tag entry nor expiry directly releases
D. Supported movement can resume even after expiry; side then remains unknown.
A qualified report clears the pending kickoff once; normal stoppage behavior
resumes. All context resets independently at each half.

This fixes the demonstrated missing state/context boundary. It does **not** prove
referee authorization: early/late/incorrect automatic tags can bias the waiting
period; pre-kickoff movement may resemble a restart; an already-live half can
receive a D prefix during confirmation. Missing/ambiguous tags retain the old
untagged X/proximity acquisition policy, so that broader ambiguity remains.
No general interior-foul detector, new tracking system or parameter search was added.

### Acceptance and safe regeneration

Fourteen new maintained tests in `tests/test_kickoff_pipeline.py` use actual
M1/M4, runner and M2: pre-kickoff stationary proximity, supported/late resumption,
live graded start, missing observations/tags, conflicting kickoff/side context,
approximate tag entry/expiry, warm-up motion, jitter, subsequent turnover and
ordinary stoppage, fresh second half, dropped/shifted/malformed initial prior,
real automatic-tag extraction, and the inclusive published diagnostic alignment.
The previous 283 tests retain their behavioral expectations; the native-half
array fixture only adds a false initial-prior array required by the revised schema.

New-source test and generation results follow below after freeze. The old
candidate's repeatability and candidate-frozen gate records are historical and
have been reset for these changed bytes. Independent teammate reproduction and
submission approval remain blocked. All run artifacts remain ignored under data/.

Pre-freeze verification: **297 maintained tests pass, no skips** (283 retained
plus 14 new methods). M1 self-test, 13 standalone M2 sequence tests and M4 tag
assertions pass. Whitespace checks pass. Existing proximity/motion thresholds,
units, missingness and full-precision transport are unchanged. The only existing
test edit is the explicit false initial-prior array in the native-half fixture.
The complete test log is `data/kickoff-fix-20261117/freeze-tests.log`.

Canonical generation remains `python run_release.py --data-dir <bundle>` with
the verified local pinned environment and OPENBLAS_NUM_THREADS/OMP_NUM_THREADS=1.
The new source will be committed before generation; old output paths are never
reused. Exact source SHA, run paths, hashes and observed diagnostics are recorded
in the result section below after the two fresh runs.
