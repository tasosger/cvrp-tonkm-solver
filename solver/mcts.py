from tabu_search import TabuSearch as SimpleTabuSearch  # Import your simpler TabuSearch class
import random
import copy
import numpy as np
from collections import deque, Counter
from local_search import LocalSearch
from moves import RelocationMove, SwapMove, TwoOptMove, InRouteSwapMove, InRouteTwoOptMove, InRouteReinsertMove
from concurrent.futures import ThreadPoolExecutor

class TabuSearch:
    def __init__(self, initial_solution, cost_matrix, capacity, tabu_tenure, max_iterations=100, max_no_improvement=30, switch_depth=20):
        self.sol = copy.deepcopy(initial_solution)
        self.current_solution = initial_solution
        self.best_solution = copy.deepcopy(initial_solution)
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.tabu_tenure = tabu_tenure
        self.tabu_arcs = deque(maxlen=tabu_tenure)
        self.tabu_nodes = deque(maxlen=tabu_tenure)
        self.max_iterations = max_iterations
        self.max_no_improvement = max_no_improvement
        self.iteration_since_last_improvement = 0
        self.switch_depth = switch_depth  # Depth threshold to switch to simpler search

        # Enhanced operator weights with adaptive learning
        self.operator_weights = {
            'cross_route_reinsert': 1.0,
            'cross_route_swap': 1.0,
            'two_opt': 1.0,
            'two_opt_within_route': 1.0,
            'swap_within_route': 1.0,
            'reinsert_within_route': 1.0
        }
        self.operator_success = Counter()
        self.operator_usage = Counter()

        # Solution management
        self.good_solutions = []
        self.solution_features = set()
        self.unchosen_good_moves = []

        # Advanced parameters
        self.diversification_threshold = 0.1
        self.intensification_threshold = 0.05
        self.learning_rate = 0.1
        self.min_weight = 0.1
        self.max_weight = 5.0

    def search(self):
        """Adaptive tabu search with depth-based switching."""
        iteration = 0
        no_improvement = 0
        best_cost = float('inf')

        while iteration < self.max_iterations:
            # Check if the search should switch to simpler Tabu Search
            if self.iteration_since_last_improvement >= self.switch_depth:
                print("Switching to simpler Tabu Search due to search depth.")
                return self.simple_tabu_search()

            neighbors = self.generate_neighbors()

            if not neighbors and self.unchosen_good_moves:
                print("No new neighbors found. Revisiting unchosen good moves.")
                neighbors = [self.unchosen_good_moves.pop(0)]

            if not neighbors:
                print(f"Iteration {iteration}: No feasible neighbors found. Diversifying search.")
                self.diversify_search()
                neighbors = self.generate_neighbors()
                if not neighbors:
                    break

            best_move = self.probabilistic_selection(neighbors)
            if not best_move:
                continue

            # Apply move and update solution
            best_move.apply()
            self.sol.update_solution_cost()

            print(f"Iteration {iteration}: Best Cost = {self.best_solution.cost}, Current Cost = {self.sol.cost}")

            # Update memory structures
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

            # Adaptive mechanism
            if no_improvement >= self.max_no_improvement:
                if no_improvement >= self.max_no_improvement * 2:
                    print("Search stagnated. Performing strong diversification.")
                    self.strong_diversification()
                else:
                    print("No improvement. Diversifying search.")
                    self.diversify_search()
                no_improvement = 0

            iteration += 1

        return self.best_solution

    def simple_tabu_search(self):
        """Switch to the simpler Tabu Search for deeper search."""
        simple_search = SimpleTabuSearch(
            initial_solution=self.sol,
            cost_matrix=self.cost_matrix,
            capacity=self.capacity,
            tabu_tenure=self.tabu_tenure,
            max_iterations=self.max_iterations - self.iteration_since_last_improvement,
            max_no_improvement=self.max_no_improvement
        )
        return simple_search.search()

    def generate_neighbors(self):
        """Enhanced neighbor generation with adaptive operator selection."""
        move_generators = {
            'cross_route_reinsert': self.cross_route_reinsert,
            'cross_route_swap': self.cross_route_swap,
            'two_opt': self.two_opt,
            'two_opt_within_route': self.two_opt_within_route,
            'swap_within_route': self.swap_within_route,
            'reinsert_within_route': self.reinsert_within_route
        }

        # Normalize weights for selection
        total_weight = sum(self.operator_weights.values())
        normalized_weights = [w / total_weight for w in self.operator_weights.values()]

        # Select operators using weighted sampling
        sampled_generators = random.choices(
            list(move_generators.keys()),
            weights=normalized_weights,
            k=min(3, len(move_generators))
        )

        neighbors = []
        for generator_name in sampled_generators:
            moves = move_generators[generator_name]()
            # Filter moves based on solution features
            moves = self.filter_promising_moves(moves)
            neighbors.extend(moves)

        # Store good moves
        for move in neighbors:
            if move.move_cost < 0 and self.is_diverse_move(move):
                self.unchosen_good_moves.append(move)

        self.unchosen_good_moves = self.unchosen_good_moves[:20]
        return neighbors
    def filter_promising_moves(self, moves):
        """Fallback to return all moves for classes without advanced filtering."""
        return moves


    def probabilistic_selection(self, neighbors):
        """Enhanced probabilistic selection with temperature control."""
        if not neighbors:
            return None

        # Calculate temperature based on search progress
        progress = self.iteration_since_last_improvement / self.max_no_improvement
        temperature = 1.0 - progress  # Higher at start, lower as search progresses

        move_costs = [move.move_cost for move in neighbors]
        max_cost = max(move_costs)
        min_cost = min(move_costs)

        # Calculate weights with temperature control
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
        """Update operator weights based on their success."""
        self.operator_usage[operator] += 1
        if success:
            self.operator_success[operator] += 1

        # Calculate success rate with smoothing
        usage = self.operator_usage[operator]
        success_rate = (self.operator_success[operator] + 1) / (usage + 2)

        # Update weight using exponential moving average
        old_weight = self.operator_weights[operator]
        new_weight = success_rate * self.learning_rate + old_weight * (1 - self.learning_rate)
        self.operator_weights[operator] = max(min(new_weight, self.max_weight), self.min_weight)

    def diversify_search(self):
        """Randomly modifies the current solution to escape local optima."""
        if self.good_solutions:
            self.sol = copy.deepcopy(random.choice(self.good_solutions))  # Restart from a good solution
        elif self.unchosen_good_moves:
            print("Revisiting an unchosen good move.")
            # Restore solution and apply stored move
            move = self.unchosen_good_moves.pop(0)
            move.apply()
            self.sol.update_solution_cost()
        else:
            for _ in range(3):  # Apply a few random perturbations
                random_route = random.choice(self.sol.routes)
                if len(random_route.sequence_of_nodes) > 2:
                    i, j = random.sample(range(1, len(random_route.sequence_of_nodes) - 1), 2)
                    random_route.sequence_of_nodes[i], random_route.sequence_of_nodes[j] = random_route.sequence_of_nodes[j], random_route.sequence_of_nodes[i]

    def is_diverse_move(self, move):
        """Check if a move leads to a diverse solution."""
        move_signature = self.get_move_signature(move)
        is_diverse = move_signature not in self.solution_features
        if is_diverse:
            self.solution_features.add(move_signature)
        return is_diverse

    def get_move_signature(self, move):
        """Generate a unique signature for a move."""
        affected_nodes = tuple(sorted(move.affected_nodes))
        affected_arcs = tuple(sorted(str(arc) for arc in move.affected_arcs))
        return hash((affected_nodes, affected_arcs, move.operator))

    def update_tabu_structures(self, move):
        """Update all tabu-related structures."""
        self.update_tabu_arcs(move.affected_arcs)
        self.update_tabu_nodes(move.affected_nodes)
        self.adjust_tabu_tenure()

    def update_tabu_nodes(self, nodes):
        """Updates the tabu list with new nodes."""
        self.tabu_nodes.extend(nodes)

    def update_tabu_arcs(self, arcs):
        """Updates the tabu list with new arcs."""
        self.tabu_arcs.extend(arcs)

    def adjust_tabu_tenure(self):
        """Dynamically adjusts the tabu tenure based on search progress."""
        if self.iteration_since_last_improvement > self.max_no_improvement:
            self.tabu_tenure = min(len(self.sol.routes) * 2, self.tabu_tenure + 1)  # Increase tenure
        else:
            self.tabu_tenure = max(5, self.tabu_tenure - 1)  # Decrease tenure

    # Include move generators (cross_route_reinsert, cross_route_swap, etc.) and all other helper methods here.

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
                for to_index in range(len(route.sequence_of_nodes)):
                    if from_index == to_index or abs(from_index - to_index) == 1:
                        continue

                    move = InRouteReinsertMove(route, from_index, to_index, self.cost_matrix, self.capacity)
                    if move.move_cost < 0:
                        move.operator = 'reinsert_within_route'
                        moves.append(move)

        return moves

# Example of how to initialize and run the Adaptive Tabu Search
# initial_solution = ... (initialize your solution here)
# cost_matrix = ... (initialize your cost matrix here)
# capacity = ... (initialize vehicle capacity here)
# adaptive_tabu = AdaptiveTabuSearch(initial_solution, cost_matrix, capacity, tabu_tenure=10, max_iterations=100)
# best_solution = adaptive_tabu.search()
# print("Best solution found:", best_solution)
