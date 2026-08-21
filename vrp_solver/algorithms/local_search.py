"""Local Search: a VND-style steepest-descent improvement algorithm.

Each iteration evaluates all 6 move neighborhoods (see `vrp_solver.moves`),
applies the best move found, and tracks the best solution seen. With 20%
probability it applies the second-best move instead of the best one, as a
light diversification mechanism to avoid always taking the same descent path.
"""

import random

from ..moves import (
    InRouteReinsertMove,
    InRouteSwapMove,
    InRouteTwoOptMove,
    RelocationMove,
    SwapMove,
    TwoOptMove,
)

MAX_ITERATIONS = 100
SECOND_BEST_ACCEPTANCE_PROBABILITY = 0.2


class LocalSearch:
    def __init__(self, solution, cost_matrix, capacity):
        self.sol = solution
        self.cost_matrix = cost_matrix
        self.capacity = capacity

    def local_search(self, max_iterations=MAX_ITERATIONS):
        best_solution = self.sol

        search_methods = [
            self.cross_route_reinsert,
            self.cross_route_swap,
            self.two_opt,
            self.swap_within_route,
            self.two_opt_within_route,
            self.reinsert_within_route,
        ]

        for _ in range(max_iterations):
            best_move = None
            second_best_move = None

            for method in search_methods:
                move = method()

                if move:
                    if best_move is None or move.move_cost < best_move.move_cost:
                        second_best_move = best_move
                        best_move = move
                    elif second_best_move is None or move.move_cost < second_best_move.move_cost:
                        second_best_move = move

            if not best_move:
                break

            if second_best_move and random.random() < SECOND_BEST_ACCEPTANCE_PROBABILITY:
                second_best_move.apply()
            else:
                best_move.apply()

            self.sol.update_solution_cost()

            if self.sol.cost < best_solution.cost:
                best_solution = self.sol

        return best_solution

    def cross_route_reinsert(self):
        best_move = None

        for from_route in self.sol.routes:
            for to_route in self.sol.routes:
                if from_route == to_route:
                    continue

                for i in range(1, len(from_route.sequence_of_nodes)):
                    node = from_route.sequence_of_nodes[i]

                    for j in range(1, len(to_route.sequence_of_nodes)):
                        move = RelocationMove(node, from_route, to_route, i, j, self.capacity, self.cost_matrix)
                        if (best_move is None or move.move_cost < best_move.move_cost) and move.move_cost < 0 and move.is_feasible:
                            best_move = move

        return best_move

    def cross_route_swap(self):
        best_move = None

        for from_route in self.sol.routes:
            for to_route in self.sol.routes:
                if from_route == to_route:
                    continue

                for i in range(1, len(from_route.sequence_of_nodes)):
                    for j in range(1, len(to_route.sequence_of_nodes)):
                        move = SwapMove(from_route, to_route, i, j, self.cost_matrix, self.capacity)
                        if move.is_feasible and move.move_cost < 0 and (best_move is None or move.move_cost < best_move.move_cost):
                            best_move = move

        return best_move

    def two_opt(self):
        best_move = None

        for route1 in self.sol.routes:
            for route2 in self.sol.routes:
                for i in range(1, len(route1.sequence_of_nodes)):
                    for j in range(1, len(route2.sequence_of_nodes)):
                        if route1 == route2:
                            continue

                        move = TwoOptMove(route1, route2, i, j, self.cost_matrix, self.capacity)

                        if move.is_feasible and move.move_cost < -1e-6 and (best_move is None or move.move_cost < best_move.move_cost):
                            best_move = move

        return best_move

    def swap_within_route(self):
        best_move = None

        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):
                for j in range(i + 1, len(route.sequence_of_nodes) - 1):
                    move = InRouteSwapMove(route, i, j, self.cost_matrix)

                    if move.move_cost < -1e-6:
                        if best_move is None or move.move_cost < best_move.move_cost:
                            best_move = move

        return best_move

    def two_opt_within_route(self):
        best_move = None

        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):
                for j in range(i + 2, len(route.sequence_of_nodes) - 1):
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)

                    if move.move_cost < -1e-6:
                        if best_move is None or move.move_cost < best_move.move_cost:
                            best_move = move

        return best_move

    def reinsert_within_route(self):
        best_move = None

        for route in self.sol.routes:
            for from_index in range(1, len(route.sequence_of_nodes)):
                for to_index in range(1, len(route.sequence_of_nodes) - 1):
                    if from_index == to_index or abs(from_index - to_index) == 1:
                        continue

                    move = InRouteReinsertMove(route, from_index, to_index, self.cost_matrix, self.capacity)

                    if move.move_cost < -1e-6:
                        if best_move is None or move.move_cost < best_move.move_cost:
                            best_move = move

        return best_move


def run(initial_solution, cost_matrix, capacity, max_iterations=MAX_ITERATIONS, **_ignored):
    """Registry entry point: uniform `run(initial, cost_matrix, capacity, **kwargs)` signature."""
    return LocalSearch(initial_solution, cost_matrix, capacity).local_search(max_iterations=max_iterations)
