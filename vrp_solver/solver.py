"""Orchestrates construction + a pluggable improvement algorithm/pipeline."""

from .algorithms import ALGORITHMS
from .construction import ClarkeWrightConstructor
from .pipeline import Pipeline


class Solver:
    def __init__(self, model):
        self.all_nodes = model.all_nodes
        self.customers = model.customers
        self.depot = model.all_nodes[0]
        self.cost_matrix = model.dist_matrix
        self.capacity = model.capacity
        self.sol = None

    def solve(self, algorithm="local_search", num_iterations=1, **algorithm_kwargs):
        """Build an initial solution with Clarke-Wright savings, then improve it.

        `algorithm` is one of:
          - a registered name (str, see `vrp_solver.algorithms.ALGORITHMS`) —
            `algorithm_kwargs` are forwarded to it, e.g. `tabu_tenure=20`.
          - a `Pipeline`, or a plain list of stages (wrapped in a `Pipeline`
            for you) — algorithms chained in sequence, each refining the
            previous stage's solution. Per-stage kwargs go on each `Stage`,
            not on this call, so `algorithm_kwargs` must be empty here.
          - any `run(solution, cost_matrix, capacity, **kwargs) -> Solution`
            callable that isn't registered.

        Repeats `num_iterations` times (each with a fresh, independently
        randomized construction) and keeps the best result.
        """
        run = self._resolve(algorithm, algorithm_kwargs)
        best_sol = None

        for _ in range(num_iterations):
            constructor = ClarkeWrightConstructor(self.depot, self.cost_matrix, self.capacity, self.customers)
            initial_solution = constructor.build()

            if isinstance(run, Pipeline):
                candidate = run(initial_solution, self.cost_matrix, self.capacity)
            else:
                candidate = run(initial_solution, self.cost_matrix, self.capacity, **algorithm_kwargs)

            if best_sol is None or candidate.cost < best_sol.cost:
                best_sol = candidate

        self.sol = best_sol
        return self.sol

    @staticmethod
    def _resolve(algorithm, algorithm_kwargs):
        if isinstance(algorithm, str):
            if algorithm not in ALGORITHMS:
                available = ", ".join(sorted(ALGORITHMS))
                raise ValueError(f"Unknown algorithm {algorithm!r}. Available: {available}")
            return ALGORITHMS[algorithm]

        if isinstance(algorithm, (list, tuple)):
            algorithm = Pipeline(algorithm)

        if isinstance(algorithm, Pipeline) and algorithm_kwargs:
            raise ValueError(
                "algorithm_kwargs aren't supported with a Pipeline/list of stages "
                "(ambiguous which stage they'd apply to) -- put kwargs on the "
                "individual Stage(...) instead."
            )

        return algorithm
