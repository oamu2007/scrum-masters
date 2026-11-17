# Reproduce the reviewed possession-quality candidate

## Identity and access

**Independent teammate reproduction is complete, as confirmed by the team owner.**
The final technical document records Armando Sánchez regenerating the selected
CSV on a second Windows AMD64 machine on 2026-11-17, from a clean clone at
`00b8ed3`, with the SHA-256 below, 342 passing tests without skips and official
validation passing. The owner physically checked that run. Its logs remain in
Armando's ignored `data/` files and were unavailable to the final-check reviewer;
this status records the team's confirmation rather than a review of those logs.
The original two same-machine agent runs establish repeat generation separately.
A matching hash proves bytes, not possession accuracy.

| Item | Verified identity |
|---|---|
| Selected CSV SHA-256 | `6D4E42C45559C71F77DF4F4198F14F51D7D8D901D5EC2620E01487AFF3327B74` |
| Original generation source / reviewed implementation | `5ed8c7ccc249c774e150addd5fc25cd8041fc309` (clean) |
| Reviewed branch tip | `9126be95bb0bb7b3a9aedff57282a2c7b6933a10` |
| Current merged inference source | Local `main` merge `00b8ed3b291692180652658c87c0f17d60f7f510`; production files identical to `5ed8c7c` |
| Original run directory, relative to original repository | `data/possession-quality-20261117/data/release/runs/20261117T170938345818Z/` |
| Same-machine repeat directory, same prefix | `data/possession-quality-20261117/data/release/runs/20261117T171127788505Z/` |

Both directories contain `scrum-masters.csv` (originally `candidate.csv`), `evidence.json`, `pipeline.json` and
test/generation/validator logs. Their actual manifests identify source `5ed8c7c`,
the command/configuration below, matching inputs and matching CSV hashes.
`2a3a89d7308bf967dd7c0354f69263a9e1e31fea` only records results;
`9126be9` adds restart-characterization tests and documentation. Neither generated
this candidate or changed production inference. The documentation commit containing
this guide is a later descendant; record its identity with `git rev-parse HEAD`.

