# Intermediate-time search validation

`standard/`: all five previous failures, 4 individuals x 2 generations, time upper 1.5T.
`extended/`: additional uniform probe, both engines at 1.2T seed and upper 2T, unchanged original launch dates.
`controls/time/`: real Mars-2028 intermediate duration release followed by independently accepted physical PSI.
`controls/joint/`: real Mars-2028 verified bridge with beta=0.7 and force 1.2 times hardware, followed by joint mass/force continuation and exact physical PSI.

Standard/extended numerical implementation: commit 69460613. Budget control: commit 50281651; all five remain partial at mass_and_thrust after uniform 180-second continuation budgets. Parent selection minimizes abs(log(force ratio)) + 1-beta; only solver budgets change. Inputs, design, image ID, code hashes and original provenance paths are retained.
Every graph artifact is included. Unselected duration trial arrays, earlier continuation arrays and plots remain in original runs.
Original paths inside JSON are provenance, not relocated links. Load archived trajectories from their actual archive folders.
For graph-aware history ingestion, pass an individual case folder containing graph.json, not this collection root.
Intermediate checkpoints are available to the Python API; graph history currently imports physical PSI references only.
