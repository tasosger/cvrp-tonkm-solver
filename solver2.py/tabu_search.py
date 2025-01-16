import copy
import random
from moves import RelocationMove, SwapMove, TwoOptMove, InRouteSwapMove, InRouteTwoOptMove, InRouteReinsertMove

class TabuSearch:
    def __init__(self, initial_solution, cost_matrix, capacity, tabu_tenure=10, max_iterations=100, lambda_factor=0.1):
        """
        Initialize Guided Tabu Search.
        :param initial_solution: Initial solution for the problem.
        :param cost_matrix: Cost matrix for the VRP.
        :param capacity: Vehicle capacity for feasibility checks.
        :param tabu_tenure: Initial tabu tenure.
        :param max_iterations: Maximum number of iterations to perform.
        :param lambda_factor: Weight factor for arc penalties.
        """
        self.solution = initial_solution
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.tabu_tenure = tabu_tenure
        self.max_iterations = max_iterations
        self.lambda_factor = lambda_factor
        self.tabu_list = {}  # Tracks nodes and arcs
        self.best_solution = copy.deepcopy(initial_solution)
        self.best_cost = initial_solution.cost
        self.arc_penalties = {}  # Penalties for arcs (i, j)
        self.stagnation_counter = 0

    def tabu_search(self):
        """
        Perform the Guided Tabu Search algorithm.
        :return: Best solution found.
        """
        iteration = 0
        diversification_threshold = 20  # Trigger diversification after stagnation
        
        while iteration < self.max_iterations:
            # Find the best non-tabu move
            best_move = None
            best_move_cost = float('inf')

            for move_type in [
                self.cross_route_reinsert,
                self.cross_route_swap,
                self.two_opt,
                self.swap_within_route,
                self.two_opt_within_route,
                self.reinsert_within_route,
            ]:
                move = move_type()
                if move and move.is_feasible:
                    penalized_cost = self.calculate_penalized_cost(move)
                    if penalized_cost < best_move_cost or self.is_aspirational(move):
                        best_move = move
                        best_move_cost = penalized_cost

            if best_move:
                # Apply the move
                self.apply_move(best_move)
                # Update tabu list
                self.update_tabu_list(best_move)

                # Update best solution if improved
                if self.solution.cost < self.best_cost:
                    self.best_solution = copy.deepcopy(self.solution)
                    self.best_cost = self.solution.cost
                    self.stagnation_counter = 0
                else:
                    self.stagnation_counter += 1
            else:
                self.stagnation_counter += 1

            # Diversification: Apply random perturbation if stagnating
            if self.stagnation_counter >= diversification_threshold:
                self.solution = self.random_perturbation(self.solution)
                self.solution.update_solution_cost()
                self.stagnation_counter = 0
                print(f"Diversification applied at iteration {iteration}.")

            # Update arc penalties periodically
            if iteration % 10 == 0:
                self.update_arc_penalties()

            # Adjust tabu tenure dynamically
            self.adjust_tabu_tenure()

            # Log iteration details
            self.log_iteration(iteration)

            iteration += 1

        return self.best_solution

    def calculate_penalized_cost(self, move):
        """
        Calculate the penalized cost of a move based on arc penalties.
        """
        penalized_cost = move.move_cost
        for arc in move.affected_arcs:
            penalized_cost += self.arc_penalties.get(tuple(arc), 0) * self.lambda_factor
        return penalized_cost

    def update_arc_penalties(self):
        """
        Update penalties for arcs frequently used in the solution.
        """
        for route in self.solution.routes:
            for i in range(len(route.sequence_of_nodes) - 1):
                arc = (route.sequence_of_nodes[i].id, route.sequence_of_nodes[i + 1].id)
                self.arc_penalties[arc] = self.arc_penalties.get(arc, 0) + 1

        # Decay penalties over time
        for arc in list(self.arc_penalties.keys()):
            self.arc_penalties[arc] *= 0.9
            if self.arc_penalties[arc] < 1e-3:
                del self.arc_penalties[arc]

    def adjust_tabu_tenure(self):
        """
        Adjust tabu tenure dynamically based on search progress.
        """
        if self.stagnation_counter > 10:
            self.tabu_tenure = min(self.tabu_tenure + 1, 20)
        elif self.stagnation_counter == 0:
            self.tabu_tenure = max(self.tabu_tenure - 1, 5)

    def log_iteration(self, iteration):
        """
        Log details of the current iteration.
        """
        print(f"Iteration {iteration}: Best Cost = {self.best_cost}, Current Cost = {self.solution.cost}")
        if iteration % 10 == 0:
            print(f"Top penalties: {sorted(self.arc_penalties.items(), key=lambda x: -x[1])[:5]}")

    def random_perturbation(self, solution):
        """
        Apply a random perturbation to escape local optima.
        """
        perturbed_solution = copy.deepcopy(solution)
        for _ in range(random.randint(1, 3)):
            random_route = random.choice(perturbed_solution.routes)
            if len(random_route.sequence_of_nodes) > 3:
                i, j = random.sample(range(1, len(random_route.sequence_of_nodes) - 1), 2)
                random_route.sequence_of_nodes[i], random_route.sequence_of_nodes[j] = \
                    random_route.sequence_of_nodes[j], random_route.sequence_of_nodes[i]
        return perturbed_solution

    def apply_move(self, move):
        """
        Apply the selected move to the current solution.
        """
        move.apply()
        self.solution.update_solution_cost()

    def update_tabu_list(self, move):
        """
        Update the tabu list with the current move.
        """
        for node_id in move.affected_nodes:
            self.tabu_list[node_id] = self.tabu_tenure

        for arc in move.affected_arcs:
            self.tabu_list[tuple(arc)] = self.tabu_tenure

        # Decrement tabu tenure for all entries
        for key in list(self.tabu_list.keys()):
            self.tabu_list[key] -= 1
            if self.tabu_list[key] <= 0:
                del self.tabu_list[key]

    def is_aspirational(self, move):
        """
        Check if a move satisfies the aspiration criterion.
        """
        return move.move_cost + self.solution.cost < self.best_cost

    def cross_route_reinsert(self):
        best_move = None
        for from_route in self.solution.routes:
            for to_route in self.solution.routes:
                if from_route == to_route:
                    continue

                for i in range(1, len(from_route.sequence_of_nodes)):
                    for j in range(1, len(to_route.sequence_of_nodes)):
                        move = RelocationMove(
                            from_route.sequence_of_nodes[i],
                            from_route,
                            to_route,
                            i,
                            j,
                            self.capacity,
                            self.cost_matrix,
                        )
                        if (
                            move.is_feasible
                            and move.move_cost < 0
                            and (best_move is None or move.move_cost < best_move.move_cost)
                            and not self.is_tabu(move)
                        ):
                            best_move = move
        return best_move

    def cross_route_swap(self):
        best_move = None
        for from_route in self.solution.routes:
            for to_route in self.solution.routes:
                if from_route == to_route:
                    continue

                for i in range(1, len(from_route.sequence_of_nodes)):
                    for j in range(1, len(to_route.sequence_of_nodes)):
                        move = SwapMove(from_route, to_route, i, j, self.cost_matrix, self.capacity)
                        if (
                            move.is_feasible
                            and move.move_cost < 0
                            and (best_move is None or move.move_cost < best_move.move_cost)
                            and not self.is_tabu(move)
                        ):
                            best_move = move
        return best_move

    def two_opt(self):
        best_move = None
        for route1 in self.solution.routes:
            for route2 in self.solution.routes:
                for i in range(1, len(route1.sequence_of_nodes)):
                    for j in range(1, len(route2.sequence_of_nodes)):
                        if route1 == route2:
                            continue
                        move = TwoOptMove(route1, route2, i, j, self.cost_matrix, self.capacity)
                        if (
                            move.is_feasible
                            and move.move_cost < 0
                            and (best_move is None or move.move_cost < best_move.move_cost)
                            and not self.is_tabu(move)
                        ):
                            best_move = move
        return best_move

    def swap_within_route(self):
        best_move = None
        for route in self.solution.routes:
            for i in range(1, len(route.sequence_of_nodes) - 1):
                for j in range(i + 1, len(route.sequence_of_nodes)):
                    move = InRouteSwapMove(route, i, j, self.cost_matrix)
                    move.is_feasible = True
                    if (
                        move.move_cost < -1e-6
                        and (best_move is None or move.move_cost < best_move.move_cost)
                        and not self.is_tabu(move)
                    ):
                        best_move = move
        return best_move

    def two_opt_within_route(self):
        best_move = None
        for route in self.solution.routes:
            for i in range(1, len(route.sequence_of_nodes) - 1):
                for j in range(i + 2, len(route.sequence_of_nodes)):
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)
                    move.is_feasible = True

                    if (
                        move.move_cost < -1e-6
                        and (best_move is None or move.move_cost < best_move.move_cost)
                        and not self.is_tabu(move)
                    ):
                        best_move = move
        return best_move

    def reinsert_within_route(self):
        best_move = None
        for route in self.solution.routes:
            for from_index in range(1, len(route.sequence_of_nodes)):
                for to_index in range(1, len(route.sequence_of_nodes)):
                    if from_index == to_index or abs(from_index - to_index) == 1:
                        continue
                    move = InRouteReinsertMove(route, from_index, to_index, self.cost_matrix, self.capacity)
                    move.is_feasible = True

                    if (
                        move.move_cost < -1e-6
                        and (best_move is None or move.move_cost < best_move.move_cost)
                        and not self.is_tabu(move)
                    ):
                        best_move = move
        return best_move

    def is_tabu(self, move):
        """
        Check if a move is tabu.
        """
        for node_id in move.affected_nodes:
            if node_id in self.tabu_list:
                return True
        return False
