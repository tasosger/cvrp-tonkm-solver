import heapq
from model import *
import random

random.seed(1)


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

    def solve(self, num_iterations=1, top_k_savings=3, use_metaheuristic='sa',lns_removal_percentage=0.1, **kwargs):
        best_solution = None
        best_cost = float('inf')

        self.set_route_flag_false_for_all_node()

        for _ in range(num_iterations):
            self.clark_n_write()
            self.update_solution_cost()
            self.local_search()
            
            
            if self.sol.cost < best_cost:
                best_solution = self.deep_copy_solution(self.sol)
                best_cost = best_solution.cost
            self.set_route_flag_false_for_all_node()

        self.sol = best_solution
        return self.sol

    def large_neighborhood_search(self, removal_percentage=0.1, regret_k=2):
        num_customers_to_remove = int(len(self.customers) * removal_percentage)
        removed_customers = random.sample(self.customers, num_customers_to_remove)

        for customer in removed_customers:
            if customer.route and customer in customer.route.sequence_of_nodes:
                customer.route.sequence_of_nodes.remove(customer)
                customer.route.load -= customer.demand
                self.update_route_customers(customer.route)
            

        for customer in removed_customers:
            best_route = None
            best_position = None
            best_cost = float('inf')
            best_regret = float('-inf')

            for route in self.sol.routes:
                for position in range(1, len(route.sequence_of_nodes)):
                    temp_route = Route(self.depot, self.capacity)
                    temp_route.sequence_of_nodes = (
                        route.sequence_of_nodes[:position]
                        + [customer]
                        + route.sequence_of_nodes[position:]
                    )
                    temp_route.load = route.load + customer.demand

                    if temp_route.load <= self.capacity:
                        cost_increase = self.calculate_total_route_cost(temp_route) - self.calculate_total_route_cost(route)

                        regret = self.calculate_regret(customer, route, position, regret_k)
                        if regret > best_regret or (regret == best_regret and cost_increase < best_cost):
                            best_regret = regret
                            best_cost = cost_increase
                            best_route = route
                            best_position = position

            if best_route and best_position is not None:
                best_route.sequence_of_nodes.insert(best_position, customer)
                best_route.load += customer.demand
                self.update_route_customers(best_route)
            

        self.update_solution_cost()
    

    def edge_based_removal(self, removal_percentage):
        num_customers_to_remove = int(len(self.customers) * removal_percentage)
        edges = []
        for route in self.sol.routes:
            for i in range(1, len(route.sequence_of_nodes) - 1):
                n1 = route.sequence_of_nodes[i]
                n2 = route.sequence_of_nodes[i + 1]
                distance = self.cost_matrix[n1.id][n2.id]
                edges.append((distance, n1, n2))
        edges.sort(reverse=True)  

        removed_customers = set()
        for _, n1, n2 in edges:
            if len(removed_customers) >= num_customers_to_remove:
                break
            removed_customers.add(n1)
            removed_customers.add(n2)

        return list(removed_customers)


    def regret_k_reinsertion(self, removed_customers, k=2):
        for customer in removed_customers:
            best_positions = []
            for route in self.sol.routes:
                for pos in range(1, len(route.sequence_of_nodes)):
                    temp_route = Route(self.depot, self.capacity)
                    temp_route.sequence_of_nodes = (
                        route.sequence_of_nodes[:pos]
                        + [customer]
                        + route.sequence_of_nodes[pos:]
                    )
                    temp_route.load = route.load + customer.demand

                    if temp_route.load <= self.capacity:
                        cost_increase = self.calculate_total_route_cost(temp_route) - self.calculate_total_route_cost(route)
                        best_positions.append((cost_increase, route, pos))

            best_positions.sort()
            if len(best_positions) >= k:
                regret = sum(pos[0] for pos in best_positions[1:k]) - best_positions[0][0]
            else:
                regret = float('inf')  

            
            if best_positions:
                _, best_route, best_position = best_positions[0]
                best_route.sequence_of_nodes.insert(best_position, customer)
                best_route.load += customer.demand
                self.update_route_customers(best_route)



    def calculate_regret(self, customer, route, position, k):
        costs = []
        for pos in range(1, len(route.sequence_of_nodes)):
            temp_route = Route(self.depot, self.capacity)
            temp_route.sequence_of_nodes = (
                route.sequence_of_nodes[:pos]
                + [customer]
                + route.sequence_of_nodes[pos:]
            )
            temp_route.load = route.load + customer.demand

            if temp_route.load <= self.capacity:
                cost = self.calculate_total_route_cost(temp_route) - self.calculate_total_route_cost(route)
                costs.append(cost)

        costs = sorted(costs)
        if len(costs) < k:
            return float('-inf')  
        return sum(costs[:k]) - costs[0]



    def calculate_acceptance_probability(self, current_cost, new_cost, temperature):
        if new_cost < current_cost:
            return 1.0
        return math.exp((current_cost - new_cost) / temperature)

    def perturb_solution(self, solution):
        route = random.choice(solution.routes)
        if len(route.sequence_of_nodes) > 3:
            i, j = sorted(random.sample(range(1, len(route.sequence_of_nodes)), 2))
            route.sequence_of_nodes[i:j] = reversed(route.sequence_of_nodes[i:j])
            self.update_route_customers(route)


    
    def deep_copy_solution(self, solution):
        new_solution = Solution()
        new_solution.cost = solution.cost
        new_solution.routes = [self.copy_route(route) for route in solution.routes]
        return new_solution

    def copy_route(self, route):
        new_route = Route(self.depot, self.capacity)
        new_route.sequence_of_nodes = list(route.sequence_of_nodes)
        new_route.load = route.load
        new_route.cost = route.cost
        new_route.length = route.length
        return new_route



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

                score =  self.calculate_saving_score(n1,n2)
                if score > 0:  
                    sav = Saving(n1, n2, score)
                    heapq.heappush(self.savings_heap, (-score, sav))




    def clark_n_write(self):
        
        self.sol = self.create_initial_routes()

        self.calculate_savings_with_pq()

        while self.savings_heap:

            top_savings = [heapq.heappop(self.savings_heap) for _ in range(min(3, len(self.savings_heap)))]

            _, selected_saving = random.choice(top_savings)

            for saving in top_savings:
                if saving != (_, selected_saving):
                    heapq.heappush(self.savings_heap, saving)

            n1 = selected_saving.n1
            n2 = selected_saving.n2
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
            rt.length = self.cost_matrix[self.depot.id][customer.id]
        return s

    def not_first_or_last(self, rt, n):
        return not (n.position_in_route == 1 or n.position_in_route == len(rt.sequence_of_nodes) - 1)

    def merge_routes(self, n1, n2):
        rt1 = n1.route
        rt2 = n2.route

        if n1.position_in_route == 1 and n2.position_in_route == len(rt2.sequence_of_nodes) - 1:
            rt1.sequence_of_nodes[1:1] = rt2.sequence_of_nodes[1:]
            rt1.length += rt2.length - self.cost_matrix[self.depot.id][n1.id] + self.cost_matrix[n2.id][n1.id]
        elif n1.position_in_route == len(rt1.sequence_of_nodes) - 1 and n2.position_in_route == 1:
            rt1.sequence_of_nodes.extend(rt2.sequence_of_nodes[1:])
            rt1.length += rt2.length - self.cost_matrix[self.depot.id][n2.id] + self.cost_matrix[n1.id][n2.id]
            


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
                if route == updated_route:  
                    continue
                first_node = route.sequence_of_nodes[1]
                last_node = route.sequence_of_nodes[-1]

                if node1 == first_node or node1 == last_node:
                    continue  

                if node1 == updated_route.sequence_of_nodes[-1]:  
                    score = self.calculate_saving_score(node1, first_node)
                    if score > 0:
                        heapq.heappush(self.savings_heap, (-score, Saving(node1, first_node, score)))
                elif node1 == updated_route.sequence_of_nodes[1]:  
                    score = self.calculate_saving_score(last_node, node1)
                    if score > 0:
                        heapq.heappush(self.savings_heap, (-score, Saving(last_node, node1, score)))

        
    def calculate_saving_score(self, node1, node2):
        rt2 = node2.route
        rt1 = node1.route

        saving = (8 + rt2.load) * self.cost_matrix[self.depot.id][node2.id] - (rt2.load * rt1.length) - (rt2.load +8) * self.cost_matrix[node1.id][node2.id]
        return saving





    def update_route_customers(self, rt):
        for i, n in enumerate(rt.sequence_of_nodes):
            n.position_in_route = i

    def update_solution_cost(self):
        cost = self.calculate_total_cost(self.sol)
        total_route_cost  = 0 
        for route in self.sol.routes:
            total_route_cost += self.calculate_total_route_cost(route)
        if (total_route_cost != cost):
            exit(1)
        self.sol.cost = cost

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
    
    def calculate_route_length(self,rt):
        length = 0
        for i in range(1, len(rt.sequence_of_nodes)):
            length += self.cost_matrix[rt.sequence_of_nodes[i-1].id][rt.sequence_of_nodes[i].id]
        return length
    
    def cross_route_two_opt(self):
        best_gain = 0
        best_swap = None

        for route1 in self.sol.routes:
            for route2 in self.sol.routes:
                if route1 == route2:
                    continue  

                nodes1 = route1.sequence_of_nodes
                nodes2 = route2.sequence_of_nodes

                for i in range(1, len(nodes1) - 1):  
                    for j in range(1, len(nodes2) - 1):  
                        segment1 = nodes1[i:]
                        segment2 = nodes2[j:]

                        new_load1 = route1.load - sum(n.demand for n in segment1) + sum(n.demand for n in segment2)
                        new_load2 = route2.load - sum(n.demand for n in segment2) + sum(n.demand for n in segment1)

                        if new_load1 > self.capacity or new_load2 > self.capacity:
                            continue

                        initial_cost = self.calculate_total_route_cost(route1) + self.calculate_total_route_cost(route2)

                        new_nodes1 = nodes1[:i] + segment2
                        new_nodes2 = nodes2[:j] + segment1

                        temp_route1 = Route(self.depot, self.capacity)
                        temp_route1.sequence_of_nodes = new_nodes1
                        temp_route1.load = sum(n.demand for n in new_nodes1)

                        temp_route2 = Route(self.depot, self.capacity)
                        temp_route2.sequence_of_nodes = new_nodes2
                        temp_route2.load = sum(n.demand for n in new_nodes2)

                        new_cost = self.calculate_total_route_cost(temp_route1) + self.calculate_total_route_cost(temp_route2)

                        gain = initial_cost - new_cost
                        if gain > best_gain + 1e-2:  
                            best_gain = gain
                            best_swap = (route1, route2, i, j, new_nodes1, new_nodes2)

        if best_swap:
            route1, route2, i, j, new_nodes1, new_nodes2 = best_swap

            route1.sequence_of_nodes = new_nodes1
            route2.sequence_of_nodes = new_nodes2

            route1.load = sum(n.demand for n in new_nodes1)
            route2.load = sum(n.demand for n in new_nodes2)

            route1.cost = self.calculate_total_route_cost(route1)
            route2.cost = self.calculate_total_route_cost(route2)

            self.update_route_customers(route1)
            self.update_route_customers(route2)
            self.update_solution_cost()
            return True 

        return False



    def cross_route_swap(self):
        best_gain = 0
        best_swap = None

        for route1 in self.sol.routes:
            for route2 in self.sol.routes:
                if route1 == route2:
                    continue

                for i in range(1, len(route1.sequence_of_nodes) - 1): 
                    for j in range(1, len(route2.sequence_of_nodes) - 1):  
                        node1 = route1.sequence_of_nodes[i]
                        node2 = route2.sequence_of_nodes[j]

                        new_load1 = route1.load - node1.demand + node2.demand
                        new_load2 = route2.load - node2.demand + node1.demand
                        if new_load1 > self.capacity or new_load2 > self.capacity:
                            continue

                        initial_cost = (
                            self.calculate_total_route_cost(route1) +
                            self.calculate_total_route_cost(route2)
                        )

                        route1.sequence_of_nodes[i], route2.sequence_of_nodes[j] = node2, node1
                        
                        new_cost = (
                            self.calculate_total_route_cost(route1) +
                            self.calculate_total_route_cost(route2)
                        )

                        route1.sequence_of_nodes[i], route2.sequence_of_nodes[j] = node1, node2
                        

                        gain = initial_cost - new_cost
                        if gain > best_gain:
                            best_gain = gain
                            best_swap = (route1, route2, i, j)

        if best_swap:
            route1, route2, i, j = best_swap
            node1 = route1.sequence_of_nodes[i]
            node2 = route2.sequence_of_nodes[j]
            
            route1.sequence_of_nodes[i], route2.sequence_of_nodes[j] = node2, node1
            
            route1.load = route1.load - node1.demand + node2.demand
            route2.load = route2.load - node2.demand + node1.demand
            
            self.update_route_customers(route1)
            self.update_route_customers(route2)
            self.update_solution_cost()

            return True     
        return False

    

    
    def local_search(self):
        iteration = 0
        max_iterations = 100
        improved = True

        while iteration < max_iterations and improved:
            improved = False

            if self.cross_route_reinsert():
                improved = True

            if self.cross_route_swap():
                improved = True

            if self.cross_route_two_opt():
                improved = True

            for route in self.sol.routes:
                if self.reinsert(route):
                    improved = True

                if self.swap(route):
                    improved = True

                if self.two_opt(route):
                    improved = True

            self.update_solution_cost()

            iteration += 1
   
        
    
    

    def calculate_route_weight(self, route):
        total = 0
        for node in route.sequence_of_nodes:
            total += node.demand
        return total
    def reinsert(self, route):
    
        best_gain = 0
        best_move = None
        nodes = route.sequence_of_nodes
        initial_route_cost = self.calculate_total_route_cost(route)
        
        
        for i in range(1, len(nodes) - 1):
            node = nodes[i]
            
            for k in range(0, len(nodes) - 1):
                if k == i or k == i - 1:
                    continue
                    
                temp_nodes = nodes.copy()
                removed_node = temp_nodes.pop(i)
                temp_nodes.insert(k + 1, removed_node)
                
                temp_route = Route(self.depot, self.capacity)
                temp_route.sequence_of_nodes = temp_nodes
                temp_route.load = route.load
                
                new_cost = self.calculate_total_route_cost(temp_route)
                gain = initial_route_cost - new_cost
                
                
                if gain > best_gain + 1e-6:
                    best_gain = gain
                    best_move = (i, k + 1)
        
        if best_move:
            i, k = best_move
            node = nodes.pop(i)
            nodes.insert(k, node)
            
            new_cost = self.calculate_total_route_cost(route)
            actual_gain = initial_route_cost - new_cost
            
            return abs(actual_gain - best_gain) < 1e-6 and actual_gain > 1e-6
        
        return False

    def calculate_total_route_cost(self, route):
        nodes = route.sequence_of_nodes
        if not nodes:
            return 0
            
        cost = 0
        total_load = 8 + sum(n.demand for n in nodes)
        current_load = total_load
        
        for i in range(len(nodes) - 1):
            from_node = nodes[i]
            to_node = nodes[i + 1]
            distance = self.cost_matrix[from_node.id][to_node.id]
            cost += distance * current_load
            current_load -= to_node.demand
        
        return cost

    def two_opt(self, route):
        best_gain = 0
        best_temp_route = None 

        nodes = route.sequence_of_nodes
        for i in range(1, len(nodes) - 2):
            for j in range(i + 1, len(nodes) - 1):
                import copy
                temp_route = copy.deepcopy(route)

                temp_nodes = temp_route.sequence_of_nodes
                temp_nodes[i:j + 1] = reversed(temp_nodes[i:j + 1])

                temp_cost = self.calculate_total_route_cost(temp_route)

                gain = route.cost - temp_cost

                if gain > best_gain:
                    best_gain = gain
                    best_temp_route = temp_route

        if best_temp_route:
            route.sequence_of_nodes = best_temp_route.sequence_of_nodes
            route.cost = self.calculate_total_route_cost(route)
            route.length = self.calculate_route_length(route)
            self.update_route_customers(route)
            self.update_solution_cost()

            return True  
        return False 


    def swap(self, route):
        best_gain = 0
        best_i, best_j = -1, -1
        current_cost = route.cost
        nodes = route.sequence_of_nodes
        for i in range(1, len(nodes) - 1):
            for j in range(i + 1, len(nodes) - 1):
                if i == j:
                    continue
                temp_route = route.copy()
                temp_route.sequence_of_nodes[i], temp_route.sequence_of_nodes[j] = temp_route.sequence_of_nodes[j], temp_route.sequence_of_nodes[i]
                new_cost = self.calculate_total_route_cost(temp_route)
                gain = current_cost - new_cost
                if gain > best_gain:
                    best_gain, best_i, best_j = gain, i, j

        if best_gain > 0:
            nodes[best_i], nodes[best_j] = nodes[best_j], nodes[best_i]
            return True
        return False

    def reinsert(self, route):
        best_gain = 0
        best_i, best_k = -1, -1

        nodes = route.sequence_of_nodes
        total_demand = route.load
        for i in range(1, len(nodes) - 1):
            for k in range(1, len(nodes) - 1):
                if k == i or k == i - 1:
                    continue
               
                temp_route = route.copy()
                temp_nodes = temp_route.sequence_of_nodes
                node = temp_nodes.pop(i)
                temp_nodes.insert(k + 1, node)
                temp_cost = self.calculate_total_route_cost(temp_route)
                gain = route.cost - temp_cost
                if gain > best_gain + 1e-6: 
                    best_gain = gain
                    #print(best_gain)
                    best_i = i
                    best_k = k

        if best_gain > 0:
            node = nodes.pop(best_i)
            nodes.insert(best_k + 1, node)
            self.update_solution_cost()
            return True
        return False
    

    def calculate_total_route_cost(self, route):
        nodes_sequence = route.sequence_of_nodes
        tot_load = 8 + sum(n.demand for n in nodes_sequence)
        route_cost = 0
        for i in range(len(nodes_sequence) - 1):
            from_node = nodes_sequence[i]
            to_node = nodes_sequence[i + 1]
            distance = self.cost_matrix[from_node.id][to_node.id]
            route_cost += distance * tot_load
            tot_load -= to_node.demand
        return route_cost

    def cross_route_reinsert(self):

        best_gain = 0
        best_move = None

        for route_from in self.sol.routes:
            for route_to in self.sol.routes:
                if route_from == route_to:
                    continue  

                for i in range(1, len(route_from.sequence_of_nodes) - 1):
                    node = route_from.sequence_of_nodes[i]
                    node_demand = node.demand

                    if route_to.load + node_demand > self.capacity:
                        continue  

                    for j in range(1, len(route_to.sequence_of_nodes)): 
                        from_prev_id = route_from.sequence_of_nodes[i - 1].id
                        from_next_id = route_from.sequence_of_nodes[i + 1].id
                        to_prev_id = route_to.sequence_of_nodes[j - 1].id
                        to_next_id = route_to.sequence_of_nodes[j].id

                        prev_from_cost = self.cost_matrix[from_prev_id][node.id] + self.cost_matrix[node.id][from_next_id]
                        new_from_cost = self.cost_matrix[from_prev_id][from_next_id]

                        prev_to_cost = self.cost_matrix[to_prev_id][to_next_id]
                        new_to_cost = self.cost_matrix[to_prev_id][node.id] + self.cost_matrix[node.id][to_next_id]

                        
                        delta_cost = (new_from_cost - prev_from_cost) + (new_to_cost - prev_to_cost)

                        if delta_cost < -1e-6:
                            gain = -delta_cost
                            if gain > best_gain:
                                best_gain = gain
                                best_move = (node, route_from, route_to, i, j, node_demand)

        if best_move:
            node, route_from, route_to, i, j, node_demand = best_move

            route_from.sequence_of_nodes.pop(i)
            route_from.load -= node_demand

            route_to.sequence_of_nodes.insert(j, node)
            route_to.load += node_demand

            if route_to.load > self.capacity:
                raise ValueError(f"Capacity violation detected: Route load is {route_to.load}, exceeds {self.capacity}")

            self.update_route_customers(route_from)
            self.update_route_customers(route_to)
            self.update_solution_cost()

            return True  
        return False 

    def large_neighborhood_search_2(self, removal_percentage=0.2):
        num_customers_to_remove = int(len(self.customers) * removal_percentage)
        removed_customers = random.sample(self.customers, num_customers_to_remove)

        for customer in removed_customers:
            if customer.route:
                customer.route.sequence_of_nodes.remove(customer)
                customer.route.load -= customer.demand
                self.update_route_customers(customer.route)
        
        for customer in removed_customers:
            best_cost_increase = float('inf')
            best_route = None
            best_position = None

            for route in self.sol.routes:
                for position in range(1, len(route.sequence_of_nodes)):
                    temp_route = Route(self.depot, self.capacity)
                    temp_route.sequence_of_nodes = (
                        route.sequence_of_nodes[:position]
                        + [customer]
                        + route.sequence_of_nodes[position:]
                    )
                    temp_route.load = route.load + customer.demand

                    if temp_route.load <= self.capacity:
                        cost_increase = self.calculate_total_route_cost(temp_route) - self.calculate_total_route_cost(route)
                        if cost_increase < best_cost_increase:
                            best_cost_increase = cost_increase
                            best_route = route
                            best_position = position

            if best_route and best_position is not None:
                best_route.sequence_of_nodes.insert(best_position, customer)
                best_route.load += customer.demand
                self.update_route_customers(best_route)
        
        self.update_solution_cost()
    
    def simulated_annealing(self, initial_temperature=1, cooling_rate=0.95, max_iterations=10):
        current_solution = self.deep_copy_solution(self.sol)
        best_solution = self.deep_copy_solution(self.sol)
        current_temperature = initial_temperature

        for iteration in range(max_iterations):
            print(iteration)
            neighbor_solution = self.generate_neighbor_solution(current_solution)

            current_cost = self.calculate_total_cost(current_solution)
            neighbor_cost = self.calculate_total_cost(neighbor_solution)
            print(neighbor_cost)
            acceptance_probability = self.calculate_acceptance_probability(current_cost, neighbor_cost, current_temperature)
            if random.random() < acceptance_probability:
                current_solution = neighbor_solution
                if neighbor_cost < self.calculate_total_cost(best_solution):
                    best_solution = self.deep_copy_solution(neighbor_solution)

            current_temperature *= cooling_rate

            if current_temperature < 1e-6:
                break

        self.sol = best_solution
        return best_solution


    def generate_neighbor_solution(self, solution):
        neighbor_solution = self.deep_copy_solution(solution)
        move_types = [self.cross_route_reinsert, self.cross_route_swap, self.cross_route_two_opt]
        move = random.choice(move_types)

        if move == self.cross_route_reinsert:
            self.cross_route_reinsert()
        elif move == self.cross_route_swap:
            self.cross_route_swap()
        elif move == self.cross_route_two_opt:
            self.cross_route_two_opt()

        return neighbor_solution


    def tabu_search(self, tabu_tenure=10, max_iterations=10):
        current_solution = self.deep_copy_solution(self.sol)
        best_solution = self.deep_copy_solution(self.sol)
        tabu_list = []
        max_tabu_size = tabu_tenure

        for iteration in range(max_iterations):
            neighbors = self.generate_all_neighbors(current_solution)

            best_neighbor = None
            best_neighbor_cost = float('inf')

            for neighbor in neighbors:
                neighbor_cost = self.calculate_total_cost(neighbor)
                if neighbor not in tabu_list and neighbor_cost < best_neighbor_cost:
                    best_neighbor = neighbor
                    best_neighbor_cost = neighbor_cost

            if best_neighbor:
                current_solution = best_neighbor
                tabu_list.append(best_neighbor)
                if len(tabu_list) > max_tabu_size:
                    tabu_list.pop(0)

                if best_neighbor_cost < self.calculate_total_cost(best_solution):
                    best_solution = self.deep_copy_solution(best_neighbor)

        self.sol = best_solution
        return best_solution


    def generate_all_neighbors(self, solution):
        
        neighbors = []

        if self.cross_route_reinsert():
            neighbors.append(self.deep_copy_solution(solution))
        if self.cross_route_swap():
            neighbors.append(self.deep_copy_solution(solution))
        if self.cross_route_two_opt():
            neighbors.append(self.deep_copy_solution(solution))

        for route in solution.routes:
            if self.reinsert(route):
                neighbors.append(self.deep_copy_solution(solution))
            if self.swap(route):
                neighbors.append(self.deep_copy_solution(solution))
            if self.two_opt(route):
                neighbors.append(self.deep_copy_solution(solution))

        return neighbors
    
    def hybrid_lns_metaheuristic(self, removal_percentage=0.2, regret_k=3, initial_temperature=1000, cooling_rate=0.95, max_iterations=1000):
        self.large_neighborhood_search(removal_percentage, regret_k)

        self.simulated_annealing(initial_temperature, cooling_rate, max_iterations)

        self.local_search()

        return self.sol

