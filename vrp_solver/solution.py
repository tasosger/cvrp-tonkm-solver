"""A candidate solution: a set of routes and their total cost."""


class Solution:
    def __init__(self, cost_matrix):
        self.cost = 0.0
        self.routes = []
        self.cost_matrix = cost_matrix

    def update_solution_cost(self):
        self.cost = sum(route.calculate_total_route_cost(self.cost_matrix) for route in self.routes)
