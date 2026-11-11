# Apophis: classical chain, 204 kg / dry 140 kg

Study: 12 November 2026. Base repository revision before the correction:
`13d4839c`. The final entry adapter and regression test are copied under
`source/`; the commit containing this archive fixes their repository version.
The original ILTT Toolbox formulas and the KIAM wheel were not changed.

The authoritative staged run is `runs/apophis_classical_204/chain_july_final`:
01 July 2029, 204/140 kg, 0.036 N, exhaust velocity 11767.98 m/s,
bounded initial excess velocity 3000 m/s. Inputs contain no prescribed duration.
ILTT → IRT → departure → Pazov → physical PSI → free duration were run
individually, then the public `solve` entry independently reproduced the result
in `standard_solve`. Its independent audit is saved at the study root.

Accepted final result: 347.201040739 days, 36.451592453 kg xenon,
167.548407547 kg final mass. Independent physical replay and KIAM pass.
The 15 June 2029 chain also passes through physical PSI at 370.242713239 days
and 33.202368867 kg xenon; its later time optimization times out without
invalidating that parent. Other dated failures are retained explicitly.

`date_catalog.json` only lists phase-derived candidate inputs, not accepted
solutions. `*_bounded.json` and `*_extended.json` compare diagnostic local
correctors. The extended R formula was rejected and is not the production
fix. `chain_2029-07-01` and `chain_july_v2` are intermediate implementation
experiments; use `chain_july_final` for the final correction and figures.
`original_date_recheck.json` records the remaining failure of 14 February 2029.

All calculations, Python checks and figure generation ran in Linux Docker.
`study_summary.json` records the actual Docker image ID, versions, source hashes
and explicit physical assumptions. SHA256 in `manifest.json` covers every
archived file except the manifest itself. Figures preserve PNG/SVG originals
and inspected compact JPEG previews.

To reproduce the public path, from the repository root:

```text
docker compose run --rm pipeline solve configs/apophis_spd50m_204.json --output runs/apophis_204_new
```

To rerun the separate modules into a new directory:

```text
docker compose run --rm -e PYTHONPATH=/workspace --entrypoint python pipeline data/benchmarks/apophis_classical_204_v1/reproduce/apophis_classical_chain.py 2029-07-01T00:00:00 runs/apophis_204_stages_new
docker compose run --rm -e PYTHONPATH=/workspace --entrypoint python pipeline data/benchmarks/apophis_classical_204_v1/reproduce/apophis_chain_accept.py runs/apophis_204_stages_new
```

The dated diagnostic scripts write to their original `runs/apophis_classical_204`
paths. Use a clean checkout or change the output root before rerunning them;
do not overwrite an existing study. Archived JSON keeps original relative
artifact paths. To replay it with the provided plotting script, restore the
archived `runs/apophis_classical_204` tree only into an absent destination.

Scope: Sun-centered body-to-body rendezvous with constant nominal F/c.
No parking-orbit impulse, local capture, UMMP, global optimum or full-matrix
acceptance is claimed. Nominal engine source:
https://keldysh.ru/smallsat/news/2024/2412/suslov.pdf
