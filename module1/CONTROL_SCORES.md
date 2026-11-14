# Module 1 control evidence handoff

M1 consumes the corrected [M3 observation contract](../starter/TACTICAL_TRACKING.md)
and produces current team proximity evidence. It does not assign possession labels,
remember a previous team, confirm turnovers or decide whether play has stopped.
Scores are evidence strengths, not calibrated probabilities, and need not sum to one.

## Callables and fields

```python
from module1.control_scores import score_frame
from starter.tactical_tracking import iter_tracking_frames

for observation in iter_tracking_frames(data_dir="D:/match-data"):
    evidence = score_frame(observation, tau=3.0)
    # The same unchanged observation can also be passed to M4.
    control_available = evidence["home_available"] and evidence["away_available"]
```

`score_frame(observation, tau=3.0)` returns a fresh dictionary with exactly these
seven fields. It treats the input and all nested dictionaries/lists as read-only.

| Field | Type | Meaning |
|---|---|---|
| `ball_visible` | bool | Both ball metre coordinates are finite. Missing ball is false. |
| `d_home`, `d_away` | float | Nearest observed player distance to the ball in metres; NaN when unavailable. |
| `score_home`, `score_away` | float | `exp(-distance / tau)`; unavailable evidence is zero. Scores are finite in [0,1]. |
| `home_available`, `away_available` | bool | Ball position and at least one observed finite player position for that team are available. |

Both coordinates must be present and finite. Player `observed` must also be true.
One missing coordinate excludes that player, not its observed teammates. A visible
ball with no observed players still has `ball_visible=True` and both sides unavailable.
Availability does not certify complete player coverage or that the nearest actual
player was tracked. A very distant available side may have a score that underflows
to zero; it remains distinct from unavailable evidence.

Only `x_m` and `y_m` enter the existing nearest-distance calculation. M3 already
scales normalized coordinates by 105.3 x 68 m; M1 does not scale them again.
`tau` is in metres and must be finite and strictly positive, even when the ball is
missing. Invalid tau raises `ValueError`. Speed is not needed: valid positions
with `speed_mps=None` remain usable, and finite speed does not create a position.
M3's corrected `speed_mps` is already m/s and must not be divided by 3.6 again.
The H/A team labels come directly from M3. Track slots are not persistent people.

For an invented ball at (10,10) m, nearest home player at (13,14) m and nearest
away player at (10,11) m, distances are 5 m and 1 m. At tau=3 m the scores are
`exp(-5/3)` and `exp(-1/3)`, and both sides are available. If every home position
disappears, `d_home=NaN`, `score_home=0`, and `home_available=False`; the away
distance and score remain available if its player and the ball are observed.

## Streaming and full-match arrays

`iter_control_scores(tau=3.0, game=GAME, data_dir=None)` yields `frame` plus the
seven fields above, using `iter_tracking_frames` as its only tracking input.
It retains no history of frame dictionaries. Indices are tactical video frames,
zero-based, including pre-match, halftime and post-match. Exhaust the iterator to
complete M3's final count validation; `close()` also closes the underlying reader
when deliberately stopping early. Structural tracking/metadata errors propagate.

`build_evidence(tau=3.0, game=GAME, data_dir=None)` streams that same path into a
dictionary of seven NumPy arrays, each of length `source_frames("tactical", game)`.
Array index is frame index; distances/scores are full-precision float64, while
visibility/availability arrays are Boolean. It checks order/count and never retains
all observation dictionaries. Use these in-memory arrays as canonical inference input:

```python
from module1.control_scores import build_evidence

evidence = build_evidence(data_dir="D:/match-data")
control_available = evidence["home_available"] & evidence["away_available"]
```

**M2 handoff:** initially require both availability flags before allowing a score
comparison to force a turnover. False availability must not manufacture opposing
control. A true flag alone also does not prove controlled possession. M2 still owns
credible magnitude/margin, persistence, missing-evidence policy and temporal state;
none of those decisions is implemented here.

## Compatibility and diagnostics

- `min_dist_per_team` retains its tuple input and nearest-distance arithmetic.
  `distance_to_score` retains its formula and infinity-to-zero behavior, now
  rejecting invalid tau.
- `build(tau=3.0, game=GAME, data_dir=None)` retains its five-array tuple
  `(visible, d_home, d_away, s_home, s_away)` and int8 visibility. It now delegates
  to M3 and `build_evidence`. This compatibility view omits availability and must
  not be used alone for the new M2 interface.
