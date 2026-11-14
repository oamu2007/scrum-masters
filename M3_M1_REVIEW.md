# M3 correction and pending M1 integration review

Review date: **November 13, 2026**, America/Tijuana. This report reviews local source and executed checks, not prior agent completion claims. No implementation, index, merge, commit, branch or remote reference was changed by the review.

## 1. Verdict

**M3's speed-correction integration gate in `INTEGRATION_PLAN.md` passes.** The committed reader converts declared km/h exactly once, preserves declared m/s, and retains the full tactical timeline, slots, positions and independent missingness. All 15 M3 tests passed. Every player observation in the local match was independently checked against its raw fields.

**M1's shared-reader and availability gate passes for the working-tree candidate.** It consumes corrected M3 observations, retains metre distances and the original score formula, exposes availability, preserves inputs and keeps temporal decisions out of M1. All 32 tests in the clone passed (17 M1 plus 15 M3). The complete candidate output exactly matches both an independent calculation and the original M1 implementation wherever equivalence is expected.

**The stronger requirement to reject all missing/inconsistent channel metadata is only partially satisfied.** Two confirmed M3 validation gaps remain: ball channel references are not validated, and contradictory position declarations can be accepted. Neither defect is triggered by the supplied local tactical metadata. They do not undo the speed correction or the measured M1 equivalence, but the reader must not be described as comprehensively validating metadata until they are fixed.

**Git recording verdict: ready for two accurately scoped milestone commits, with those M3 limitations recorded; not ready for an unconditional “all metadata validation complete” sign-off.** No M1 implementation correction is required by the executed checks. The current index alone records only the dependency merge; it omits the new M1 implementation, tests and documentation. Record the dependency merge separately, then explicitly stage the three M1 files. This is a recommendation only; none of those actions was executed.

The next implementation task should be the small M3 metadata-validation follow-up below, followed by M4 evidence work. M2 can use the new availability contract for its planned repairs, but M1 has not implemented those repairs or a final submission pipeline.

## 2. Exact reviewed state

For brevity, **original** means `C:\Users\oamu2\more-than-a-hack-2027`; **clone** means `C:\Users\oamu2\more-than-a-hack-2027\data\integration-attempt`.

| State | Original repository | Isolated integration clone |
|---|---|---|
| Branch | `module-3-tracking-reader` | `integration-attempt` |
| HEAD | `e0a0fd2f098194704b0493a2ea335ea3b4b9d06c` | `06e4c9bc232c751fb9aaec00093fa8c087349527` |
| MERGE_HEAD | Absent | `e0a0fd2f098194704b0493a2ea335ea3b4b9d06c` |
| Initial porcelain status | Empty; tracked tree and index clean | Exact status below |
| Unresolved index conflicts | None | None (`git ls-files -u` empty) |
| Corrected M3 in HEAD history | Yes | **No**: `merge-base --is-ancestor e0a0fd2 HEAD` exits 1 |
| Corrected M3 in index/working tree | Yes | Yes, pending merge |

Clone status at the start and end of source review:

```text
M  .gitignore
 M module1/control_scores.py
A  starter/TACTICAL_TRACKING.md
A  starter/tactical_tracking.py
A  tests/test_tactical_tracking.py
?? module1/CONTROL_SCORES.md
?? tests/test_control_scores.py
```

The first column describes the index; the second describes unstaged changes. Thus:

- **Already committed in the original:** corrected M3 implementation, tests and contract at `e0a0fd2`, plus that commit's `.gitignore` changes.
- **Already committed in clone HEAD:** original M1 implementation at `06e4c9b`; corrected M3 is not yet an ancestor.
- **Staged in the clone:** three M3 files plus `.gitignore`.
- **Unstaged in the clone:** replacement contents of `module1/control_scores.py`—this is the implementation reviewed, not its older HEAD/index version.
- **Untracked in the clone:** `module1/CONTROL_SCORES.md` and `tests/test_control_scores.py`; both were read and tested.

