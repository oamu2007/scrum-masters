# Team tasks 2 — route to submission

**Updated November 14, 2026.** Aim for a candidate on **November 15** and internal submission on **November 16**. [SUBMISSION.md](SUBMISSION.md) gives **November 17** as the official deadline, but does not give a cutoff hour or timezone. Must confirm those details with the organisers.

The shared reader and control scoring are already working together on `integration-attempt` [NOTE: the current integration-attempt state is the constantly mentioned 18270a1]. Keep that work. The smallest remaining route is to add M4's tracking-based stoppage evidence, repair M2's possession memory, connect them through M1's runner, and have M5 independently regenerate the release file. `main` does not yet contain the module integration.

## Current position

| Module | Branch | Completed work | Required dependency update | Remaining work | Acceptance gate |
|---|---|---|---|---|---|
| M1 — control and runner | `module1-control-scores`; newer implementation on `integration-attempt` | Shared-reader scoring, team availability, full-precision evidence and legacy compatibility are integrated. | Fast-forward the owner branch from `06e4c9b` to tested integration `18270a1`. | Own the runner, connect M4/M2 and write the final CSV. | Actual producer-consumer tests; full run and official validation. |
| M2 — temporal possession | `modulo2` | Simple label loop; retains previous control on missing ball/ties; optional outside-half mask. | Merge tested integration `18270a1` into this divergent branch, then consume the agreed M4 interface. | Confirm turnovers, retain dead state, support restarts, handle unavailable/conflicting evidence and reset halves. | Invented sequences pass through actual evidence producers. |
| M3 — shared reader | `module-3-tracking-reader`; same implementation also on `integration-attempt` | Mapping, units, channel validation, indexing, missingness and complete-stream checks. Its tip is already in integration. | None for its implementation; help consumers obtain `18270a1`. | Contract support and fixes only for demonstrated regressions. | Preserve its 19 fixture tests and the established full-stream contract. |
| M4 — stoppages/restarts | `module4-stoppage-restarts` | Automatic set-piece window extraction and known/unknown side mapping. | Merge tested integration `18270a1` into this divergent branch. | Add tracking-based dead/restart evidence and availability; keep windows approximate. | Pass/occlusion, boundary stoppage and known/unknown restart cases. |
| M5 — validation/release | No separate branch supplied | 36 integration component tests, M1 self-test, M4's standalone assertions and official validator exist. | Create proposed a `module5-validation` from tested integration `18270a1` (M3 and M1 proved changes); later use accepted integrated M2/M4. | Cross-module tests, reproducible environment, independent regeneration and submission package. | Behavioral tests, official validation and another teammate's matching output SHA-256. |

### Evidence behind this status

Both repositories successfully fetched remote references on November 14. These are refreshed references, not cached guesses. The original checkout remains on `module-3-tracking-reader`; `data/integration-attempt/` remains on `integration-attempt`. Both were clean when inspected.

| Inspected remote branch, in both repositories | Full tip SHA |
|---|---|
| `main` | `ae65c5f212c1bec4675f1a703e134dfe4752be4f` |
| `module-3-tracking-reader` | `63e64755d9333d72fc853ac47362b790578c02dc` |
| `module1-control-scores` | `06e4c9bc232c751fb9aaec00093fa8c087349527` |
| `module4-stoppage-restarts` | `aa9cf275fc8d82a1ed7cfc0e409cc777750038b7` |
| `modulo2` | `aae0fe03fcd30fa7b4db9bc64fcf187191e012f1` |
| `integration-attempt` | `18270a1c582dc853645f49afa40683c076baacf6` |

History confirms `e0a0fd2` corrected M3 metadata mapping/speed conversion, `63e6475` added ball-reference and ambiguous-position validation, `303513d` completed shared-reader M1 scoring, and `18270a1` merged the M3 validation fixes into integration. Integration's M1 implementation/tests match `303513d`; its M3 implementation/tests match `63e6475`.

