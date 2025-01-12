class RelocationMove:
    def __init__(self, node, from_route, to_route, from_index, to_index, capacity, cost_matrix):
        
        self.node = node
        self.from_route = from_route
        self.to_route = to_route
        self.from_index = from_index
        self.to_index = to_index
        self.cost_matrix = cost_matrix

        self.is_feasible = (
            (self.from_route.load - self.node.demand >= 0) and
            (self.to_route.load + self.node.demand <= capacity)
        )

        self.move_cost = self.calculate_move_cost_temp() if self.is_feasible else float('inf')

    def apply(self):
        
        if not self.is_feasible:
            raise ValueError("Cannot apply an infeasible move.")

        self.from_route.sequence_of_nodes.pop(self.from_index)

        self.to_route.sequence_of_nodes.insert(self.to_index, self.node)
        
        #print("applied")
        self.update_route_loads()
        self.update_route_distances()

    def update_route_loads(self):
        self.from_route.prefix_loads = self._recalculate_prefix_loads(self.from_route)
        self.to_route.prefix_loads = self._recalculate_prefix_loads(self.to_route)

        self.from_route.load = self.from_route.prefix_loads[-1]
        self.to_route.load = self.to_route.prefix_loads[-1]
    
    def update_route_distances(self):
        self.from_route.prefix_distances = self._recalculate_prefix_distances(self.from_route)
        self.to_route.prefix_distances = self._recalculate_prefix_distances(self.to_route)

    def calculate_move_cost(self):
        
        from_prev_id = (
            self.from_route.sequence_of_nodes[self.from_index - 1].id
            if self.from_index > 0 else self.from_route.sequence_of_nodes[0].id
        )
        from_next_id = (
            self.from_route.sequence_of_nodes[self.from_index + 1].id
            if self.from_index + 1 < len(self.from_route.sequence_of_nodes)
            else self.from_route.sequence_of_nodes[0].id
        )

        
        to_prev_id = (
            self.to_route.sequence_of_nodes[self.to_index - 1].id
            if self.to_index > 0 else self.to_route.sequence_of_nodes[0].id
        )
        to_next_id = (
            self.to_route.sequence_of_nodes[self.to_index].id
            if self.to_index < len(self.to_route.sequence_of_nodes)
            else self.to_route.sequence_of_nodes[0].id
        )

        load_after_n = self.from_route.load - self.from_route.prefix_loads[self.from_index]
        load_after_n_to = self.to_route.load - self.to_route.prefix_loads[self.to_index - 1]
        
        cost_effect_from_route =   (load_after_n) * (self.cost_matrix[from_prev_id][from_next_id] - self.cost_matrix[from_prev_id][self.node.id] - 
                                                        self.cost_matrix[self.node.id][from_next_id])  - self.node.demand * self.from_route.prefix_distances[self.from_index]
        cost_effect_to_route =   (load_after_n_to) * (self.cost_matrix[to_prev_id][self.node.id] + self.cost_matrix[self.node.id][to_next_id] - 
                                                        self.cost_matrix[to_prev_id][to_next_id]) + self.node.demand * (self.to_route.prefix_distances[self.to_index - 1] + self.cost_matrix[to_prev_id][self.node.id])
       
        total_cost_change = cost_effect_to_route + cost_effect_from_route

        return total_cost_change


    def calculate_move_cost_temp(self):
        
        temp_from_route = self.from_route.copy()
        temp_to_route = self.to_route.copy()

        removed_node = temp_from_route.sequence_of_nodes.pop(self.from_index)
       

        temp_to_route.sequence_of_nodes.insert(self.to_index, removed_node)
        

        from_route_cost = temp_from_route.calculate_total_route_cost( self.cost_matrix)
        to_route_cost = temp_to_route.calculate_total_route_cost(self.cost_matrix)

        original_cost = self.from_route.calculate_total_route_cost( self.cost_matrix) + self.to_route.calculate_total_route_cost( self.cost_matrix)
        new_cost = from_route_cost + to_route_cost

        return new_cost - original_cost

    
    def _recalculate_prefix_loads(self,route):
        cumulative_load = 0
        prefix_loads = []
        for node in route.sequence_of_nodes:
            cumulative_load += node.demand
            prefix_loads.append(cumulative_load)
        return prefix_loads
    
    
    def _recalculate_prefix_distances(self,route):
        cumulative_dist = 0
        prefix_dists = [0]  

        for i in range(1, len(route.sequence_of_nodes)):
            prev_node = route.sequence_of_nodes[i - 1]
            current_node = route.sequence_of_nodes[i]
            cumulative_dist += self.cost_matrix[prev_node.id][current_node.id]
            prefix_dists.append(cumulative_dist)

        return prefix_dists


