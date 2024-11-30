import heapq
from model import *


class Solution:
    def __init__(self):
        self.cost = 0.0
        self.routes = []


class Saving:
    def __init__(self, n1, n2, sav):
        self.n1 = n1
        self.n2 = n2
        self.score = sav
    
    def __lt__(self, other):
        return self.score > other.score


class Solver:
    def __init__(self, m: VrpModel):
        self.all_nodes = m.all_nodes
        self.customers = m.customers
        self.depot = m.all_nodes[0]
        self.cost_matrix = m.dist_matrix
        self.capacity = m.capacity
        self.sol = None
        self.savings_heap = []  

    def solve(self):
        self.set_route_flag_false_for_all_node()
        self.clark_n_write()
        self.update_solution_cost()
        return self.sol

    def set_route_flag_false_for_all_node(self):
        for c in self.customers:
            c.is_routed = False

    def calculate_savings_with_pq(self):
        self.savings_heap = []
        for i in range(len(self.customers)):
            n1 = self.customers[i]
            for j in range(i + 1, len(self.customers)):
                n2 = self.customers[j]
                if n1.demand + n2.demand > self.capacity:  
                    continue

                distance = self.cost_matrix[n1.id][n2.id]
                

                load_at_n1 = 8 + sum(node.demand for node in n1.route.sequence_of_nodes[:n1.position_in_route + 1])
                load_at_n2 = 8 + sum(node.demand for node in n2.route.sequence_of_nodes[:n2.position_in_route + 1])

                cost_individual = (
                    load_at_n1 * self.cost_matrix[n1.route.sequence_of_nodes[n1.position_in_route - 1].id][n1.id] +
                    load_at_n2 * self.cost_matrix[n2.route.sequence_of_nodes[n2.position_in_route - 1].id][n2.id]
                )

                load_merged = load_at_n1 + sum(node.demand for node in n2.route.sequence_of_nodes[n2.position_in_route:])
                cost_direct = load_merged * self.cost_matrix[n1.id][n2.id]

                score = cost_individual - cost_direct
                if score > 0:  
                    sav = Saving(n1, n2, score)
                    heapq.heappush(self.savings_heap, (-score, sav))



    def clark_n_write(self):
        self.sol = self.create_initial_routes()
        self.calculate_savings_with_pq()
        
        while self.savings_heap:
            _, sav = heapq.heappop(self.savings_heap)
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
        return not (n.position_in_route == 1 or n.position_in_route == len(rt.sequence_of_nodes) - 1)

    def merge_routes(self, n1, n2):
        rt1 = n1.route
        rt2 = n2.route

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

        self.update_solution_cost()

        self.recalculate_savings_for_route(rt1)

    def recalculate_savings_for_route(self, updated_route):
        new_edge_nodes = {updated_route.sequence_of_nodes[1], updated_route.sequence_of_nodes[-1]}

        merged_nodes = set(updated_route.sequence_of_nodes)

        self.savings_heap = [
            (priority, sav) for priority, sav in self.savings_heap
            if sav.n1 not in merged_nodes and sav.n2 not in merged_nodes
        ]
        heapq.heapify(self.savings_heap)  
        
        for node1 in new_edge_nodes:
            if node1.id == 0:  
                continue
            for route in self.sol.routes:
                other_edge_nodes = [route.sequence_of_nodes[1], route.sequence_of_nodes[-1]]

                for node2 in other_edge_nodes:
                    if node1 == node2 or node1.route == node2.route:
                        continue  

                    load_at_n1 = 8 + sum(n.demand for n in node1.route.sequence_of_nodes[:node1.position_in_route + 1])
                    load_at_n2 = 8 + sum(n.demand for n in node2.route.sequence_of_nodes[:node2.position_in_route + 1])

                    cost_individual = (
                        load_at_n1 * self.cost_matrix[node1.route.sequence_of_nodes[node1.position_in_route - 1].id][node1.id] +
                        load_at_n2 * self.cost_matrix[node2.route.sequence_of_nodes[node2.position_in_route - 1].id][node2.id]
                    )

                    load_merged = load_at_n1 + sum(n.demand for n in node2.route.sequence_of_nodes[node2.position_in_route:])
                    cost_direct = load_merged * self.cost_matrix[node1.id][node2.id]

                    score = cost_individual - cost_direct
                    if score > 0:  
                        heapq.heappush(self.savings_heap, (-score, Saving(node1, node2, score)))
        




    def update_route_customers(self, rt):
        for i, n in enumerate(rt.sequence_of_nodes):
            n.position_in_route = i

    def update_solution_cost(self):
        self.sol.cost = self.calculate_total_cost(self.sol)

    def calculate_total_cost(self, sol):
        total_cost = 0
        for route in sol.routes:
            nodes_sequence = route.sequence_of_nodes
            tot_load = 8 + sum(n.demand for n in nodes_sequence)
            route_cost = 0
            for i in range(len(nodes_sequence) - 1):
                from_node = nodes_sequence[i]
                to_node = nodes_sequence[i + 1]
                distance = self.cost_matrix[from_node.id][to_node.id]
                route_cost += distance * tot_load
                tot_load -= to_node.demand
            total_cost += route_cost
        return total_cost
