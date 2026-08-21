"""Orchestrates construction + a pluggable improvement algorithm."""

from .algorithms import ALGORITHMS
from .construction import ClarkeWrightConstructor


class Solver:
    def __init__(self, model):
        self.all_nodes = model.all_nodes
        self.customers = model.customers
        self.depot = model.all_nodes[0]
        self.cost_matrix = model.dist_matrix
        self.capacity = model.capacity
        self.sol = None

    def solve(self, algorithm="local_search", num_iterations=1, **algorithm_kwargs):
        """Build an initial solution with Clarke-Wright savings, then improve it
        with the named algorithm (see `vrp_solver.algorithms.ALGORITHMS` for the
        available names). Repeats `num_iterations` times (each with a fresh,
        independently randomized construction) and keeps the best result.
        """
        if algorithm not in ALGORITHMS:
            available = ", ".join(sorted(ALGORITHMS))
            raise ValueError(f"Unknown algorithm {algorithm!r}. Available: {available}")

        run = ALGORITHMS[algorithm]
        best_sol = None

        for _ in range(num_iterations):
            constructor = ClarkeWrightConstructor(self.depot, self.cost_matrix, self.capacity, self.customers)
            initial_solution = constructor.build()

            candidate = run(initial_solution, self.cost_matrix, self.capacity, **algorithm_kwargs)

            if best_sol is None or candidate.cost < best_sol.cost:
                best_sol = candidate

        self.sol = best_sol
        return self.sol