class SwapMove:
    

    def __init__(self, route1, route2, index1, index2, cost_matrix, capacity):
        self.route1 = route1
        self.route2 = route2
        self.index1 = index1
        self.index2 = index2
        self.cost_matrix = cost_matrix
        self.node1 = route1.sequence_of_nodes[index1]
        self.node2 = route2.sequence_of_nodes[index2]
        self.is_feasible = (
            (route1.load - self.node1.demand + self.node2.demand <= capacity) and
            (route2.load - self.node2.demand + self.node1.demand <= capacity)
        )
        self.move_cost = self.calculate_move_cost()

    def apply(self):
        """
        Apply the swap move, swapping the nodes in the respective routes.
        """
        if not self.is_feasible:
            raise ValueError("Cannot apply an infeasible move.")
        
        # Perform the swap
        self.route1.sequence_of_nodes[self.index1], self.route2.sequence_of_nodes[self.index2] = \
            self.route2.sequence_of_nodes[self.index2], self.route1.sequence_of_nodes[self.index1]
        
        # Update loads and distances
        self.update_route_loads()
        self.update_route_distances()

    def update_route_loads(self):
        self.route1.prefix_loads = self._recalculate_prefix_loads(self.route1)
        self.route2.prefix_loads = self._recalculate_prefix_loads(self.route2)

        self.route1.load = self.route1.prefix_loads[-1]
        self.route2.load = self.route2.prefix_loads[-1]

    def calculate_move_cost(self):
        
        temp_route1 = self.route1.copy()
        temp_route2 = self.route2.copy()

        temp_route1.sequence_of_nodes[self.index1], temp_route2.sequence_of_nodes[self.index2] = \
            temp_route2.sequence_of_nodes[self.index2], temp_route1.sequence_of_nodes[self.index1]

        cost_before = (
            self.route1.calculate_total_route_cost(self.cost_matrix) +
            self.route2.calculate_total_route_cost(self.cost_matrix)
        )

        cost_after = (
            temp_route1.calculate_total_route_cost(self.cost_matrix) +
            temp_route2.calculate_total_route_cost(self.cost_matrix)
        )

        return cost_after - cost_before
    
    def update_route_distances(self):
        self.route1.prefix_distances = self._recalculate_prefix_distances(self.route1)
        self.route2.prefix_distances = self._recalculate_prefix_distances(self.route2)


    def _recalculate_prefix_loads(self,route):
        cumulative_load = 0
        prefix_loads = []
        for node in route.sequence_of_nodes:
            cumulative_load += node.demand
            prefix_loads.append(cumulative_load)
        return prefix_loads
    
    
    def _recalculate_prefix_distances(self,route):
        cumulative_dist = 0
        prefix_dists = [0]  

        for i in range(1, len(route.sequence_of_nodes)):
            prev_node = route.sequence_of_nodes[i - 1]
            current_node = route.sequence_of_nodes[i]
            cumulative_dist += self.cost_matrix[prev_node.id][current_node.id]
            prefix_dists.append(cumulative_dist)

        return prefix_dists



class TwoOptMove:
    

    def __init__(self, route1, route2, i, j, cost_matrix, capacity):
        
        self.route1 = route1
        self.route2 = route2
        self.i = i
        self.j = j
        self.cost_matrix = cost_matrix

        if route1 == route2:
            load1_after = (
                sum(node.demand for node in route1.sequence_of_nodes[:i]) +
                sum(node.demand for node in route1.sequence_of_nodes[j:])
            )
            self.is_feasible = load1_after <= capacity
        else:
            load1_after = (
                route1.load - sum(node.demand for node in route1.sequence_of_nodes[i:]) +
                sum(node.demand for node in route2.sequence_of_nodes[j:])
            )
            load2_after = (
                route2.load - sum(node.demand for node in route2.sequence_of_nodes[j:]) +
                sum(node.demand for node in route1.sequence_of_nodes[i:])
            )
            self.is_feasible = load1_after <= capacity and load2_after <= capacity

        self.move_cost = self.calculate_move_cost()

    def apply(self):
        
        if not self.is_feasible:
            raise ValueError("Cannot apply an infeasible move.")

        segment1 = self.route1.sequence_of_nodes[self.i:]
        segment2 = self.route2.sequence_of_nodes[self.j:]

        
        self.route1.sequence_of_nodes = self.route1.sequence_of_nodes[:self.i] + segment2
        self.route2.sequence_of_nodes = self.route2.sequence_of_nodes[:self.j] + segment1

        self.route1.load = sum(node.demand for node in self.route1.sequence_of_nodes)
        self.route2.load = sum(node.demand for node in self.route2.sequence_of_nodes)

        self.route1.cost = self.route1.calculate_total_route_cost(self.cost_matrix)
        self.route2.cost = self.route2.calculate_total_route_cost(self.cost_matrix)

        self.update_route_loads()
        self.update_route_distances()

    def update_route_loads(self):
        self.route1.prefix_loads = self._recalculate_prefix_loads(self.route1)
        self.route2.prefix_loads = self._recalculate_prefix_loads(self.route2)

        self.route1.load = self.route1.prefix_loads[-1]
        self.route2.load = self.route2.prefix_loads[-1]

    def calculate_move_cost(self):
        
        temp_route1 = self.route1.copy()
        temp_route2 = self.route2.copy()

        segment1 = temp_route1.sequence_of_nodes[self.i:]
        segment2 = temp_route2.sequence_of_nodes[self.j:]

        temp_route1.sequence_of_nodes = temp_route1.sequence_of_nodes[:self.i] + segment2
        temp_route2.sequence_of_nodes = temp_route2.sequence_of_nodes[:self.j] + segment1

        cost_before = (
            self.route1.calculate_total_route_cost(self.cost_matrix) +
            self.route2.calculate_total_route_cost(self.cost_matrix)
        )

        cost_after = (
            temp_route1.calculate_total_route_cost(self.cost_matrix) +
            temp_route2.calculate_total_route_cost(self.cost_matrix)
        )

        return cost_after - cost_before



    def update_route_distances(self):
        self.route1.prefix_distances = self._recalculate_prefix_distances(self.route1)
        self.route2.prefix_distances = self._recalculate_prefix_distances(self.route2)


    def _recalculate_prefix_loads(self,route):
        cumulative_load = 0
        prefix_loads = []
        for node in route.sequence_of_nodes:
            cumulative_load += node.demand
            prefix_loads.append(cumulative_load)
        return prefix_loads
    
    
    def _recalculate_prefix_distances(self,route):
        cumulative_dist = 0
        prefix_dists = [0]  

        for i in range(1, len(route.sequence_of_nodes)):
            prev_node = route.sequence_of_nodes[i - 1]
            current_node = route.sequence_of_nodes[i]
            cumulative_dist += self.cost_matrix[prev_node.id][current_node.id]
            prefix_dists.append(cumulative_dist)

        return prefix_dists