The short checks were rerun in the integration clone: **36 tests passed** and **M1 self-test passed**. The saved November 14 verification reports support **199,319 ordered frames**, indices **0–199318**, **46 slots per frame**, **113,488 observed-ball frames**, and **1,069 observed-ball frames missing evidence from at least one team**. They also record exact equality of all seven M1 arrays with the checked integration snapshot. Source inspection and tests confirm finite score ranges and availability semantics. The unchanged full-match scan was not repeated for this plan.

My local evidence (for future reference): `data/_m3_metadata_verification_20261114/full_reader.json`, `evidence_integration_snapshot.json` and `sandbox.json`; supporting review: [M3_M1_REVIEW.md](M3_M1_REVIEW.md). These local data-directory reports are evidence for the team, not public deliverables. A fresh recalculation recorded there is not independent reproduction by another teammate.

### What changed since the older reviews

Read [TEAM_TASKS.md](TEAM_TASKS.md) for module purposes and [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) for the earlier proposal.

| Earlier finding | Current conclusion |
|---|---|
| M3 speed units/mapping; ball references and ambiguous position declarations | **Resolved** by `e0a0fd2` and `63e6475`; integrated in `18270a1`. Do not implement these again. |
| M1 bypasses M3; partial coordinates and missing-team evidence cause problems | **Resolved in integration** by `303513d`, including availability flags. The standalone M1 branch is stale, not proof that this work is missing. M2 still needs to use those flags. |
| Rounded evidence can change decisions | Full-precision arrays are available. **Runner wiring remains to verify**; diagnostic CSV must not become inference input. |
| M4 only extracts tags; M2 immediately switches, copies tag intervals into D, forgets D and leaks state across halves | **Still open.** Current tips and source retain those behaviors. |
| Pending merge/staging risk in M3/M1 review | That merge is now committed, followed by `303513d` and `18270a1`; both inspected checkouts are clean. Preserve existing data exclusions. |
| Missing release runner and independent reproduction | **Still open.** The older isolated harness and same-machine repeat runs do not satisfy release acceptance. |

## Dependency updates: recommended, not performed

Use the tested integration commit as the common base. It contains both required M3 commits and the completed M1 implementation. Before any later update, check for uncommitted work, fetch and inspect new changes if a branch tip has moved. [I also plan on submitting all the integration-attempt and TEAM_TASKS_2 current changes to main, for easier pulling]

| Branch to update later | History-preserving path at the inspected tips |
|---|---|
| `module1-control-scores` | Its tip is an ancestor of `18270a1`. On that branch, `git merge --ff-only 18270a1` advances it without replaying commits. Stop and inspect if the fast-forward is no longer possible. |
| `module4-stoppage-restarts` | Neither tip contains the other. On that branch, `git merge 18270a1` preserves its tag-extractor commit and brings in tested M3/M1. Review conflicts and run checks before further work. |
| `modulo2` | Also divergent. On that branch, `git merge 18270a1` preserves its decoder history and supplies the shared contracts. |
| M5's proposed branch | Start `module5-validation` at `18270a1`. No supplied M5 branch needs rescuing or merging. |
| `module-3-tracking-reader` | No extra merge needed: `63e6475` is already an ancestor of integration. |

These commands describe future actions on the indicated branches, not instructions to switch the current checkout during this planning task. Do not cherry-pick the same fixes onto every branch, merge the stale M1 branch as a substitute for `303513d`, or move `main` before release gates pass.

## M1 — control evidence and the integration runner

**Purpose.** Provide per-frame control evidence and own the command that connects all modules into the submission CSV.

**Already available—retain this.** Integration's [control_scores.py](data/integration-attempt/module1/control_scores.py) and [usage guide](data/integration-attempt/module1/CONTROL_SCORES.md) provide `score_frame`, `iter_control_scores` and `build_evidence`. Distances are metres; proximity scores use `exp(-distance/tau)`. `home_available` and `away_available` say whether that side has usable ball/player evidence. Legacy entry points remain available. These are completed scoring tasks.

