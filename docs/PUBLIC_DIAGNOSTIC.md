# Limited public diagnostic — November 17, 2026

This is one evaluation of one fixed investigation candidate against the supplied
public reference, solely to check pipeline correctness and describe observed
errors. No inference, labels, parameters, release gates or version selection were
changed. The results do not approve the candidate or establish full-match accuracy.

## Identity and provenance

All paths below are relative to this repository unless explicitly absolute.

| Item | Verified identity |
|---|---|
| Repository | `C:/Users/oamu2/more-than-a-hack-2027/data/integration-attempt` |
| Frozen inference source | `48d67bb271ce0dd50d0d6a1ce9dd24111a32fe78` |
| Checkout HEAD during diagnostic | `4a2695eb0fb5abd43c5c48376ec650a1d510752f` |
| Designated candidate | `data/release/runs/20261117T105211791158Z/candidate.csv` |
| Candidate bytes | 1,682,773 |
| Expected and observed SHA-256, before and after | `E533FCDDF4522A1E2F7CB2F12E15DEDD65C7C0E9508FBF9EDA3F1652E81D0C01` |
| Recorded generation evidence | Same run's `evidence.json`, SHA-256 `059E2999A990595031BA4F544FAFA42141E7CE085F437B93101D719BF897F4DC` |
| Recorded pipeline report | Same run's `pipeline.json`, SHA-256 `EE14974852B7E5273AE1803B1C2CA0EC83EE4BD09A32B704062A64809DF13344` |

Identity was verified **before scoring**. The generation manifest records a clean
`integration-attempt` source at the frozen SHA, integrated mode, successful
generation and official validation, 199,319 rows, and the same candidate hash.
Its pipeline-report hash was rechecked. All three recorded input byte lengths and
SHA-256 hashes were rechecked successfully: tactical ATD metadata, raw tactical
ATD and automatic Smart Tagging. Historical generation argv is retained in that
manifest; inference was not rerun for this diagnostic.

HEAD is a later diagnostic-record commit, not the candidate's inference source.
The intervening commits are:

- `def5fc8a43a9f4fa88891ab5e1b37b8e9f532f09`: status document and release-gate records.
- `4c9a23998b625ad3e9913d7e54fb52e456a30202`: debug handoff document.
- `4a2695eb0fb5abd43c5c48376ec650a1d510752f`: status/handoff documents and startup tests.

The complete source-to-HEAD path diff contains only those documents,
`release_gates.json` and `tests/test_startup_diagnosis.py`. Inference, `games.py`
and evaluation files have no differences from the frozen source. Initial tracked
worktree/index status was clean. The official scorer, metrics, validator and
public reference also match the supplied parent checkout. Applicable ancestor
and affected-directory `AGENTS.md` checks found none. Read `RULES.md`,
`EVALUATION.md`, `SUBMISSION.md` and the current `docs/INTEGRATION_STATUS.md`;
consulted local DATA/FAQ and implementation contracts for timing/label semantics.

These checks establish consistency with the recorded generation provenance.
They are not independent reproduction of the candidate from inputs.

## Commands and environment

Executed locally November 17, 2026, approximately 08:09 America/Tijuana
(manifest start `2026-11-17T16:09:41.110764+00:00`). Windows 11
`Windows-11-10.0.26300-SP0`, PowerShell 7.6.9, existing project-local Python
3.12.10 (64-bit AMD64), NumPy 2.5.4, pandas 3.1.1, python-dateutil 4.0.0 and
tzdata 2026.6. No dependencies were installed or changed.

Working directory was the repository above. The executed wrapper command was:

```powershell
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& data/release-env/Scripts/python.exe -B data/public-diagnostic-20261117/run_diagnostic.py
```

The wrapper checked identity/provenance and frame coverage, made a byte-identical
copy in a new directory, then invoked these official commands exactly once each
(absolute paths in the execution manifest; equivalent relative spelling here):

```powershell
$python = (Resolve-Path data/release-env/Scripts/python.exe).Path
& $python -B evaluation/validate_submission.py data/release/runs/20261117T105211791158Z/candidate.csv
& $python -B evaluation/run_evaluation.py --gt public --results data/public-diagnostic-20261117/results --out data/public-diagnostic-20261117/official --bootstrap 1000
```

Wrapper, validator and evaluator all exited **0**. `git check-ignore` confirmed
the diagnostic location is ignored. The evaluator's input directory `results/`
contained **only `candidate.csv`**; no baseline or alternate candidate was scored.
Outputs are isolated under `data/public-diagnostic-20261117/`:

- `run_diagnostic.py`, `manifest.json`: checks, exact argv/statuses, environment,
  coverage, official-file hashes and before/after preservation inventory.
