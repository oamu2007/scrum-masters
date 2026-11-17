# Bounded possession-contract investigation — November 17, 2026

**Recommendation: retain the existing method with its documented limitations.
No concrete implementation defect or independently justified missing functionality
was demonstrated in this bounded audit. No prediction correction or replacement
candidate was produced.** The added cases establish specific contract behavior,
not football accuracy or release readiness.

## Time boundary and decision

Started **16:26:31 UTC / 08:26:31 America/Tijuana**. The planned 45-minute checkpoint
was 17:11:31 UTC; the absolute 90-minute stop was 17:56:31 UTC.
The finite hypothesis set was exhausted early. The **stop decision was brought
forward to approximately 16:38:37 UTC (12 minutes elapsed)**: no failed production
contract remained to justify algorithm work. Rather than fill the remaining time
with new hypotheses, tuning or redesign, algorithm investigation stopped there.
Only final verification, preservation and this record followed. This is an early
stop, not a claim that a 45-minute investigation was performed.

## Protected baseline and isolated work

| Item | Identity |
|---|---|
| Original checkout | `C:/Users/oamu2/more-than-a-hack-2027/data/integration-attempt` |
| Frozen inference | `48d67bb271ce0dd50d0d6a1ce9dd24111a32fe78` |
| Integration HEAD at entry / debug base | `4a2695eb0fb5abd43c5c48376ec650a1d510752f` |
| Annotated local tag | `candidate/pre-debug-20261117` |
| Tag object | `73d81ec5f21d83f93cf8a0d37f8990cc17b1f2f0` |
| Tag target | `48d67bb271ce0dd50d0d6a1ce9dd24111a32fe78` |
| Candidate, relative to original checkout | `data/release/runs/20261117T105211791158Z/candidate.csv` |
| SHA-256 | `E533FCDDF4522A1E2F7CB2F12E15DEDD65C7C0E9508FBF9EDA3F1652E81D0C01` |
| Debug worktree | `C:/Users/oamu2/more-than-a-hack-2027/data/possession-debug` |
| Debug branch | `debug/possession-contract` |
| Resulting audit/test commit | `e9b0144c91ebc87746d15498afeb2f1959171d4b` |
| Resulting inference revision | Unchanged; frozen source above. The subsequent result-record commit adds this document only. |

Command access, branch/HEAD/status and candidate hash were checked first. The tag
name and debug branch/directory were unused; no suffix, forced update or overwrite
was needed. The annotation includes the full candidate path/hash and known kickoff,
retrieval, dead-state/fragmentation and independent-reproduction limitations. The
tag is a preservation anchor, not approval. VS Code's status confirmed a separate
`Welcome - possession-debug` window. An initially restricted launch failed; the
authorized retry opened it. No source or candidate change was involved.

An ignored `data/bounded-debug-20261117T162631Z/baseline-manifest.json` in the
original checkout records entry HEAD/status, frozen source, current and recorded
configuration, candidate hash, recorded input identities, and **108 protected file
hashes**, including all **24 files across four existing run directories** and the
then-untracked `docs/PUBLIC_DIAGNOSTIC.md`. A copy is in the same relative ignored
directory in the debug worktree. No CSV or licensed asset was copied or committed.

No applicable AGENTS.md was found in checked ancestors/affected directories. Read
the current integration status, checkpoint and original checkout's untracked
PUBLIC_DIAGNOSTIC, CHALLENGE possession definitions, RULES, original TEAM_TASKS_2
requirements, M1/M2/M4 contracts/source, M3's reader contract/source, and relevant
M3/M1 and November 17 M2/M4 reviews. Historical findings were distinguished from
accepted corrections and scope decisions. No external annotations or web evidence
were used. Public diagnostic results were motivation only.

## Hypotheses and evidence

New `tests/test_bounded_contract.py` constructs invented three-slot EPTS XML/raw
files and automatic tag XML. It runs actual public M3 reading, actual M1/M4, the
canonical collector/validator, actual M2 and the CSV writer. Only fixture frame
count/half boundaries are rebased. Read-only spies compare every producer field
with the collected arrays and verify the exact selected arrays reach M2. No toy
decoder, fabricated producer score or replacement tracking reader is substituted.
Nine methods exercise 22 complete fixture pipeline runs.