The original has no `module1/control_scores.py`, `module1/CONTROL_SCORES.md` or `tests/test_control_scores.py`; that is expected for its M3 branch. Those files were reviewed in the clone. The old M1 comparison source was extracted separately from the recorded `06e4c9b` commit.

### Freshness and preservation

A read-only command was attempted, without fetching or changing either repository's Git state:

```powershell
git ls-remote origin refs/heads/main refs/heads/module-3-tracking-reader refs/heads/module1-control-scores refs/heads/integration-attempt
```

It failed with `getaddrinfo() thread failed to start`. Remote freshness is therefore **unverified**. Both repositories locally record `origin/module-3-tracking-reader=e0a0fd2...`, `origin/module1-control-scores=06e4c9b...`, and `origin/main=ae65c5f212c1bec4675f1a703e134dfe4752be4f`. No latest-remote claim is made. The review applies to the exact local sources identified here.

Git reads used `GIT_OPTIONAL_LOCKS=0` where state was captured. Before/after evidence records index and Git control-file hashes, refs, source hashes and status. Python ran with `PYTHONDONTWRITEBYTECODE=1`; an existing local review environment was reused. New harnesses and aggregate results are under the ignored `data/_m3_m1_review_20261113/`. The only new unignored deliverable is this report. Existing reports and ignore rules were preserved.

Applicable instructions: the supplied SCRUM MASTERS instructions. No on-disk `AGENTS.md` was found in either repository or the checked ancestors. Read the current `INTEGRATION_PLAN.md`, historical `MODULE_REVIEW.md`, relevant `TEAM_TASKS.md`, `DATA.md`, `RULES.md`, `games.py`, dependency declarations, and all requested implementation/test/contract files where present.

### M3 equality across the two locations

For each of `starter/tactical_tracking.py`, `starter/TACTICAL_TRACKING.md` and `tests/test_tactical_tracking.py`:

- The clone's **staged Git blob is byte-for-byte identical** to the corresponding blob at `e0a0fd2`.
- Original and clone working copies equal that commit's contents after CRLF normalization.
- Working-copy bytes differ only in line endings: the original reader has LF, while the clone reader has CRLF. This is not a source-logic difference. No unstaged M3 changes exist.

Presence in the merge index does not change ancestry. Only recording a merge commit would make corrected M3 a parent/ancestor of the integration branch's HEAD.

Working-tree SHA-256 identifiers for the unrecorded M1 candidate:

| Clone path | SHA-256 |
|---|---|
| `module1/control_scores.py` | `3869bd7a7539622a28066ae07fe358a211a8a7705b7becdcfd97ddbfb470afd1` |
| `module1/CONTROL_SCORES.md` | `68dfb9f35794f743085f06dd7b45374957f9134fd926b2c7b95947874a47aad0` |
| `tests/test_control_scores.py` | `42067dec3a5696ef732aef30698450c8b19cd2b3c187df17358609fa06a3ef46` |

## 3. Actionable findings, ordered by severity

No defect was demonstrated in the normal M3→M1 inference path on the supplied data. The following are confirmed validation gaps and recording risks, not style requests.

### R1 — Medium: ball channel references bypass metadata validation

**Location:** original and clone, `starter/tactical_tracking.py:76–79`, `:86–116`, `:180–182`; original commit `e0a0fd2`. The tests' ball metadata is declared at `tests/test_tactical_tracking.py:50–54`, but the negative metadata tests at `:150–190` do not alter it.

**Trigger:** an XML ball register with no `BallChannelRef` children, an unknown `channelId`, or reversed x/y references. The outer separator remains comma, so the shape check passes. `_speed_divisor` validates player references but never resolves the ball references. `_iter_frames` nevertheless assumes the first two ball fields are normalized x/y.

**Executed evidence:** all three independently invented invalid variants were accepted and yielded observations. With reversed ball x/y declarations, an invented raw pair `(0.2,0.8)` is still interpreted as x=0.2/y=0.8. A reader restricted to x/y order should reject that layout instead of accepting coordinates with the wrong meaning. The actual local tactical ball x/y references were independently checked and are correctly ordered, so this did not corrupt the reviewed full-match run.

