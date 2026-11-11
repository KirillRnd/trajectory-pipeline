# Fresh date-first ILTT audit

Source for the numerical matrix: e113b305 (module hashes and Docker image ID
are saved per search). All 15 original cases have tof_days=null on input.
Historical physical references are absent. The Moon is excluded.

`snapshot/runs/` preserves original relative paths, intermediate arrays,
requests, graph edges, continuation histories and checks. Derived plot files
are omitted; they can be rendered from the saved arrays. No numerical endpoint
is replaced by a plot or a controller success flag.

The primary and supplementary studies are separate. The latter only covers
up to two viable, unvisited date/branch inputs per case without an accepted
primary solution; its protocol and selection are saved explicitly.

The January Mars standard-solve control is additional to the 15 cases. The
sweep control intentionally gives the fast route a tiny budget to exercise
standard fallback; its partial physical outcome is not a successful solution.

For read-only replay, load any saved trajectory.json/trajectory.npz pair with
Trajectory.load and the corresponding independent verifier in Linux Docker.
To reuse original graph paths in a clean clone, copy snapshot/runs/* into the
empty repository runs/ directory before running the report. Do not overwrite
an existing study. To recalculate instead, use reproduce/run_fresh_iltt_matrix_v4.py
with a new output directory; the script refuses an existing output directory.

The optional download/refinement scripts describe preparation of the frozen
2020–2080 ephemerides. The actual verified tables and raw Horizons responses
are versioned in data/ephemerides; no network is needed to run the matrix.
Interpolation probes are not a bound on orbital prediction uncertainty.
