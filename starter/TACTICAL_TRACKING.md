# Shared tactical tracking reader

Run examples from the repository root with Python 3.8 or newer. This module uses the
standard library. It reads the tactical XML/TXT pair through the existing `games.py`
helpers and streams one frame at a time.

This is M3's **proposed stable handoff contract** for Modules 1 and 4. It does not
claim that downstream adapters or evidence interfaces are agreed or implemented.

```python
from starter.tactical_tracking import iter_tracking_frames

observed_ball_frames = 0
for observation in iter_tracking_frames():
    observed_ball_frames += observation["ball"] is not None
print("Frames with a ball observation:", observed_ball_frames)
```

The public interface is `iter_tracking_frames(game=GAME, data_dir=None)`. The default
data folder comes from `games.py`. Set `MTAH_DATA_DIR` before starting Python, or pass
`data_dir` pointing to the bundle root containing `tactical/`.

## What each frame contains

| Field | Meaning |
|---|---|
| `frame` | Zero-based tactical video index, equal to the supplied tracking ID minus one |
| `time_s` | Seconds from video start, computed as `frame / fps` using `games.py` |
| `players` | List with every metadata track slot, in XML `Player` document order |
| `ball` | Dictionary with `x_norm`, `y_norm`, `x_m`, `y_m`, or `None` if either coordinate is nonfinite |

Each player dictionary contains these fields.

| Field | Meaning |
|---|---|
| `track_slot` | One-based position in the metadata's `Player` order. Stable within this export. Slots may change which person they track. |
| `team` | `H` or `A`, resolved from `teamId`. The first metadata `Team` is home and the second is away. |
| `x_norm`, `y_norm` | Supplied normalized pitch coordinates |
| `x_m`, `y_m` | Normalized coordinates multiplied by the configured pitch length and width, currently 105.3 and 68 m |
| `speed_mps` | Finite source player speed converted once to metres per second, independently nullable |
| `observed` | `True` when both supplied position coordinates are finite |

If either player coordinate is NaN or infinite, **all four position fields are `None`**
and `observed` is `False`. The slot stays in the list. A finite speed is retained even
when position is missing. A nonfinite speed becomes `None` without hiding a valid position.
Finite coordinates outside 0–1 are retained. An observed `(0, 0)` is a valid position.

### Source channels and speed units

The supplied tactical XML declares `position_x` and `position_y` with unit
`normalized`, followed by `speed_kph` with unit `kph`. The third raw field in each
player group is therefore **km/h**, not m/s. The reader divides it by **3.6**:
raw `36` becomes `speed_mps = 10.0`. Consumers must not divide it again.
Nonfinite speed becomes `None`; position and speed availability remain independent.
The ball still exposes only coordinates, never speed.

Before opening the raw stream, the reader resolves each `PlayerChannelRef` through
`PlayerChannel` to its `Channel` definition. It requires x/y/speed order, normalized
position units, and a consistent speed declaration across every player slot. The
supplied bundle has 46 such groups, each matching XML `Player` document order.
`PlayerChannel` declaration order and IDs are not column order. A register order
that disagrees with `Player` order is rejected rather than silently relabeling slots.

The ball register must contain exactly three `BallChannelRef` entries. Every
`channelId`, including the third reference, must resolve to a declared channel.
The first two must declare normalized `position_x` then normalized `position_y`;
missing, unknown or swapped references are rejected before streaming. The third
raw field is still parsed as a number, but ball speed is not exposed publicly.

Each referenced player **and ball** position channel must contain exactly one
`Name` and exactly one `Unit`, matching the supported position name and
`normalized` unit. Duplicate declarations are rejected even when their values
agree; contradictory, missing, empty or unsupported position declarations also
fail. Separate channel IDs for ball and player positions are supported when
their declarations meet these same checks. No metadata remapping is performed.

Supported speed declarations are deliberately limited to these exact pairs:

| Channel name | Unit | Conversion to `speed_mps` |
|---|---|---|
| `speed_kph` | `kph` | Divide by 3.6 (supplied export) |
| `speed_mps` | `m/s` | Retain unchanged (tested invented variant) |

Invalid references, ambiguous position declarations, and missing, unsupported,
contradictory or inconsistent player-speed declarations raise
`TrackingDataError` before any observation is yielded. This is a validator for this
export layout, not a general EPTS loader. Unit declarations, rather than plausible
numerical values or a loader's output convention, determine conversion.

For an invented example, `(0.5, 0.5)` becomes `(52.65, 34)` metres. For homography
projection, pass the **normalized** coordinates to `project(H[frame], x_norm, y_norm)`
and check that frame's `valid` flag first. See [the homography helper](load_homography.py).

An invented observation excerpt illustrates the unchanged schema; remaining slots
are omitted here only. A raw player group `0.5,0.5,36` with km/h metadata yields:

```python
{
    "frame": 0,
    "time_s": 0.0,
    "players": [{
        "track_slot": 1, "team": "H", "observed": True,
        "x_norm": 0.5, "y_norm": 0.5,
        "x_m": 52.65, "y_m": 34.0, "speed_mps": 10.0,
    }],
    "ball": None,
}
```

## Sharing the same observation between Modules 1 and 4

Pass each observation to both consumers inside one loop. The functions below are
teammate-provided callbacks, so the reader can be used before either module is finished.

```python
from starter.tactical_tracking import iter_tracking_frames

def run_consumers(module_1, module_4, data_dir=None):
    for observation in iter_tracking_frames(data_dir=data_dir):
        module_1(observation)
        module_4(observation)
```

Consumers should treat the shared dictionaries as read-only. Each yielded frame has
its own dictionaries and player list, so advancing the iterator leaves earlier frames
intact. Keeping all frames in a list will use substantially more memory than processing
them as they arrive.

