# Kickoff debugging checkpoint — 2026-11-17

**Stopped at user request. Partial correction only; release remains blocked.**
This checkpoint records existing evidence, not another algorithm experiment.
Paths below are relative to `C:/Users/oamu2/more-than-a-hack-2027/data/integration-attempt`.

## Verified workspace

- Branch: `integration-attempt`.
- HEAD/result record: `def5fc8a43a9f4fa88891ab5e1b37b8e9f532f09`.
- Frozen investigation inference source: `48d67bb271ce0dd50d0d6a1ce9dd24111a32fe78`.
- Previous result record: `3dec1799e6878f118fc367fde17669c916d88703`.
- Before this checkpoint, index/worktree were clean. HEAD differs from the frozen
  source only in `docs/INTEGRATION_STATUS.md` and `release_gates.json`.
- Local `origin/integration-attempt` currently equals HEAD; no fetch or push was
  performed for this checkpoint. This describes the local reference only.
- No merge, rebase, cherry-pick, revert, bisect, sequencer or index-lock marker.
- This checkpoint is intentionally saved **untracked and unstaged**; no new commit.
  No other file is changed. No inference/test process is left running by this task.

## Defect and scoped change

FAQ defines graded frames **110808–113741 inclusive (2,934 frames) as D** before
second kickoff. Original output was H 2,235 / A 688 / X 11 / D 0. M2 started X
and accepted 12 credible proximity samples as possession without first establishing
live play. M1 measures proximity, not authorization. M4 discarded kickoff type;
generic interior set-piece context did not establish a strong dead-ball anchor.
The baseline scan reproduced the old CSV exactly: 1,716 credible-control samples,
zero strong dead/restart samples in this interval.

The general correction makes a unique automatic kickoff context an initial-D
prior, then requires existing observed restart support to leave D. No published
frame boundary is used by prediction. Exact changed production functions:

| File | Changed functions / declarations |
|---|---|
| `module4/evidence.py` | `StoppageEvidence.__init__` retains kickoff windows and exposes `initial_dead_frames`; `_clear_motion` resets pending kickoff state; `__call__` initializes pending state per half and supplies kickoff eligibility to existing motion logic |
| `modulos/modulo2.py` | `modulo2` adds optional keyword-only `initial_dead`, validates Boolean alignment and half-start-only support; `_decodificar_half` initializes D when supported, otherwise X |
| `run_possession.py` | `validate_evidence` requires the integrated Boolean prior; `collect_evidence` transports it; `decode_match` passes it to actual M2; `main` reports `initial_dead_halves` |
| `kickoff_check.py` (new) | `PUBLISHED_SECOND_KICKOFF`, `check`, `main`: isolated FAQ diagnostic, never imported by inference |
| `release_check.py` | `REQUIRED_GATES` adds `published_kickoff_diagnostic`; no function changed |

Other files in source commit: new `tests/test_kickoff_pipeline.py` (helper `kickoff`
and 14 test methods); one all-false prior added to an existing native-half fixture
in `tests/test_integrated_pipeline.py`; contract/record updates in `RELEASE.md`,
`module1/RUNNER.md`, `module4/EVIDENCE.md`, `modulos/M2.md`,
`docs/INTEGRATION_STATUS.md`, `release_gates.json`. The subsequent result commit
changes only the last two records. Historical reviews are preserved.

## Actual evidence and transitions

- Windows are half-open `[start,end)`. A nonempty, case-insensitive `Kick Off (Start)`
  window qualifies when it intersects the native inclusive half; exactly one match
  supplies initial D at that half's first frame. Missing/multiple matches supply
  no prior (legacy X/proximity acquisition remains). Supplied data has one 125-frame
  window per half, both unknown side: first overlaps graded start, second is future
  at graded start. Approximate tag entry/expiry is not a restart event.
- While kickoff is pending, ordinary boundary-pause anchoring is suppressed.
  Before tag start, restart evidence is withheld. At/after start the first usable
  ball seeds the origin. Existing short ball history is **not explicitly cleared
  at tag start**; it is cleared at half reset, excessive gap or impossible jump.
  Tag expiry does not erase pending eligibility. This history distinction is worth
  inspecting, not an established explanation of the residual error.
- Unchanged motion defaults: rolling 0.2 s, minimum span 0.08 s, gap limit 0.2 s,
  jump limit 80 m/s. Restart requires ball inside pitch and net progress speed
  at least 2 m/s. Path A: displacement at least 0.8 m, at least 3 observed nearby
  players within 20 m, at least 2/3 active at 2 m/s; score `0.8*active + 0.1*tagged`.
  Path B: displacement at least 2 m, sustained qualifying motion for 0.2 s and
  additional displacement at least 0.5 m; score `0.6 + 0.1*tagged`.
  Player availability is not required for B. Proximity or side alone is insufficient.
