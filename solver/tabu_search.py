import random
from local_search import LocalSearch
from moves import RelocationMove, SwapMove, TwoOptMove, InRouteSwapMove, InRouteTwoOptMove
import copy

class TabuSearch:
    def __init__(self, initial_solution, cost_matrix, capacity, tabu_tenure):
        self.current_solution = initial_solution
        self.best_solution = copy.deepcopy(initial_solution)
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.tabu_tenure = tabu_tenure
        self.tabu_arcs = set()

    def generate_neighbors(self):
        neighbors = []

        for route1 in self.current_solution.routes:
            for route2 in self.current_solution.routes:
                # Generate RelocationMove neighbors
                for i, node in enumerate(route1.sequence_of_nodes[1:], start=1):
                    prev_node = route1.sequence_of_nodes[i - 1]
                    next_node = route1.sequence_of_nodes[i + 1] if i + 1 < len(route1.sequence_of_nodes) else None
                    if ((prev_node.id, node.id) in self.tabu_arcs or
                        (node.id, next_node.id) in self.tabu_arcs if next_node else False):
                        continue
                    for j in range(1, len(route2.sequence_of_nodes)):
                        move = RelocationMove(
                            node=node,
                            from_route=route1,
                            to_route=route2,
                            from_index=i,
                            to_index=j,
                            capacity=self.capacity,
                            cost_matrix=self.cost_matrix
                        )
                        if move.is_feasible:
                            neighbors.append((move, move.move_cost))

                # Generate SwapMove neighbors
                for i in range(1, len(route1.sequence_of_nodes)):
                    for j in range(1, len(route2.sequence_of_nodes)):
                        arc1 = (route1.sequence_of_nodes[i - 1].id, route1.sequence_of_nodes[i].id)
                        arc2 = (route2.sequence_of_nodes[j - 1].id, route2.sequence_of_nodes[j].id)
                        if arc1 in self.tabu_arcs or arc2 in self.tabu_arcs:
                            continue
                        move = SwapMove(
                            route1=route1,
                            route2=route2,
                            index1=i,
                            index2=j,
                            cost_matrix=self.cost_matrix,
                            capacity=self.capacity
                        )
                        if move.is_feasible:
                            neighbors.append((move, move.move_cost))

                # Generate TwoOptMove neighbors
                for i in range(1, len(route1.sequence_of_nodes)):
                    for j in range(1, len(route2.sequence_of_nodes)):
                        arc1 = (route1.sequence_of_nodes[i - 1].id, route1.sequence_of_nodes[i].id)
                        arc2 = (route2.sequence_of_nodes[j - 1].id, route2.sequence_of_nodes[j].id)
                        if arc1 in self.tabu_arcs or arc2 in self.tabu_arcs:
                            continue
                        move = TwoOptMove(
                            route1=route1,
                            route2=route2,
                            i=i,
                            j=j,
                            cost_matrix=self.cost_matrix,
                            capacity=self.capacity
                        )
                        if move.is_feasible:
                            neighbors.append((move, move.move_cost))

                # Generate InRouteTwoOptMove neighbors (intra-route optimization)
                for i in range(1, len(route1.sequence_of_nodes) - 1):
                    for j in range(i + 1, len(route1.sequence_of_nodes)):
                        arc = (route1.sequence_of_nodes[i - 1].id, route1.sequence_of_nodes[i].id)
                        if arc in self.tabu_arcs:
                            continue
                        move = InRouteTwoOptMove(
                            route=route1,
                            i=i,
                            j=j,
                            cost_matrix=self.cost_matrix
                        )
                        neighbors.append((move, move.move_cost))

                # Generate InRouteSwapMove neighbors (intra-route optimization)
                for i in range(1, len(route1.sequence_of_nodes) - 1):
                    for j in range(i + 1, len(route1.sequence_of_nodes)):
                        arc = (route1.sequence_of_nodes[i - 1].id, route1.sequence_of_nodes[i].id)
                        if arc in self.tabu_arcs:
                            continue
                        move = InRouteSwapMove(
                            route=route1,
                            index1=i,
                            index2=j,
                            cost_matrix=self.cost_matrix
                        )
                        neighbors.append((move, move.move_cost))

        # Sort neighbors by move cost
        neighbors.sort(key=lambda x: x[1])
        return neighbors

    def update_tabu_arcs(self, arcs):
        """
        Add arcs to the tabu list and maintain the list within the tabu tenure.
        """
        self.tabu_arcs.update(arcs)
        while len(self.tabu_arcs) > self.tabu_tenure:
            self.tabu_arcs.pop()

    def search(self, max_iterations):
        iteration = 0

        while iteration < max_iterations:
            neighbors = self.generate_neighbors()

            if not neighbors:
                print("No feasible neighbors found. Terminating search.")
                break

            best_candidate = None
            for move, cost in neighbors:
                # Check tabu arcs for the move
                if hasattr(move, 'node') and hasattr(move.node, 'id'):
                    arc = (move.from_route.sequence_of_nodes[move.from_index - 1].id, move.node.id)
                    if  self.current_solution.cost >= self.best_solution.cost:
                        continue
                best_candidate = move
                break

            if not best_candidate:
                print("No valid candidate found. Terminating search.")
                break

            # Apply the best move
            best_candidate.apply()

            # Update the current solution
            self.current_solution.update_solution_cost()

            # Print progress
            print(f"Iteration {iteration}: Best Cost = {self.best_solution.cost}, Current Cost = {self.current_solution.cost}")

            # Update the best solution if improved
            if self.current_solution.cost < self.best_solution.cost:
                self.best_solution = copy.deepcopy(self.current_solution)

            # Update the tabu arcs
            if hasattr(best_candidate, 'from_route') and hasattr(best_candidate, 'to_route'):
                affected_arcs = [
                    (best_candidate.from_route.sequence_of_nodes[best_candidate.from_index - 1].id, best_candidate.node.id),
                    (best_candidate.node.id, best_candidate.to_route.sequence_of_nodes[best_candidate.to_index].id)
                ]
                self.update_tabu_arcs(affected_arcs)

            iteration += 1

        return self.best_solution
