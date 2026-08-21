"""Variable Neighborhood Search (VNS).

Cycles through the 6 move neighborhoods in a fixed order, taking the best
move in the current neighborhood and restarting from the first neighborhood
whenever a move improves the solution (classic VNS "restart on improvement");
otherwise it advances to the next neighborhood. Move selection uses a
penalized objective (`evaluate_move_cost`) rather than raw move cost.
"""

import copy

from ..moves import (
    InRouteReinsertMove,
    InRouteSwapMove,
    InRouteTwoOptMove,
    RelocationMove,
    SwapMove,
    TwoOptMove,
)

PENALTY_FACTOR = 1000


class VNS:
    def __init__(self, initial_solution, cost_matrix, capacity):
        self.sol = copy.deepcopy(initial_solution)
        self.best_solution = copy.deepcopy(initial_solution)
        self.cost_matrix = cost_matrix
        self.capacity = capacity

        self.neighborhoods = [
            self.cross_route_reinsert,
            self.cross_route_swap,
            self.two_opt,
            self.swap_within_route,
            self.two_opt_within_route,
            self.reinsert_within_route,
        ]

    def search(self, max_iterations=1000, max_no_improvement=5):
        iteration = 0
        no_improvement = 0

        while iteration < max_iterations:
            neighborhood_index = 0

            while neighborhood_index < len(self.neighborhoods):
                neighbors = self.neighborhoods[neighborhood_index]()

                if not neighbors:
                    neighborhood_index += 1
                    continue

                best_candidate = min(neighbors, key=self.evaluate_move_cost)

                best_candidate.apply()
                self.sol.update_solution_cost()

                if self.sol.cost < self.best_solution.cost:
                    self.best_solution = copy.deepcopy(self.sol)
                    no_improvement = 0
                    neighborhood_index = 0
                else:
                    no_improvement += 1
                    neighborhood_index += 1

                if no_improvement >= max_no_improvement:
                    return self.best_solution

            iteration += 1

        return self.best_solution

    def evaluate_move_cost(self, move):
        """Penalized objective: move cost plus load-balance and capacity penalties."""
        base_cost = move.move_cost

        capacity_excess = max(0, sum(route.load for route in self.sol.routes) - self.capacity)
        load_difference = max(route.load for route in self.sol.routes) - min(route.load for route in self.sol.routes)
        compactness_penalty = sum(route.calculate_total_route_cost(self.cost_matrix) for route in self.sol.routes)

        return base_cost + PENALTY_FACTOR * (capacity_excess + load_difference + compactness_penalty)

    def cross_route_reinsert(self):
        moves = []
        for from_route in self.sol.routes:
            for to_route in self.sol.routes:
                if from_route == to_route:
                    continue

                for i in range(1, len(from_route.sequence_of_nodes)):
                    node = from_route.sequence_of_nodes[i]

                    for j in range(1, len(to_route.sequence_of_nodes)):
                        move = RelocationMove(node, from_route, to_route, i, j, self.capacity, self.cost_matrix)
                        if move.is_feasible:
                            moves.append(move)

        return moves

    def cross_route_swap(self):
        moves = []
        for from_route in self.sol.routes:
            for to_route in self.sol.routes:
                if from_route == to_route:
                    continue

                for i in range(1, len(from_route.sequence_of_nodes)):
                    for j in range(1, len(to_route.sequence_of_nodes)):
                        move = SwapMove(from_route, to_route, i, j, self.cost_matrix, self.capacity)
                        if move.is_feasible:
                            moves.append(move)

        return moves

    def two_opt(self):
        moves = []
        for route1 in self.sol.routes:
            for route2 in self.sol.routes:
                if route1 == route2:
                    continue

                for i in range(1, len(route1.sequence_of_nodes)):
                    for j in range(1, len(route2.sequence_of_nodes)):
                        move = TwoOptMove(route1, route2, i, j, self.cost_matrix, self.capacity)
                        if move.is_feasible:
                            moves.append(move)

        return moves

    def swap_within_route(self):
        moves = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):
                for j in range(i + 1, len(route.sequence_of_nodes) - 1):
                    moves.append(InRouteSwapMove(route, i, j, self.cost_matrix))

        return moves

    def two_opt_within_route(self):
        moves = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):
                for j in range(i + 2, len(route.sequence_of_nodes) - 1):
                    moves.append(InRouteTwoOptMove(route, i, j, self.cost_matrix))

        return moves

    def reinsert_within_route(self):
        moves = []
        for route in self.sol.routes:
            for from_index in range(1, len(route.sequence_of_nodes)):
                for to_index in range(1, len(route.sequence_of_nodes) - 1):
                    if from_index == to_index or abs(from_index - to_index) == 1:
                        continue

                    move = InRouteReinsertMove(route, from_index, to_index, self.cost_matrix, self.capacity)
                    if move.move_cost < -1e-6:
                        moves.append(move)

        return moves


def run(initial_solution, cost_matrix, capacity, max_iterations=1000, max_no_improvement=5, **_ignored):
    """Registry entry point: uniform `run(initial, cost_matrix, capacity, **kwargs)` signature."""
    vns = VNS(initial_solution=initial_solution, cost_matrix=cost_matrix, capacity=capacity)
    return vns.search(max_iterations=max_iterations, max_no_improvement=max_no_improvement)
