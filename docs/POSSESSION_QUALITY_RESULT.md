# Possession quality: corroborated set-piece dwell

## Decision and time boundary

**Focused inference proposal: recognize a sustained, spatially confined collective
pause during an automatic set-piece phase, including away from the touchline.**
This is a predictive-policy change, not a repaired transport defect. Invented
examples establish improved behavior for this mechanism; full-match accuracy
remains unverified. Candidate adoption and independent teammate reproduction are
separate decisions.

Work began 2026-11-17 **16:52:27 UTC / 08:52:27 America/Tijuana**. The requested
30-minute checkpoint is 17:22:27 UTC; the hard 90-minute stop is 18:22:27 UTC.
The strongest hypothesis and bounded approach were reported earlier while work
continued. The previous audit's lack of a contract defect was not treated as
evidence of predictive adequacy. No history-reset or backdating experiment was
repeated. The completion decision was brought forward to **17:12:40 UTC / 09:12:40
America/Tijuana**, about **20 minutes** after starting, once both validated runs
matched. Final preservation and documentation followed. Work completed before the
30-minute checkpoint, so no claim of having run for 30 or 90 minutes is made.

## Workspace, source and preservation

| Item | Identity |
|---|---|
| Original repository | `C:/Users/oamu2/more-than-a-hack-2027` |
| Integration checkout | `data/integration-attempt` under the original repository |
| New isolated worktree | `C:/Users/oamu2/more-than-a-hack-2027/data/possession-quality-20261117` |
| New branch | `debug/possession-quality-20261117` |
| Verified integration HEAD / new branch base | `f8edf252ebf17361d66bc847ca7b35a988b2e2f5` |
| Frozen prior inference | `48d67bb271ce0dd50d0d6a1ce9dd24111a32fe78` |
| Resulting source/test/contract commit | `5ed8c7ccc249c774e150addd5fc25cd8041fc309` |
| Preservation tag object | `73d81ec5f21d83f93cf8a0d37f8990cc17b1f2f0` |
| Preservation tag target | `48d67bb271ce0dd50d0d6a1ce9dd24111a32fe78` |
| Protected CSV, relative to integration checkout | `data/release/runs/20261117T105211791158Z/candidate.csv` |
| Protected SHA-256 | `E533FCDDF4522A1E2F7CB2F12E15DEDD65C7C0E9508FBF9EDA3F1652E81D0C01` |

The frozen source is an ancestor of entry HEAD. Their difference contains only
status/handoff/public-diagnostic documents, release-gate records and startup tests;
inference is unchanged. Integration was clean. The original repository had an
existing `.gitignore` modification, which was left alone. No applicable AGENTS.md
was found in checked ancestors or tracked source/test/document directories.
No existing checkout was reset, reused for editing, rebased or merged. The previous
debug worktree was read only. Its focused tests were copied into this new branch,
then their explicitly superseded interior-pause expectation was revised here.

Ignored `data/quality/preservation-before.json` inventories **108 integration files**,
including all 24 files in the four historical run directories. The candidate hash
and tag were verified before work. Final preservation results are recorded below.

## Problem interpretation and inspected evidence

Read CHALLENGE, RULES, DATA, FAQ, evaluation/submission definitions; integration
INTEGRATION_STATUS, DEBUG_HANDOFF and PUBLIC_DIAGNOSTIC; the previous
BOUNDED_DEBUG_RESULT and its focused tests; M1 CONTROL_SCORES/RUNNER, M2 contract
and implementation, M4 EVIDENCE/stoppages/producer, M3 TACTICAL_TRACKING and parser,
and integrated runner/release behavior. The supplied problem documents resolve
the allowed-input boundary; no external match evidence was sought.

The desired labels describe **controlled team possession while live**, with the
last team retained through loose/contested play, and **D whenever play is stopped**.
Dead-ball ownership is not requested. The current production path instead uses:

1. M3: one validated tactical stream, normalized coordinates scaled to metres,
   player km/h converted once, explicit missingness, no persistent identities.
2. M1: `exp(-nearest_team_distance/3)` proximity, not control or live status.
3. M4: short path-speed and nearby-player evidence, predominantly corroborated
   boundary pauses; ordinary interior tag contribution capped at 0.15 by formula.
4. Runner: same read-only observation to actual M1/M4, exact full-precision arrays,
   the initial-dead prior and native inclusive halves to actual M2.
5. M2: 12 consecutive credible proximity samples for ownership changes, three
   strong reports for D/restart, persistent D; exact ordered CSV serialization.

The audit already tested that transport and these contracts. A correct execution
of proximity and a narrow boundary rule remains a poor approximation of the full
label definitions. Proximity-based fragmentation, retrieval and startup ambiguity
remain credible weaknesses, but broad control redesign was not combined with this
focused stoppage change.

