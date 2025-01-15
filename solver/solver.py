import heapq
from model import *
import random
random.seed(1)
from clark_n_write import ClarkNWrite
from local_search import LocalSearch
from tabu_search import TabuSearch
from vns import VNS
from rvns import RVNS
from mcts import TabuSearch

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


    def solve_tabu(self, num_iterations=1, tabu_search_iterations=1000, tabu_tenure=30):
        best_sol = None
        self.clark_n_write_helper = ClarkNWrite(self.depot, self.cost_matrix, self.capacity, self.customers, self.sol)
        for _ in range(num_iterations):
            initial_solution = self.clark_n_write_helper.clark_n_write()

            tabu_search = TabuSearch(
                initial_solution=initial_solution,
                cost_matrix=self.cost_matrix,
                capacity=self.capacity,
                tabu_tenure=tabu_tenure,
                max_iterations=tabu_search_iterations
            )
            tabu_solution = tabu_search.search()

            if not best_sol or tabu_solution.cost < best_sol.cost:
                best_sol = tabu_solution

        self.sol = best_sol
        return self.sol
    

    def solve_vns(self, num_iterations=1, vns_iterations=1000, tabu_tenure=30):
        best_sol = None
        self.clark_n_write_helper = ClarkNWrite(self.depot, self.cost_matrix, self.capacity, self.customers, self.sol)

        for _ in range(num_iterations):
            initial_solution = self.clark_n_write_helper.clark_n_write()

            vns_solver = VNS(
                initial_solution=initial_solution,
                cost_matrix=self.cost_matrix,
                capacity=self.capacity
            )
            vns_solution = vns_solver.search(max_iterations=vns_iterations)

            if not best_sol or vns_solution.cost < best_sol.cost:
                best_sol = vns_solution

        self.sol = best_sol
        return self.sol
    
    def solve_rvns(self, num_iterations=1, vns_iterations=1000, tabu_tenure=30):
        best_sol = None
        self.clark_n_write_helper = ClarkNWrite(self.depot, self.cost_matrix, self.capacity, self.customers, self.sol)

        for _ in range(num_iterations):
            initial_solution = self.clark_n_write_helper.clark_n_write()

            vns_solver = RVNS(
                initial_solution=initial_solution,
                cost_matrix=self.cost_matrix,
                capacity=self.capacity
            )
            vns_solution = vns_solver.search(max_iterations=vns_iterations)

            if not best_sol or vns_solution.cost < best_sol.cost:
                best_sol = vns_solution

        self.sol = best_sol
        return self.sol
    

    def solve_monte_carlo(self, num_iterations=1, tabu_search_iterations=1000, tabu_tenure=30):
        best_sol = None
        self.clark_n_write_helper = ClarkNWrite(self.depot, self.cost_matrix, self.capacity, self.customers, self.sol)

        for _ in range(num_iterations):
            initial_solution = self.clark_n_write_helper.clark_n_write()

            tabu_search = TabuSearch(
                initial_solution=initial_solution,
                cost_matrix=self.cost_matrix,
                capacity=self.capacity,
                tabu_tenure=tabu_tenure,
                max_iterations=tabu_search_iterations
            )
            tabu_solution = tabu_search.search()

            if not best_sol or tabu_solution.cost < best_sol.cost:
                best_sol = tabu_solution

        self.sol = best_sol
        return self.sol




    
    