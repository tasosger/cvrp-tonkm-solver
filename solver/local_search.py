from moves import RelocationMove, SwapMove, TwoOptMove, InRouteSwapMove, InRouteTwoOptMove

class LocalSearch:
    

    def __init__(self, solution, cost_matrix, capacity):
        
        self.sol= solution
        self.cost_matrix = cost_matrix
        self.capacity = capacity

    def local_search(self):
        max_iterations = 20
        iteration = 0

        search_methods = [
            self.cross_route_reinsert,
            self.cross_route_swap,
            self.two_opt_within_route,
            self.swap_within_route
        ]

        while iteration < max_iterations:
            improved = False
            overall_best = None

            for method in search_methods:
                best_move = method()
                if best_move and best_move.move_cost < 0:
                    if overall_best is None or best_move.move_cost + 0.1< overall_best.move_cost:
                        overall_best = best_move

            if overall_best:
                overall_best.apply()
                self.sol.update_solution_cost()
                print(f"Updated solution cost: {self.sol.cost}")
                improved = True

            if not improved:
                break  

            iteration += 1

        print(f"Local search completed after {iteration} iterations.")
        return self.sol



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
                        if move.move_cost < 0 and (best_move is None or move.move_cost < best_move.move_cost) and move.is_feasible:
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

                        if move.is_feasible and move.move_cost < 0 and (best_move is None or move.move_cost < best_move.move_cost):
                            best_move = move

        return best_move

    def swap_within_route(self):
        best_move = None

        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):  
                for j in range(i + 1, len(route.sequence_of_nodes) - 1):  
                    move = InRouteSwapMove(route, i, j, self.cost_matrix)

                    if  move.move_cost < 0:
                        if best_move is None or move.move_cost < best_move.move_cost:
                            best_move = move

        return best_move


    def two_opt_within_route(self):
        
        best_move = None

        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 2):  
                for j in range(i + 1, len(route.sequence_of_nodes) - 1):
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)

                    if move.move_cost < 0:
                        if best_move is None or move.move_cost < best_move.move_cost:
                            best_move = move

        return best_move
