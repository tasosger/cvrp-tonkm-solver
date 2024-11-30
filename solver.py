from model import *
import sys

class Solution:
    def __init__(self):
        self.cost = 0.0 
        self.routes = []
    
class Saving:
    def __init__(self, n1, n2, sav):
        self.n1 = n1
        self.n2 = n2
        self.score = sav
    

class Solver:
    def __init__(self, m: VrpModel):
        self.all_nodes = m.all_nodes
        self.customers = m.customers
        self.depot = m.all_nodes[0]
        self.cost_matrix = m.dist_matrix
        self.capacity = m.capacity
        self.sol = None
    

    def solve(self):
        self.set_route_flag_false_for_all_node()
        self.clark_n_write()
        return self.sol 
    

    def set_route_flag_false_for_all_node(self):
        for c in self.customers:
            c.is_routed = False
    
    def calculate_total_cost(self, sol):
        total_cost = 0

        for route in sol.routes:
            nodes_sequence = route.sequence_of_nodes
            
            tot_dem = sum(n.demand for n in nodes_sequence)

            tot_load = 8 + tot_dem  

            route_cost = 0

            for i in range(len(nodes_sequence) - 1):
                from_node = nodes_sequence[i]
                to_node = nodes_sequence[i + 1]

                distance = self.cost_matrix[from_node.id][to_node.id]

                route_cost += distance * tot_load

                tot_load -= to_node.demand

            total_cost += route_cost

        return total_cost




    
    def update_route_cost_and_load(self, rt: Route):
        cumulative_load = 8  
        cost = 0
        for i in range(len(rt.sequence_of_nodes) - 1):
            a = rt.sequence_of_nodes[i]
            b = rt.sequence_of_nodes[i + 1]
            cumulative_load += a.demand
            cost += cumulative_load * self.cost_matrix[a.id][b.id]
            cumulative_load -= a.demand
        rt.cost = cost
        rt.load = sum(n.demand for n in rt.sequence_of_nodes)

    
    def clark_n_write(self):
        self.sol = self.create_initial_routes()
        savings: list = self.calculate_savings()
        savings.sort(key=lambda s: s.score, reverse=True)
        for i in range(0, len(savings)):
            sav = savings[i]
            n1 = sav.n1
            n2 = sav.n2
            rt1 = n1.route
            rt2 = n2.route
            

            if n1.route == n2.route:
                continue
            if self.not_first_or_last(rt1, n1) or self.not_first_or_last(rt2, n2):
                continue
            if rt1.load + rt2.load > self.capacity:
                continue
                
            self.merge_routes(n1, n2)

            self.sol.cost -= sav.score
            self.update_solution_cost()
            
    

    def create_initial_routes(self):
        s = Solution()
        for customer in self.customers:
            rt = Route(self.depot, self.capacity)
            customer.route = rt
            customer.position_in_route = 1
            rt.sequence_of_nodes.append(customer)
            rt.load = customer.demand
            rt.cost = (rt.load + 8) * self.cost_matrix[self.depot.id][customer.id] 
            s.routes.append(rt)
            s.cost += rt.cost
        return s
  
    

    def not_first_or_last(self, rt, n):
        if n.position_in_route != 1 and n.position_in_route != len(rt.sequence_of_nodes) - 1:
            return True
        return False
    
    def calculate_savings(self):
        savings = []
        for i in range(len(self.customers)):
            n1 = self.customers[i]
            for j in range(i + 1, len(self.customers)):
                n2 = self.customers[j]

                # Ensure positions are valid
                if n1.position_in_route < 1 or n2.position_in_route < 1:
                    continue

                # Calculate load at n1 and n2
                load_at_n1 = 8 + sum(node.demand for node in n1.route.sequence_of_nodes[:n1.position_in_route + 1])
                load_at_n2 = 8 + sum(node.demand for node in n2.route.sequence_of_nodes[:n2.position_in_route + 1])

                # Calculate cost of keeping routes separate
                cost_individual_n1 = (
                    load_at_n1 * self.cost_matrix[n1.route.sequence_of_nodes[n1.position_in_route - 1].id][n1.id]
                    if n1.position_in_route > 0 else 0
                )
                cost_individual_n2 = (
                    load_at_n2 * self.cost_matrix[n2.route.sequence_of_nodes[n2.position_in_route - 1].id][n2.id]
                    if n2.position_in_route > 0 else 0
                )
                cost_individual = cost_individual_n1 + cost_individual_n2

                # Calculate cost of merging the routes
                load_merged = load_at_n1 + sum(node.demand for node in n2.route.sequence_of_nodes[n2.position_in_route:])
                cost_direct = load_merged * self.cost_matrix[n1.id][n2.id]

                # Calculate savings
                score = cost_individual - cost_direct
                if score > 0:  # Only consider beneficial merges
                    savings.append(Saving(n1, n2, score))
        
        return savings




    

    def merge_routes(self, n1, n2):
        rt1 = n1.route
        rt2 = n2.route

        original_nodes = set(rt1.sequence_of_nodes + rt2.sequence_of_nodes)

        if n1.position_in_route == 1 and n2.position_in_route == len(rt2.sequence_of_nodes) - 1:
            rt1.sequence_of_nodes[1:1] = rt2.sequence_of_nodes[1:]
        elif n1.position_in_route == len(rt1.sequence_of_nodes) - 1 and n2.position_in_route == 1:
            rt1.sequence_of_nodes.extend(rt2.sequence_of_nodes[1:])
        else:
            return

        rt1.load += rt2.load

        for node in rt2.sequence_of_nodes:
            node.route = rt1
        
        self.sol.routes.remove(rt2)
        


        self.update_route_customers(rt1)


    def update_route_customers(self, rt):
        for i in range(1, len(rt.sequence_of_nodes) - 1):
            n = rt.sequence_of_nodes[i]
            n.position_in_route = i
    
    def update_solution_cost(self):
        self.sol.cost = self.calculate_total_cost(self.sol)
