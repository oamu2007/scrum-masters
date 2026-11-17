# M4 tracking evidence contract

Updated November 17, 2026 for F2/F3/F5/F6. This component returns uncertain
evidence, never possession labels or referee decisions. M2 owns persistent D and
H/A/X transitions. M1 runner transport remains external work.

## APIs and outputs

```python
from module4.evidence import StoppageEvidence, iter_stoppage_evidence, build_evidence
from module4.stoppages import restart_windows
from starter.load_smart_tagging import load

producer = StoppageEvidence(restart_windows(load(data_dir=bundle)))
result = producer(index, observation)  # inside the existing single M3 loop
rows = iter_stoppage_evidence(data_dir=bundle)  # standalone component tool
arrays = build_evidence(data_dir=bundle)        # five aligned NumPy arrays
```

The per-frame signature is **`producer(index, observation) -> mapping`**.
Construct `StoppageEvidence(windows=(), *, game=GAME, config=None)` per match.
Inputs are read-only corrected M3 dictionaries: metre positions, already-converted
`speed_mps`, explicit missing values, export slots rather than persistent people.
Calls are contiguous, with integer `index == frame` and `time_s == index/fps`.
The first call may start within a half with fresh state. `reset()` clears all
state, including order validation. Returned dictionaries are independent.

Wrappers accept keyword-only `game=GAME, data_dir=None, config=None, windows=None`.
`None` windows loads automatic tags; `()` disables them. The iterator adds `frame`
and retains every tactical frame; exhaust it for final source/count validation.
Closing it closes M3. Arrays have float64 scores, Boolean availability and object
H/A/None sides. Scalars/streaming require the standard library; arrays/tests use
NumPy. Do not add the standalone wrappers as extra tracking scans in M1's runner.

| Field | Meaning |
|---|---|
| `dead_score` | Finite [0,1] support for stopping; not a probability |
| `dead_available` | Current ball motion and enough nearby player positions/speeds can be assessed |
| `restart_score` | Finite [0,1] support for fresh resumption after an eligible supported pause |
| `restart_available` | Unconsumed same-half eligibility and current usable ball-motion baseline; independent of player/dead availability |
| `restart_side` | Optional current tag side H/A/None, independently of availability |

Unavailable scores are exactly zero with flag false. Available zero means the
observations do not support that signal. Known side alone cannot release D.
Unknown/conflicting overlapping tags yield None, including known plus unknown.
No side is inferred from slots/motion. `restart_windows(events)` and its mapping
are unchanged. Automatic windows remain approximate **half-open `[start,end)`**
context; neither endpoint implies stopped/resumed play. Side disappears at end.

## Features, observation requirements and comparisons

1. **Ball motion.** Use metre coordinates directly, retaining outside positions.
   The short deque retains 0.20 s and at most 7 observed points at 25 fps. Motion
   requires at least two samples spanning >=0.08 s. Path speed is summed observed
   path length / elapsed seconds; restart progress speed is net displacement from
   the oldest retained point / those same seconds. Short missing gaps count in
   elapsed time; there is no interpolation. A gap >0.20 s or intersample speed
   >80 m/s clears short history and movement/report candidates, not unreported
   eligibility. A missing current ball returns unavailable zero scores and clears
   continuous pause/movement/report candidates. Jump rejection alone cannot
   reject small oscillation with high cumulative path speed.
2. **Players.** Select current finite observed positions and finite nonnegative
   speeds within <=20 m of the current ball. At least three usable slots enable
   dead evidence and the player-backed restart fraction. Slow means <=1.5 m/s;
   active means >=2 m/s. Fractions use current usable slots only. Missing position
   or speed is not zero; M3 speeds must not be converted again. No player history
   or identity is inferred.
3. **Dead evidence.** Let signed edge distance be `e=min(x,L-x,y,W-y)`, dimensions
   from games.py, and `b=clip((1.5-e)/1.5,0,1)`. Require path speed <=0.7 m/s,
   slow fraction >=2/3 and boundary (`b>0`) or tag context continuously for >=0.40 s.
   Raw support is `(0.65*b + 0.15*tagged)*slow_fraction`. Boundary support is
   capped at 0.30 unless corroborated by a current automatic tag or recent exit:
   >=3 consecutive samples on/outside the line (`e<=0`), most recent within <=2 s.
   **Elapsed slow play never removes this cap.** Unsupported live drift or hold
   0.2 m inside the line stays weak regardless of duration. Tagged centre-pitch
   pause is at most 0.15; tag-only missing ball is unavailable.
4. **Eligibility.** Dead support >=0.50 stores/refreshes one fixed-size record
   containing the supported ball point, last support time and report status.
   Unreported eligibility survives any same-half gap. There is no age timeout
   and no saved live team. Age, missingness, old displacement and tag endpoints
   cannot themselves emit restart support: short motion must be rebuilt.
