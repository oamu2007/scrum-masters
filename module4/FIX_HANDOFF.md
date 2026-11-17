# M4 fixes execution handoff — November 17, 2026

**Focused actual-M4 -> actual-M2 gate: PASS within the documented envelope.**
F2/F3/F5/F6 implementation and mechanical checks pass. On November 17, 2026,
the **M3 owner decided to accept the documented restricted envelope for
integration**, including retrieval/stale-eligibility risks, with tested defaults
unchanged. Final release remains conditional on actual transport/combined gates
and independent reproduction; football accuracy remains unverified.
The original execution left the review unchanged; the subsequent focused review
and documentation-only decision amendment are now in `docs/M4_PROGRESS_REVIEW.md`.

## Provenance and preservation

Workspace: `C:/Users/oamu2/more-than-a-hack-2027/data/m4-execution`, branch
`module4-stoppage-restarts`. Starting HEAD, refreshed remote tip and final HEAD:
**`1c578db49a830e2c43dc866d611b65761a3b90a5`**. Initial tree/index were clean.
Approved `git fetch origin` succeeded; M4 had not advanced, so no new branch
delta required adoption. Freshness is as of that fetch, not subsequent pushes.

Actual read-only M2 dependency: `../m2-execution`, branch `modulo2`, clean at
**`d1500582493069cbd9a7b74c86cd217fb279772c`**. Decoder SHA-256:
`6976c1f65e87b3e8e6088d1e9905162430abd5eb937e9dd156bfc68a7b53eda4`.
Tests verify its exact HEAD and clean decoder, load the selected file without
bytecode writes, and print dependency provenance. No M1/M2/M5 implementation or
other feature branch was changed or merged.

Uncommitted producer SHA-256 used for the complete tactical scan:
`616f0be6cdb9376a2c9f43d141f4978cee1db0a2a09b1532d5b9ab2582d356f7`.
Historical review SHA-256, unchanged:
`9af822546ac20edcbe6636c30a79a1393b882ee8cfc2385292cce45499bfabd1`.

## Findings and acceptance evidence

| Finding | Change | Maintained evidence |
|---|---|---|
| F2 | Replace expiring pause age with one bounded same-half eligibility record; rebuild short motion; consume qualified report episodes | 32/60/120 s returns with active/stationary/sparse/absent players and missing speeds; missing positions; interrupted pulses; consumption during missing data; native/adjacent half resets |
| F3 | Remove elapsed slow-play corroboration; retain weak cap without tag or repeated exit observations | 3/10/30 s live drift and holds stay below unchanged default M2 entry gate; outside supported pause remains strong and recoverable |
| F5 | Require net progress speed and fresh ball-only spatial progress; retain independent availability | Exact 4 s gap then 30/150 +/-0.1 m jitter samples, also active-player jitter, stay in actual M2 D; genuine ball-only returns recover; outside/slow retrieval and isolated jump-return remain negative |
| F6 | Replace stale committed contract; document all actual settings, paths, retention/consumption, availability and corrected M2 triples/policies | `EVIDENCE.md` plus explicit pinned dependency-selection command; old ignored HANDOFF has an obsolete-history banner |

Before modifying the producer, the newly maintained gate reproduced the reviewed
failures: all 15 long-gap/player combinations lacked supported restarts, while
six prolonged drift/hold and two jitter subcases failed. The initial nine-method
run reported eight failures and 15 missing-positive errors. Successful controls
were retained. The final gate adds report-consumption, interrupted-pulse and
missing-position controls and replaces all previous TinyDecoder assertions with
actual M1/M2 calls. No alternate decoder or silent dependency skip remains.

## Commands and results

Commands ran from M4's root. `$python` was the existing executable
`C:/Users/oamu2/more-than-a-hack-2027/data/_review_20261113/env/Scripts/python.exe`:
Python **3.14.7**, NumPy **2.5.2**. No installation or environment-pinning claim.
For portable commands use a working Python with NumPy as in `EVIDENCE.md`.