**Consequence:** malformed or unsupported metadata can silently move the ball and therefore change M1 distances and future M4 boundary evidence.

**Smallest fix:** validate the ball register's reference count/types, resolve its referenced channels, and require the supported normalized x/y ordering before opening the raw stream. Add missing/unknown/swapped-reference regressions. Ball speed need not become a public output. Do not build a general EPTS remapper.

### R2 — Medium: contradictory position declarations are accepted

**Location:** original and clone, `starter/tactical_tracking.py:99–107`; contract claim in `starter/TACTICAL_TRACKING.md:71–74` and `:135–139`.

**Trigger:** a position channel contains `<Unit>normalized</Unit>` followed by another `<Unit>m</Unit>`. Position validation uses `findtext`, which checks only the first value. Speed validation, in contrast, explicitly requires exactly one Name and Unit.

**Executed evidence:** the independently invented duplicate, contradictory x-position unit was accepted. The supplied local metadata has the expected single declarations.

**Consequence:** the broad promise that contradictory metadata fails before streaming is not fully true. Ambiguous input can be interpreted as normalized and scaled to metres without a clear failure.

**Smallest fix:** apply the same exactly-one, nonempty Name/Unit validation to position channels; then require the supported pairs. Add duplicate Name/Unit regressions. Existing explicit checks for missing/unsupported/conflicting player-speed units can be retained.

### R3 — Recording risk: committing only the index omits the M1 candidate

**Location:** clone index versus `module1/control_scores.py:63–139`; untracked `tests/test_control_scores.py` and `module1/CONTROL_SCORES.md`.

**Trigger:** a plain commit of the current index, described as completing M1 integration. That index still has the **old** M1 implementation and neither new M1 file. It contains only the M3 dependency merge and inherited ignore changes.

**Consequence:** the recorded branch would not contain the implementation that passed this review. Conversely, `git commit -a` would mix M1 code into the merge while still omitting its untracked tests and contract.

**Action:** use the two-commit sequence below. This is a Git-scope issue, not a missing M1 algorithm.

### R4 — Scope note: the merge includes unrelated ignore-policy changes

**Location:** `.gitignore:67–69` in both repositories and the clone's staged diff, inherited from `e0a0fd2`.

The staged change retains `REPO_ANALYSIS.md`, **removes the `TEAM_PLAN.md` ignore entry**, and adds `INTEGRATION_PLAN.md` and `MODULE_REVIEW.md`. It is identical to the M3 commit's `.gitignore`; it is not a new unstaged M1 edit. It does not affect inference or belong to M1's functional gate. Keep it visible in the dependency merge's description and preserve it. If the team later wants a different rule for `TEAM_PLAN.md`, handle that as a separate intentional change; do not quietly undo it during this review or discard local reports.

### Nonblocking API boundaries

The canonical APIs expect M3-shaped dictionaries. Wrong coordinate types are rejected by Python `TypeError`; unknown observed teams raise an explicit `ValueError`. Missing/nonfinite numerical coordinates are handled as unavailable, as intended. There is no general schema/coercion layer, which is acceptable for this small internal handoff. The retained low-level distance/score helpers assume meaningful nonnegative distances; the canonical path supplies them. No new schema framework or broader API redesign is justified here.

## 4. M3 gate assessment