### Selected weakness and bounded permitted-input diagnostic

**A tagged interior pause can never cross the default 0.50 dead gate**, even with
a perfectly stationary ball and all nearby players stopped: its maximum score is
0.15. In addition, accumulated short-window path length mistakes local position
jitter for movement. Both effects systematically discard observable restart-setup
evidence. These are method limitations, not contract violations.

One sequential actual M3/M4 scan inspected only automatic set-piece phases, with
compact counts and no frame-level display. A second pass added aggregate grouping
by automatic type without changing any diagnostic threshold. The complete stream
was read to preserve actual M4 history and M3 count validation; no unrestricted
frame-by-frame match investigation was performed. Inputs came directly from the
original licensed `data` directory. Diagnostic scripts/results remain ignored in
`data/quality/`; no large assets were copied.

At a single preselected diagnostic scale of one second / one-metre spatial spread:

| Aggregate observation | Count |
|---|---:|
| Automatic set-piece phases | 59 |
| Frames in their union | 43,987 |
| Observed ball / missing ball in that union | 29,880 / 14,107 |
| Phases with a quiet, confined one-second interval | 38 |
| Phases with such an interval in the pitch interior | 35 |
| Quiet/confined frames whose short path-speed exceeded the old slow gate | 1,020 |
| Phases with any strong old dead support | 7 |

These are **feature opportunities, not inferred true stops or accuracy results**.
The diagnostic did not apply final common-phase/consumption eligibility and is
not an estimate of the final admission count. Overlapping phase-group counts
are not additive. No target count, dead-frame total, known match interval or
public score was used to select the change. The public diagnostic was read as
requested background only; individual public labels and evaluation reports were
not inspected for design. No new candidate was scored against that reference.

## Change and independent justification

Only production `module4/evidence.py` changes. M1, M2, runner transport, evaluator,
tracking, kickoff initialization and restart thresholds remain unchanged.

- A bounded one-second history requires an observed ball and at least three
  valid nearby player speeds on every frame, with slow fraction at least 2/3.
- The bounding-box diagonal of ball positions must be at most 1.0 m. Spatial
  confinement tolerates local jitter without allowing a fast translating pass.
- One common unspent ordinary set-piece phase must span the complete history.
  Adjacent short phases cannot accumulate support; half-start kickoff tags are
  excluded and keep their separate, still-limited startup policy.
- Score is `0.80 * minimum slow fraction over the dwell`, combined by maximum
  with original evidence. Even the minimum qualifying default fraction supplies
  >0.50, without reducing M2's gate or promoting a tag alone.
- Existing M2 confirmation and persistent-D/restart policies apply. No output is
  backdated. Missing observations and tag expiry never release D.
- A confirmed restart spends its supporting and currently active phases for this
  new pause-admission path. Otherwise an approximate phase extending into live
  play could repeatedly turn later quiet holds into D. Fresh phases may rearm;
  ordinary boundary stops still work independently. Half resets clear this state.

The three explicit new defaults are `tagged_pause_s=1.0`,
`tagged_pause_span_m=1.0`, `tagged_pause_weight=0.80`. One second is longer than the
old 0.4 s short pause; one-metre spread tolerates sub-metre localization jitter
while staying below the existing two-metre ball-only departure requirement. The
0.80 support scale matches fully corroborated boundary support; the minimum
qualifying conjunction remains strong enough for the unchanged consumer. These
are bounded operating assumptions, not empirically calibrated optima. No sweep,
threshold fit or alternate-candidate score comparison was performed.

Expected benefit: fewer missed set-piece pauses and fewer proximity ownership
changes while such pauses persist. This does **not** demonstrate better ownership
control, a full-match metric gain or perfect stoppage timing.

## Invented examples, counterexamples and test review

Before production edits, 14 proposed tests ran against the unchanged source:
**10 failed, 4 passed**, exposing the missing target behavior. A first diagnostic
invocation was interrupted because unittest's long-list failure diff was slow;
the same semantic assertion was changed to `all(...)` for compact failure output,
and the complete baseline run finished. Production edits followed that run.

