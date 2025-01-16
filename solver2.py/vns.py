import copy
import random
from moves import RelocationMove, SwapMove, TwoOptMove, InRouteSwapMove, InRouteTwoOptMove, InRouteReinsertMove
from tabu_search import TabuSearch

class VNS:
    def __init__(self, initial_solution, cost_matrix, capacity, max_iterations=1, max_neighborhood_size=1):
        """
        Initialize the VNS algorithm.
        :param initial_solution: Initial solution for the problem.
        :param cost_matrix: Cost matrix for the problem.
        :param capacity: Capacity constraint for routes.
        :param max_iterations: Maximum number of iterations.
        :param max_neighborhood_size: Number of neighborhood structures to explore.
        """
        self.best_solution = initial_solution
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.max_iterations = max_iterations
        self.max_neighborhood_size = max_neighborhood_size

    def vns(self):
        """
        Perform the VNS algorithm.
        :return: Best solution found.
        """
        iteration = 0
        while iteration < self.max_iterations:
            print(iteration)
            k = 1  # Start with the first neighborhood structure

            while k <= self.max_neighborhood_size:
                print('k',k)
                # Step 1: Shaking - Apply a random perturbation
                perturbed_solution = self.shaking(self.best_solution, k)

                # Step 2: Local Search - Improve the solution using Tabu Search
                improved_solution = self.local_search(perturbed_solution)

                # Step 3: Acceptance Criterion
                if improved_solution.cost < self.best_solution.cost:
                    self.best_solution = improved_solution
                    k += 1  # Reset neighborhood index if improvement is found
                else:
                    k += 1  # Move to the next neighborhood

            iteration += 1
            print(f"Iteration {iteration}: Best Cost = {self.best_solution.cost}")

        return self.best_solution

    def shaking(self, solution, k):
        """
        Apply a random perturbation to the solution based on the neighborhood structure.
        :param solution: Current solution.
        :param k: Neighborhood index (determines type of perturbation).
        :return: Perturbed solution.
        """
        perturbed_solution = copy.deepcopy(solution)

        # Neighborhood-specific moves
        if k == 1:
            # Random RelocationMove
            for _ in range(3):  # Try 3 random moves
                from_route = random.choice(perturbed_solution.routes)
                to_route = random.choice(perturbed_solution.routes)
                if len(from_route.sequence_of_nodes) > 2:
                    from_index = random.randint(1, len(from_route.sequence_of_nodes) - 1)
                    to_index = random.randint(1, len(to_route.sequence_of_nodes))
                    node = from_route.sequence_of_nodes[from_index]
                    move = RelocationMove(node, from_route, to_route, from_index, to_index, self.capacity, self.cost_matrix)
                    if move.is_feasible:
                        move.apply()
                        break

        elif k == 2:
            # Random SwapMove
            for _ in range(3):  # Try 3 random moves
                route1 = random.choice(perturbed_solution.routes)
                route2 = random.choice(perturbed_solution.routes)
                if len(route1.sequence_of_nodes) > 1 and len(route2.sequence_of_nodes) > 1:
                    index1 = random.randint(1, len(route1.sequence_of_nodes) - 1)
                    index2 = random.randint(1, len(route2.sequence_of_nodes) - 1)
                    move = SwapMove(route1, route2, index1, index2, self.cost_matrix, self.capacity)
                    if move.is_feasible:
                        move.apply()
                        break

        elif k == 3:
            # Random TwoOptMove
            for _ in range(3):  # Try 3 random moves
                route1 = random.choice(perturbed_solution.routes)
                route2 = random.choice(perturbed_solution.routes)
                if len(route1.sequence_of_nodes) > 1 and len(route2.sequence_of_nodes) > 1:
                    i = random.randint(1, len(route1.sequence_of_nodes) - 1)
                    j = random.randint(1, len(route2.sequence_of_nodes) - 1)
                    move = TwoOptMove(route1, route2, i, j, self.cost_matrix, self.capacity)
                    if move.is_feasible:
                        move.apply()
                        break

        elif k == 4:
            # Random InRouteSwapMove
            for _ in range(3):  # Try 3 random moves
                route = random.choice(perturbed_solution.routes)
                if len(route.sequence_of_nodes) > 2:
                    index1, index2 = sorted(random.sample(range(1, len(route.sequence_of_nodes)), 2))
                    move = InRouteSwapMove(route, index1, index2, self.cost_matrix)
                    move.apply()
                    break

        elif k == 5:
            # Random InRouteTwoOptMove
            for _ in range(3):  # Try 3 random moves
                route = random.choice(perturbed_solution.routes)
                if len(route.sequence_of_nodes) > 3:
                    i, j = sorted(random.sample(range(1, len(route.sequence_of_nodes) - 1), 2))
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)
                    move.apply()
                    break

        elif k == 6:
            # Random InRouteReinsertMove
            for _ in range(3):  # Try 3 random moves
                route = random.choice(perturbed_solution.routes)
                if len(route.sequence_of_nodes) > 2:
                    from_index = random.randint(1, len(route.sequence_of_nodes) - 1)
                    to_index = random.randint(1, len(route.sequence_of_nodes))
                    move = InRouteReinsertMove(route, from_index, to_index, self.cost_matrix, self.capacity)
                    move.apply()
                    break

        return perturbed_solution

    def local_search(self, solution):
        """
        Perform local search using Tabu Search.
        :param solution: The solution to improve.
        :return: Improved solution.
        """
        tabu_search = TabuSearch(solution, self.cost_matrix, self.capacity)
        print('tabu')
        return tabu_search.tabu_search()