- M4 emits positive scores immediately when a path qualifies; after 3 consecutive
  positive reports it clears pending kickoff and records the first report time
  for eligibility consumption after 1 s. Interrupted reports reset confirmation.
  Missing ball emits no positive evidence and resets motion/report confirmation.
- M2 requires 3 consecutive available restart scores >=0.5 while D; simultaneous
  strong dead evidence takes priority. A single consistent known side across that
  confirmation becomes H/A; unknown or conflicting sides become X. Proximity then
  needs 12 consecutive credible samples (both teams available, visible ball,
  max score >=0.1, margin >0.05) to acquire/change ownership. Those 12 are **not**
  the restart-confirmation count. D persists otherwise; ordinary entry into D
  still requires 3 strong dead samples. All counters reset each half.
- **No label backdating**: transition applies on its confirming frame; earlier D/X
  labels remain. M4's first-report timestamp controls retirement, not output rewriting.
  Native halves remain `(1,11185,90651)` and `(2,110808,190197)` at 25 fps.

## Why incomplete: facts versus hypotheses

**Verified:** new interval totals are D 2,864 / A 54 / H 1 / X 15: **70 non-D remain**.
Both halves receive initial D. In the pre-second-kickoff interval M4 emits 35
available and 25 strong restart samples; M2 releases initial D after its 2,864-frame
prefix. A fresh actual-pipeline scan reproduced every new CSV label. The mechanism
is early heuristic restart support, not dropped transport, a fallback, serialization
or an indexing shift. The separate FAQ check uses 113742; the burned-in clock
anchor converts to 113741. That one-frame diagnostic distinction was corrected
without changing inference and does not explain 70 discrepancies.

**Verified:** first-half output begins with **12 D frames** where grading begins at
kickoff; first 125 labels are D 12 / X 11 / A 50 / H 52. Initial D plus waiting for
observed restart/confirmation creates startup latency; no backdating removes it.
The 12-frame duration must not be attributed to M2's 12-sample ownership rule merely
because the numbers coincide. The existing aggregate probe does not split the
latency among history availability, path A/B qualification and confirmation.

**Unresolved hypotheses:** approximate context plus preparatory movement may be
indistinguishable from authorized play; tag timing or retained pre-window motion
may contribute. Existing aggregates do not identify which motion path first fired
or establish referee authorization. No video annotation or external match evidence
was used. The correction cannot be called a reliable kickoff solution.

## Candidates, verified on checkpoint creation

All four CSV hashes were recomputed and matched their source manifests. All 12
original run files still match `data/kickoff-fix-20261117/previous-artifacts.json`.
Each candidate has 199,319 ordered rows; both pairs passed official format validation
and matched in separate same-machine runs. Neither is independently reproduced or
approved, and format/repeatability is not football accuracy.

| Purpose | Source | Candidate and repeat directories under `data/release/runs/` |
|---|---|---|
| Historical baseline; known 2,934-frame kickoff semantics failure | `90d1f4efa969f21b0b932d770e1011d23a7ed14d` | `20261117T102236151903Z/`, `20261117T102424208440Z/` |
| Current investigation only; 70 residual discrepancies and first-half latency | `48d67bb271ce0dd50d0d6a1ce9dd24111a32fe78` | `20261117T105211791158Z/`, `20261117T105410694264Z/` |

Each directory contains `candidate.csv`, `pipeline.json`, `evidence.json` and logs.

- Old SHA-256: `BE262BB468B3610289F94F4A45CB8D8A1D8879F675C2668E6267F68E62FCE62D`.
- New SHA-256: `E533FCDDF4522A1E2F7CB2F12E15DEDD65C7C0E9508FBF9EDA3F1652E81D0C01`.
- Exact investigation file: `data/release/runs/20261117T105211791158Z/candidate.csv`.

## Tests, evidence and reproduction

Prior runs passed **297 maintained tests, no skips**, including 14 new tests for
stationary pre-kickoff proximity; approximate tag entry/expiry; known/unknown
resumption; already-live start; missing observations; ambiguous tags; conflicting
sides; warm-up/jitter; later turnover/stop; fresh second half; dropped/shifted or
malformed prior; actual tag extraction; inclusive FAQ diagnostic. Existing 283
expectations were retained, including passes/deflections, turnovers, persistent D,
long-gap recovery, live boundary drift, jitter and half resets. M1 self-test,
13 standalone M2 tests and M4 tag assertions passed. These tests do not assert
perfect labeling at a live half start. No tests or generation rerun for this handoff.