class InRouteTwoOptMove:
    def __init__(self, route, i, j, cost_matrix):
        
        self.route = route
        self.i = i
        self.j = j
        self.cost_matrix = cost_matrix

        self.move_cost = self.calculate_move_cost()

    def calculate_move_cost(self):
        temp_route = self.route.copy()

        temp_route.sequence_of_nodes[self.i:self.j + 1] = reversed(temp_route.sequence_of_nodes[self.i:self.j + 1])

        cost_before = self.route.calculate_total_route_cost(self.cost_matrix)
        cost_after = temp_route.calculate_total_route_cost(self.cost_matrix)

        return cost_after - cost_before

    def apply(self):
        
        self.route.sequence_of_nodes[self.i:self.j + 1] = reversed(self.route.sequence_of_nodes[self.i:self.j + 1])
        self.route.cost = self.route.calculate_total_route_cost(self.cost_matrix)

        self.route.prefix_loads = self._recalculate_prefix_loads(self.route)
        self.route.prefix_distances = self._recalculate_prefix_distances(self.route)

    
    def _recalculate_prefix_loads(self,route):
        cumulative_load = 0
        prefix_loads = []
        for node in route.sequence_of_nodes:
            cumulative_load += node.demand
            prefix_loads.append(cumulative_load)
        return prefix_loads

    
    def _recalculate_prefix_distances(self,route):
        cumulative_dist = 0
        prefix_distances = [0]  
        for i in range(1, len(route.sequence_of_nodes)):
            prev_node = route.sequence_of_nodes[i - 1]
            current_node = route.sequence_of_nodes[i]
            cumulative_dist += self.cost_matrix[prev_node.id][current_node.id]
            prefix_distances.append(cumulative_dist)
        return prefix_distances

class InRouteSwapMove:
    def __init__(self, route, index1, index2, cost_matrix):
        self.route = route
        self.index1 = index1
        self.index2 = index2
        self.cost_matrix = cost_matrix

        self.move_cost = self.calculate_move_cost()

    def calculate_move_cost(self):
        temp_route = self.route.copy()

        temp_route.sequence_of_nodes[self.index1], temp_route.sequence_of_nodes[self.index2] = \
            temp_route.sequence_of_nodes[self.index2], temp_route.sequence_of_nodes[self.index1]

        cost_before = self.route.calculate_total_route_cost(self.cost_matrix)
        cost_after = temp_route.calculate_total_route_cost(self.cost_matrix)

        return cost_after - cost_before



    def apply(self):
        
        self.route.sequence_of_nodes[self.index1], self.route.sequence_of_nodes[self.index2] = \
            self.route.sequence_of_nodes[self.index2], self.route.sequence_of_nodes[self.index1]

        self.route.cost = self.route.calculate_total_route_cost(self.cost_matrix)
        self.route.prefix_loads = self._recalculate_prefix_loads(self.route)
        self.route.prefix_distances = self._recalculate_prefix_distances(self.route)

    def _recalculate_prefix_loads(self,route):
        cumulative_load = 0
        prefix_loads = []
        for node in route.sequence_of_nodes:
            cumulative_load += node.demand
            prefix_loads.append(cumulative_load)
        return prefix_loads

    def _recalculate_prefix_distances(self,route):
        cumulative_dist = 0
        prefix_distances = [0]  
        for i in range(1, len(route.sequence_of_nodes)):
            prev_node = route.sequence_of_nodes[i - 1]
            current_node = route.sequence_of_nodes[i]
            cumulative_dist += self.cost_matrix[prev_node.id][current_node.id]
            prefix_distances.append(cumulative_dist)
        return prefix_distances