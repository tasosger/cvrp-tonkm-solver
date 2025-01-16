class Solution:
    def __init__(self, cost_matrix):
        self.cost = 0.0
        self.routes = []
        self.cost_matrix = cost_matrix
    
    def update_solution_cost(self):
        total_route_cost  = 0 
        for route in self.routes:
            total_route_cost += route.calculate_total_route_cost(self.cost_matrix)
        
        self.cost = total_route_cost