import random
from local_search import LocalSearch
from moves import RelocationMove, SwapMove, TwoOptMove, InRouteSwapMove, InRouteTwoOptMove
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

    def generate_neighbors(self):
        neighbors = []

        neighbors.extend(
            self.cross_route_reinsert()
        )
        neighbors.extend(
            self.cross_route_swap()
        )
        neighbors.extend(
            self.two_opt()
        )
        neighbors.extend(
            self.two_opt_within_route()
        )
        neighbors.extend(
            self.swap_within_route()
        )
                
        
        return neighbors

    def update_tabu_arcs(self, arcs):
        """
        Add arcs to the tabu list and maintain the list within the tabu tenure.
        """
        self.tabu_arcs.update(arcs)
        while len(self.tabu_arcs) > self.tabu_tenure:
            self.tabu_arcs.pop()

    def search(self, max_iterations, max_no_improvement=5):
        iteration = 0
        no_improvement = 0

        while iteration < max_iterations:
            neighbors = self.generate_neighbors()

            if not neighbors:
                print("No feasible neighbors found. Terminating search.")
                break

            best_candidate = None
            for move in neighbors:
                # Check tabu arcs for the move
                

                if  move.move_cost < 0 and (best_candidate is None or move.move_cost < best_candidate.move_cost):
                    best_candidate = move                
                
                

            if not best_candidate:
                print("No valid candidate found. Terminating search.")
                break
            print(best_candidate.move_cost)
            # Apply the best move
            best_candidate.apply()
            print(self.current_solution.cost)
            # Update the current solution
            self.sol.update_solution_cost()

            # Print progress
            print(f"Iteration {iteration}: Best Cost = {self.best_solution.cost}, Current Cost = {self.sol.cost}")

            # Update the best solution if improved
            

            

            iteration += 1

        return self.sol


    

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
                for j in range(i + 1, len(route.sequence_of_nodes) - 1):  
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
                for j in range(i + 2, len(route.sequence_of_nodes) - 1):
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)

                    if move.move_cost < 0:
                        moves.append(move)

        return moves