| Requirement | Evidence and result |
|---|---|
| Resolve raw fields to player slots and x/y/speed definitions | `_read_metadata`/`_speed_divisor` follow PlayerChannelRef→PlayerChannel→Channel, check player IDs against XML Player order, and require x/y/speed layout. Shuffled declarations/IDs work; mismatched/reversed player registers fail. **Pass for player fields. Ball-reference gap is R1.** |
| km/h converted exactly once | Supported pair `speed_kph`/`kph` selects divisor 3.6; only player parsing uses it. Independent 36→10 regression passed, as did every finite speed in the full file. **Pass.** |
| Declared m/s unchanged | Supported `speed_mps`/`m/s` selects divisor 1.0. Independent raw 36 remains 36, and the branch test also checks 10 remains 10. **Pass.** |
| Unsupported/missing/inconsistent metadata errors | Missing/unknown player references, wrong slot order, nonnormalized position units, unsupported/conflicting/missing speed declarations and mixed slot-speed units are covered. **Partial overall: R1/R2.** |
| Independent position/speed missingness | Both coordinates must be finite for a position; nonfinite speed becomes None independently. Finite speed survives absent position. **Pass.** |
| Coordinate conventions | x/y normalized values retained; metre coordinates use 105.3×68. Ball exposes coordinates only. Out-of-pitch finite positions are retained. **Pass.** |
| Index/order/slots/count | Every ATD ID is checked against record number; yielded frame is ID−1. Full read verified 199,319 frames and 46 slots per frame, including ungraded periods. **Pass.** |
| Independent returned observations | Existing tests mutate a later observation; independent full check retains and compares the first observation after exhaustion. **Pass.** |
| Streaming/final validation | Metadata checked before raw reading; per-record checks remain lazy; count verified on exhaustion. Truncated/duplicate fixtures fail, and invalid CLI input exits 1. **Pass.** |

The updated M3 fixtures are materially better than the earlier speed tests. They explicitly declare km/h, use 7.2/10.8 as 2/3 m/s, test 36→10 and the separate m/s variant, and shuffle PlayerChannel declaration order and IDs. Those assertions would expose the original unit bug and a parser that incorrectly used declaration order. The uncovered cases are specific metadata-negative tests, not a failure of all test evidence.

## 5. M1 and actual handoff assessment

`module1/control_scores.py` now imports `starter.tactical_tracking.iter_tracking_frames` directly (`:18–19`). The duplicate raw parser is removed. No canonical code path reads ATD independently; the separate raw reading performed by this review is an independent oracle, not an adapter added to the candidate.

| API | Actual behavior | Review result |
|---|---|---|
| `score_frame(observation, tau=3.0)` (`:63–98`) | Fresh dictionary with seven evidence fields; metre positions only; observed finite players grouped by H/A. No input mutation, slot-identity tracking or temporal state. | **Pass.** Known 5 m/1 m distances and formula, symmetry, missingness, speed independence and immutability independently checked. |
| `iter_control_scores(...)` (`:101–112`) | Directly streams M3, adds frame to evidence, closes its source in `finally`. | **Pass.** Actual XML/TXT handoff and laziness/close tests; full `build_evidence` exhausts this path. |
| `build_evidence(...)` (`:115–132`) | Seven `(n,)` arrays; bool flags, float64 distances/scores; checks sequential frame indices and expected count. | **Pass.** All seven arrays exactly match the independent full-data oracle. |
| Legacy `build(...)` (`:135–139`) | Calls `build_evidence`, returns five arrays in the original order, with int8 visibility. | **Pass.** Compatibility tested on invented data; new evidence values exactly match old committed implementation on the full file. |
| `write_csv(...)` / CLI (`:142–166`, `:185–209`) | Old six-column writer calls remain valid; two optional availability columns must be supplied together. CLI now emits eight diagnostic columns, documented as rounded and not canonical inference. | **Pass for stated compatibility.** Tests exercise headers, blanks, rounding and invalid-input nonzero exit. No final `frame,label` submission is claimed. |

Evidence contract verified:

- `ball_visible`: both ball metre coordinates finite.
- `home_available` / `away_available`: an observed ball plus at least one observed finite position for that side. Speed availability is irrelevant.
- Unavailable distances are NaN; unavailable scores are zero and the corresponding flag is false.
- Scores use `exp(-distance/tau)`; tau is checked as finite and strictly positive before processing, including missing-ball cases. Full-data scores were finite in [0,1].
- Available weak evidence can also score zero through underflow; the flags distinguish it from unavailable evidence. Existing tests explicitly cover that distinction.
- Full-precision arrays are the documented inference input. Neither build path rereads the rounded CSV. Legacy `build` deliberately omits availability and is documented as insufficient on its own for the new M2 interface.
- `CONTROL_SCORES.md:70–77` gives `home_available & away_available` as the initial comparative-control gate. Lines 33–35 correctly explain that availability does not imply complete player coverage. No flag claims controlled possession, and no H/A/D labels, persistence thresholds or restart decisions have moved into M1.

