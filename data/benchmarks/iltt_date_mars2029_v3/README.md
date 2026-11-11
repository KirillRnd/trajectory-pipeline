# Date-first ILTT / Mars 2029

Run in Linux Docker from the repository root:

    docker compose run --rm -T pipeline search runs/mars2029_date_request.json --design configs/search_graph_date_v3.json --history data/benchmarks/search_matrix_v1/earth_mars_2029 --output runs/mars2029_date_graph_v3

The input JSON is in reproduction/. It has no prescribed duration. Copy it to the command path and use a fresh output folder when repeating.
The graph retains the actual request/source hashes and unmodified numerical records. The working tree at calculation time was based on 50550acc; date-first entry changes were present. After the run, cache/filter validation and error reporting were hardened without changing numerical formulas. The full final test log is retained.
All stored intermediate graph artifacts and IRT branch 0 were independently checked. Branch 1 failed independent IRT tolerance and is not a solution. No final physical PSI was accepted.
figures/sources.json binds plotted stages to their source paths and hashes; the initial ILTT approximation is deliberately not marked as an accepted endpoint. Internal runs/ paths are provenance, not relocated archive paths.