**Integrate before starting.** Fast-forward the owner branch as above. Read `module1/CONTROL_SCORES.md` there, then agree the M4 fields and M2 call together. The links above point into the local integration clone because this original checkout does not yet contain M1.

**Next work, in priority order.**

1. Add the runner proposed below. Stream M3 once and pass the same observation to M1 and M4 without modifying it. Store compact evidence arrays, not every tracking dictionary.
2. Give M2 full-precision score arrays and both availability flags. Rounded evidence CSVs remain diagnostic. Do not use the legacy five-array return as the complete new decoder contract.
3. Obtain frame count, frame rate, paths and half blocks from [games.py](games.py). Exhaust M3, check evidence lengths/types and write every frame, including X outside the halves. Respect `MTAH_DATA_DIR` and an explicit data-directory argument.
4. Make errors fail the command clearly; do not leave a partial file presented as a successful submission. Fix encoding/newline/output behavior and document configuration and overwrite rules.

**Done when.** One command from the repository root produces the full CSV without ground-truth input, actual M1/M4 outputs reach M2 correctly, existing scoring tests still pass, and the official validator accepts the exact output. Proposed command to implement, **not available yet**:

```powershell
python run_possession.py --data-dir C:\path\to\bundle --out data/release/<team_name>.csv
```

Replace `<team_name>` with the registered name. The bundle directory contains `tactical/`. Record the configuration used; thresholds must not be chosen using public labels.

**Handoff to the next module.** M2 gets named, full-precision evidence arrays. M5 gets the runner command, configuration, dependency list, aggregate run report and candidate output for independent comparison.

## M2 — temporal possession

**Purpose.** Convert evidence into H, A, D or X while remembering possession through passes and brief deflections.

**Already available—retain this.** `modulos/modulo2.py` on `modulo2` returns a label list, remembers control through missing-ball/tied-score frames and can emit X through a supplied half mask. Keep the simple loop and list output. Its immediate score winner, initial D, raw-window dead mask and lack of half resets still need repair.

**Integrate before starting.** Merge the tested common base. Use M1's named arrays and the proposed M4 contract below. Revise the decoder input explicitly: stoppage evidence replaces the assumption that every restart window is dead time. Make the half information mandatory in the canonical runner.

**Next work, in priority order.**

1. Require `home_available & away_available` before a score comparison can force a turnover. Require credible opposing control over the agreed confirmation period; one nearest-player change is insufficient. Keep magnitude, margin and duration in a documented configuration.
2. Store D as a persistent state. Window expiry, missing ball or a closer player alone must not resume play. Leave D only on supported restart evidence; resolve side from supported side/control evidence, never default unknown to away.
3. Handle unavailable, weak, tied and conflicting evidence explicitly. Proposed policy for agreement: retain an established live side during uncertainty; use X before any supported state; remain D until play is supported as resumed; if resumed but side unknown, use X until credible control. Specify priority when dead and restart evidence conflict.
4. Reset current state, last controlled side and pending confirmation at each half. Use `half_video_blocks(GAME)`: inclusive **11185–90651** and **110808–190197**. Emit X everywhere else. Do not substitute the second-half kickoff anchor for the graded start.
5. Validate lengths, finite scores and legal side values. Remove reliance on `periodosDetenido` as truth: it both copies approximate windows into D and incorrectly includes their exclusive end frame.

**Done when.** Invented pass and brief-deflection sequences retain H; sustained credible away control switches once; missing home evidence never makes away win by comparison with zero. Confirmed stoppage stays D beyond a tag window and through missing observations, until a supported restart. Known/unknown/conflicting restarts follow the agreed policy. Running half two independently gives the same result as half two in a full run. Every input frame has one legal output.

