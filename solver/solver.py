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

        
        
    def solve(self):
        self.clark_n_write_helper = ClarkNWrite(self.depot, self.cost_matrix, self.capacity, self.customers, self.sol)
        self.sol = self.clark_n_write_helper.clark_n_write()
        self.local_search =  LocalSearch(solution=self.sol, cost_matrix=self.cost_matrix, capacity=self.capacity)
        self.sol = self.local_search.local_search()
        return self.sol
    


    
    