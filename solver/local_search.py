from moves import RelocationMove, SwapMove, TwoOptMove, InRouteSwapMove, InRouteTwoOptMove
import math
import random
from heapq import heappush, heappop


class SolutionNode:
    def __init__(self, solution, move=None, parent=None, cost=None):
        
        self.solution = solution
        self.move = move
        self.parent = parent
        self.children = []
        self.cost = cost if cost is not None else solution.cost

    def add_child(self, child_node):
        self.children.append(child_node)


class LocalSearch:
    

    def __init__(self, solution, cost_matrix, capacity):
        
        self.sol= solution
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.initial_temperature = 100.0
        self.cooling_rate = 0.95
        self.min_temperature = 1e-3

    def local_search(self):
        
        max_iterations = 100
        iteration = 0

        root_node = SolutionNode(self.sol)
        current_node = root_node
        best_node = root_node

        search_methods = [
            self.cross_route_reinsert,
            self.cross_route_swap,
            self.two_opt,
            self.swap_within_route,
            self.two_opt_within_route,
        ]

        while iteration < max_iterations:
            best_move = None
            second_best_move = None

            for method in search_methods:
                move = method()
                
                if move:
                    move.type = method.__name__
                    if best_move is None or move.move_cost < best_move.move_cost:
                        second_best_move = best_move  
                        best_move = move
                    elif second_best_move is None or move.move_cost < second_best_move.move_cost:
                        second_best_move = move  

            if best_move:
                #print(f"Iteration {iteration + 1}: Best move type: {best_move.type}, Cost: {best_move.move_cost}")
                if second_best_move and random.random() < 0.2:
                    second_best_move.apply()
                    new_solution = self.sol
                    new_node = SolutionNode(new_solution, move=second_best_move, parent=current_node)
                    current_node.add_child(new_node)
                    current_node = new_node
                else:  
                    best_move.apply()
                    new_solution = self.sol
                    new_node = SolutionNode(new_solution, move=best_move, parent=current_node)
                    current_node.add_child(new_node)
                    current_node = new_node

                self.sol.update_solution_cost()

                if current_node.cost < best_node.cost:
                    best_node = current_node

            else:
                break
            #print(best_node.solution.cost)
            iteration += 1

        return best_node.solution





    def cross_route_reinsert(self):
        best_move = None

        for from_route in self.sol.routes:
            for to_route in self.sol.routes:
                if from_route == to_route:
                    continue  

                for i in range(1, len(from_route.sequence_of_nodes) - 1): 
                    node = from_route.sequence_of_nodes[i]

                    for j in range(1, len(to_route.sequence_of_nodes)): 
                        move = RelocationMove(node, from_route, to_route, i, j, self.capacity, self.cost_matrix)
                        #print(move.move_cost)
                        if (best_move is None or move.move_cost < best_move.move_cost) and move.move_cost < 0 and move.is_feasible:
                            best_move = move

        
        return best_move

    
    def cross_route_swap(self):
        best_move = None

        for from_route in self.sol.routes:
            for to_route in self.sol.routes:
                if from_route == to_route:
                    continue

                for i in range(1, len(from_route.sequence_of_nodes) - 1):
                    for j in range(1, len(to_route.sequence_of_nodes) - 1):
                        move = SwapMove(from_route, to_route, i, j, self.cost_matrix, self.capacity)
                        if move.is_feasible and move.move_cost < 0 and (best_move is None or move.move_cost < best_move.move_cost):
                            best_move = move

        return best_move

    def two_opt(self):
        
        best_move = None

        for route1 in self.sol.routes:
            for route2 in self.sol.routes:
                for i in range(1, len(route1.sequence_of_nodes) - 1):  
                    for j in range(1, len(route2.sequence_of_nodes) - 1):  
                        if route1 == route2:  
                            continue
                        
                        move = TwoOptMove(route1, route2, i, j, self.cost_matrix, self.capacity)

                        if move.is_feasible  and move.move_cost < 0 and (best_move is None or move.move_cost < best_move.move_cost):
                            best_move = move

        return best_move

    def swap_within_route(self):
        best_move = None

        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):  
                for j in range(i + 1, len(route.sequence_of_nodes) - 1):  
                    move = InRouteSwapMove(route, i, j, self.cost_matrix)

                    if  move.move_cost < -1e-6:
                        if best_move is None or move.move_cost < best_move.move_cost:
                            best_move = move

        return best_move


    def two_opt_within_route(self):
        
        best_move = None

        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):  
                for j in range(i + 2, len(route.sequence_of_nodes) - 1):
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)

                    if move.move_cost < 0:
                        if best_move is None or move.move_cost < best_move.move_cost:
                            best_move = move

        return best_move