**Handoff to the next module.** M1 gets the documented decoder signature, configuration and label list. M5 gets executable sequence tests and a short explanation of each transition rule. Decisions about uncertainty, conflict priority and confirmation timing belong in the team discussion; implementing the agreed rules is M2's task.

## M3 — shared tracking reader

**Purpose.** Give M1 and M4 the same trusted observations without duplicate raw-file parsing.

**Already available—retain this.** [tactical_tracking.py](starter/tactical_tracking.py), [its contract](starter/TACTICAL_TRACKING.md) and [tests](tests/test_tactical_tracking.py) cover metadata slot/team mapping, channel references, normalized positions, metre conversion, supplied speeds converted from km/h to m/s where declared, strict frame order and missing observations. Participant frame ID minus one is the mapping; million-scale corrected-tracking offsets do not apply. Keep all metadata slots and all frames. `None` stays missing; a slot is not a real player identity.

**Integrate before starting.** No new reader feature is required. Ensure both producers obtain `18270a1`; point them to `iter_tracking_frames(game=GAME, data_dir=None)` and the existing fields. M4 must not divide the already-corrected `speed_mps` by 3.6 again. Homography helpers take normalized coordinates, not metres.

**Next work, in priority order.**

1. Help M1/M4 verify their dependency versions and consume the contract correctly.
2. Answer concrete contract questions, especially independent speed missingness, partially missing positions and unknown metadata references.
3. Fix only demonstrated reader regressions, with a small invented regression test. Repeat full-file validation only if reader/input changes justify it.

**Done when.** Both producers use the tested reader with correct units/missingness, all 19 reader tests pass, and no integration change invalidates the documented full-stream result. Full-length validation completes only when the iterator is exhausted.

**Handoff to the next module.** M1/M4 receive unchanged frame dictionaries and an explicit reader revision. M5 retains the reader tests and aggregate evidence. There is no requirement to invent extra features to occupy this module.

## M4 — stoppage and restart evidence

**Purpose.** Supply evidence about stopping/resuming play; M2 owns the final state transition.

**Already available—retain this.** `module4/stoppages.py` on its branch extracts set-piece windows and maps known club tags to H/A while preserving unknown sides as `None`. Its small `test_stoppages.py` assertions cover extraction and side mapping. Current code still has no tracking-based evidence producer. Reuse [load_smart_tagging.py](starter/load_smart_tagging.py); its `end_frame` is exclusive.

**Integrate before starting.** Merge the tested common base, use corrected M3 observations and agree this minimal per-frame contract with M2/M1. These fields are **proposed, not implemented**:

| Field | Meaning |
|---|---|
| `dead_score`, `restart_score` | Finite support values in [0,1], not calibrated probabilities. |
| `dead_available`, `restart_available` | Separate booleans: enough observations existed to evaluate that signal. An unavailable score is zero with its flag false. |
| `restart_side` | H, A or `None`. A known side does not by itself establish that play resumed. |

Provide these for every tactical frame, as scalars from a frame function or matching full-length arrays. Document which observations each signal requires and reset movement history at half boundaries.

**Next work, in priority order.**

1. Add a small history of observed ball movement/boundary clues and nearby/team player movement. Use metres, corrected m/s and elapsed seconds from the configured frame rate. Do not infer long player identities from track slots.
2. Combine clues conservatively: observed boundary movement plus a pause can support dead evidence; renewed ball/player activity can support a restart. One noisy outside-pitch point is not conclusive. Missing ball alone must never prove a stoppage.
3. Use automatic windows as approximate context. A window's start/end is not an exact whistle/restart, and its entire interval must not become D. Unknown tag sides remain unknown; conflicting side clues must not silently become H/A.
4. Add invented cases: live pass with occlusion; boundary exit followed by a pause; resumed movement with known side; supported restart with unknown side; tag-only window and missing observations. Cover exact exclusive endpoints.

