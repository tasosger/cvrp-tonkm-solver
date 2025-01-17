import copy
import random
from moves import RelocationMove, SwapMove, TwoOptMove, InRouteSwapMove, InRouteTwoOptMove, InRouteReinsertMove
from tabu_search import TabuSearch
from local_search import LocalSearch

class VNS:
    def __init__(self, initial_solution, cost_matrix, capacity, max_iterations=1, max_neighborhood_size=1):
        self.best_solution = initial_solution
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.max_iterations = max_iterations
        self.max_neighborhood_size = max_neighborhood_size

    def vns(self):
        iteration = 0
        while iteration < self.max_iterations:
            print(iteration)
            k = 1  
            while k <= self.max_neighborhood_size:
                perturbed_solution = self.shaking(self.best_solution, k)

                improved_solution = self.local_search(perturbed_solution)

                if improved_solution.cost < self.best_solution.cost:
                    self.best_solution = improved_solution
                    k += 1 #so vns is stopped after this due to time constraints
                else:
                    k += 1 

            iteration += 1
            print(f"Iteration {iteration}: Best Cost = {self.best_solution.cost}")
   
        return self.best_solution

    def shaking(self, solution, k):
        perturbed_solution = copy.deepcopy(solution)

        if k == 1:
            for _ in range(3): 
                from_route = random.choice(perturbed_solution.routes)
                to_route = random.choice(perturbed_solution.routes)
                if len(from_route.sequence_of_nodes) > 2:
                    from_index = random.randint(1, len(from_route.sequence_of_nodes) - 1)
                    to_index = random.randint(1, len(to_route.sequence_of_nodes))
                    node = from_route.sequence_of_nodes[from_index]
                    move = RelocationMove(node, from_route, to_route, from_index, to_index, self.capacity, self.cost_matrix)
                    if move.is_feasible:
                        move.apply()
                        break

        elif k == 2:
            for _ in range(3):  
                route1 = random.choice(perturbed_solution.routes)
                route2 = random.choice(perturbed_solution.routes)
                if len(route1.sequence_of_nodes) > 1 and len(route2.sequence_of_nodes) > 1:
                    index1 = random.randint(1, len(route1.sequence_of_nodes) - 1)
                    index2 = random.randint(1, len(route2.sequence_of_nodes) - 1)
                    move = SwapMove(route1, route2, index1, index2, self.cost_matrix, self.capacity)
                    if move.is_feasible:
                        move.apply()
                        break

        elif k == 3:
            for _ in range(3):  
                route1 = random.choice(perturbed_solution.routes)
                route2 = random.choice(perturbed_solution.routes)
                if len(route1.sequence_of_nodes) > 1 and len(route2.sequence_of_nodes) > 1:
                    i = random.randint(1, len(route1.sequence_of_nodes) - 1)
                    j = random.randint(1, len(route2.sequence_of_nodes) - 1)
                    move = TwoOptMove(route1, route2, i, j, self.cost_matrix, self.capacity)
                    if move.is_feasible:
                        move.apply()
                        break

        elif k == 4:
            for _ in range(3):  
                route = random.choice(perturbed_solution.routes)
                if len(route.sequence_of_nodes) > 2:
                    index1, index2 = sorted(random.sample(range(1, len(route.sequence_of_nodes)), 2))
                    move = InRouteSwapMove(route, index1, index2, self.cost_matrix)
                    move.apply()
                    break

        elif k == 5:
            for _ in range(3): 
                route = random.choice(perturbed_solution.routes)
                if len(route.sequence_of_nodes) > 3:
                    i, j = sorted(random.sample(range(1, len(route.sequence_of_nodes) - 1), 2))
                    move = InRouteTwoOptMove(route, i, j, self.cost_matrix)
                    move.apply()
                    break

        elif k == 6:
            for _ in range(3):  
                route = random.choice(perturbed_solution.routes)
                if len(route.sequence_of_nodes) > 2:
                    from_index = random.randint(1, len(route.sequence_of_nodes) - 1)
                    to_index = random.randint(1, len(route.sequence_of_nodes))
                    move = InRouteReinsertMove(route, from_index, to_index, self.cost_matrix, self.capacity)
                    move.apply()
                    break

        return perturbed_solution

    def local_search(self, solution):
        tabu_search = TabuSearch(solution, self.cost_matrix, self.capacity)
        return tabu_search.tabu_search()