This satisfies the **M1 evidence milestone** in the integration plan. The broader Module 1 responsibility to eventually provide the final match-submission command is still pending and was not part of this implementation gate.

## 6. Executed checks and results

### Environment and isolation

Used the existing interpreter:

```text
C:\Users\oamu2\more-than-a-hack-2027\data\_review_20261113\env\Scripts\python.exe
Python 3.14.7, Windows x64
NumPy 2.5.2
```

M3 uses the standard library; M1 additionally needs NumPy. No dependencies were installed and no global environment was changed. pandas, kloppy, notebooks, video decoding and public ground-truth labels were unnecessary. No training, tuning or parameter selection was performed.

Commands executed (PowerShell; `$original`, `$clone` and `$review` refer to the paths above):

```powershell
$original = 'C:\Users\oamu2\more-than-a-hack-2027'
$clone = Join-Path $original 'data\integration-attempt'
$review = Join-Path $original 'data\_m3_m1_review_20261113'
$python = Join-Path $original 'data\_review_20261113\env\Scripts\python.exe'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:GIT_OPTIONAL_LOCKS = '0'

# Executed with the original repository as working directory:
& $python -m unittest discover -s tests -v

# Executed with the integration clone as working directory:
& $python -m unittest discover -s tests -v
& $python module1/control_scores.py --test

# Review-only scripts, stored outside candidate source:
& $python "$review\prepare_review.py"
& $python "$review\probes.py"
& $python "$review\full_check.py" reader
& $python "$review\full_check.py" candidate
& $python "$review\full_check.py" legacy
& $python "$review\full_check.py" compare
& $python "$review\legacy_m1\module1\control_scores.py" --test

git -C $clone diff --check
git -C $clone diff --cached --check
```

`prepare_review.py` records the Git/source manifests and extracts `06e4c9b` through read-only `git archive`; it does not create a worktree or change Git state. `full_check.py` passes the **explicit original data directory** to every reader/build. `probes.py` creates its own invented metadata, including shuffled channel declarations, without reusing the candidate tests' fixture builder. Its summary reports failed validation expectations but does not return a failing process status; it is a review diagnostic, not a replacement release test suite.

| Check | Result |
|---|---|
| Original M3 tests | **15 passed**, exit 0. |
| Clone tests | **32 passed**: 17 M1 + 15 M3, exit 0. |
| Retained M1 self-test in candidate | **Pass**, exit 0. |
| Original M1 self-test from archived commit | **Pass**, exit 0. |
| Independent invented probes | **35 passed, 4 failed expectations**. Three failures demonstrate R1; one demonstrates R2. |
| Known distances/formula, team swapping, input immutability | Pass. |
| Missing ball, one/both teams absent, partial/nonfinite coordinates | Pass. |
| Missing speed with valid position; invalid tau | Pass. |
| Real M3 APIs on invented XML/TXT into M1 single/stream/array APIs | Pass, with the same field values. |
| Invalid-input M1 CLI subprocesses | Duplicate ID and tau=0 each exited **1**, printed FAIL, and created no diagnostic output. |
| Invalid-input M3 CLI subprocess | Duplicate ID exited **1**, naming record 2. |
| `git diff --check`, including staged diff | Pass. |

The invalid-tau probe covered zero, negative, NaN, both infinities, None and a string. Wrong coordinate strings raise TypeError; an unknown observed team raises ValueError. These were caller-error probes, not changes to the accepted M3 schema.

### Independent full-length results