- `validator.log`, `evaluation.log`: complete official console output.
- `official/scoreboard.csv`, `official/reports/candidate.json` and
  `official/reports/candidate_transitions.csv`: official artifacts.

The wrapper refuses to rerun into an existing results directory. This report
was prepared from that single evaluation; no further scoring or configuration
comparison was performed. The designated candidate, all six files in its
historical run directory, release gates and integration status matched their
before/after hashes. The scored copy also retained the expected candidate hash.

## Mechanical alignment and label interpretation

Official validation passed: exactly **199,319** rows, integer frames
**0..199318**, ordered, contiguous and duplicate-free, with legal nonblank labels.
The actual header is `frame,label`. Candidate and reference frame columns are
identical. The supplied public CSV itself passed the same frame/label checks.
Its only non-X run is **[11185, 18685)**, or frames **11185..18684** inclusive:
7,500 frames at 25 fps, exactly five minutes, matching public metadata. Every
public frame is covered by the candidate, including its explicit abstentions.

The frozen reader maps sequential one-based tactical ATD record IDs to zero-based
video rows (`record - 1`). The runner requires each observation's index to equal
its array position; the writer enumerates the decoded labels without adding a
time offset. The recorded native half blocks match the published video blocks.
No broadcast indexing, additional native-ID offset or CSV row shift was found.
This checks the transport/index contract; it does not establish that inferred
football events occur at the correct instant.

`H` is home/Barcelona possession with the ball alive; `A` is away/Athletic
possession with the ball alive; `D` is dead ball; predicted `X` is abstention.
The supplied EPTS metadata lists Barcelona first and `Atletic Club` second.
The reader maps those team IDs to H/A, M1 maps H/A to home/away scores, and M2
maps those scores back to H/A. No H/A swap was demonstrated. This inspection
does not prove each inferred team decision is correct.

Reference `X` means **ungraded**, including all frames outside this public window;
it is not a dead-ball label. Raw predicted X is a miss for macroF1. The official
temporal metrics forward-fill X, back-filling at a graded run's head, within
reference non-X runs. Here there is one such run. D stretches are excluded from
possession spells. SpellF1 averages same-team, one-to-one temporal-IoU matching
F1 at 0.3/0.4/0.5/0.6/0.7. No label remapping, shift trial or repair was used.

**No mechanical alignment or label-code interpretation defect was demonstrated.**
Passing these checks is not proof that the entire implementation is defect-free.

## Public-window results

Values are rounded here; the official JSON retains full precision.

| Measure | Result |
|---|---:|
| Graded frames / true segments / true possessions | 7,500 / 21 / 17 |
| Candidate abstentions on graded frames | 11 (0.1467%) |
| macroF1 | **0.477438** |
| spellF1, mean over the five official IoUs | **0.257627** |
| macroF1 bootstrap 5th–95th percentiles | 0.375769–0.523049 |
| spellF1 bootstrap 5th–95th percentiles | 0.189831–0.332203 |
| Predicted / true possessions | **42 / 17** (difference +25) |
| Predicted / true mean possession duration | 7.121 s / 14.191 s |
| Predicted / true segments; fragmentation | 43 / 21; 2.047619 |

Per-class metrics use only graded reference frames and raw predictions:

| Class | Precision | Recall | F1 | True support | Raw predicted frames |
|---|---:|---:|---:|---:|---:|
| H | 0.597317 | 0.837869 | 0.697433 | 3,454 | 4,845 |
| A | 0.727204 | 0.742724 | 0.734882 | 2,577 | 2,632 |
| D | 0.000000 | 0.000000 | 0.000000 | 1,469 | 12 |
| X | — | — | — | 0 | 11 |

Official confusion matrix, **rows = reference, columns = raw prediction**:

| Reference / predicted | H | A | D | X |
|---|---:|---:|---:|---:|
| H | 2,894 | 560 | 0 | 0 |
| A | 640 | 1,914 | 12 | 11 |
| D | 1,311 | 158 | 0 | 0 |
| X — ungraded, outside public window | 76,123 | 71,618 | 3,505 | 40,573 |

Only the first three rows contribute to graded frame metrics. The last row is
included because the official report emits the full-length matrix; it supplies
**no correctness evidence outside the public window**. The validator's full-file
709-possession count uses X as gaps and is not the public evaluator's 42-spell
count; no full-match truth count is available or inferred here.

Official public-window transition diagnostics (after X filling): 20 true and
42 predicted transitions. Matching uses the official default destination-label
typing and one-to-one assignment.

