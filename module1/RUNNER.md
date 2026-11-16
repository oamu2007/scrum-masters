# Release runner (M1)

`run_possession.py` (repository root) turns the tactical tracking into one possession label per
video frame and writes the submission CSV. One command, no ground-truth input.

## Command

From the repository root:

```powershell
python run_possession.py --data-dir C:\path\to\bundle --out data/release/<team_name>.csv
```

- `--data-dir`: bundle root, the folder that contains `tactical/`. If omitted, `MTAH_DATA_DIR`
  (set before Python starts) or the repository default is used.
- `--out`: submission CSV to write. Replace `<team_name>` with the registered team name.
- `--tau`: metres for the proximity score `exp(-distance / tau)`. Default `3.0`.
- `--game`: defaults to the match in `games.py`.

Then validate the exact file:

```powershell
python evaluation/validate_submission.py "data/release/<team_name>.csv"
```

## Pipeline

1. **M3** (`starter/tactical_tracking.py`) streams the tactical tracking once.
2. Each unchanged observation goes to **M1** (`module1/control_scores.py`, `score_frame`) and to
   any other evidence producer in the `PRODUCERS` list. M4's stoppage/restart evidence plugs in
   there.
3. M1's evidence is kept as full-precision arrays (not rounded CSV): `score_home`, `score_away`,
   `d_home`, `d_away`, `ball_visible`, `home_available`, `away_available`.
4. A decoder turns the arrays into labels, half by half, using `half_video_blocks` from
   `games.py` (1st half 11185-90651, 2nd half 110808-190197, inclusive). State starts fresh in
   each half.
5. Every frame is written: `H` / `A` / `D` inside the halves, `X` outside them.

Frame count, frame rate, paths and half blocks all come from `games.py`; nothing is hard-coded
in the runner.

## Current decoder: fallback

`decode_half` is a simple placeholder so a valid candidate exists. It will be replaced by M2's
decoder with the same inputs. It uses only M1 evidence:

- A score comparison is considered only when **both** `home_available` and `away_available`
  are true. Missing evidence never creates opposing control.
- The leading side must have score >= `MIN_SCORE` and beat the other by >= `MARGIN`.
- A change of side needs that lead for `CONFIRM_FRAMES` consecutive frames. One nearest-player
  flip does not switch possession.
- Missing, weak or tied evidence keeps the current side (passes and occlusions do not end it).
- Before the first confirmed side the label is `X` (no guess).
- It does **not** produce `D`. Dead-ball evidence is M4's job and is not connected yet.

## Configuration used

| Parameter | Value | Meaning |
|---|---|---|
| `tau` | 3.0 m | Distance at which a proximity score falls to 1/e |
| `MIN_SCORE` | 0.10 | Leading side must be at least this close (about 7 m at tau = 3) |
| `MARGIN` | 0.05 | Leading side must beat the other by at least this much |
| `CONFIRM_FRAMES` | 12 | About 0.5 s at 25 fps of consecutive control before switching |

These are fixed constants chosen for plausibility. They were **not** tuned on the public ground
truth, which is too short (17 possessions) to select parameters. Do not change them by looking
at public-label scores.

## Environment

Tested with Python 3.12.10 and NumPy 2.5.4 (installed from `requirements.txt`). The runner
itself needs only NumPy. Install with:

```powershell
python -m pip install -r requirements.txt
```

## Output and overwrite rules

- Header `frame,label`, then one row per frame, frames `0..199318` in order, 199,319 data rows,
  LF line endings.
- The file is first written to `<out>.tmp` and renamed to `<out>` only after the whole run
  succeeds. A failed run never leaves a partial submission. An existing `<out>` is replaced only
  by a successful run.
- On any error the runner prints `ERROR: ...` to stderr and exits with status 1.

## Result of the fallback run (format check only)

Run on the tactical bundle: ball visible on 113,488 of 199,319 frames. Output counts were
`H 83,631`, `A 75,224`, `D 0`, `X 40,464` (40,462 of them are the ungraded frames outside the
halves). The official validator accepts the file and reports 710 possessions of mean 8.9 s.
That count is high for a real match, which is expected without stoppage evidence and without
M2's possession memory. The validator checks format only; it says nothing about label quality.

## Tests

```powershell
python -m unittest discover -s tests -v
python module1/control_scores.py --test
```

## Rules

No ground-truth labels are read, nothing is trained, and no label is produced or corrected by
hand. Restricted match data and generated CSVs are not committed (`data/` is gitignored).
