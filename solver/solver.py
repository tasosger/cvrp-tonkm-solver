import heapq
from model import *
import random
random.seed(1)
from clark_n_write import ClarkNWrite






class Solver:
    def __init__(self, model):
        self.all_nodes = model.all_nodes
        self.customers = model.customers
        self.depot = model.all_nodes[0]
        self.cost_matrix = model.dist_matrix
        self.capacity = model.capacity
        self.sol = None

        self.clark_n_write_helper = ClarkNWrite(self.depot, self.cost_matrix, self.capacity, self.customers, self.sol)

    def solve(self):
        self.sol = self.clark_n_write_helper.clark_n_write()
        return self.sol
    


    
    