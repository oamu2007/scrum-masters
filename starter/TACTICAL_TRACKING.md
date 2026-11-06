# Shared tactical tracking reader

Run examples from the repository root with Python 3.8 or newer. This module uses the
standard library. It reads the tactical XML/TXT pair through the existing `games.py`
helpers and streams one frame at a time.

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
| `speed_mps` | Supplied speed in metres per second, independently nullable |
| `observed` | `True` when both supplied position coordinates are finite |

If either player coordinate is NaN or infinite, **all four position fields are `None`**
and `observed` is `False`. The slot stays in the list. A finite speed is retained even
when position is missing. A nonfinite speed becomes `None` without hiding a valid position.
Finite coordinates outside 0–1 are retained. An observed `(0, 0)` is a valid position.

For an invented example, `(0.5, 0.5)` becomes `(52.65, 34)` metres. For homography
projection, pass the **normalized** coordinates to `project(H[frame], x_norm, y_norm)`
and check that frame's `valid` flag first. See [the homography helper](load_homography.py).

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

The reader checks every tracking ID in order, the number of player groups on each row,
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
