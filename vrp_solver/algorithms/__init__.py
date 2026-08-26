"""Registry of improvement algorithms, keyed by the name used everywhere else
(CLI `--algorithm` flag, `Solver.solve(algorithm=...)`).

Every entry is a `run(initial_solution, cost_matrix, capacity, **kwargs) -> Solution`
callable. To add a new algorithm: implement it as a module here exposing a
`run` function with that signature, then add one line below.
"""

from . import adaptive_tabu_search, lns, local_search, penalty_tabu_search, rvns, tabu_search, vns

ALGORITHMS = {
    "local_search": local_search.run,
    "tabu": tabu_search.run,
    "adaptive_tabu": adaptive_tabu_search.run,
    "penalty_tabu": penalty_tabu_search.run,
    "vns": vns.run,
    "rvns": rvns.run,
    "lns": lns.run,
}

__all__ = ["ALGORITHMS"]
