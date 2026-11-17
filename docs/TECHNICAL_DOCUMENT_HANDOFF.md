# Technical-document briefing: reviewed possession-quality method

Use this as an evidence map for the final few-page document. The selected method is
`5ed8c7ccc249c774e150addd5fc25cd8041fc309`, reviewed through `9126be9`, now merged
locally into `main` at `00b8ed3b291692180652658c87c0f17d60f7f510`.
The selected CSV hash is
`6D4E42C45559C71F77DF4F4198F14F51D7D8D901D5EC2620E01487AFF3327B74`.
Later test/result/document commits do not change its generation provenance.

## 1. Approach and rationale

**M3 → M1/M4 → M2 → CSV:** `starter/tactical_tracking.py` streams validated tactical
EPTS once, maps tracking counters onto video frames per half, scales normalized
positions to a 105.3 × 68 m pitch, converts player km/h to m/s once, and exposes
missingness. Slots are not persistent player identities. `run_possession.py` gives
the same recursively read-only observation to actual M1 and M4, transports
full-precision arrays plus native inclusive half triples and the initial-dead prior
to actual M2, then serializes every video frame as `frame,label`.

M1 uses `exp(-nearest_team_distance/3)` as simple geometric evidence. M2 requires
credible magnitude, margin and consecutive samples to reduce proximity flicker.
M4 combines automatic set-piece context with ball motion and nearby player speeds
because tags alone do not establish referee stoppage. These are inspectable,
bounded heuristics justified by semantics and invented cases, not learned
probabilities or evidence of an optimal football-control model.

The new **interior-pause rule** addresses a specific blind spot: old interior tag
support could never exceed 0.15 against M2's 0.50 dead gate, while accumulated
path length mistook local jitter for travel. Require one second of continuously
observed ball positions, at least three valid nearby player speeds on every frame,
at least 2/3 slow players (≤1.5 m/s within 20 m), ball bounding-box diagonal ≤1 m,
and one common unspent ordinary set-piece phase spanning the dwell. Support is
`0.80 × minimum slow fraction`, combined by maximum with existing evidence.
Three strong reports still confirm D, without backdating. Kickoff phases are
excluded from this new admission path; reported restart confirmation spends the
supporting/current phases, and half resets clear that history. Defaults are
operating assumptions, not fitted optima. See the current result's “Change and
independent justification” and `module4/evidence.py`.

## 2. Assets used, dropped and unused

Production reads **three licensed tactical files**: ATD XML for slot/team/channel
and unit metadata, raw ATD TXT for ball/player observations, and automatic Smart
Tagging XML for set-piece intervals/type/team. Metrica generates these tags
automatically without manual review ([FAQ](../FAQ.md), Smart Tagging question).
They are correlated evidence with false positives/negatives, not human truth.
Exact input identities are in [the reproduction guide](CANDIDATE_REPRODUCTION.md).

Production does **not** load homography, tactical/broadcast video, broadcast ATD,
external event data, corrected tracking, or a pretrained model. Homography loaders
and starter notebooks existing in the repository do not establish experimental
use. **Needs teammate confirmation:** did any earlier teammate actually try those
unused assets/models, then drop them? If so, name the experiment, source and outcome;
there is no evidence here to claim such experiments. A documented diagnostic
ablation cleared short history at phase activation; it did not fix startup timing
and was not adopted (`INTEGRATION_STATUS`, “Uncertainty, rejected correction”).
The old M1-only fallback decoder remains available but is not this candidate's path.

## 3. Training, labels and development evidence

Current production has no learned weights, fitting stage or external model/data
dependency. M1/M2/M4 records explicitly describe fixed heuristics and invented
fixtures, with no public-label threshold fitting or candidate ranking. The quality
change used aggregate automatic set-piece/tracking diagnostics as feature evidence,
not target labels, and no sweep or alternate-candidate score comparison.