| Measurement | Result |
|---|---:|
| Tactical observations/evidence rows | **199,319** |
| Ordered frame indices | **0…199318** |
| Metadata slots per frame | **46** |
| Observed-ball frames | **113,488** |
| Home evidence available | **112,589** |
| Away evidence available | **113,318** |
| Visible ball but at least one side unavailable | **1,069** |
| Finite raw player speeds checked exactly against `/3.6` | **3,412,124** |
| Nonfinite player speeds checked as None | **5,756,550** |

The independent reader pass used the original corrected M3 implementation and consumed the entire raw file alongside it. It checked each raw ID, normalized and metre position, observed flag, ball, slot/team mapping, frame time and speed. It independently verified the actual metadata's player-channel and ball x/y order. It retained the first observation and verified that later iteration left it unchanged. Expected team availability and distances were computed independently from finite raw positions and the metadata's team mapping.

The candidate full pass used the clone's **working-tree** `build_evidence`, which exhausted `iter_control_scores` and the corrected reader. All array lengths/order checks completed, scores were finite in [0,1], unavailable distances were NaN, unavailable scores zero, and availability never occurred without a ball. All seven arrays matched the independent oracle exactly, with NaNs compared explicitly as equal missing values.

The original M1 ran in a **different process**, loading `module1/control_scores.py` from an archive of commit `06e4c9b`, not from the clone. Each process recorded `__file__` and source SHA-256. The candidate source hash was `3869bd7a...`; archived original M1 was `3840de92...`. Distinct paths and processes prevent module caching or import precedence from comparing the candidate to itself.

| Candidate versus original committed M1 | Comparison | Differing elements |
|---|---|---:|
| Visibility | Exact element equality | 0 |
| Home distance | Exact equality, NaNs equal | 0 |
| Away distance | Exact equality, NaNs equal | 0 |
| Home score | Exact equality | 0 |
| Away score | Exact equality | 0 |

**No tolerance-based equivalence was used in these full-data comparisons.** Byte-identical files are not claimed: Boolean versus int8 visibility is an intentional API type difference, and the diagnostic CLI now includes extra columns. Existing geometric unit tests sometimes use approximate float assertions; the full arrays themselves matched exactly. Old-parser behavior on malformed/partial-NaN fixtures intentionally differs and is now rejected or represented explicitly by M3.

### Verified, qualified and unverified claims

- **Verified:** 15/32 existing test counts, speed correction, full frame/slot preservation, visibility and availability totals, exact old/new numerical equivalence, no input mutation on tested calls, actual shared-reader consumption, and nonzero CLI failures.
- **Qualified:** “M3 files match the corrected commit” is true for staged Git blobs and normalized source text, not for raw working-copy line-ending bytes. “Corrected M3 dependency available” is true in the pending index/working tree, not in HEAD ancestry.
- **Unsupported as a blanket statement:** all missing/inconsistent channel metadata is rejected. R1/R2 are executed counterexamples.
- **Not established:** latest remote state; clean-machine/second-teammate reproduction; downstream M2 honoring flags; M4 evidence behavior; a final runner/submission CSV; possession quality. These component checks do not establish any of those.
- The prior agent's full diagnostic CLI success is supported by source/test behavior but was not independently rerun over the full match in this review; the full **in-memory** inference path was rerun. The small successful CLI path and malformed-input subprocesses were executed through the existing tests and independent probes.

Local evidence files: `state_before.json`, `m3_tests.log`, `candidate_tests.log`, `probes.json`, `reader_results.json`, `candidate_provenance.json`, `legacy_provenance.json`, `comparison_results.json`, the three harness scripts and local `.npz` comparison arrays. Restricted inputs and frame-level arrays remain under ignored `data/`; only aggregate results appear here.

## 7. Git readiness and recommended recording sequence

**Do not equate a successful commit with a completed integration gate.** The narrow speed/M1 gates pass, while R1/R2 remain follow-up corrections. It is reasonable to record the tested milestones now with that scope stated; do not describe such commits as comprehensive metadata validation or a complete possession pipeline.