| Tolerance | Precision | Recall | F1 | Matched | Missed | Spurious |
|---|---:|---:|---:|---:|---:|---:|
| ±12 frames (0.48 s) | 0.071429 | 0.150000 | 0.096774 | 3 | 17 | 39 |
| ±25 frames (1.00 s) | 0.119048 | 0.250000 | 0.161290 | 5 | 15 | 37 |

For the five matches at ±25 frames: mean signed latency **+7.2 frames**
(+0.288 s), median **−1 frame** (−0.04 s), mean absolute latency **9.2 frames**
(0.368 s), and 90th-percentile absolute latency **21 frames** (0.84 s).
Reported ambiguous matches: **0**. These latencies describe the small matched
subset; they do not estimate a global offset or justify shifting predictions.

SpellF1 at IoU 0.3/0.4/0.5/0.6/0.7 is respectively
0.508475 / 0.372881 / 0.203390 / 0.135593 / 0.067797. At IoU 0.5 there are
6 matched, 11 missed and 36 spurious possessions (precision 0.142857,
recall 0.352941).

The optional bootstrap was included in this same invocation: 1,000 draws,
official seed 0, 5th–95th percentiles. MacroF1 resamples the 21 true segments;
spellF1 resamples matched flags over the 17 true possessions, with the predicted
count fixed. These are uncertainty summaries conditional on this tiny window
and the official resampling procedure, not full-match confidence bounds.
Frames are correlated; 7,500 frames are not 7,500 independent observations.
Small score differences should not be treated as meaningful, and no comparison
or configuration decision was made.

## What the numerical observations establish

On this window the candidate missed **all 1,469 reference dead-ball frames**:
1,311 were predicted H and 158 A. Its 12 predicted D frames occur on reference A.
It also overcounts possession spells and exhibits substantial fragmentation and
transition disagreement. These are observed performance failures against the
supplied public labels, not evidence of a newly proven indexing, serialization,
H/A mapping or decoder implementation bug. The numbers alone do not identify
which feature, policy or missing observation caused each error. No parameter
recommendation or frame-specific prediction exception follows from this report.

## Separate, already documented startup diagnostics

This section summarizes existing `docs/INTEGRATION_STATUS.md` evidence; it is not
another evaluation and no startup probe was rerun here.

**Second half:** the FAQ's graded pre-kickoff interval is
**110808..113741**, with kickoff at 113742. This interval is wholly outside the
public five-minute reference. The designated candidate has D 2,864 / A 54 / H 1 /
X 15 there: **70 non-D frames**, with D exited at frame 113672, 70 frames
(2.8 s) before the published kickoff. Prior actual-pipeline tracing established
that the ball-only restart path B supplies the confirmation; collective path A
does not. The approximate automatic kickoff phase plus observed movement meets
the implemented heuristic without establishing authorized live play. This is a
documented semantic false start, not a demonstrated transport/indexing failure.
The one-frame difference between the `games.py` clock anchor (113741) and FAQ
kickoff (113742) is already documented; the separate FAQ diagnostic uses 113742,
and that diagnostic constant is not used by inference.

**First half:** grading starts at kickoff, frame 11185. Existing tracing records
12 D frames, then 11 X, with the first H/A label at offset 23. The first 125
frames are D 12 / X 11 / A 50 / H 52. The D prefix comprises two initially
missing samples, two to build a motion baseline, one more to meet displacement,
five sustained-motion frames, then two additional confirmation frames. The
following 11 X arise from separate ownership acquisition. No retrospective
labeling is implemented. These are observed/computed pipeline latencies, not
validated event-time estimates. This prefix overlaps the public window and is
visible in its confusion counts; its causal timing breakdown comes from the
earlier startup investigation, not from the aggregate public scorer.

The existing investigation concludes that initial-D/context assumptions and
ball-only restart evidence cannot reliably distinguish preparatory movement from
authorized play. It did not establish a defensible prediction correction or a
new M2 implementation defect. Passing failure-characterization tests does not
clear those known semantic problems. No earlier candidate was evaluated or
compared in this diagnostic, and no version was selected.

## Limits and plain-language assessment

The reference contains only **7,500 graded frames and 17 possessions** from one
short interval. There is no full-match ground truth available to this diagnostic,
and no independent candidate reproduction yet. Recorded same-machine repeatability
is different from independent reproduction. No online possession estimates,
event data, corrected tracking, human annotations or other external game evidence
were searched for or used. No human labels were created or repaired.

The file is mechanically scoreable, but this public sample exposes missed dead
balls and broken-up possessions. It does not establish full-match accuracy or
which implementation change would solve those errors. Known kickoff/startup
failures remain unresolved. Format validation, any previously documented kickoff
improvement and a public score do not constitute submission approval. The
candidate remains byte-for-byte preserved; no release gate, push, merge,
submission or approval was performed.