| Labeled material actually evidenced | Source, labeler and amount | Role / boundary |
|---|---|---|
| Invented unit/integration sequences, including invented XML/EPTS/tag fixtures | Authored in tracked tests; multiple developers/agents, individual attribution needs teammate confirmation; 342 maintained tests overall, not 342 labeled datasets | Expected outputs test semantics, contracts and known failures; no real-match annotation or parameter learning. There is no consolidated labeled-frame inventory. |
| Public five-minute BAR-ATH reference | Supplied by organizers; mechanically derived from corrected tracking per CHALLENGE; identity of upstream tracking correctors not stated. 7,500 labeled frames, 17 possessions, video 11185..18684 | Existing shape/alignment/metric tests and one historical fixed-candidate pipeline diagnostic; **not training, tuning or candidate selection**. |

The public diagnostic evaluated the **older protected candidate**
`E533FC…0C01`, inference `48d67bb`, not the selected quality candidate. Its numbers
must not appear as this candidate's measurements or as evidence of improvement.
No new public evaluation was run. Full-match private truth was not used in the
reviewed work; do not imply that the public reference was never read anywhere.

**Needs teammate confirmation:** has any team member used any other labeled dataset,
manual annotations, learned parameters or external model during earlier work?
For each, supply dataset/game/source, who labeled it, amount and exact role. The
reviewed pipeline evidences none, but that is not an audit of unrecorded team work.
Also confirm fixture authors and total labeled fixture sequences/frames if the
final document needs an exact synthetic-data amount; test count is not that amount.
[RULES](../RULES.md), “Training and validation data,” forbids hand labels on the
provided game in any amount, including validation, and permits accessible labeled
other-game data. Any undisclosed same-game human labels, public-label tuning or
frame-specific fitted constants would be a possible rules issue requiring explicit
resolution before the final claim. None is established by the inspected records.

## 4. Possession definitions versus implementation

The challenge asks for controlled live possession; loose/contested play retains the
last controlling team. Touches, deflections and aerial-duel wins without control
do not switch it. Stopped play is D regardless of restart ownership.

| Topic | Implemented approximation and remaining gap |
|---|---|
| Control / turnover | Proximity, not measured control. Visible ball and both teams available; winning score ≥0.10, margin >0.05, 12 consecutive credible samples for acquisition/switch. No pass-completion or reception model. |
| Loose ball, passes, challenges/deflections | Established live team persists through missing, weak or tied evidence; interruptions clear pending opposing confirmation. Brief flips are filtered, but sustained opposing proximity can still misclassify a deflection, chase or contest. No explicit duel/deflection classifier. |
| Dead balls | Three consecutive available scores ≥0.50 enter persistent D. M4 uses corroborated boundary pauses plus the new tagged spatial dwell. Disappearance, tag alone or tag expiry cannot establish/release D. Untagged interior stops remain weak. |
| Restarts | Same-half pause/kickoff eligibility plus fresh in-pitch ball progress ≥2 m/s. Player-backed path requires ≥0.8 m displacement and ≥2/3 active nearby players; ball-only path requires ≥2 m, ≥0.2 s sustain and ≥0.5 m further progress. Three strong reports release D; unique known tag side gives H/A, unknown/conflicting side gives X pending control. Referee authorization is not observed. |
| Abstention / resets | Initial X unless an automatic kickoff-context prior supplies D; weak initial evidence stays X. X outside graded halves. All counters, prior team, M4 histories and spent phases reset per half. Confirmation changes only its current frame. |

See `modulos/modulo2.py`, `modulos/M2.md` and `module4/evidence.py`. Do not confuse
M2's prior-free historical X initialization with the current integrated kickoff prior.

## 5. Limitations and unimplemented improvements

Dead-ball misses and proximity-driven fragmentation remain. Approximate or false
tags can turn a live hold or **0.5 m/s live drift into false D**; sparse observation
can prevent dwell admission. Long/late tags and same-phase consumption can miss
real stops or admit a pause late. Duplicate slots/missing players bias fractions.
Ball retrieval can resemble restart, and startup uncertainty remains unresolved.

The follow-up's fully observed invented 25-fps cases enter D at frame 27; a tag
expires at frame 40. A **0.84 m tap at 3 m/s followed by three seconds stationary**
stays D through frame 121; a **4 m drift over four seconds at 1 m/s** stays D
through frame 139. Sustained 3 m/s movement is the control that releases D at 63.
These reconstruct requested conditions; exact reviewer-fixture equivalence is
unverified. Passing `KnownTaggedPauseLimitations` and
`TaggedPauseRestartCharacterizations.test_known_failure_*` preserves known semantic
failures; it does not demonstrate correct possession/restart recognition.