5. **Restart A, ball plus players.** Require on/in-pitch ball (`e>=0`), net progress
   speed >=2 m/s, displacement >=0.8 m from the supported pause, enough usable
   nearby players and active fraction >=2/3. Score is
   `0.80*active_fraction + 0.10*tagged`.
6. **Restart B, ball only.** Require on/in-pitch ball, net progress speed >=2 m/s,
   displacement >=2 m from the pause, and continuous qualifying observations for
   >=0.20 s. Also require >=0.50 m fresh net progress from that candidate's first
   point. This rejects local jitter around a distant reacquired position: path
   length and old-pause displacement alone are insufficient. Score is
   `0.60 + 0.10*tagged`. Players may be stationary, sparse, absent or missing
   positions/speeds. The returned score is the maximum of A/B. Both require
   eligibility and current observed motion.
7. **Consumption.** Three consecutive positive outputs qualify a report burst;
   its first output time starts a one-second report window. At age >=1 s,
   eligibility is consumed before processing that frame, even during missing
   ball. Later motion cannot repeatedly reuse the old pause. An interrupted
   burst shorter than three resets its pending report run without spending
   eligibility, allowing later adequately observed recovery. This is aligned
   with default corrected M2 confirmation, not feedback about its labels.

All history, eligibility, exit clues and counters reset on entering each inclusive
games.py half block, including adjacent blocks. Outside-half frames remain with
unavailable zeros/None and accumulate no history. All 199,319 tactical frames
are retained; no corrected-tracking offset is applied to M3 indices.

## Complete immutable configuration

Comparisons are defined above; time comparisons use 1e-9 s floating tolerance.
Nonfinite/nonpositive values, noninteger counts, contradictory speed gates,
weak cap >= anchor score and invalid weight sums are rejected.

| Settings | Defaults | Rationale |
|---|---|---|
| `boundary_margin_m` | 1.5 m | Soft noisy edge region |
| `nearby_radius_m`, `min_nearby_players` | 20 m, 3 | Current collective context |
| `motion_window_s`, `min_motion_s`, `max_ball_gap_s` | 0.20, 0.08, 0.20 s | Observed baseline; refuse long-gap velocity |
| `max_ball_mps` | 80 m/s | Reject implausible intersample jumps |
| `ball_slow_mps`, `player_slow_mps` | 0.7, 1.5 m/s | Low ball motion / walking players |
| `player_active_mps`, `collective_fraction` | 2 m/s, 2/3 | Collective path A activity |
| `pause_s` | 0.40 s | Reject isolated pause noise |
| `exit_memory_s`, `min_out_samples` | 2 s, 3 | Repeated recent outside/on-line observations |
| `weak_dead_cap`, `pause_anchor_score` | 0.30, 0.50 | Weak boundary clues cannot seed eligibility |
| `boundary_dead_weight`, `tag_dead_weight` | 0.65, 0.15 | Geometry plus modest tag support |
| `restart_ball_mps`, `restart_displacement_m` | 2 m/s, 0.8 m | Path A motion/displacement |
| `restart_ball_displacement_m`, `restart_ball_sustain_s` | 2 m, 0.20 s | Stronger ball-only requirements |
| `restart_progress_m` | 0.50 m | Fresh progress exceeding the tested 0.2 m jitter region |
| `movement_restart_weight`, `ball_restart_weight`, `tag_restart_weight` | 0.80, 0.60, 0.10 | Player / ball-only support plus tag context |
| `restart_consume_s`, `restart_report_samples` | 1 s, 3 | Bounded report compatible with default M2 |

`pause_context_s` and `still_strong_s` were removed: age expiry and elapsed
stillness are not admission rules. Historical `restart_memory_s` is not a current
setting. Defaults are heuristics justified with invented cases, not learned or
calibrated probabilities. No public labels, desired match counts or parameter
sweeps were used. Changing consumer thresholds/counts requires joint validation.

## Corrected M2 and reproducible required gate

The actual corrected dependency is `d1500582493069cbd9a7b74c86cd217fb279772c`.
Its exact selected-field call uses native inclusive half triples:

```python
labels = modulo2(
    **{k: m1[k] for k in ("score_home", "score_away", "ball_visible", "home_available", "away_available")},
    **{k: m4[k] for k in ("dead_score", "dead_available", "restart_score", "restart_available", "restart_side")},
    half_blocks=half_video_blocks(GAME),
)
```

Default M2 confirms dead/restart after three consecutive available samples >=0.50,
labeling the confirmation frame. D persists until supported restart. A unique
known side establishes H/A; unknown/conflict releases to X until control confirms.
Its control gates are score >=0.10, margin >0.05, 12 samples; simultaneous strong
evidence defaults to dead priority. Weak scores/side alone are not decisive.
Do not lower M2's D threshold to admit unsupported M4 categories.

In the combined integration checkout the maintained loader imports the integrated
`modulos/modulo2.py` directly. No external clone/environment selection is needed:

```powershell
python -B -m unittest discover -s tests -v
python -B -m unittest discover -s tests -p test_stoppage_m2_gate.py -v
python -B module4/test_stoppages.py
python -B module1/control_scores.py --test
python -B -m module4.evidence --data-dir C:/path/to/licensed-bundle
git diff --check
```