| Invented case | Before | Proposed behavior |
|---|---|---|
| Tagged interior stationary ball, three quiet players | H after proximity acquisition; never D | First strong report at frame 25; D at 27 |
| Same setup with +/-0.2 m local jitter | No strong D; high path speed | Same D onset; jitter alone cannot resume |
| Brief 0.76 s quiet interval then translating ball | No D | No D or eligibility |
| 0.96 s interval whose first departing point still fits the spatial envelope | No D | Sub-three-report evidence pulse allowed; no D |
| Missing ball/players/speeds, active players, moving pass, or no tag | No D from these alone | Preserved |
| Tagged supported pause, 32/60/120 s missing ball, stationary reacquisition | No new interior D | D persists; no time-based restart |
| Fresh supported movement with known / unknown / conflicting side | No interior-pause context | Existing restart confirms A / X / X |
| Restart followed by quiet hold within same phase | Live | Stays live; phase is spent |
| New phase after that restart | No interior D | Fresh one-second dwell can enter D |
| Untagged live boundary drift / reacquired jitter | Protected by old guards | Preserved |
| Adjacent phases, interrupted quiet history, tracking jump, half reset | No such interior evidence | Cannot pool stale evidence |

New tests include actual invented XML/raw EPTS and automatic tag XML through M3,
M1/M4, transport, M2 and exact LF CSV serialization; repeated generated fixture
hashes agree. Tests also cover two-dimensional spread, minimum collective fraction,
fractional-duration rounding, bounded history and invalid configuration.

**Explicitly reviewed superseded expectations:**

- `test_stoppage_resume` formerly called 60 stationary frames plus three stationary
  players plus a tag "tag alone" and required support <=0.15. It now explicitly
  tests the corroborated conjunction and exact D timing. Its separate missing-ball
  and known-side-only negative checks remain.
- The copied prior audit's 125-frame interior pause expectation is intentionally
  replaced with a brief-pause weak-evidence check **and** a new 125-frame strong
  dwell check. All original transport, interruption, long-gap, unit, side, reset
  and serialization assertions are retained. The prior checkout is untouched.
- An initial proposed short-pause test incorrectly required zero restart evidence
  even when its first departing point completed a valid spatial dwell. It was
  split into the clear shorter negative and the near-threshold pulse case above;
  the no-false-D requirement remains explicit.

`KnownTaggedPauseLimitations` deliberately demonstrates two semantic failures:
a false tag during a live hold, and a false/overlong tag during 0.5 m/s live drift,
can produce D. Passing those assertions documents an ambiguity; it is not a
negative-control success. The inherited two startup failure characterizations
and fast in-pitch retrieval ambiguity also remain visible and unresolved.

## Validation, remaining limitations and execution

Focused verification before final freeze: 22 quality tests (20 safeguards/target
tests plus two limitation characterizations) and 10 carried-forward audit tests
pass. The first full suite passed 327 tests before adding the final audit and
limitation cases. The final pre-freeze maintained suite passed **339 tests, no
skips, in 20.480 s**. M1 self-test, all 13 standalone M2 tests, M4 standalone tag
tests and `git diff --check` pass. No public candidate evaluation was run.
Existing public-reference shape/metric tests remain pipeline checks.

Tags and tracking are correlated automatic evidence, not referee observation.
Wrong, broad or late tags can still support false D or miss the beginning of a
stop. A late tag may meet the rule only after live play has started. A low-motion
live hold is observationally ambiguous. Continuous observation requirements miss
sparse stops; false D can persist through gaps or an unobserved quick restart.
Unknown/conflicting restart side can add X latency. Duplicate slots and missing
players distort collective fractions. The bounding-box diagonal is conservative
and direction dependent. Same-phase consumption can miss a second real stop
inside one broad phase. Untagged interior fouls/offside, proximity-based turnovers,
retrieval versus real resumption and startup uncertainty remain unresolved.

No hand labels/corrections, external human match data, new tracking/detection/
calibration system, private truth, frame exception or public-label tuning was used.
Restricted inputs and derived outputs remain local and ignored. No push, merge,
publication, message to teammates or submission occurred.

## Final execution record

**Frozen generation source: `5ed8c7ccc249c774e150addd5fc25cd8041fc309`**, clean on
`debug/possession-quality-20261117` for both runs. The subsequent result-record
commit changes only this document; it does not change inference or candidate bytes.

| Check | Result |
|---|---|
| New quality suite | 22 pass, including two explicitly named semantic-limit characterizations |
| Carried-forward focused audit | 10 pass; superseded expectation reviewed above |
| Final pre-freeze maintained suite | 339 pass, no skips, 20.480 s |
| First generation's maintained suite | 339 pass, no skips, 25.259 s |
| Repeat generation's maintained suite | 339 pass, no skips, 20.291 s |
| M1 / standalone M2 / standalone M4 | Pass / 13 pass / pass |
| Both actual integrated generations | Exit 0 |
| Both official format validations | Exit 0; 199,319 ordered rows, frames 0..199318 |
| Separate fresh-process hashes | Identical |
| Source, configuration, input and environment manifests | Identical across runs |
| Preserved integration files | All 108 byte-identical, including all 24 prior run files |
| Integration HEAD, status and preservation tag | Unchanged |
| Whitespace check | Pass |

