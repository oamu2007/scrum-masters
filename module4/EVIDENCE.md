# M4 tracking evidence

Implemented November 16, 2026. This component supplies uncertain evidence to M2.
It produces no H/A/D/X decisions and stores no possession or persistent dead state.
`restart_windows(events)` and its team mapping remain unchanged in `stoppages.py`.
Windows are approximate, half-open `[start_frame, end_frame)` context.

## APIs

```python
from module4.evidence import StoppageEvidence, iter_stoppage_evidence, build_evidence
from module4.stoppages import restart_windows
from starter.load_smart_tagging import load

(local)
bundle = "C:/Users/oamu2/more-than-a-hack-2027/data"
producer = StoppageEvidence(restart_windows(load(data_dir=bundle)))
# Inside the existing single M3 loop, passing the same read-only dictionary as M1:
# result = producer(index, observation)

for row in iter_stoppage_evidence(data_dir=bundle):
    pass  # frame plus five scalar fields; exhaust to validate the complete source

arrays = build_evidence(data_dir=bundle)  # five full-length aligned NumPy arrays
```

The **one callable signature is `producer(index, observation) -> mapping`**.
Construct a fresh `StoppageEvidence(windows=(), *, game=GAME, config=None)` per
match. It owns bounded ball history, a pause timer and one recent pause anchor.
`reset()` clears all of these and frame-order validation. Calls must be contiguous,
with `index == observation['frame']` and `time_s == index / games.py fps`. A first
call can start within a half, with fresh history. Each result is independent.

Both wrappers accept keyword-only `game=GAME, data_dir=None, config=None,
windows=None`. `None` windows loads automatic tags with the starter loader; `()`
disables tag context. Streaming adds `frame`; array indices themselves are frames.
Arrays contain float64 scores, Boolean availability and object H/A/None sides.
No rounding or frame dictionaries are retained. Closing the stream closes M3.
The scalar producer and streaming checker use only the standard library;
`build_evidence` requires the existing NumPy dependency.

| Field | Meaning |
|---|---|
| `dead_score` | Finite [0,1] support for a stoppage; default 0 |
| `dead_available` | Current ball motion and enough current nearby player positions/speeds can be evaluated |
| `restart_score` | Finite [0,1] support for resumed play following a recent supported pause; default 0 |
| `restart_available` | Dead-feature observations are available and a recent same-half pause anchor exists |
| `restart_side` | Optional current automatic-tag side; H, A or None, independently of score availability |

Unavailable scores are exactly zero with flag false. Available zero means the
observations did not support that signal. A known side can accompany zero or
unavailable restart evidence; **side alone must never release M2 from D**. Without
an active known tag the side is None. Any unknown or conflicting overlapping tag
also leaves it None. No team is guessed from track-slot identity or proximity.

## Features and missingness

1. Use M3 `x_m/y_m` directly. Retain out-of-pitch points. Signed distance to the
   nearest edge is `e=min(x,L-x,y,W-y)` using the pitch in `games.py`. Boundary
   support is `b=clip((boundary_margin_m-e)/boundary_margin_m,0,1)`. A boundary
   point supplies noisy context, never a referee decision by itself.
2. Keep observed ball points in a 0.20 s deque. Motion is observed path length
   divided by elapsed seconds, including short missing-sample gaps. Require at
   least 0.08 s between the oldest/current retained points. A gap exceeding
   0.20 s clears motion history. There is no interpolation, extrapolation or
   supplied ball-speed assumption. The deque holds at most 7 points at 25 fps.
3. Select current observed players within 20 m of the current ball, requiring
   both finite position coordinates and finite nonnegative `speed_mps`. M3 has
   already converted speed to m/s: **do not divide by 3.6 again**. At least three
   usable slots are required. Compute fractions slow (<=1.5 m/s) and active
   (>=2 m/s). No player positions, identities or individual trajectories are
   remembered. Speed without position cannot select a nearby player; position
   without speed cannot enter the movement fraction. Neither becomes zero.
4. A pause candidate requires ball speed <=0.7 m/s, slow fraction >=2/3 and
   boundary or active-tag context. These requirements must hold continuously
   for 0.40 s. Missing ball/player evidence or conflicting motion resets the
   timer. Then `dead_score=(0.65*b + 0.15*tagged)*slow_fraction`; otherwise 0.
   A stationary interior ball without a tag gives available zero evidence.
   A tagged interior pause alone is weak (at most 0.15).
5. A pause score >=0.50 records the current ball as a recent pause anchor. This
   internal evidence gate does not classify the frame or persist D. The anchor
   expires 3 s after its last supporting observation. Missing ball emits no
   positive evidence, even if an anchor survives. A supported restart requires
   current ball inside/on the pitch, ball speed >=2 m/s, displacement >=0.8 m
   from that anchor, and active fraction >=2/3. Then
   `restart_score=0.80*active_fraction + 0.10*tagged`; otherwise 0.
   Restart support may occur anywhere inside a window or without a window, and
   can repeat while the anchor remains recent. Neither endpoint causes it.

All evidence/history clears when entering a new inclusive `half_video_blocks(game)`
block, including adjacent blocks. Every outside-half frame remains in the stream
with unavailable zero scores and None side; no history accumulates there. All
199,319 tactical frames are retained. No corrected-tracking offset is applied.