**Done when.** The pass/occlusion has no positive stoppage claim caused solely by absence. The boundary-pause case supplies supported dead evidence, and observed resumption supplies restart evidence. Unknown side remains `None`; unavailable evidence is distinguishable from available zero support. The actual outputs work in M2 tests. Document that some fouls/interior stoppages may remain undetected.

**Handoff to the next module.** M2 gets the five evidence fields and examples of their meaning. M1 gets the callable producer and its configuration. M5 gets the synthetic tests, including missing and conflicting evidence.

## M5 — validation, reproduction and release

**Purpose.** Catch cross-module mistakes and prove another teammate can regenerate the exact release file.

**Already available—retain this.** Integration has 19 M3 tests plus 17 M1 tests and the M1 self-test. M4 has a separate assertion script on its branch; it is not included in those 36 tests. [validate_submission.py](evaluation/validate_submission.py) checks the official file contract. Historical harness results are useful evidence, not a maintained acceptance suite.

**Integrate before starting.** Create the proposed validation branch from the tested common base when implementation work resumes. Read [CHALLENGE.md](CHALLENGE.md), [EVALUATION.md](EVALUATION.md), [SUBMISSION.md](SUBMISSION.md) and [RULES.md](RULES.md). Start tests now, alongside M2/M4; do not wait for the full runner.

**Next work, in priority order.**

1. Write small invented tests that drive the actual M3 → M1/M4 → M2 handoffs. Early stubs can specify the contract, but replace them with the real producers before acceptance. Ensure the test command includes M4 and the new behavioral tests and exits unsuccessfully on failures.
2. Cover indexing/units/missingness, weak or unavailable opposing evidence, pass/deflection retention, confirmed turnover, persistent D, restart side/availability/conflicts, exclusive tag endpoints and fresh half state. Check inclusive half endpoints and X immediately outside them. No restricted tracking rows in fixtures.
3. Test runner serialization and repeat-run determinism, then run the full candidate and official validator. Log aggregate counts and configuration, not restricted tracking exports. Existing component checks are `python -m unittest discover -s tests -v` and `python module1/control_scores.py --test` on integration.
4. Pin the Python version and actually used dependency versions. Current requirements leave NumPy/Pandas unpinned; record a reproducible runtime, not merely a copied local environment. A clean checkout must work without ignored review files, the nested integration clone or undeclared packages.
5. Have another teammate independently install the fixed candidate checkout, use their supplied bundle and run the documented command. Compare file SHA-256 with M1's result. Record both runs' candidate SHA, configuration, environment, validator result and hash. A second run on one machine is useful but insufficient.
6. Prepare the team-named technical document and release checklist. M5 is responsible for submission coordination, designating the actual teammate who will submit and a backup, and retaining the confirmation. No submission is being made by this plan.

**Done when.** Behavioral tests and the official validator pass, two teammates independently regenerate identical bytes, public source can reproduce the file without restricted assets, and the three deliverables and submission access are ready.

**Handoff to the next module.** Give M1 actionable failures while building. Give the designated submitter the fixed source revision, exact validated CSV/hash, technical document, public repository URL and completed checklist.

## November 14–17 schedule and gates

| Date | Work that can run concurrently | Gate / decision |
|---|---|---|
| **Nov 14** | Update owner branches and agree interfaces/policies. M4 implements evidence; M2 repairs state logic against invented inputs; M1 builds runner wiring; M5 writes acceptance tests. M3 supports dependencies and contract questions. | Shared tested base and agreed field/transition meanings. Do not redesign the architecture. |
| **Nov 15 — candidate target** | Complete real producer-consumer tests while M5 prepares pinned dependencies and the technical document. | Integrate reviewed M4 evidence, then its M2 consumer, then completed M1 runner and M5 release checks. Tests can land earlier; this is the dependency gate order. Run the full candidate and official validator. |
| **Nov 16 — internal submission target** | Another teammate regenerates from a clean checkout; M5 checks access, public source and deliverables. | Freeze candidate SHA/configuration/dependencies and obtain matching SHA-256. Submit only after the checklist passes; retain confirmation. |
| **Nov 17 — official deadline** | Buffer for confirmed defects, access issues or an allowed replacement response. | Verify the organisers' cutoff beforehand. Any changed candidate must repeat affected tests, official validation and independent hash verification before replacing the submission. |