M1 can read `team`, `observed` and metre coordinates to compute team proximity
evidence. M4 can read those same positions and the independently nullable
`speed_mps` for movement evidence, keeping any small history in its own state.
Neither consumer should add fields, alter lists or replace missing values in the
shared frame. An observed position does not guarantee speed availability, and a
finite speed does not guarantee a position or persistent player identity.

## Verification

```powershell
python -m starter.tactical_tracking
python -m starter.tactical_tracking --data-dir "D:\match-data"
python -m unittest discover -s tests -v
```

`python starter/tactical_tracking.py` also works. The verification command reads the
complete input, prints only aggregate counts and coverage, and exits with status 1
on invalid input. Tests use tiny invented fixtures in temporary directories and need
neither match files nor ground-truth labels.

The reader checks metadata channels/units and slot mapping before streaming, then
every tracking ID in order, the number of player groups on each row,
all numeric fields and the total record count. It validates the ball's three input
fields even though only ball coordinates are exposed. Unknown metadata team references,
blank lines and malformed rows raise `TrackingDataError`, a `ValueError` subclass.
Messages identify the file and record or metadata location without echoing source rows.
Missing or unreadable files raise `OSError` subclasses.

**Full validation completes when the iterator is exhausted.** If a consumer stops early,
later corruption or a missing final record may still be undetected. Call `close()` on
an iterator that you deliberately stop early to release its file handle promptly.

Pre-match, halftime and post-match frames are included. The reader applies no possession
labels, interpolation or smoothing. Modules 1 and 4 decide which observations to use.
The large corrected-tracking offsets in `games.py` do not enter participant ATD alignment.

Local verification on November 6, 2026 passed all nine fixture tests and read 199,319
tactical frames, indices 0 through 199318, with 46 slots per frame. The ball was observed
on 113,488 frames (56.9%), matching [DATA.md](../DATA.md).

The speed correction was verified locally on the working tree based on reviewed
commit `a7ab2b1f224d9eb575d5aacc804c0fa3a4b2fe5c`:

- All **15** invented fixture tests pass, including the regression that failed on
  the reviewed code (`36` was returned instead of `10`), zero/nonfinite speed,
  independent missingness, channel/slot mapping and m/s without double conversion.
- The verification command exits 0 after all **199,319** frames, indices
  **0..199318**, with **46** slots each and **113,488** observed-ball frames.
- A streamed local comparison against that reviewed implementation checks every
  position, missingness flag, ball, team, slot and frame/time value: **zero changes**.
  All **3,412,124** finite raw player speeds match division by 3.6; all
  **5,756,550** nonfinite speeds remain `None`.
- Pre-match **11,185**, first-half **79,467**, halftime **20,156**, second-half
  **79,390** and post-match **9,121** frames are retained.
- An invented duplicate-ID input returns process exit status **1**. Missing or
  unsupported unit declarations also fail before streaming.

These checks used Python **3.14.7** with no additional reader dependencies. The
commands above use `python` for portability; if Windows aliases cannot launch,
use a working interpreter explicitly, for example
`& "C:\path\to\env\Scripts\python.exe" -m unittest discover -s tests -v`.
The existing local review environment was reusable here; its absolute path is not
a teammate setup requirement. Remote freshness could not be verified (fetch lacked
permission to write `FETCH_HEAD`; the read-only remote query failed on DNS).
This is local M3 gate evidence, not independent Module 5 or downstream sign-off.

### Metadata follow-up verification

The two metadata gaps R1/R2 in `M3_M1_REVIEW.md` were addressed in the M3 working
tree based on corrected commit `e0a0fd2f098194704b0493a2ea335ea3b4b9d06c`.
Before the fix, **27** invalid invented variants were accepted: 11 malformed ball
reference layouts and 16 duplicate/contradictory player or ball position
declarations. The valid fixture with separate ball-position channels passed.
The new regressions require all invalid variants to fail before yielding a frame.

The public function, schema, player-speed conversion and M1 handoff are unchanged.
Verification with the existing Python 3.14.7 environment:

- `python -m unittest discover -s tests -v`: **19 M3 tests pass**.
- `python -m starter.tactical_tracking`: exit 0, **199,319** frames indexed
  **0..199318**, **46** slots per frame and **113,488** observed-ball frames.
- A streamed comparison of every complete frame dictionary against `e0a0fd2`
  found **zero output differences**, covering **9,168,674** player slots as well
  as ball fields, speed, position, missingness, teams and frame/time alignment.
- An isolated temporary snapshot of published `integration-attempt` commit
  `303513da2247387945f00b6c347090f0be65d79e`, overlaid with the M3 follow-up,
  passed the full **36-test M3/M1 suite** using the same unittest command.
  The actual integration clone's status, refs, index and relevant files remained
  unchanged. No M1 implementation adjustment was needed.
- `git diff --check` passed. Remote freshness remains unverified: fetch could
  not write `FETCH_HEAD`, and a read-only remote query failed on DNS.

The change is intentionally uncommitted on `module-3-tracking-reader`. Handoff:
after the M3 owner records and publishes these three M3 files, the integration
owner should refresh remote refs, inspect any intervening changes, and ordinarily
merge the updated `origin/module-3-tracking-reader` into `integration-attempt`.
Rerun its full suite (currently 36 tests) and the tactical verification command.
No commit, push or merge was performed for this follow-up. Existing
speed-correction evidence above remains historical evidence for that earlier change.

**Regenerate previous local previews before reuse:** outputs generated with the
reviewed reader may contain raw km/h values mislabeled as `speed_mps`. Relabeling
those values as already converted m/s would preserve the defect.
