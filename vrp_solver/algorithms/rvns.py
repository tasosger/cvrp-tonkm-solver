"""Randomized/Reactive VNS (RVNS).

Like `vns.VNS`, but picks which neighborhood to explore next by sampled
priority (neighborhoods that recently produced improvements get sampled
more often) instead of a fixed cycle, and only evaluates a random subsample
of each neighborhood's moves for speed.
"""

import copy
import random

from ..moves import (
    InRouteSwapMove,
    InRouteTwoOptMove,
    RelocationMove,
    SwapMove,
    TwoOptMove,
)


class RVNS:
    def __init__(self, initial_solution, cost_matrix, capacity):
        self.sol = copy.deepcopy(initial_solution)
        self.best_solution = copy.deepcopy(initial_solution)
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.current_iteration = 0

        self.neighborhoods = [
            self.cross_route_reinsert,
            self.cross_route_swap,
            self.two_opt,
            self.swap_within_route,
            self.two_opt_within_route,
        ]

    def search(self, max_iterations=1000, max_no_improvement=10, sample_size=10):
        no_improvement = 0
        neighborhood_priorities = [1] * len(self.neighborhoods)

        for self.current_iteration in range(max_iterations):
            neighborhood_index = self.select_neighborhood(neighborhood_priorities)

            neighbors = self.neighborhoods[neighborhood_index]()

            if not neighbors:
                neighborhood_priorities[neighborhood_index] = max(1, neighborhood_priorities[neighborhood_index] - 1)
                continue

            sampled_neighbors = random.sample(neighbors, min(len(neighbors), sample_size))

            best_candidate = min(sampled_neighbors, key=self.evaluate_move_cost)

            best_candidate.apply()
            self.sol.update_solution_cost()

            if self.sol.cost < self.best_solution.cost:
                self.best_solution = copy.deepcopy(self.sol)
                no_improvement = 0
                neighborhood_priorities[neighborhood_index] += 1
            else:
                no_improvement += 1
                neighborhood_priorities[neighborhood_index] = max(1, neighborhood_priorities[neighborhood_index] - 1)

            if no_improvement >= max_no_improvement:
                break

        return self.best_solution

    def select_neighborhood(self, priorities):
        total_priority = sum(priorities)
        probabilities = [priority / total_priority for priority in priorities]
        return random.choices(range(len(self.neighborhoods)), weights=probabilities, k=1)[0]

    def evaluate_move_cost(self, move):
        """Penalized objective with a penalty weight that grows over the search."""
        base_cost = move.move_cost

        total_load = sum(route.load for route in self.sol.routes)
        capacity_excess = max(0, total_load - self.capacity)

        max_load = max(route.load for route in self.sol.routes)
        min_load = min(route.load for route in self.sol.routes)
        load_difference = max_load - min_load

        total_compactness = sum(route.calculate_total_route_cost(self.cost_matrix) for route in self.sol.routes)

        penalty_factor = max(1, self.current_iteration // 10)
        return base_cost + penalty_factor * (capacity_excess + load_difference + total_compactness)

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
                    move = InRouteSwapMove(route, i, j, self.cost_matrix)
                    moves.append(move)

        return moves

    def two_opt_within_route(self):
        moves = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):
                for j in range(i + 2, len(route.sequence_of_nodes) - 1):
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)
                    moves.append(move)

        return moves


def run(initial_solution, cost_matrix, capacity, max_iterations=1000, max_no_improvement=10, sample_size=10, **_ignored):
    """Registry entry point: uniform `run(initial, cost_matrix, capacity, **kwargs)` signature."""
    rvns = RVNS(initial_solution=initial_solution, cost_matrix=cost_matrix, capacity=capacity)
    return rvns.search(max_iterations=max_iterations, max_no_improvement=max_no_improvement, sample_size=sample_size)