```powershell
$env:MTAH_M2_ROOT = (Resolve-Path ../m2-execution).Path
& $python -B -m unittest discover -s tests -v
& $python -B -m unittest discover -s tests -p test_stoppage_m2_gate.py -v
& $python -B module4/test_stoppages.py
& $python -B module1/control_scores.py --test
& $python -B -m module4.evidence --data-dir C:/Users/oamu2/more-than-a-hack-2027/data
git diff --check
```

- Combined discovery: **132 pass** = 66 M4 (53 retained + 13 new focused methods)
  and 66 inherited (17 M1, 19 M3, 30 runner).
- Focused actual-M2 gate: **13 pass** using shipped M2 configuration and actual
  M1 `score_frame`; label transitions occur on actual M2 confirmation frames.
- Existing tag assertions and M1 self-test: **pass**.
- Explicit missing-dependency negative: **fails as required**, not skipped or
  substituted. Standard discovery requires the documented dependency selection.
- Diff/new-file whitespace, source preservation and dependency checks: **pass**.

Full tactical stream used the original bundle directly, without asset copying,
ground truth or frame-level exports. Actual M3 was exhausted and every evidence
output checked for count/order, finite [0,1] scores, Boolean flags, unavailable
zeros and legal sides. Current aggregate-only results:

| Diagnostic | Result |
|---|---:|
| Ordered frames | 199,319 |
| Dead available / positive / >=0.50 | 88,292 / 1,488 / 368 |
| Restart available / positive / >=0.50 | 791 / 129 / 129 |
| Dead / restart score ranges | [0,0.8] / [0,0.7] |
| Side H / A / None | 12,800 / 7,682 / 178,837 |

These are invariants/diagnostics, not accuracy or target counts. Parameters were
not selected from public labels, these totals or full-match comparisons. The
full scan is M3 -> M4, not proof of actual runner transport or possession quality.

## Operating envelope and integration handoff

Supported pauses near/outside a boundary can recover after long same-half gaps
once fresh motion qualifies; missing/insufficient observations keep evidence
unavailable or weak and actual M2 retains D. Known, unknown and conflicting sides,
half-open endpoints, input immutability and fresh halves are covered. A consumed
eligibility record cannot produce repeated restarts without a new supported stop.

**Accepted integration limitation — M3 owner's decision, November 17, 2026:**
ball-only progression at 3 m/s can also represent
in-pitch retrieval. A maintained fixture expressly records that this releases
M2 D. Keep this path enabled and retain unreported eligibility until the half
ends, accepting the risk of unrelated later motion after an ambiguous pause.
The rationale, exact candidate identity, unchanged default policies and release
conditions are authoritative in `EVIDENCE.md`, under "Integration-adoption
decision — November 17, 2026". Acceptance of this restricted scope does not prove
true resumed play. Persistent outside sensor bias, noisy tags, curved/reversing
motion and sparse samples also limit coverage. Weak interior pauses remain
excluded from default M2 D.

M1 must collect/validate all five returns from `producer(index, observation)` in
its existing single M3 loop, pass the selected five M1 fields plus five M4 arrays
to corrected actual M2, and supply native inclusive games.py half triples. M2's
default three-sample >=0.50 dead/restart confirmation is unchanged; its D state
must not expire on timeout or restore an old team. Real M1 transport, combined
acceptance, M5 release checks and independent reproduction remain separate work.

## Files and final Git state

Seven nonignored feature files, all **uncommitted and unstaged**:

- `module4/evidence.py`
- `module4/EVIDENCE.md`
- `module4/FIX_HANDOFF.md`
- `tests/test_stoppage_evidence.py`
- `tests/test_stoppage_resume.py`
- `tests/m2_dependency.py`
- `tests/test_stoppage_m2_gate.py`

Additionally, ignored `module4/HANDOFF.md` retains its original content beneath
an explicit obsolete-history banner. It is not a current gate result. The
independent historical review and its prior artifacts were preserved.

HEAD/branch remain the starting values. No staging, commit, merge, push or
submission occurred; no merge is pending. Inherited M1/M3/runner/game paths and
the tag extractor/assertions are unchanged. M2 remains clean at its recorded SHA.