- The duplicate raw parsing helper/path was retired. Malformed IDs, truncation
  and invalid metadata now raise M3 errors rather than silently producing arrays.
- `write_csv(path, visible, d_home, d_away, s_home, s_away)` retains the original
  six-column diagnostic format. Optional keyword arrays `home_available` and
  `away_available` must be supplied together and append those two columns.
- The CLI now writes eight diagnostic columns, including availability. Distances
  are rounded to three decimals, scores to four; unavailable distances are blank.
  The CLI overwrites its diagnostic output after a successful full read. Its CSV
  is not a submission and must not be read back as an implicit inference route.
  Rounding can change score comparisons; retain full precision in memory.

## Execution and tests

From this clone's repository root, with NumPy installed:

```powershell
python -m unittest discover -s tests -v
python module1/control_scores.py --test
python -m starter.tactical_tracking --data-dir "D:\match-data"
python -m module1.control_scores --data-dir "D:\match-data" --out data/control_scores_diagnostic.csv
```

`data_dir` is the bundle root containing `tactical/`; `MTAH_DATA_DIR` set before
Python starts is also supported. The scripts accept `--game` and `--tau` where
applicable. `python module1/control_scores.py ...` remains supported. If Windows
aliases fail, invoke a working interpreter with `& "C:\path\to\python.exe"`.
Invalid tau/input returns CLI status 1 without writing a new diagnostic CSV.
Fixture tests need no match files, labels or network access. They cover the real
M3-to-M1 handoff using invented XML/TXT, units, geometry, symmetry, missingness,
availability, invalid tau, laziness, input immutability and error propagation.

## Branch provenance and local validation

- Original checkout: `module-3-tracking-reader` at corrected M3 commit
  `e0a0fd2f098194704b0493a2ea335ea3b4b9d06c`, clean and left unchanged.
- This isolated clone: `data/integration-attempt`, branch `integration-attempt`,
  started at reviewed M1 commit `06e4c9bc232c751fb9aaec00093fa8c087349527`.
- The ordinary merge of corrected M3 commit `e0a0fd2f098194704b0493a2ea335ea3b4b9d06c`
  was prepared with `--no-commit --no-ff`, without conflicts. Its staged M3 files
  match that commit exactly; its 15 fixture tests pass. No commit was created.
  Therefore M3 is present in the working tree and recorded as `MERGE_HEAD`, but
  is not yet an ancestor of branch HEAD. An owner must commit the pending merge
  before claiming the corrected dependency is recorded in branch history.
- Remote refresh was attempted. The original checkout could not write
  `FETCH_HEAD`; refresh in this clone failed on DNS. Freshness remains unverified.
- Local fixture verification used Python 3.14.7 and existing NumPy 2.5.2:
  **32 tests pass** (17 M1 plus 15 M3), and the original M1 self-test passes.
- A local full-match check exhausted `build_evidence` while checking every
  `iter_control_scores` index: **199,319** outputs, exactly **0..199318**,
  **113,488** observed-ball frames. All scores were finite in [0,1]; unavailable
  scores were zero, distances NaN, and availability never occurred without a ball.
- The previous M1 `build` from starting commit `06e4c9b` was run separately on
  the same tactical assets. Visibility, both distances (including NaNs), and both
  scores match **exactly**, with zero differing elements. Thus no numerical
  difference needs explaining on this bundle. Partial-NaN and malformed-input
  corrections are exercised by invented fixtures; the actual matched values do
  not remove those old-parser defects on other inputs.
- Home evidence is available on **112,589** frames and away evidence on
  **113,318**. There are **1,069** visible-ball frames lacking at least one side.
  Those pre-existing absences now have explicit flags; they are not newly
  inferred turnovers. These are coverage diagnostics, not possession-quality
  measurements.
- The full diagnostic CLI also completed with status 0 and 199,319 rows; an
  invented malformed-input subprocess returned status 1. `git diff --check`
  passed. Restricted inputs and detailed diagnostic CSVs stayed local. No
  ground-truth labels were read, and no training or tuning was performed.

This is an M1 handoff proposal, not downstream M2 acceptance or independent M5
reproduction. Historical review findings and the full integration plan remain
unchanged.