| Hypothesis | Expected behavior from requirements/contracts | Invented attempted counterexample and observed result | Classification |
|---|---|---|---|
| Computed evidence is dropped, shifted or rounded | RUNNER: one ordered M3 stream; seven M1/five M4 fields retained; exact selected arrays and half blocks reach M2 | Live -> boundary stop -> occlusion -> known-side restart, with outside-half frames: every field equals the actual producer return; decoder gets the original arrays; exact LF CSV and repeated hash match | No implementation defect demonstrated |
| Availability is mistaken for evidence strength, or one signal masks another | M1/M2 require both team flags for control; M4 restart availability is independent of dead/player availability; known side alone is non-decisive | Missing all player positions after a supported stop still permits ball-only D -> X. Tagged stationary interior/unsupported boundary holds have available weak scores, remain below D threshold, and do not restart from side context | Transport/consumer defect rejected; weak interior detection is a known heuristic limitation (3) |
| Default M4 outputs cannot satisfy M2 confirmation | EVIDENCE/M2: three consecutive strong reports; default restart scores must reach 0.50 | Active players produce first restart report on departure; stationary/missing speeds use five sustain frames; all positive scores reach the consumer threshold and M2 exits on report three | Default contract mismatch rejected |
| Reader/producer speed conversion selects the wrong path | M3/M1/M4: normalized positions scaled once; player km/h converted once, no second division in M4 | Invented raw 10.8 km/h reaches the collective path as 3 m/s; stationary and missing-speed controls take the ball-only path with its documented delay | No unit/path defect demonstrated |
| Interrupted opposing control accidentally accumulates | TEAM_TASKS_2/M2: 12 consecutive credible samples; missing, weak, tied or current-team evidence clears pending turnover | Established H; 11 A samples; missing ball, missing home, missing away, negligible scores, tie or H; another 11 A; H; finally 12 A. Only the final sample changes to A | Unintended-turnover hypothesis rejected |
| Interrupted dead confirmation is retained | M2: three consecutive available strong dead samples | Two strong dead reports, then missing ball or one missing player speed, then fresh pause: no early D; only the fresh three-report run enters D | Counter/reset defect rejected |
| Short restart pulses consume eligibility or leak a previous side | EVIDENCE/M2: sub-three-report burst must not consume; missing report clears pending confirmation and sides | Two H-sided reports, 60 seconds missing ball, then fresh A-sided restart: D persists across the gap; third fresh report releases to A | Premature consumption/side leakage rejected |
| Consumed eligibility can be reused, or new stops cannot rearm | EVIDENCE: consume qualified reports after one second even while missing; new supported stop supplies new eligibility | Confirmed restart followed by 60-second occlusion and renewed motion emits no old-context restart. A later new boundary stop enters D and supplies fresh resumption | Eligibility defect rejected |
| Non-kickoff initialization or half reset leaks state | M2/M4: fresh state/counters at inclusive half start; outside X | Adjacent and separated halves following established D equal a freshly run second half; no old restart support; exact outside labels remain X | Reset/indexing hypothesis rejected |
| Required interior-stop or controlled-possession functionality is missing from the accepted implementation | Original requirements explicitly permit missed interior fouls; accepted M1 is proximity, M2 is a documented persistence proxy, and M4 has a restricted boundary envelope | Tagged centre-pitch pause emits at most 0.15; unsupported boundary hold at most 0.30; neither reaches the adopted 0.50 D gate. Existing pass/deflection/turnover controls pass | Known heuristic limitation (3), not independently established missing intended functionality (2) |
| Motion reliably identifies authorized resumption | CHALLENGE distinguishes ball in play from proximity/movement; M4 review explicitly accepts retrieval overlap | Prior kickoff/retrieval findings remain applicable; no history-reset or backdating experiment was repeated. Maintained retrieval/jitter controls were retained | Observational ambiguity (4) |

The default-strength check also follows directly from the contracts: collective
path A's minimum positive score is `0.8 * (2/3) > 0.5`; ball-only B is at least
0.6. Producer and consumer both require three reports. Weak dead categories are
deliberately below 0.5 and cannot create eligibility. These facts do not establish
that every real stoppage supplies three observations or that a positive movement
signal is authorized play. Nondefault consumer/producer settings still require
joint validation as documented; no settings were changed here.

