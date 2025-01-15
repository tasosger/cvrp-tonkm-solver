import random
from local_search import LocalSearch
from moves import RelocationMove, SwapMove, TwoOptMove, InRouteSwapMove, InRouteTwoOptMove, InRouteReinsertMove
import random


import copy

class VNS:
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
            self.reinsert_within_route
        ]
    
    def search(self, max_iterations, max_no_improvement=5):
        """Performs Variable Neighborhood Search (VNS) with manipulated objective function."""
        iteration = 0
        no_improvement = 0

        while iteration < max_iterations:
            neighborhood_index = 0  # Start with the first neighborhood

            while neighborhood_index < len(self.neighborhoods):
                neighbors = self.neighborhoods[neighborhood_index]()

                if not neighbors:
                    # No feasible moves in the current neighborhood
                    neighborhood_index += 1
                    continue

                # Evaluate moves using the manipulated objective function
                best_candidate = min(neighbors, key=lambda move: self.evaluate_move_cost(move))

                best_candidate.apply()
                self.sol.update_solution_cost()

                if self.sol.cost < self.best_solution.cost:
                    # Found a better solution; update and reset
                    self.best_solution = copy.deepcopy(self.sol)
                    no_improvement = 0
                    neighborhood_index = 0  # Restart neighborhoods
                    print(f"Iteration {iteration}: New Best Cost = {self.best_solution.cost}")
                else:
                    # No improvement; move to the next neighborhood
                    no_improvement += 1
                    neighborhood_index += 1

                if no_improvement >= max_no_improvement:
                    print("No improvement for several iterations. Terminating search.")
                    return self.best_solution

            iteration += 1

        return self.best_solution

    def evaluate_move_cost(self, move):
        """Manipulated objective function with penalties."""
        base_cost = move.move_cost

        capacity_excess = max(0, sum(route.load for route in self.sol.routes) - self.capacity)

        load_difference = max(route.load for route in self.sol.routes) - min(route.load for route in self.sol.routes)
        compactness_penalty = sum(route.calculate_total_route_cost(self.cost_matrix) for route in self.sol.routes)

        penalty_factor = 1000  # Weight for penalties
        return base_cost + penalty_factor * (capacity_excess + load_difference + compactness_penalty)

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
        """Generates swap moves within a single route."""
        moves = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):
                for j in range(i + 1, len(route.sequence_of_nodes) - 1):
                    move = InRouteSwapMove(route, i, j, self.cost_matrix)
                    moves.append(move)

        return moves

    def two_opt_within_route(self):
        """Generates two-opt moves within a single route."""
        moves = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):
                for j in range(i + 2, len(route.sequence_of_nodes) - 1):
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)
                    
                    moves.append(move)

        return moves



    def reinsert_within_route(self):
        
        best_move = None

        for route in self.sol.routes:
            # Iterate over all possible nodes to reinsert
            for from_index in range(1, len(route.sequence_of_nodes) ):
                for to_index in range(len(route.sequence_of_nodes)-1):
                    if from_index == to_index or abs(from_index - to_index) == 1:
                        # Skip invalid reinsertions (same position or adjacent)
                        continue

                    # Create a move for the reinsertion
                    move = InRouteReinsertMove(route, from_index, to_index, self.cost_matrix, self.capacity)
                    
                    if move.move_cost < -1e-6:
                        if best_move is None or move.move_cost < best_move.move_cost:
                            best_move = move

        return best_move