## Configuration and rationale

`EvidenceConfig` is immutable; pass a replacement instance to the producer or
wrappers. Units and complete defaults follow. Invalid/nonfinite/nonpositive
values, contradictory speed gates and weights summing above one are rejected.

| Settings | Default | Rationale |
|---|---|---|
| `boundary_margin_m` | 1.5 m | Soft edge region for tracking noise |
| `nearby_radius_m`, `min_nearby_players` | 20 m, 3 slots | Local collective context, rather than one player |
| `motion_window_s`, `min_motion_s`, `max_ball_gap_s` | 0.20, 0.08, 0.20 s | Short observed motion baseline; refuse long occlusions |
| `ball_slow_mps`, `player_slow_mps` | 0.7, 1.5 m/s | Low ball motion and approximately walking players |
| `player_active_mps`, `collective_fraction` | 2 m/s, 2/3 | Require collective renewed movement |
| `pause_s`, `restart_memory_s` | 0.40, 3.0 s | Reject isolated noise; bound pause-to-restart memory |
| `restart_ball_mps`, `restart_displacement_m` | 2 m/s, 0.8 m | Require motion and meaningful observed displacement |
| `boundary_dead_weight`, `tag_dead_weight` | 0.65, 0.15 | Boundary dominates; automatic tags add modest support |
| `pause_anchor_score` | 0.50 | Weak interior tag context cannot seed a restart anchor |
| `movement_restart_weight`, `tag_restart_weight` | 0.80, 0.10 | Observed resumption dominates tag context |

These are plausibility choices exercised on invented fixtures, not learned or
calibrated probabilities. Full-stream checks validate mechanical invariants only.
No public ground truth, human labels or other-match labels were used to select
parameters. Maximum default scores are 0.80 dead and 0.90 restart. M2 must choose
and test its own acceptance, persistence and conflict policy.

## Verification and invented examples

Run from the isolated checkout with a working Python and NumPy for the tests:

```powershell
$python = 'C:/Users/oamu2/more-than-a-hack-2027/data/_review_20261113/env/Scripts/python.exe'
$bundle = 'C:/Users/oamu2/more-than-a-hack-2027/data'
& $python -m unittest discover -s tests -v
& $python module1/control_scores.py --test
& $python module4/test_stoppages.py
& $python -m module4.evidence --data-dir $bundle
git diff --check
```

For M4 only: `python -m unittest discover -s tests -p test_stoppage_evidence.py -v`.
The full checker exhausts actual M3 dictionaries and validates count, exact order,
finite bounded scores, Boolean availability, unavailable zeros and legal sides.
It prints aggregate counts/ranges/configuration only, without writing frame data.
The absolute interpreter above is the verified local environment, not a portable
installation requirement or proof of the M1 release pins.

Invented tests put a ball at (-0.3,34) m with three slow nearby players. After
the motion baseline and pause duration, a known-side tag yields dead score 0.80.
The ball then moves to (2,34) m with three players at 3 m/s: restart score 0.90,
even though the window has not ended. Without a tag, scores are 0.65 and 0.80
and side remains None. A passing ball with brief occlusion yields no positive
dead signal; a stationary centre-pitch ball without context also yields zero.
Tests additionally cover unknown/conflicting tags, exact endpoints, missingness,
unit-correct real M3 parsing of invented files, elapsed time across missing samples,
fresh halves, bounded history, nonmutation, order errors and a simple return-value
consumer. Existing standalone tag assertions are retained unchanged.

## Required M1/M2 handoff — not implemented here

M1's current `collect_evidence` calls `producer(index, observation)` but discards
the returned mapping; its comment describes a different one-argument signature.
Registering this producer alone does **not** integrate it. M1 source is unchanged.

M1 must construct the instance with loaded windows, feed each unchanged M3
observation to M1 and M4 in its existing single loop, collect all five returned
fields into aligned full-precision arrays, validate lengths/types/ranges/sides and
zero-on-unavailable, and explicitly pass the mapping to actual M2. Avoid a second
tracking scan in the runner: the wrappers above are standalone component tools.
Add a test proving these actual returned fields reach the decoder. No global
state or side-effect transport is necessary.

M2 must consume those five arrays alongside M1 control evidence and availability,
and the required half mask from `games.py`. Its fourth argument should become
documented stoppage evidence rather than exact restart windows, as proposed in
the integration plan. M2 owns H/A/D/X, confirming/retaining D through unavailable
evidence, supported restart exit, control persistence, half reset and conflicts.
Neither a positive weak score nor a known restart side is an automatic decision.
The current M1 fallback and old M2 signature are not this accepted consumer;
actual M1 transport and M2 behavioral acceptance remain proposed work.

## Limited coverage

Interior fouls, offside, referee delays, goals and distant-player restarts often
cannot be confidently inferred. Sparse players/speeds and long ball occlusions
cause abstention. A restart more than 3 s after the last observed supported pause
is deliberately unsupported. Motion may reflect tracking noise, retrieval,
warmup or a moving dead ball; slow live play near an edge can resemble a pause.
The collective sample can include duplicate export slots and incomplete teams;
it does not prove how every player moves. Observed paths underestimate unobserved
motion and can be distorted by tracking errors. No exact whistle time, exhaustive
stoppage coverage, possession quality, independent release reproduction or
completed pipeline is claimed.