**Public source:** [scrum-masters](https://github.com/oamu2007/scrum-masters)
and this guide were accessible without authentication during the 2026-11-17 final
submission check. Published `main` was `4f1abae849a1d72df532d25512175a9703f0fa11`,
which contains the merge and handoffs. Clone the public repository with Git history.
Use a dedicated clean checkout of `00b8ed3` (or this documentation descendant).
For historical-source reproduction, a separate checkout of `5ed8c7c` is equivalent
for generation, but its maintained suite has 339 rather than 342 tests.

The conflict-free merge preserves local main `ae65c5f` and reviewed tip `9126be9`
as parents. It brings 46 existing commits / 57 changed files from that main base,
including M3/M1 integration, accepted M4/M2/M5 merges (`4f202d1`, `25051b0`,
`e33a4d3`), integrated release wiring `90d1f4e`, kickoff policy `48d67bb`, and
their tests/records before the quality change. Inspect the complete incoming
history with `git log --oneline ae65c5f..9126be9`; the merge tree equals `9126be9`.

## Root, environment and licensed inputs

All commands below run from **the source repository root**, the directory containing
`run_possession.py`, `games.py` and `requirements-release.txt`. Substitute your own
bundle path. No original developer path or environment is needed.

Install Python **3.12.10** and create a fresh environment. Recorded Windows 11 pins
are NumPy 2.5.4, pandas 3.1.1, python-dateutil 4.0.0 and tzdata 2026.6, all tracked in
[`requirements-release.txt`](../requirements-release.txt). Fresh installation and
cross-platform byte equivalence were not retested during this handoff.

PowerShell (choose an unused environment directory):

```powershell
py -3.12 -m venv data/reproduction-env
$py = './data/reproduction-env/Scripts/python.exe'
& $py -c "import sys; assert sys.version_info[:3] == (3,12,10); print(sys.version)"
& $py -m pip install -r requirements-release.txt
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $py -m pip freeze
git rev-parse HEAD
git status --short
```

On macOS/Linux use `python3.12 -m venv data/reproduction-env`, then
`py=./data/reproduction-env/bin/python`; replace `& $py` with `"$py"` and set
`export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Run the same version assertion,
installation and source checks. The exact patch version assertion must pass.

Acquire the competition bundle through your own licensed access; do not redistribute
it. Only these three assets are read by production (video/homography are unnecessary):

```text
<LICENSED_BUNDLE_ROOT>/
  tactical/
    BAR-ATH_tactical_atd.xml
    BAR-ATH_tactical_atd.txt
    BAR-ATH_tactical_smart_tagging.xml
```

| File under `tactical/` | Bytes | SHA-256 |
|---|---:|---|
| `BAR-ATH_tactical_atd.xml` | 59,057 | `327E35E32E46A647389B88F883D4F9A2AB931E3E6148AEF2FCF8F22B1E93C43A` |
| `BAR-ATH_tactical_atd.txt` | 195,714,285 | `F130E350D2BFDF734B7E32F072931FCCC6D015C1E837D082064875FE0A700431` |
| `BAR-ATH_tactical_smart_tagging.xml` | 261,055 | `0594D35E3DF01B9C5002372D8615E2E8EF5379AC8F4E84C5EF7A53F4304C9019` |

`--data-dir` takes the bundle root, **not** its `tactical/` subdirectory.
`MTAH_DATA_DIR`, set before Python starts, is an alternative; the explicit argument
below avoids dependence on a local environment variable.

## Execute once into a new directory

The recorded production child command is `python -B run_possession.py --mode
integrated --out <fresh>/candidate.csv --report <fresh>/pipeline.json --game
BAR-ATH --tau 3.0 --data-dir <LICENSED_BUNDLE_ROOT>`. Its portable spelling follows.
The exclusive directory creation refuses reuse because the runner itself can
replace an existing output. Change the run name for another attempt.

```powershell
$bundle = '<LICENSED_BUNDLE_ROOT>'
$run = 'data/reproduction/teammate-01'
& $py -c "from pathlib import Path; Path('$run').mkdir(parents=True, exist_ok=False)"
# Stop if directory creation or any subsequent command fails.
& $py -B -m unittest discover -s tests
& $py -B run_possession.py --mode integrated --out "$run/candidate.csv" --report "$run/pipeline.json" --game BAR-ATH --tau 3.0 --data-dir "$bundle"
& $py -B evaluation/validate_submission.py "$run/candidate.csv" --rows 199319
Get-FileHash -Algorithm SHA256 -LiteralPath "$run/candidate.csv"
```

For macOS/Linux set `bundle='<LICENSED_BUNDLE_ROOT>'` and
`run='data/reproduction/teammate-01'`, then use the same arguments with `"$py"`.
A platform-independent hash command (PowerShell spelling) is:

```powershell
& $py -c "import hashlib,sys; print(hashlib.file_digest(open(sys.argv[1],'rb'),'sha256').hexdigest())" "$run/candidate.csv"
```

POSIX also supports `sha256sum "$run/candidate.csv"` (Linux) or
`shasum -a 256 "$run/candidate.csv"` (macOS). Hexadecimal case is immaterial.

Configuration is **integrated**, BAR-ATH, tau **3.0 m**, 25 fps, inclusive half
triples `[(1,11185,90651),(2,110808,190197)]`, with M4-inferred initial-D priors
for halves 1 and 2. M2/M4 use the source defaults, with **no configuration file or
extra CLI overrides**. Compare the generated report with this complete manifest
configuration (field order is immaterial):

```json
{
  "m2": {"confirm_frames":12,"dead_confirm_frames":3,"dead_min_score":0.5,"min_margin":0.05,"min_score":0.1,"restart_confirm_frames":3,"restart_min_score":0.5,"same_frame_priority":"dead"},
  "m4": {
    "ball_restart_weight":0.6,"ball_slow_mps":0.7,"boundary_dead_weight":0.65,"boundary_margin_m":1.5,
    "collective_fraction":0.6666666666666666,"exit_memory_s":2.0,"max_ball_gap_s":0.2,"max_ball_mps":80.0,
    "min_motion_s":0.08,"min_nearby_players":3,"min_out_samples":3,"motion_window_s":0.2,
    "movement_restart_weight":0.8,"nearby_radius_m":20.0,"pause_anchor_score":0.5,"pause_s":0.4,
    "player_active_mps":2.0,"player_slow_mps":1.5,"restart_ball_displacement_m":2.0,"restart_ball_mps":2.0,
    "restart_ball_sustain_s":0.2,"restart_consume_s":1.0,"restart_displacement_m":0.8,"restart_progress_m":0.5,
    "restart_report_samples":3,"tag_dead_weight":0.15,"tag_restart_weight":0.1,
    "tagged_pause_s":1.0,"tagged_pause_span_m":1.0,"tagged_pause_weight":0.8,"weak_dead_cap":0.3
  }
}
```

The report calls these objects `m2_config` and `m4_config`. All required inference,
configuration defaults and dependency pins are tracked. The ignored historical
`data/quality/review-gates.json`, manifests, virtual environment and licensed assets
are not delivered by Git. This guide carries their essential reproduction facts;
the direct runner does not need that gate file. Historical `run_release.py`
orchestration returned 2 because approval gates were blocked, although tests,
generation and validation children returned 0. Do not reuse old release approvals
or interpret byte reproduction as adoption/submission approval.

## Expected result and return record

Official validation must exit 0: header `frame,label`, **199,319 data rows**, ordered
frames **0..199318**, no duplicates/gaps/blank labels, labels H/A/D/X. H/A mean live
home/away control; D means stopped play; X is abstention. The runner writes X outside
the two graded halves, UTF-8 with LF endings. Recorded counts are H 78,992 / A 72,741 /
D 6,614 / X 40,972; these are output fingerprints, not accuracy measures.
Merged verification passed **342 tests, no skips**, and the merged official validator
accepted the preserved selected CSV. No fresh full-match generation or public
evaluation was performed for this handoff.

Return source commit and dirty status; full command and configuration/report;
OS, Python and installed dependency versions; permitted input identifiers/hashes;
test and validator exit status/logs; candidate SHA-256; and every discrepancy.
Record your name/machine/date so independent reproduction is distinguishable from
the original agent's two runs. Keep licensed assets and candidate CSVs out of Git.

Likely setup issues: wrong Python launcher/patch version, unavailable pinned wheels
or package index, wrong bundle nesting, broadcast assets, or differing/truncated
input files. Compare versions and input hashes first. Missing metadata, invalid
units/counts or ordering must be fixed at acquisition/setup, not bypassed by padding,
trimming or editing labels. If hashes differ despite matching inputs/configuration,
retain both results and report the environment/source discrepancy; do not tune.
