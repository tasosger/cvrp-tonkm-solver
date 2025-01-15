import random
from local_search import LocalSearch
from moves import RelocationMove, SwapMove, TwoOptMove, InRouteSwapMove, InRouteTwoOptMove, InRouteReinsertMove
import copy
import random

class TabuSearch:
    def __init__(self, initial_solution, cost_matrix, capacity, tabu_tenure):
        self.sol = copy.deepcopy(initial_solution)
        self.current_solution = initial_solution
        self.best_solution = copy.deepcopy(initial_solution)
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.tabu_tenure = tabu_tenure
        self.tabu_arcs = set()
        self.tabu_nodes = set()

    def generate_neighbors(self):
        """Generates neighbors by applying all move operators."""
        return (
            self.cross_route_reinsert() +
            self.cross_route_swap() +
            self.two_opt() +
            self.two_opt_within_route() +
            self.swap_within_route() +
            self.cross_route_reinsert()
        )

    

    def search(self, max_iterations, max_no_improvement=5):
        """Performs the tabu search optimization."""
        iteration = 0
        no_improvement = 0

        while iteration < max_iterations:
            neighbors = self.generate_neighbors()

            if not neighbors:
                print("No feasible neighbors found. Terminating search.")
                break

            best_candidate = None
            for move in neighbors:
                if not self.is_tabu(move) or move.move_cost + self.sol.cost < self.best_solution.cost:
                    best_candidate = move
                    break

            if not best_candidate:
                print("No valid candidate found. Terminating search.")
                break

            best_candidate.apply()
            self.sol.update_solution_cost()

            print(f"Iteration {iteration}: Best Cost = {self.best_solution.cost}, Current Cost = {self.sol.cost}")

            if self.sol.cost < self.best_solution.cost:
                self.best_solution = copy.deepcopy(self.sol)
                no_improvement = 0
            else:
                no_improvement += 1

            self.update_tabu_arcs(best_candidate.affected_arcs)
            self.update_tabu_nodes(best_candidate.affected_nodes)

            if no_improvement >= max_no_improvement:
                print("No improvement for several iterations. Terminating search.")
                break

            iteration += 1

        return self.best_solution

    

    def is_tabu(self, move):
        """Checks if the move affects any arcs or nodes currently in the tabu list."""
        # Check arcs
        for arc in move.affected_arcs:
            if arc in self.tabu_arcs:
                return True
        
        for node in move.affected_nodes:
            if node in self.tabu_nodes:
                return True
        
    def update_tabu_nodes(self, nodes):
        """Updates the tabu list with new nodes while maintaining the tabu tenure."""
        self.tabu_nodes.update(nodes)
        while len(self.tabu_nodes) > self.tabu_tenure:
            self.tabu_nodes.pop()
    
    def update_tabu_arcs(self, arcs):
        """Updates the tabu list with new arcs while maintaining the tabu tenure."""
        self.tabu_arcs.update(arcs)
        while len(self.tabu_arcs) > self.tabu_tenure:
            self.tabu_arcs.pop()

    

    def cross_route_reinsert(self):
        best_move = None
        moves = []
        for from_route in self.sol.routes:
            for to_route in self.sol.routes:
                if from_route == to_route:
                    continue  

                for i in range(1, len(from_route.sequence_of_nodes) ): 
                    node = from_route.sequence_of_nodes[i]

                    for j in range(1, len(to_route.sequence_of_nodes)): 
                        move = RelocationMove(node, from_route, to_route, i, j, self.capacity, self.cost_matrix)
                        #print(move.move_cost)
                        if move.is_feasible:
                            if move.move_cost < 0:
                                moves.append(move)

        
        return moves

    
    def cross_route_swap(self):
        best_move = None
        moves = []
        for from_route in self.sol.routes:
            for to_route in self.sol.routes:
                if from_route == to_route:
                    continue

                for i in range(1, len(from_route.sequence_of_nodes) ):
                    for j in range(1, len(to_route.sequence_of_nodes) ):
                        move = SwapMove(from_route, to_route, i, j, self.cost_matrix, self.capacity)
                        if move.is_feasible:
                            if move.move_cost < 0:
                                moves.append(move)

        return moves

    def two_opt(self):
        moves = []

        best_move = None

        for route1 in self.sol.routes:
            for route2 in self.sol.routes:
                for i in range(1, len(route1.sequence_of_nodes) ):  
                    for j in range(1, len(route2.sequence_of_nodes) ):  
                        if route1 == route2:  
                            continue
                        
                        move = TwoOptMove(route1, route2, i, j, self.cost_matrix, self.capacity)

                        if move.is_feasible:
                            if move.move_cost < 0:
                                moves.append(move)

        return moves

    def swap_within_route(self):
        best_move = None
        moves = []

        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):  
                for j in range(i + 1, len(route.sequence_of_nodes) -1):  
                    move = InRouteSwapMove(route, i, j, self.cost_matrix)

                    if  move.move_cost < -1e-6:
                        if move.move_cost < 0:
                            moves.append(move)

        return moves


    def two_opt_within_route(self):
        moves = []
        best_move = None

        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):  
                for j in range(i + 2, len(route.sequence_of_nodes) -1):
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)

                    if move.move_cost < 0:
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
