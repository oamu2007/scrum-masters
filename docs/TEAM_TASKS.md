Choose the module you want to work on as a team. The numbers identify modules, not assigned people.

## Module 1 - Decide which team looks in control

Use Module 3's player and ball positions to give Module 2 two scores per frame, one for Barcelona and one for Athletic. Once the pieces work together, provide the command that produces the match CSV.

**Start here.** On paper, put the ball at (10, 10) metres, a home player at (13, 14) and an away player at (10, 11). Their distances to the ball are 5 m and 1 m. Write a function that finds the shortest distance for each team. Then move the ball through a pass across several frames. A defender may be closest for an instant while the pass still reaches a home teammate. [Python's distance function](https://docs.python.org/3/library/math.html#math.dist)

**Repo:** [What counts as control](../CHALLENGE.md#possession-rules) · [Nearest-player baseline](../starter/baseline.py)

**Done when** swapping the teams swaps their scores, a missing ball gives neither team a proximity advantage, and the person working on Module 5 can run your command to write the CSV.

## Module 2 - Decide when possession changes

Turn Module 1's team scores and Module 4's stoppage evidence into a sequence of labels. Remember the last team in control during a pass or brief deflection. Switch when the other team gains control, or mark the ball dead when play stops.

**Start here.** Draw three circles on paper: home (`H`), away (`A`) and dead ball (`D`). Draw an arrow for each change you allow and write what would trigger it. Walk through an invented play: home passes, away deflects, away takes control, the referee stops play. Your labels should read `H H A D`. That diagram is enough to write the first version with a loop and a variable for the current state. [MDN's introduction to state machines](https://developer.mozilla.org/en-US/docs/Glossary/State_machine)

**Repo:** [Possession rules](../CHALLENGE.md#possession-rules) · [How whole possessions are scored](../EVALUATION.md) · [Half boundaries](../games.py)

**Done when** the invented play produces those four labels, a brief loss of sight during a home pass preserves `H`, and the second half starts fresh. Return one label per tactical frame, using `X` outside the graded halves.

## Module 3 - Give everyone the same tracking data

Build the reader that Modules 1 and 4 will use. For each tactical frame, return the players' teams, positions and speeds, plus the ball position when visible. Keep missing observations marked as missing.

**Start here.** Read one frame in the tracking notebook. A position of (0.5, 0.5) means midfield. On this pitch that's (52.65, 34) metres. For a separate visual check, pass the original (0.5, 0.5) into the supplied homography helper to find midfield in video pixels. [NumPy's beginner guide to arrays and indexing](https://numpy.org/doc/stable/user/absolute_beginners.html)

**Repo:** [Tracking walkthrough](../starter/02_tracking_atd.ipynb) · [Frame alignment](../starter/load_atd.py) · [Pitch-to-pixel helper](../starter/load_homography.py)

**Done when** tracking IDs 1 through 199,319 produce frame indices 0 through 199,318 in order, a missing ball stays missing, and the people working on Modules 1 and 4 can read the same frame without parsing the raw files themselves.

## Module 4 - Find stoppages and restarts

Give Module 2 evidence for when play stops and resumes. Combine the ball's position near a boundary, movement of nearby players and the automatic set-piece tags.

**Start here.** Sketch two plays: a pass disappears behind a player and play continues, or the ball goes over the touchline and play pauses for a throw-in. List which tracking clues distinguish them. Then open the tagging notebook and find the kickoff example. The tag covers several seconds around the restart. [IFAB's illustrated guide to when the ball is out of play](https://www.theifab.com/laws/latest/the-ball-in-and-out-of-play/)

**Repo:** [Smart Tagging walkthrough](../starter/01_smart_tagging.ipynb) · [Tag reader and kickoff timing check](../starter/load_smart_tagging.py)

**Done when** your invented pass can stay live through the missing observation, your throw-in supplies stoppage and restart evidence, and a tag with an unknown team leaves the restarting side unknown.

## Module 5 - Check the labels and reproduce the file

Write small checks for invented plays, then run Module 1's command independently and validate the resulting CSV.

**Start here.** Write down an expected sequence of `H H H H H`. Compare it with `H H A H H`. Only one frame differs, but the prediction splits one home possession into two and invents an away possession. Turn that example into a check. Then try the official validator on a known file: `python evaluation/validate_submission.py evaluation/results/baseline_smooth50.csv`. [Python's basic testing example](https://docs.python.org/3/library/unittest.html#basic-example)

**Repo:** [Scoring guide](../EVALUATION.md) · [CSV validator](../evaluation/validate_submission.py) · [Submission format](../SUBMISSION.md) · [Rules for using public labels](../RULES.md)

**Done when** your checks catch a one-frame indexing shift and a false possession change, the official validator accepts all 199,319 rows, and your independently generated CSV has the same file hash as Module 1's.



## Note: make and build on your own branches
