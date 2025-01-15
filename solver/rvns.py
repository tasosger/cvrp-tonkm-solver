import random
import copy
from local_search import LocalSearch
from moves import RelocationMove, SwapMove, TwoOptMove, InRouteSwapMove, InRouteTwoOptMove

class RVNS:
    def __init__(self, initial_solution, cost_matrix, capacity):
        self.sol = copy.deepcopy(initial_solution)
        self.best_solution = copy.deepcopy(initial_solution)
        self.cost_matrix = cost_matrix
        self.capacity = capacity

        # Define neighborhood structures
        self.neighborhoods = [
            self.cross_route_reinsert,
            self.cross_route_swap,
            self.two_opt,
            self.swap_within_route,
            self.two_opt_within_route,
        ]

    def search(self, max_iterations=100, max_no_improvement=10, sample_size=10):
        """Performs smarter Variable Neighborhood Search (SmartVNS)."""
        iteration = 0
        no_improvement = 0
        neighborhood_priorities = [1] * len(self.neighborhoods)  # Equal priority for all neighborhoods initially

        while iteration < max_iterations:
            # Select the best neighborhood based on priority
            neighborhood_index = self.select_neighborhood(neighborhood_priorities)

            neighbors = self.neighborhoods[neighborhood_index]()

            if not neighbors:
                # If no moves in the neighborhood, deprioritize and continue
                neighborhood_priorities[neighborhood_index] = max(1, neighborhood_priorities[neighborhood_index] - 1)
                continue

            # Randomly sample moves to improve efficiency
            sampled_neighbors = random.sample(neighbors, min(len(neighbors), sample_size))

            # Evaluate moves using the manipulated objective function
            best_candidate = min(sampled_neighbors, key=lambda move: self.evaluate_move_cost(move))

            # Apply the best move
            best_candidate.apply()
            self.sol.update_solution_cost()

            if self.sol.cost < self.best_solution.cost:
                # Found a better solution; update and increase neighborhood priority
                self.best_solution = copy.deepcopy(self.sol)
                no_improvement = 0
                neighborhood_priorities[neighborhood_index] += 1  # Reward this neighborhood
                print(f"Iteration {iteration}: New Best Cost = {self.best_solution.cost}")
            else:
                # No improvement; decrease neighborhood priority
                no_improvement += 1
                neighborhood_priorities[neighborhood_index] = max(1, neighborhood_priorities[neighborhood_index] - 1)

            if no_improvement >= max_no_improvement:
                print("No improvement for several iterations. Terminating search.")
                break

            iteration += 1

        return self.best_solution

    def select_neighborhood(self, priorities):
        """Select a neighborhood based on priority."""
        total_priority = sum(priorities)
        probabilities = [priority / total_priority for priority in priorities]
        return random.choices(range(len(self.neighborhoods)), weights=probabilities, k=1)[0]

    def evaluate_move_cost(self, move):
        """Manipulated objective function with adaptive penalties."""
        base_cost = move.move_cost

        # Calculate penalties
        total_load = sum(route.load for route in self.sol.routes)
        capacity_excess = max(0, total_load - self.capacity)

        max_load = max(route.load for route in self.sol.routes)
        min_load = min(route.load for route in self.sol.routes)
        load_difference = max_load - min_load

        total_compactness = sum(route.calculate_total_route_cost(self.cost_matrix) for route in self.sol.routes)

        # Dynamic weights for penalties
        penalty_factor = max(1, iteration // 10)  # Increase penalty weight as iterations progress
        return base_cost + penalty_factor * (capacity_excess + load_difference + total_compactness)

    def cross_route_reinsert(self):
        """Generates cross-route reinsert moves."""
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
        """Generates cross-route swap moves."""
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
        """Generates two-opt moves between routes."""
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
        """Generates swap moves within a single route."""
        moves = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):
                for j in range(i + 1, len(route.sequence_of_nodes) - 1):
                    move = InRouteSwapMove(route, i, j, self.cost_matrix)
                    if move.is_feasible:
                        moves.append(move)

        return moves

    def two_opt_within_route(self):
        """Generates two-opt moves within a single route."""
        moves = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):
                for j in range(i + 2, len(route.sequence_of_nodes) - 1):
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)
                    if move.is_feasible:
                        moves.append(move)

        return moves