The gate loads actual integrated M2, prints source/hash provenance, feeds actual M1 `score_frame` and actual
M4 outputs, and calls shipped M2 configuration. **No TinyDecoder, duplicate state
logic or silent skip.** Missing dependencies fail; ordinary discovery includes
this gate. Compact invented arrays rebase half triples; M4 receives native frame
IDs, except explicitly named compact adjacent-half overrides.

The full checker exhausts actual M3 -> M4 and prints aggregate counts/ranges/config
only. It validates order/count, Boolean flags, finite bounds, unavailable zeros
and legal sides. Current results/Git state are in `FIX_HANDOFF.md`; ignored
historical `HANDOFF.md` is obsolete.

## Supported envelope and adoption decision

Controls cover supported outside pauses and genuine observed movement after
32/60/120-second gaps with active/stationary/sparse/absent players or missing
positions/speeds. Inadequate/intermittent observations retain uncertainty/D.
Unsupported in-pitch drift/hold stays weak at 3, 10 and 30 s. Specified reacquired
jitter, outside retrieval, slow retrieval and isolated jump-return remain
non-decisive in actual M2. Consumption and interrupted pulses are covered.

**Unresolved ambiguity:** 3 m/s in-pitch retrieval can satisfy ball-only motion
and release D. A maintained ambiguity fixture records this accepted-by-code
behavior; it is not a negative-control pass or proof of resumed play. Preserving
genuine ball-only restarts accepts this observational overlap. The M3 owner's
integration-adoption decision below accepts this limitation for the stated scope;
it does not establish that a particular movement is referee-authorized play.
Persistent outside sensor bias or wrong tags can falsely support D.

Interior fouls/offside without boundary support remain poorly covered; weak tagged
interior pauses cannot enter default D. Unreported eligibility can persist the
whole half, so fresh unrelated motion after an ambiguous prior stop remains a
risk. Curved/reversing genuine motion may fail progress gates. Missing samples
are never filled; sparse pulses may fail M2 confirmation. Duplicate/incomplete
slots limit collective inference. No match accuracy, independent reproduction
or full-pipeline readiness is claimed by these component tests. Combined transport
and release results are recorded separately in `docs/INTEGRATION_STATUS.md`.

### Integration-adoption decision — November 17, 2026

**Decision owner: M3 owner. Decision: accept the current restricted M4 operating
envelope for integration, retain the tested defaults, and keep final release
approval conditional on the remaining integration and reproduction gates.**
This records the M3 owner's decision communicated in the review conversation.

Candidate: branch `module4-stoppage-restarts`, base HEAD
`1c578db49a830e2c43dc866d611b65761a3b90a5`, with the reviewed **uncommitted**
producer SHA-256
`616f0be6cdb9376a2c9f43d141f4978cee1db0a2a09b1532d5b9ab2582d356f7`.
The fixes are not in that HEAD. Record the resulting commit SHA in the combined
integration/release record when these exact changes are committed. Consumer:
actual corrected M2 at `d1500582493069cbd9a7b74c86cd217fb279772c`.

- **Keep ball-only restarts enabled.** Accept that qualifying fast in-pitch
  retrieval can release D incorrectly. This preserves the tested recovery path
  with stationary, sparse or absent players; its real-match error frequency is
  unverified.
- **Keep unreported eligibility until the half ends.** Accept that fresh unrelated
  movement after an ambiguous earlier supported pause can qualify as a restart.
  This preserves recovery after long observation gaps. Qualified report
  consumption, new-stop requirements after consumption and half resets remain
  unchanged; time, disappearance or tag endpoints alone never release D.
- **Keep the tested producer and default M2 policies unchanged.** This includes
  three consecutive available dead/restart samples >=0.50, confirmation-frame
  labeling, initial/unknown-restart X, trusted unique known-side restart,
  dead-first conflict priority, and score >=0.10 / margin >0.05 / 12 consecutive
  samples for proximity-based control. These are adopted integration heuristics,
  with the other coverage limitations above retained.

Rationale: the present rules repair reproduced delayed/sparse recovery and
live-play/jitter failures while exposing the remaining observational overlap.
This is acceptance of a limited engineering scope, not a match-accuracy finding.
No parameter changes, public-label tuning or additional detection redesign are
authorized or required by this decision.

**Release conditions still pending:** prove that actual M1 transport collects and
validates all five M4 returns and invokes actual M2; pass actual combined
producer/transport/decoder acceptance and M5's validation/reproduction gates,
including independent regeneration. Integration correctness and reproduction do
not establish football accuracy, which remains unverified. This decision does
not authorize a merge, publication or submission.

Revisit the decision if evidence exposes another failure, the required coverage
changes, or producer/consumer source, thresholds, confirmation counts or relevant
input semantics change. Rerun affected behavioral gates before adopting a revised
candidate. Documentation-only recording of this decision changes no algorithm.