**If critical work slips on November 15:** hold a team checkpoint before adding features. Drop optional evidence refinements and diagnostics first; concentrate on the smallest tracking-based M4 rules and tested M2 transitions. If the candidate still fails on November 16, explicitly decide which defects can be fixed and fully reverified before the confirmed deadline. Do not describe a format-valid harness or untested fallback as the completed pipeline.

Keep essential correctness: dependency versions, units/indexing, availability, temporal/dead-state behavior, supported restarts, half resets, deterministic output and reproduction. Defer extra heuristics, broad smoothing/interpolation, visual dashboards and parameter sweeps. No replacement tracking, identity reconstruction, broadcast synchronization, broad architecture redesign or public-window optimization. Public labels may check pipeline correctness, never choose parameters or select the winning candidate; do not create human labels for this match.

**Component tests and a valid CSV do not establish full-match possession quality.** Invented cases establish specific behaviors, and the validator establishes format. Record model limitations honestly without claiming unmeasured accuracy.

## Release checklist

- [ ] One documented inference command uses only permitted inputs and no ground-truth input; it works from a clean checkout with the provided data bundle.
- [ ] Exact header `frame,label`; **199,319 data rows**, frames **0–199318 in order**, legal H/A/D/X labels and no missing cells; X outside the published half blocks.
- [ ] Actual producer-consumer behavioral acceptance tests pass, including deflections, availability, dead-state persistence, restarts and half resets.
- [ ] Official validation passes on the exact team-named file: `python evaluation/validate_submission.py "data/release/<team_name>.csv"`.
- [ ] Candidate commit, configuration, Python and dependency versions are fixed and recorded. Repeat generation is deterministic.
- [ ] Another teammate independently regenerates from a clean checkout and obtains matching SHA-256. PowerShell check: `Get-FileHash -Algorithm SHA256 "data/release/<team_name>.csv"`.
- [ ] Public reproducible source includes installation/run instructions and tests. Restricted assets and reconstructive derived data are excluded; preserve the existing data ignore rules and inspect tracked files/history before publication.
- [ ] `<team_name>.csv` and `<team_name>.md` or `<team_name>.pdf` are ready. The technical document states approach, assets used/dropped, training data (or none), possession rules, limitations and reproduction steps.
- [ ] Registered team identity, emailed form URL, Google upload access and official deadline cutoff/timezone are confirmed. The repository currently supplies the date only.
- [ ] **M5 owns submission coordination:** record one actual submitter and backup, submit one team response using the verified artifacts, and retain confirmation. The team authorizes that later action; this planning task submits nothing.

## Next three actions

1. **M1/M2/M4, with M3 support:** obtain the tested integration base using the history-preserving paths above; agree M4 fields and M2's uncertainty/restart rules.
2. **M4 and M2 implement; M5 tests in parallel:** finish the minimal evidence and state transitions against invented acceptance cases. M1 connects the real producers through the runner.
3. **M1 and M5:** produce the November 15 candidate, fix failures, then arrange independent regeneration and the November 16 submission package.

**Decisions for a short team discussion:** choose control credibility/confirmation parameters and confirmation-versus-backdating behavior without public-label tuning; agree initial/unknown-side and conflicting dead/restart policies; name the independent reproducer, submitter and backup; confirm submission access/cutoff and the reduced scope to use if the candidate slips. Record these decisions in the configuration and technical document so teammates implement the same rules.