The following sequence is a recommendation for a later authorized task. **It was not executed.** Before using it, recheck that HEAD/MERGE_HEAD and the index still match this report and that no additional staged files appeared.

1. **Record only the existing dependency merge.** Verify the staged list is exactly `.gitignore` and the three M3 files. Preserve the unrelated inherited ignore change and all unstaged/untracked M1 work. A plain commit, without `-a`, records this index and concludes the already prepared merge. Describe it as merging the corrected speed reader, with R1/R2 still outstanding.

   ```powershell
   git diff --cached --name-status
   git diff --cached --check
   git commit -m "Merge corrected M3 reader into integration-attempt"
   git merge-base --is-ancestor e0a0fd2f098194704b0493a2ea335ea3b4b9d06c HEAD
   ```

   The ancestry check should now exit 0. Do not use path-limited commit tricks during the pending merge, `commit -a`, `reset`, `merge --abort` or history rewriting to obtain this separation.

2. **Record M1 separately, including its acceptance tests and contract.** Stage only these exact three paths, review the staged diff, rerun the clone suite and self-test, then commit:

   ```powershell
   git add -- module1/control_scores.py module1/CONTROL_SCORES.md tests/test_control_scores.py
   git diff --cached --name-status
   git diff --cached --check
   # Run the 32-test suite and M1 --test with the reviewed interpreter.
   git commit -m "Consume M3 observations for control evidence with availability"
   ```

   Avoid `git add .` or `git add -A`; neither local reports nor review data should be swept into these commits. This second commit is the one that records the M1 code actually reviewed here. Do not claim R1/R2 were fixed by it.

3. **Make the small M3 validation follow-up in an ordinary subsequent commit and bring it into integration history without rewriting existing commits.** Add the four failing probe variants as real regression tests, plus duplicate position-name coverage. Preserve the accepted M1 API. If the team requires a single “fully approved integration” checkpoint, wait to name or release that checkpoint until these regressions pass and the dependency follow-up is recorded.

This separates history cleanly without losing the current M1 edits or silently changing `.gitignore`. If the team prefers to finish R1/R2 before any milestone commit, keep the current state pending and arrange the follow-up deliberately; do not claim the current index already contains those fixes.

## 8. Smallest remaining work and next module

**M1:** no implementation changes required for this evidence gate. Include both currently untracked files when recording it. Future M2 must actually apply `home_available & away_available`; legacy callers that ignore flags have not become safe temporal decoders merely because the fields now exist.

**M3:** add strict validation for the existing ball-register shape/references and unambiguous position Name/Unit declarations. Reject unsupported layouts rather than adding remapping or general export support. Retain the demonstrated speed conversion and all existing position/index behavior. Re-run the 15/32 tests plus the new regressions and a complete stream check after that change.

**Next implementation priority:** this bounded M3 prerequisite correction, then **M4 tracking-based stoppage/restart evidence**. Correct speed and stable observations are available for that work; resolving the validation gaps first closes the newly identified contract holes. M2 repairs remain necessary, but M4's evidence interface is the next substantive integration dependency. No new full four-module assessment was performed here.

## Team briefing

- **Safe to keep:** the committed km/h correction, ordered shared observations, candidate M1 scoring/availability APIs, full-precision handoff, legacy compatibility and meaningful fixture tests. The full-data equivalence claim was independently verified exactly.
- **Before recording:** separate the existing merge from M1; explicitly include M1 code, tests and contract. No M1 source correction is required. Preserve the inherited ignore changes and local reports.
- **Ready for commit?** Yes for these scoped milestone commits; **not** an unconditional sign-off on comprehensive M3 metadata validation or the complete pipeline. R1/R2 must be corrected before claiming that stronger gate.
- **Next three actions:** (1) integration owner records the M3 dependency merge alone; (2) M1 owner records the three M1 files after staged review/tests; (3) M3 owner closes the two validation gaps with regressions, then hands the stable reader to M4 for evidence work.
