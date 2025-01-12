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
        return self.sol
    


    
    