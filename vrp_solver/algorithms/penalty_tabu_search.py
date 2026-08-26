"""Tabu Search with Guided-Local-Search-style penalized move selection.

Reuses `TabuSearch`'s neighborhood generation and tabu bookkeeping, but
changes move *selection*: instead of taking the first admissible candidate
in list order, it evaluates every admissible (non-tabu, or aspirational)
move by a penalized cost that adds a decaying per-arc usage penalty on top
of the raw move cost, and takes the best one. Arcs that keep reappearing in
the solution accumulate penalty and become progressively less attractive to
reuse even while still technically allowed, which pushes the search into
new territory without forbidding anything outright.
"""

import copy

from .tabu_search import TabuSearch


class PenaltyTabuSearch(TabuSearch):
    def __init__(
        self,
        initial_solution,
        cost_matrix,
        capacity,
        tabu_tenure=30,
        max_iterations=1000,
        max_no_improvement=15,
        lambda_factor=0.3,
        penalty_decay=0.9,
        penalty_update_every=10,
    ):
        super().__init__(initial_solution, cost_matrix, capacity, tabu_tenure, max_iterations, max_no_improvement)
        self.lambda_factor = lambda_factor
        self.penalty_decay = penalty_decay
        self.penalty_update_every = penalty_update_every
        self.arc_penalties = {}

    def search(self):
        iteration = 0
        no_improvement = 0

        while iteration < self.max_iterations:
            neighbors = self.generate_neighbors()
            if not neighbors:
                break

            best_candidate = None
            best_penalized_cost = float("inf")
            for move in neighbors:
                if self.is_tabu(move) and not self.aspiration_criterion(move):
                    continue
                penalized_cost = move.move_cost + self.lambda_factor * sum(
                    self.arc_penalties.get(arc, 0.0) for arc in move.affected_arcs
                )
                if penalized_cost < best_penalized_cost:
                    best_candidate = move
                    best_penalized_cost = penalized_cost

            if best_candidate is None:
                break

            best_candidate.apply()
            self.sol.update_solution_cost()

            if self.sol.cost < self.best_solution.cost:
                self.best_solution = copy.deepcopy(self.sol)
                no_improvement = 0
                self.iteration_since_last_improvement = 0
            else:
                no_improvement += 1
                self.iteration_since_last_improvement += 1

            self.update_tabu_arcs(best_candidate.affected_arcs)
            self.update_tabu_nodes(best_candidate.affected_nodes)
            self.adjust_tabu_tenure()

            if iteration % self.penalty_update_every == 0:
                self._update_arc_penalties()

            if no_improvement >= self.max_no_improvement:
                self.diversify_search()
                no_improvement = 0

            iteration += 1

        return self.best_solution

    def _update_arc_penalties(self):
        for route in self.sol.routes:
            nodes = route.sequence_of_nodes
            for i in range(len(nodes) - 1):
                arc = (nodes[i].id, nodes[i + 1].id)
                self.arc_penalties[arc] = self.arc_penalties.get(arc, 0.0) + 1

        for arc in list(self.arc_penalties.keys()):
            self.arc_penalties[arc] *= self.penalty_decay
            if self.arc_penalties[arc] < 1e-3:
                del self.arc_penalties[arc]


def run(
    initial_solution,
    cost_matrix,
    capacity,
    tabu_tenure=30,
    max_iterations=1000,
    max_no_improvement=15,
    lambda_factor=0.3,
    penalty_decay=0.9,
    penalty_update_every=10,
    **_ignored,
):
    """Registry entry point: uniform `run(initial, cost_matrix, capacity, **kwargs)` signature."""
    search = PenaltyTabuSearch(
        initial_solution=initial_solution,
        cost_matrix=cost_matrix,
        capacity=capacity,
        tabu_tenure=tabu_tenure,
        max_iterations=max_iterations,
        max_no_improvement=max_no_improvement,
        lambda_factor=lambda_factor,
        penalty_decay=penalty_decay,
        penalty_update_every=penalty_update_every,
    )
    return search.search()