The **new review candidate** is:

`C:/Users/oamu2/more-than-a-hack-2027/data/possession-quality-20261117/data/release/runs/20261117T170938345818Z/candidate.csv`

Fresh repeat:

`C:/Users/oamu2/more-than-a-hack-2027/data/possession-quality-20261117/data/release/runs/20261117T171127788505Z/candidate.csv`

Both SHA-256:

```text
6D4E42C45559C71F77DF4F4198F14F51D7D8D901D5EC2620E01487AFF3327B74
```

Both directories contain their own `evidence.json`, `pipeline.json`, `tests.log`,
`generation.log` and `official_validator.log`. Manifests bind the exact source,
commands, configuration, environment, input hashes, CSV hash and report hash.
`data/quality/verification.json` records the final cross-run and preservation
assertions. The original candidate still has exactly the protected hash above.
The old debug checkout remains clean at `20994301ca6d80849c668270f9bc168cbe129035`;
the original repository retains its pre-existing `.gitignore` modification.

### Configuration and permitted input provenance

Actual integrated mode, game BAR-ATH, tau 3.0, native half triples and unchanged
M2 defaults were used. M4 uses the shipped configuration plus the three new defaults
documented above. Full values are in each manifest and pipeline report.
Existing pinned Python **3.12.10**, NumPy **2.5.4**, pandas **3.1.1**,
python-dateutil **4.0.0**, tzdata **2026.6** on Windows 11 were reused, with
`OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1`. No package was installed.

Licensed inputs were referenced explicitly from
`C:/Users/oamu2/more-than-a-hack-2027/data/tactical/`, not copied:

| File | Bytes | SHA-256 |
|---|---:|---|
| `BAR-ATH_tactical_atd.xml` | 59,057 | `327E35E32E46A647389B88F883D4F9A2AB931E3E6148AEF2FCF8F22B1E93C43A` |
| `BAR-ATH_tactical_atd.txt` | 195,714,285 | `F130E350D2BFDF734B7E32F072931FCCC6D015C1E837D082064875FE0A700431` |
| `BAR-ATH_tactical_smart_tagging.xml` | 261,055 | `0594D35E3DF01B9C5002372D8615E2E8EF5379AC8F4E84C5EF7A53F4304C9019` |

Exact parent command pattern, from the new worktree:

```powershell
$qualityPython = 'C:/Users/oamu2/more-than-a-hack-2027/data/integration-attempt/data/release-env/Scripts/python.exe'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $qualityPython -B run_release.py --data-dir C:/Users/oamu2/more-than-a-hack-2027/data --gates data/quality/review-gates.json
& $qualityPython -B run_release.py --data-dir C:/Users/oamu2/more-than-a-hack-2027/data --gates data/quality/review-gates.json --expect-sha256 6D4E42C45559C71F77DF4F4198F14F51D7D8D901D5EC2620E01487AFF3327B74
```

`review-gates.json` is an ignored local copy of the gate schema with **every gate
blocked for this new proposal**; no historical approvals/reproduction records were
transferred. Both parent orchestration commands return **2** for unapproved review
output, while their required tests/generation/validator children each return 0.
This is deliberately separate from candidate adoption. The protected tracked
`release_gates.json` is unchanged. A clean independent checkout can reproduce the
CSV directly with `run_possession.py --mode integrated --data-dir <original bundle>
--out <new ignored file> --report <new ignored report>`, then use the official
validator; local review-gate bookkeeping is not an inference input.

### What the new output does and does not establish

Diagnostic totals are H 78,992 / A 72,741 / D 6,614 / X 40,972. M4 emitted 1,931
strong dead and 838 strong restart reports. The validator reports 729 possessions
using its X-as-gap convention. These totals are recorded **after** freezing the
rule, not used as success criteria or to revise it. Inserting D can split an H/A
spell even if the same team restarts; more or fewer spells is not itself accuracy.
No candidate was evaluated against public truth, and no alternate parameter set
or version was selected by metrics. Format validity and same-machine repeatability
are not independent reproduction or football-quality proof.

**Demonstrated:** previously impossible tagged interior pauses now enter persistent
D under the explicit conjunction, local jitter no longer automatically vetoes that
evidence, existing safeguards and file contracts pass, and a new candidate is
reproducible. **Unverified expectation:** this improves actual match stoppage and
possession quality enough to offset false-tag/live-hold errors. It does not solve
all missed D, possession fragmentation, retrieval or startup uncertainty.

**Smallest next action:** review the proposed M4 dwell rule, its tests and the
false-tag/live-hold tradeoff. If accepted, independently reproduce this exact source
and hash before adoption. No merge, push, publication or submission is requested
or performed. Work stops with a concrete review candidate, within the budget.
