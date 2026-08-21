"""Adaptive (reactive) Tabu Search.

A more elaborate Tabu Search that learns per-operator success weights (an
operator that has recently produced improving moves is sampled more often),
keeps a short memory of "good but unchosen" moves to revisit, and falls back
to the plain `TabuSearch` once it has gone `switch_depth` iterations without
improving.

Historical note: this module used to be named `mcts.py` and its class was
also called `TabuSearch`, which silently shadowed the real `TabuSearch`
import in the old `Solver` (see the `algorithms/tabu_search.py` docstring).
It isn't Monte Carlo Tree Search — renamed here to `AdaptiveTabuSearch` and
given its own registry entry so both are actually reachable.
"""

import copy
import random
from collections import Counter, deque

import numpy as np

from ..moves import (
    InRouteReinsertMove,
    InRouteSwapMove,
    InRouteTwoOptMove,
    RelocationMove,
    SwapMove,
    TwoOptMove,
)
from .tabu_search import TabuSearch as SimpleTabuSearch


class AdaptiveTabuSearch:
    def __init__(self, initial_solution, cost_matrix, capacity, tabu_tenure=30, max_iterations=100, max_no_improvement=30, switch_depth=20):
        self.sol = copy.deepcopy(initial_solution)
        self.best_solution = copy.deepcopy(initial_solution)
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.tabu_tenure = tabu_tenure
        self.tabu_arcs = deque(maxlen=tabu_tenure)
        self.tabu_nodes = deque(maxlen=tabu_tenure)
        self.max_iterations = max_iterations
        self.max_no_improvement = max_no_improvement
        self.iteration_since_last_improvement = 0
        self.switch_depth = switch_depth  # depth threshold to switch to plain Tabu Search

        # Adaptive operator weights, learned from move success rate.
        self.operator_weights = {
            'cross_route_reinsert': 1.0,
            'cross_route_swap': 1.0,
            'two_opt': 1.0,
            'two_opt_within_route': 1.0,
            'swap_within_route': 1.0,
            'reinsert_within_route': 1.0,
        }
        self.operator_success = Counter()
        self.operator_usage = Counter()

        # Solution management
        self.good_solutions = []
        self.solution_features = set()
        self.unchosen_good_moves = []

        self.learning_rate = 0.1
        self.min_weight = 0.1
        self.max_weight = 5.0

    def search(self):
        """Adaptive tabu search with depth-based fallback."""
        iteration = 0
        no_improvement = 0
        best_cost = float('inf')

        while iteration < self.max_iterations:
            if self.iteration_since_last_improvement >= self.switch_depth:
                return self.simple_tabu_search()

            neighbors = self.generate_neighbors()
            replayed = False

            if not neighbors and self.unchosen_good_moves:
                neighbors = [self.unchosen_good_moves.pop(0)]
                replayed = True

            if not neighbors:
                self.diversify_search()
                neighbors = self.generate_neighbors()
                if not neighbors:
                    break

            best_move = self.probabilistic_selection(neighbors)
            if not best_move:
                continue

            if replayed:
                # A move popped from `unchosen_good_moves` was generated
                # against a route that may have been mutated by other moves
                # since; only apply it if it's still valid and capacity-feasible.
                if not self._apply_move_safely(best_move):
                    iteration += 1
                    continue
            else:
                best_move.apply()
            self.sol.update_solution_cost()

            move_improved = self.sol.cost < best_cost
            self.update_operator_weights(best_move.operator, move_improved)

            if self.sol.cost < self.best_solution.cost:
                self.best_solution = copy.deepcopy(self.sol)
                self.good_solutions.append(copy.deepcopy(self.sol))
                best_cost = self.sol.cost
                no_improvement = 0
                self.iteration_since_last_improvement = 0
            else:
                no_improvement += 1
                self.iteration_since_last_improvement += 1

            self.update_tabu_structures(best_move)

            if no_improvement >= self.max_no_improvement:
                if no_improvement >= self.max_no_improvement * 2:
                    self.strong_diversification()
                else:
                    self.diversify_search()
                no_improvement = 0

            iteration += 1

        return self.best_solution

    def simple_tabu_search(self):
        """Fall back to plain Tabu Search once the adaptive search has stalled."""
        simple_search = SimpleTabuSearch(
            initial_solution=self.sol,
            cost_matrix=self.cost_matrix,
            capacity=self.capacity,
            tabu_tenure=self.tabu_tenure,
            max_iterations=self.max_iterations - self.iteration_since_last_improvement,
            max_no_improvement=self.max_no_improvement,
        )
        return simple_search.search()

    def generate_neighbors(self):
        """Neighbor generation with adaptive, weighted operator sampling."""
        move_generators = {
            'cross_route_reinsert': self.cross_route_reinsert,
            'cross_route_swap': self.cross_route_swap,
            'two_opt': self.two_opt,
            'two_opt_within_route': self.two_opt_within_route,
            'swap_within_route': self.swap_within_route,
            'reinsert_within_route': self.reinsert_within_route,
        }

        total_weight = sum(self.operator_weights.values())
        normalized_weights = [w / total_weight for w in self.operator_weights.values()]

        sampled_generators = random.choices(
            list(move_generators.keys()),
            weights=normalized_weights,
            k=min(3, len(move_generators)),
        )

        neighbors = []
        for generator_name in sampled_generators:
            moves = move_generators[generator_name]()
            neighbors.extend(moves)

        for move in neighbors:
            if move.move_cost < 0 and self.is_diverse_move(move):
                self.unchosen_good_moves.append(move)

        self.unchosen_good_moves = self.unchosen_good_moves[:20]
        return neighbors

    def probabilistic_selection(self, neighbors):
        """Probabilistic move selection with a temperature that cools as the search stalls."""
        if not neighbors:
            return None

        progress = self.iteration_since_last_improvement / self.max_no_improvement
        temperature = max(1e-6, 1.0 - progress)

        move_costs = [move.move_cost for move in neighbors]
        max_cost = max(move_costs)
        min_cost = min(move_costs)

        if max_cost != min_cost:
            weights = [
                np.exp(-((cost - min_cost) / (max_cost - min_cost)) / temperature)
                for cost in move_costs
            ]
        else:
            weights = [1.0] * len(move_costs)

        total_weight = sum(weights)
        if total_weight == 0:
            return None

        probabilities = [w / total_weight for w in weights]
        selected_index = random.choices(range(len(neighbors)), weights=probabilities, k=1)[0]
        return neighbors[selected_index]

    def update_operator_weights(self, operator, success):
        self.operator_usage[operator] += 1
        if success:
            self.operator_success[operator] += 1

        usage = self.operator_usage[operator]
        success_rate = (self.operator_success[operator] + 1) / (usage + 2)

        old_weight = self.operator_weights[operator]
        new_weight = success_rate * self.learning_rate + old_weight * (1 - self.learning_rate)
        self.operator_weights[operator] = max(min(new_weight, self.max_weight), self.min_weight)

    def diversify_search(self):
        """Randomly modifies the current solution to escape local optima."""
        if self.good_solutions:
            self.sol = copy.deepcopy(random.choice(self.good_solutions))
        elif self.unchosen_good_moves:
            move = self.unchosen_good_moves.pop(0)
            if self._apply_move_safely(move):
                self.sol.update_solution_cost()
            else:
                self.strong_diversification()
        else:
            self.strong_diversification()

    def _apply_move_safely(self, move):
        """Apply a move popped from `unchosen_good_moves`.

        These moves were generated against routes at some earlier point in
        the search; by the time they're replayed, other moves may have
        mutated those same route objects, making the stored indices invalid
        or the move no longer capacity-feasible. Snapshot first and roll
        back if the move turns out to be stale, rather than crash or leave
        an infeasible solution in place.
        """
        backup = copy.deepcopy(self.sol)
        before_ids = sorted(n.id for route in self.sol.routes for n in route.sequence_of_nodes[1:])
        try:
            move.apply()
        except (IndexError, ValueError):
            self.sol = backup
            return False

        after_ids = sorted(n.id for route in self.sol.routes for n in route.sequence_of_nodes[1:])
        if after_ids != before_ids or any(route.load > self.capacity for route in self.sol.routes):
            self.sol = backup
            return False

        return True

    def strong_diversification(self):
        for _ in range(3):
            random_route = random.choice(self.sol.routes)
            if len(random_route.sequence_of_nodes) > 3:
                i, j = random.sample(range(1, len(random_route.sequence_of_nodes) - 1), 2)
                random_route.sequence_of_nodes[i], random_route.sequence_of_nodes[j] = random_route.sequence_of_nodes[j], random_route.sequence_of_nodes[i]

    def is_diverse_move(self, move):
        move_signature = self.get_move_signature(move)
        is_diverse = move_signature not in self.solution_features
        if is_diverse:
            self.solution_features.add(move_signature)
        return is_diverse

    def get_move_signature(self, move):
        affected_nodes = tuple(sorted(move.affected_nodes))
        affected_arcs = tuple(sorted(str(arc) for arc in move.affected_arcs))
        return hash((affected_nodes, affected_arcs, move.operator))

    def update_tabu_structures(self, move):
        self.update_tabu_arcs(move.affected_arcs)
        self.update_tabu_nodes(move.affected_nodes)
        self.adjust_tabu_tenure()

    def update_tabu_nodes(self, nodes):
        self.tabu_nodes.extend(nodes)

    def update_tabu_arcs(self, arcs):
        self.tabu_arcs.extend(arcs)

    def adjust_tabu_tenure(self):
        if self.iteration_since_last_improvement > self.max_no_improvement:
            self.tabu_tenure = min(len(self.sol.routes) * 2, self.tabu_tenure + 1)
        else:
            self.tabu_tenure = max(5, self.tabu_tenure - 1)

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
                        move.operator = 'cross_route_reinsert'
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
                            move.operator = 'cross_route_swap'
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
                            move.operator = 'two_opt'
                            moves.append(move)

        return moves

    def two_opt_within_route(self):
        moves = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):
                for j in range(i + 2, len(route.sequence_of_nodes) - 1):
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)
                    if move.move_cost < 0:
                        move.operator = 'two_opt_within_route'
                        moves.append(move)

        return moves

    def swap_within_route(self):
        moves = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):
                for j in range(i + 1, len(route.sequence_of_nodes) - 1):
                    move = InRouteSwapMove(route, i, j, self.cost_matrix)
                    if move.move_cost < 0:
                        move.operator = 'swap_within_route'
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
                        move.operator = 'reinsert_within_route'
                        moves.append(move)

        return moves


def run(initial_solution, cost_matrix, capacity, tabu_tenure=30, max_iterations=100, max_no_improvement=30, switch_depth=20, **_ignored):
    """Registry entry point: uniform `run(initial, cost_matrix, capacity, **kwargs)` signature."""
    search = AdaptiveTabuSearch(
        initial_solution=initial_solution,
        cost_matrix=cost_matrix,
        capacity=capacity,
        tabu_tenure=tabu_tenure,
        max_iterations=max_iterations,
        max_no_improvement=max_no_improvement,
        switch_depth=switch_depth,
    )
    return search.search()
