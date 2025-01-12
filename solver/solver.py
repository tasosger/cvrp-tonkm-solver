import heapq
from model import *
import random
random.seed(1)
from clark_n_write import ClarkNWrite
from local_search import LocalSearch





class Solver:
    def __init__(self, model):
        self.all_nodes = model.all_nodes
        self.customers = model.customers
        self.depot = model.all_nodes[0]
        self.cost_matrix = model.dist_matrix
        self.capacity = model.capacity
        self.sol = None

        
        
    def solve(self, num_iterations = 1):
        best_sol = None
        for _ in range(num_iterations):
            temp_sol = None
            self.clark_n_write_helper = ClarkNWrite(self.depot, self.cost_matrix, self.capacity, self.customers, self.sol)
            temp_sol = self.clark_n_write_helper.clark_n_write()
            self.local_search =  LocalSearch(solution=temp_sol, cost_matrix=self.cost_matrix, capacity=self.capacity)
            temp_sol = self.local_search.local_search()
            if not best_sol or (best_sol.cost > temp_sol.cost):
                best_sol = temp_sol
        self.sol  = best_sol
        TOLERANCE = 1e-6
        for route_index, route in enumerate(self.sol.routes):
            # Dynamically recalculate prefix loads and distances
            recalculated_loads = []
            recalculated_distances = []
            
            cumulative_load = 0
            cumulative_distance = 0

            for i in range(len(route.sequence_of_nodes)):
                node = route.sequence_of_nodes[i]
                cumulative_load += node.demand
                recalculated_loads.append(cumulative_load)

                if i > 0:  # Compute distance from previous node
                    prev_node = route.sequence_of_nodes[i - 1]
                    cumulative_distance += self.cost_matrix[prev_node.id][node.id]
                recalculated_distances.append(cumulative_distance)

            # Compare recalculated loads and distances with stored values
            if abs(recalculated_loads[i] - route.prefix_loads[i]) > TOLERANCE:
                print(f"Prefix load mismatch in route {route_index}:")
                print(f"Expected: {route.prefix_loads}")
                print(f"Recalculated: {recalculated_loads}")
                exit(1)

            if abs(recalculated_distances[i] - route.prefix_distances[i]) > TOLERANCE:
                print(f"Prefix distance mismatch in route {route_index}:")
                print(f"Expected: {route.prefix_distances}")
                print(f"Recalculated: {recalculated_distances}")
                exit(1)

        print("All prefix loads and distances are correct!")


                

            
        return self.sol
    


    
    