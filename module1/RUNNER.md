# Integrated possession runner

Canonical command from the combined checkout (Python 3.12.10):

```powershell
python run_possession.py --mode integrated --data-dir C:/path/to/bundle --out data/release/candidate.csv --report data/release/pipeline.json
```

Integrated is the default. The bundle contains `tactical/`; `MTAH_DATA_DIR`, set
before Python starts, is also supported. No ground-truth path is accepted.
For reproducible fresh generation with tests, official validation and provenance,
use `python run_release.py --data-dir C:/path/to/bundle`. See [RELEASE.md](../RELEASE.md).

## Actual transport

One M3 `iter_tracking_frames` stream is exhausted. Every frame must be an integer
index in exact order 0..199318, with exactly 199,319 observations. Each observation
is wrapped recursively read-only; the same wrapper goes to actual M1 `score_frame`
and an instance of actual M4 `StoppageEvidence`. M4 loads automatic Smart Tagging
windows once; it does not create a second tracking reader. Compact NumPy arrays
retain all seven M1 fields and all five M4 fields, without rounding or retaining
the tracking dictionaries. M4's automatic kickoff-context prior is also transported
as `initial_dead`, a Boolean array true only at supported graded-half starts.
Unknown/extra/missing producer keys and invalid scalar
types fail before assignment can coerce them.

Actual `modulos.modulo2.modulo2` receives exactly:

- M1: `score_home`, `score_away`, `ball_visible`, `home_available`, `away_available`.
- M4: `dead_score`, `dead_available`, `restart_score`, `restart_available`, `restart_side`.
- Native inclusive `games.half_video_blocks(GAME)` triples, unchanged.
- M4's `initial_dead` prior as an explicit keyword; missing transport fails.

Distances remain validated diagnostics, not M2 inputs. Arrays must be one-dimensional
and exactly aligned. Scores are finite real numbers in [0,1], flags are Boolean,
unavailable scores are zero, available distances are finite/nonnegative, and
unavailable distances are NaN. Team availability implies visible ball. Available
zero evidence is legal. Restart availability is independent of team availability;
H/A/None side context alone is not positive restart evidence.

## Unchanged component policy

M1 uses `exp(-distance/tau)` with tau=3 metres. Corrected M2 defaults require
score >=0.10, margin >0.05 and 12 consecutive control samples; dead and restart
confirmation require three consecutive available scores >=0.50. Labels change on
the confirmation frame. Initial and unknown/conflicting restart side can yield X.
Default simultaneous strong evidence priority remains dead. Every half starts
fresh, and all frames outside the native inclusive halves are X. X is also legal
inside halves. Thresholds remain unchanged. The scoped kickoff follow-up adds
M4's unique automatic Kick Off (Start) prior and fresh-motion eligibility; M2
initializes those tagged halves in D and otherwise retains X initialization.
See the current kickoff section of M4's contract for ambiguity and timing limits.

M4's accepted restricted envelope, including ball-only retrieval ambiguity and
whole-half unreported eligibility, is in [EVIDENCE.md](../module4/EVIDENCE.md).
Tests and format validity do not establish match accuracy.

## API and compatibility

`collect_evidence(tau, game, data_dir, *, mode='integrated', windows=None)` returns
13 named arrays (the original 12 plus `initial_dead`). `windows=None` loads automatic tags; an explicit iterable is useful
for invented fixtures. `decode_match(evidence, n_frames, game, *, mode='integrated')`
returns one H/A/D/X label per frame and validates outside-half labels.
Missing M2 or M4 is an error; no silent fallback is allowed.

`--mode fallback` explicitly selects the retained historical M1-only decoder.
It uses immediate first acquisition and the old margin >=0.05 convention, never
emits D, and is **not eligible for an integrated release**. `decode_half` and the
fallback-only legacy `PRODUCERS` diagnostic hooks remain available. Their historical
regressions are retained and explicitly run in fallback mode. They are not evidence
that integrated transport works. M1's legacy five-array tuple and rounded diagnostic
CSV APIs remain unchanged; neither is used by integrated inference.

## Output and failure behavior

The UTF-8 CSV has no BOM, LF newlines, a final newline, and `frame,label` header.
The writer atomically replaces `--out` only after complete successful inference.
A failed run can leave a prior output intact; therefore a file check alone never
proves regeneration. The release procedure always creates a unique ignored run
directory and writes successful evidence only after all required steps pass.
`--report` writes aggregate JSON/configuration only. Any required read, inference,
write or report failure returns nonzero. Use one process per output path.

## Tests

```powershell
python -B -m unittest discover -s tests -v
python -B module1/control_scores.py --test
python -B modulos/test_modulo2.py -q
python -B module4/test_stoppages.py
```

The M4 loader imports M2 from this checkout; no `MTAH_M2_ROOT` or other clone is
needed. Invented pipeline tests exercise actual M1/M4/M2, and an invented EPTS
fixture includes the actual M3 parser through serialization. Existing M5 metric
and supplied baseline/public-label shape checks are retained. They are format/
metric tests, not training, tuning, version selection or accuracy acceptance.
Current execution evidence is in [INTEGRATION_STATUS.md](../docs/INTEGRATION_STATUS.md).