Recorded environment: project-local Python 3.12.10; NumPy 2.5.4, pandas 3.1.1,
python-dateutil 4.0.0, tzdata 2026.6; Windows 11. Exact historical commands below
are for future reproduction, **not executed during checkpoint creation**. Full
generation must run from a clean separate checkout of frozen `48d67bb`, with the
same licensed inputs/pins; do not reset this checkout or reuse old output directories.
Manifests preserve exact child argv, input hashes, configuration and environment.

```powershell
# Working directory: integration checkout (frozen source for generation).
$python = 'C:/Users/oamu2/more-than-a-hack-2027/data/integration-attempt/data/release-env/Scripts/python.exe'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $python -B -m unittest discover -s tests -p test_kickoff_pipeline.py -v
& $python -B -m unittest discover -s tests -v
& $python -B module1/control_scores.py --test
& $python -B modulos/test_modulo2.py -q
& $python -B module4/test_stoppages.py
& $python -B run_release.py --data-dir C:/Users/oamu2/more-than-a-hack-2027/data
& $python -B run_release.py --data-dir C:/Users/oamu2/more-than-a-hack-2027/data --expect-sha256 E533FCDDF4522A1E2F7CB2F12E15DEDD65C7C0E9508FBF9EDA3F1652E81D0C01
# Existing exact investigation file, from the original integration checkout:
& $python -B evaluation/validate_submission.py data/release/runs/20261117T105211791158Z/candidate.csv
& $python -B kickoff_check.py data/release/runs/20261117T105211791158Z/candidate.csv
```

Check each required command status before proceeding. Recorded release runs exit 2
(blocked approval), required tests/generation/validator each exit 0; FAQ check exits
2 (semantic discrepancy). `run_release.py` creates unique directories automatically.
For future generated outputs, validate/check their new exact paths, not these old ones.

Existing ignored artifacts under `data/kickoff-fix-20261117/`:

- `baseline-diagnostics.json`, `corrected-evidence-diagnostics.json`: aggregate
  pipeline diagnoses and exact candidate reproduction assertions.
- `previous-kickoff-diagnostic.json`, `new-kickoff-diagnostic.json`,
  `repeated-kickoff-diagnostic.json`: published interval checks.
- `freeze-tests.log`, `kickoff-tests.log`, `full-tests.log`, `final-tests.log`;
  `first-release.log`, `second-release.log`: prior execution results.
- `repeat-verification.json`, `final-gates.json`, `previous-artifacts.json`:
  provenance/repeatability, blocked gates and historical preservation.
- `baseline_probe.py`, `corrected_probe.py` and their logs: local diagnostic
  helpers; `baseline-evidence.npz` contains restricted arrays. Keep these local,
  ignored and out of chat/Git; no raw observations are copied into this checkpoint.

## Scope retained, blocked gates and next questions

Unchanged: M3/M1 algorithms, numeric thresholds, units/missingness/full precision,
native frame indexing/half resets, explicit integrated execution, ordinary M2
transition policy, and X legality inside/outside halves. No public-window scoring,
parameter search, interval mask, external annotations or new data/model was used.
Only one general correction was tried; no subsequent tuning was performed.
Rejected approaches: overwrite the FAQ interval; treat tag start/end as exact
kickoff; accept proximity/side alone as restart; carry old approval claims forward.

Still blocked: `published_kickoff_diagnostic`, `independent_reproduction`,
`submission_approval`. M4/M2 plus integration owner must resolve semantics;
M5 plus a second teammate must independently reproduce an accepted source/hash;
M5/team lead must finish registered-name packaging and explicit submission approval.
Other-match generalization, referee authorization and full-match accuracy remain
unverified. Same-machine hashes cannot clear those gates.

Next three focused questions, for a later authorized debugging session:

1. Which restart path and consecutive samples first release D in each half, and
   does retained pre-tag history affect qualification? Add aggregate trace evidence
   before attributing causality; do not fit thresholds to the published interval.
2. Can permitted automatic inputs distinguish preparatory movement from live play
   beyond approximate kickoff context, or must the component contract expose that
   uncertainty? Justify any rule with invented/other permitted cases.
3. What general initialization/transition policy handles already-live graded starts
   without a false D prefix while preserving true pre-kickoff D and existing ordinary
   restart regressions? Any backdating proposal needs an explicit evidence contract,
   not a special-case boundary or relaxation to make the current interval green.

Candidates and historical reports preserved. No push, main merge, submission,
release approval or claim of resolution. Work stops after saving this checkpoint.