**Category 1 confirmed implementation defects: none in these cases. Category 2
independently justified missing intended functionality: none demonstrated.**
This does not prove the absence of other defects. It does not explain individual
public-window failures, and no individual public labels were examined to invent
rules. Inferring control from proximity, sparse observation coverage, weak interior
stop support, false tags, retrieval ambiguity and initial-state uncertainty remain
limitations. Fixing those generally would require policy/model work outside this
bounded correction task, not silently lowering thresholds or adding frame rules.

## Verification and change scope

Production/configuration/interfaces/release gates are unchanged. The only debug
changes are the nine contract tests and this record; no existing test was weakened.
Affected tests ran before the complete suite:

| Check | Result |
|---|---|
| New invented actual-file contract suite | 9 pass |
| Existing integrated pipeline | 12 pass |
| Existing M2 suites | 34 pass |
| Existing M4 stoppage suites | 66 pass |
| Final complete maintained suite | **315 pass, no skips** (306 retained + 9 new) |
| M1 self-test / standalone M2 / standalone M4 | Pass / 13 pass / pass |
| Whitespace check | Pass |

The complete suite was repeated once after adding an exact timing assertion that
detects incorrect speed conversion/path selection. Its final run took 24.155 s.
Existing pass/occlusion, brief deflection, sustained turnover, weak/missing control,
persistent D, supported restart, 32/60/120-second recovery, live drift, retrieval
ambiguity, jitter, half reset and exact file-contract checks remain intact. The
previous startup failure-characterization tests remain failures of football
semantics even though their assertions pass.

Used existing pinned Python 3.12.10, NumPy 2.5.4, pandas 3.1.1,
python-dateutil 4.0.0 and tzdata 2026.6, with `OPENBLAS_NUM_THREADS=1` and
`OMP_NUM_THREADS=1`. No installation was performed. All test commands used `-B` and
the executable at the original checkout's `data/release-env/Scripts/python.exe`.
From the debug root, run `-m unittest discover -s tests -p test_bounded_contract.py
-v` for the new cases or `-m unittest discover -s tests -v` for the complete suite.
Actual dependency provenance in the test log resolves M2 to this debug worktree.

Logs, baseline copy and `verify_preservation.py`/`preservation-after.json` are in
debug `data/bounded-debug-20261117T162631Z/`. The complete suite retains its existing
public-reference shape/count checks and synthetic/baseline metric tests; **no
candidate public evaluation, score comparison or parameter sweep was run**.

## Preservation outcome and candidate comparability

All **108 protected files, including all 24 historical run files**, remain
byte-identical to the entry manifest. The original candidate retains the exact
SHA-256 above. The annotated tag still points to the frozen inference commit.
The protected configuration and release gates are unchanged.

The original integration Git state did change concurrently: at **08:35:12 local**,
commit **`f8edf252ebf17361d66bc847ca7b35a988b2e2f5`** added only the pre-existing
`docs/PUBLIC_DIAGNOSTIC.md`; its bytes match the protected untracked document.
The original checkout is now clean at that commit. This task did not create,
reset, merge or overwrite that commit. The first preservation check correctly
stopped on its unexpected HEAD change; inspection established the exact
documentation-only change, which is explicitly recorded in the final verification.
The debug branch stays based on entry HEAD `4a2695e`, with no rebase or merge.

**New candidate: none.** No supplied tracking scan or new generation was warranted
without a correction. No fresh official-validation or repeat-generation claim is
made for this audit; earlier candidate validation/repeatability records remain
historical. Any future changed source/output needs fresh generation, official
validation, repeat hashing and its own independent teammate reproduction. No old
approval/reproduction claim transfers. No branch/tag push, integration/main merge,
candidate overwrite, submission or release approval occurred.

## Smallest next action

The integration owner should review this bounded result and retain the frozen
candidate as an explicitly limited investigation artifact. There is **no algorithm
patch to adopt**. The new contract tests may be reviewed separately. Decide the
remaining scope/limitations explicitly before any release decision; do not start
another public-score tuning loop. Adoption, independent teammate reproduction,
packaging, publication and submission remain separate and unapproved.
