# Integration status — November 17, 2026

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

Source/configuration freeze and candidate run results will be appended after the
local integration commit. No full combined candidate is claimed at this checkpoint.
Independent teammate reproduction and submission approval remain blocked.

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