Possible future work: a distinct uncertain-start policy, stronger control/reception
evidence, better phase reliability handling, and short/slow restart detection that
also rejects jitter/retrieval. Validate changes using invented cases and permitted
other-game labels, without tuning on the provided game's public sample. These
improvements are **not implemented**. Full-match accuracy remains unverified.

## 6. Reproduction and validation claims

Follow [CANDIDATE_REPRODUCTION.md](CANDIDATE_REPRODUCTION.md): obtain authorized
source and licensed inputs, create Python 3.12.10 with tracked pins, run maintained
tests, invoke `run_possession.py --mode integrated --game BAR-ATH --tau 3.0` with
explicit data/output/report paths, officially validate, then compare SHA-256.
The guide includes complete configuration and input identities without depending
on ignored developer files.

Recorded original runs both passed 339 tests, generation and official validation
with identical hashes/configuration/input manifests. Reviewed follow-up and local
merged verification pass **342 tests, no skips** (merged run 24.021 s). The merged
validator also accepts the preserved selected CSV: 199,319 ordered rows. Inference
matches `5ed8c7c`; no full-match generation was repeated for these handoffs.
**Independent teammate reproduction is complete, as confirmed by the team owner;
full-match accuracy is unverified.** The final technical document records Armando
Sánchez's second-machine Windows run on 2026-11-17 from clean source `00b8ed3`,
with the selected CSV hash, 342 passing tests without skips and official validation
passing. The owner physically checked the run; its logs remain in Armando's ignored
`data/` files and were unavailable to the final-check reviewer. See the reproduction
guide for this evidence boundary and the now-public source URL.
Local merge is not release approval. Existing release gates and historical candidate
records remain unchanged. Publication was verified during the final check; adoption
and submission remain separate team decisions. No submission was performed here.

## Reference map

| Topic | Authoritative file / section | What it supports |
|---|---|---|
| Task/rules | [CHALLENGE](../CHALLENGE.md), “Possession rules”; [RULES](../RULES.md), “Training and validation data” | Control/loose-ball semantics, allowed data and label restrictions |
| Stream/assets | [TACTICAL_TRACKING](../starter/TACTICAL_TRACKING.md); `starter/tactical_tracking.py`; `games.py` | Units, missingness, asset selection, timeline/half mapping |
| Actual pipeline | [run_possession.py](../run_possession.py), `collect_evidence`, `decode_match`, `write_submission` | Actual modules, transport, defaults, serialization |
| M1/M2 | [CONTROL_SCORES](../module1/CONTROL_SCORES.md), “Callables and fields”; [M2](../modulos/M2.md), “Defaults” / “Preserved transition policies” | Proximity and state-machine semantics; old execution statuses are historical |
| M4/current change | [evidence.py](../module4/evidence.py), `EvidenceConfig`, `_tagged_pause`, `__call__`; [quality result](POSSESSION_QUALITY_RESULT.md), “Change” / “Bounded restart-characterization follow-up” | Exact rule, rationale, known failures and current verification |
| Candidate/reproduction | [quality result](POSSESSION_QUALITY_RESULT.md), “Final execution record”; [reproduction guide](CANDIDATE_REPRODUCTION.md) | Generation provenance, environment, configuration, hash and team-confirmed independent reproduction |
| Earlier diagnosis | [PUBLIC_DIAGNOSTIC](PUBLIC_DIAGNOSTIC.md), “Identity and provenance” / “Limits”; [INTEGRATION_STATUS](INTEGRATION_STATUS.md), startup diagnosis | Older candidate only; pipeline check and unresolved startup ambiguity, not new accuracy |
| Format | [validate_submission.py](../evaluation/validate_submission.py); [SUBMISSION](../SUBMISSION.md) | Official file contract, not accuracy certification |

`TEAM_TASKS*`, early review findings, older integration milestones and legacy
fallback instructions are historical context, not current implementation authority.
