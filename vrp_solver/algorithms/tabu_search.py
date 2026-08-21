"""Tabu Search: descent with a short-term memory of recently-touched nodes/arcs.

Forbids moves that touch recently-changed nodes or arcs (unless the move
would beat the best known solution — the aspiration criterion), adapts the
tabu tenure based on search progress, and randomly perturbs the solution
after a run of iterations without improvement.
"""

import copy
import random

from ..moves import (
    InRouteReinsertMove,
    InRouteSwapMove,
    InRouteTwoOptMove,
    RelocationMove,
    SwapMove,
    TwoOptMove,
)


class TabuSearch:
    def __init__(self, initial_solution, cost_matrix, capacity, tabu_tenure=30, max_iterations=1000, max_no_improvement=15):
        self.sol = copy.deepcopy(initial_solution)
        self.best_solution = copy.deepcopy(initial_solution)
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.tabu_tenure = tabu_tenure
        self.tabu_arcs = set()
        self.tabu_nodes = set()
        self.max_iterations = max_iterations
        self.max_no_improvement = max_no_improvement
        self.iteration_since_last_improvement = 0

    def generate_neighbors(self):
        return (
            self.cross_route_reinsert() +
            self.cross_route_swap() +
            self.two_opt() +
            self.two_opt_within_route() +
            self.swap_within_route() +
            self.reinsert_within_route()
        )

    def search(self):
        iteration = 0
        no_improvement = 0

        while iteration < self.max_iterations:
            neighbors = self.generate_neighbors()

            if not neighbors:
                break

            best_candidate = None
            for move in neighbors:
                if not self.is_tabu(move) or self.aspiration_criterion(move):
                    best_candidate = move

            if not best_candidate:
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

            if no_improvement >= self.max_no_improvement:
                self.diversify_search()
                no_improvement = 0

            iteration += 1

        return self.best_solution

    def is_tabu(self, move):
        for arc in move.affected_arcs:
            if arc in self.tabu_arcs:
                return True

        for node in move.affected_nodes:
            if node in self.tabu_nodes:
                return True

        return False

    def aspiration_criterion(self, move):
        return move.move_cost + self.sol.cost < self.best_solution.cost

    def update_tabu_nodes(self, nodes):
        self.tabu_nodes.update(nodes)
        while len(self.tabu_nodes) > self.tabu_tenure:
            self.tabu_nodes.pop()

    def update_tabu_arcs(self, arcs):
        self.tabu_arcs.update(arcs)
        while len(self.tabu_arcs) > self.tabu_tenure:
            self.tabu_arcs.pop()

    def adjust_tabu_tenure(self):
        if self.iteration_since_last_improvement > self.max_no_improvement:
            self.tabu_tenure = min(len(self.sol.routes) * 2, self.tabu_tenure + 1)
        else:
            self.tabu_tenure = max(5, self.tabu_tenure - 1)

    def diversify_search(self):
        for _ in range(3):
            random_route = random.choice(self.sol.routes)
            if len(random_route.sequence_of_nodes) > 3:
                i, j = random.sample(range(1, len(random_route.sequence_of_nodes) - 1), 2)
                random_route.sequence_of_nodes[i], random_route.sequence_of_nodes[j] = random_route.sequence_of_nodes[j], random_route.sequence_of_nodes[i]

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
                        if move.is_feasible and move.move_cost < 0:
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
                        if move.is_feasible and move.move_cost < 0:
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
                        if move.is_feasible and move.move_cost < 0:
                            moves.append(move)

        return moves

    def swap_within_route(self):
        moves = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes)):
                for j in range(i + 1, len(route.sequence_of_nodes)):
                    move = InRouteSwapMove(route, i, j, self.cost_matrix)
                    if move.move_cost < 0:
                        moves.append(move)

        return moves

    def two_opt_within_route(self):
        moves = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes)):
                for j in range(i + 2, len(route.sequence_of_nodes)):
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)
                    if move.move_cost < 0:
                        moves.append(move)

        return moves

    def reinsert_within_route(self):
        moves = []
        for route in self.sol.routes:
            for from_index in range(1, len(route.sequence_of_nodes)):
                for to_index in range(1, len(route.sequence_of_nodes)):
                    if from_index == to_index or abs(from_index - to_index) == 1:
                        continue

                    move = InRouteReinsertMove(route, from_index, to_index, self.cost_matrix, self.capacity)
                    if move.move_cost < 0:
                        moves.append(move)

        return moves


def run(initial_solution, cost_matrix, capacity, tabu_tenure=30, max_iterations=1000, max_no_improvement=15, **_ignored):
    """Registry entry point: uniform `run(initial, cost_matrix, capacity, **kwargs)` signature."""
    search = TabuSearch(
        initial_solution=initial_solution,
        cost_matrix=cost_matrix,
        capacity=capacity,
        tabu_tenure=tabu_tenure,
        max_iterations=max_iterations,
        max_no_improvement=max_no_improvement,
    )
    return search.search()
