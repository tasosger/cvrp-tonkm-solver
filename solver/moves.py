import copy

class RelocationMove:
    def __init__(self, node, from_route, to_route, from_index, to_index, capacity, cost_matrix):
        
        self.node = node
        self.from_route = from_route
        self.to_route = to_route
        self.from_index = from_index
        self.to_index = to_index
        self.cost_matrix = cost_matrix
        self.affected_nodes = self.calculate_affected_nodes()
        self.is_feasible = (
            (self.from_route.load - self.node.demand >= 0) and
            (self.to_route.load + self.node.demand <= capacity)
        )
        self.affected_arcs = self.calculate_affected_arcs()
        self.move_cost = self.calculate_move_cost() if self.is_feasible else float('inf')

    def apply(self):
        
        if not self.is_feasible:
            raise ValueError("Cannot apply an infeasible move.")

        self.from_route.sequence_of_nodes.pop(self.from_index)

        self.to_route.sequence_of_nodes.insert(self.to_index, self.node)
        
        #print("applied")
        self.update_route_loads()
        self.update_route_distances()
        self.from_route.cost = self.from_route.calculate_total_route_cost(self.cost_matrix)
        self.to_route.cost = self.to_route.calculate_total_route_cost(self.cost_matrix)


    def update_route_loads(self):
        self.from_route.prefix_loads = self._recalculate_prefix_loads(self.from_route)
        self.to_route.prefix_loads = self._recalculate_prefix_loads(self.to_route)

        self.from_route.load = self.from_route.prefix_loads[-1]
        self.to_route.load = self.to_route.prefix_loads[-1]
    
    def update_route_distances(self):
        self.from_route.prefix_distances = self._recalculate_prefix_distances(self.from_route)
        self.to_route.prefix_distances = self._recalculate_prefix_distances(self.to_route)


    def calculate_affected_arcs(self):
        affected_arcs = []

        # Arcs removed from the from_route
        if self.from_index > 0:
            affected_arcs.append((self.from_route.sequence_of_nodes[self.from_index - 1].id, self.node.id))
        if self.from_index < len(self.from_route.sequence_of_nodes) - 1:
            affected_arcs.append((self.node.id, self.from_route.sequence_of_nodes[self.from_index + 1].id))

        # Arc added to reconnect the from_route
        if self.from_index > 0 and self.from_index < len(self.from_route.sequence_of_nodes) - 1:
            affected_arcs.append((self.from_route.sequence_of_nodes[self.from_index - 1].id,
                                  self.from_route.sequence_of_nodes[self.from_index + 1].id))


        # Arcs removed from the to_route
        if self.to_index > 0:
            affected_arcs.append((self.to_route.sequence_of_nodes[self.to_index - 1].id,
                                  self.to_route.sequence_of_nodes[self.to_index].id))

        # Arc added to the to_route
        if self.to_index > 0:
            affected_arcs.append((self.to_route.sequence_of_nodes[self.to_index - 1].id, self.node.id))
        if self.to_index < len(self.to_route.sequence_of_nodes):
            affected_arcs.append((self.node.id, self.to_route.sequence_of_nodes[self.to_index].id))

        return affected_arcs

    def calculate_affected_nodes(self):
        affected_nodes = set()

        # Nodes in from_route
        if self.from_index > 0:
            affected_nodes.add(self.from_route.sequence_of_nodes[self.from_index - 1].id)
        affected_nodes.add(self.node.id)
        if self.from_index < len(self.from_route.sequence_of_nodes) - 1:
            affected_nodes.add(self.from_route.sequence_of_nodes[self.from_index + 1].id)

        # Nodes in to_route
        if self.to_index > 0:
            affected_nodes.add(self.to_route.sequence_of_nodes[self.to_index - 1].id)
        affected_nodes.add(self.node.id)
        if self.to_index < len(self.to_route.sequence_of_nodes):
            affected_nodes.add(self.to_route.sequence_of_nodes[self.to_index].id)

        return list(affected_nodes)


    def calculate_move_cost(self):
        
        
        from_prev_id = (
            self.from_route.sequence_of_nodes[self.from_index - 1].id
            if self.from_index > 0 else self.from_route.sequence_of_nodes[0].id
        )

        from_next_id = (
            self.from_route.sequence_of_nodes[self.from_index + 1].id
            if self.from_index +1  < len(self.from_route.sequence_of_nodes)
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
        self.from_route.cost = self.from_route.calculate_total_route_cost(self.cost_matrix)
        self.to_route.cost = self.to_route.calculate_total_route_cost(self.cost_matrix)

        load_after_n = self.from_route.load - self.from_route.prefix_loads[self.from_index]
        load_after_n_to = self.to_route.load - self.to_route.prefix_loads[self.to_index-1]
        if from_next_id !=0:
            cost_effect_from_route =   (load_after_n + 8) * (self.cost_matrix[from_prev_id][from_next_id] - self.cost_matrix[from_prev_id][self.node.id] - 
                                                            self.cost_matrix[self.node.id][from_next_id])  - self.node.demand * self.from_route.prefix_distances[self.from_index]
        else:
            cost_effect_from_route =   - self.node.demand * self.from_route.prefix_distances[self.from_index] - 8 * self.cost_matrix[from_prev_id][self.node.id]
        if to_next_id !=0:
            cost_effect_to_route =   (load_after_n_to + 8) * (self.cost_matrix[to_prev_id][self.node.id] + self.cost_matrix[self.node.id][to_next_id] - 
                                                            self.cost_matrix[to_prev_id][to_next_id]) + self.node.demand * (self.to_route.prefix_distances[self.to_index - 1] + self.cost_matrix[to_prev_id][self.node.id])
        else:
            cost_effect_to_route =  self.node.demand * (self.to_route.prefix_distances[self.to_index - 1] + self.cost_matrix[to_prev_id][self.node.id]) +8 *self.cost_matrix[to_prev_id][self.node.id]
        total_cost_change = cost_effect_to_route + cost_effect_from_route
        
        return total_cost_change

    def calculate_move_cost_temp(self):
        
        temp_from_route = self.from_route.copy()
        temp_to_route = self.to_route.copy()

        removed_node = temp_from_route.sequence_of_nodes.pop(self.from_index)

        temp_to_route.sequence_of_nodes.insert(self.to_index, removed_node)

        temp_from_route.update_route_customers()
        temp_to_route.update_route_customers()

        from_cost_before = self.from_route.calculate_total_route_cost(self.cost_matrix)
        from_cost_after = temp_from_route.calculate_total_route_cost(self.cost_matrix)

        to_cost_before = self.to_route.calculate_total_route_cost(self.cost_matrix)
        to_cost_after = temp_to_route.calculate_total_route_cost(self.cost_matrix)

        return (from_cost_after - from_cost_before) + (to_cost_after - to_cost_before)
    
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
        self.affected_arcs = self.calculate_affected_arcs()
        self.affected_nodes = self.calculate_affected_nodes()

    def calculate_affected_nodes(self):
        affected_nodes = set()

        # Nodes in route1
        if self.index1 > 0:
            affected_nodes.add(self.route1.sequence_of_nodes[self.index1 - 1].id)
        affected_nodes.add(self.node1.id)
        if self.index1 < len(self.route1.sequence_of_nodes) - 1:
            affected_nodes.add(self.route1.sequence_of_nodes[self.index1 + 1].id)

        # Nodes in route2
        if self.index2 > 0:
            affected_nodes.add(self.route2.sequence_of_nodes[self.index2 - 1].id)
        affected_nodes.add(self.node2.id)
        if self.index2 < len(self.route2.sequence_of_nodes) - 1:
            affected_nodes.add(self.route2.sequence_of_nodes[self.index2 + 1].id)

        return list(affected_nodes)

    def calculate_move_cost_temp(self):
        node1 = self.route1.sequence_of_nodes[self.index1]
        node2 = self.route2.sequence_of_nodes[self.index2]

        from_prev_id1 = self.route1.sequence_of_nodes[self.index1 - 1].id \
            if self.index1 > 0 else self.route1.sequence_of_nodes[0].id
        from_next_id1 = self.route1.sequence_of_nodes[self.index1 + 1].id \
            if self.index1 + 1 < len(self.route1.sequence_of_nodes) else self.route1.sequence_of_nodes[-1].id

        to_prev_id2 = self.route2.sequence_of_nodes[self.index2 - 1].id \
            if self.index2 > 0 else self.route2.sequence_of_nodes[0].id
        to_next_id2 = self.route2.sequence_of_nodes[self.index2 + 1].id \
            if self.index2 + 1 < len(self.route2.sequence_of_nodes) else self.route2.sequence_of_nodes[-1].id

        cost1_before = self.cost_matrix[from_prev_id1][node1.id] + self.cost_matrix[node1.id][from_next_id1]
        cost1_after = self.cost_matrix[from_prev_id1][node2.id] + self.cost_matrix[node2.id][from_next_id1]

        cost2_before = self.cost_matrix[to_prev_id2][node2.id] + self.cost_matrix[node2.id][to_next_id2]
        cost2_after = self.cost_matrix[to_prev_id2][node1.id] + self.cost_matrix[node1.id][to_next_id2]

        return (cost1_after - cost1_before) + (cost2_after - cost2_before)
    def calculate_affected_arcs(self):
        affected_arcs = []

        # Arcs removed from route1
        if self.index1 > 0:
            affected_arcs.append((self.route1.sequence_of_nodes[self.index1 - 1].id, self.node1.id))
        if self.index1 < len(self.route1.sequence_of_nodes) - 1:
            affected_arcs.append((self.node1.id, self.route1.sequence_of_nodes[self.index1 + 1].id))

        # Arcs added to route1
        if self.index1 > 0:
            affected_arcs.append((self.route1.sequence_of_nodes[self.index1 - 1].id, self.node2.id))
        if self.index1 < len(self.route1.sequence_of_nodes) - 1:
            affected_arcs.append((self.node2.id, self.route1.sequence_of_nodes[self.index1 + 1].id))

        # Arcs removed from route2
        if self.index2 > 0:
            affected_arcs.append((self.route2.sequence_of_nodes[self.index2 - 1].id, self.node2.id))
        if self.index2 < len(self.route2.sequence_of_nodes) - 1:
            affected_arcs.append((self.node2.id, self.route2.sequence_of_nodes[self.index2 + 1].id))

        # Arcs added to route2
        if self.index2 > 0:
            affected_arcs.append((self.route2.sequence_of_nodes[self.index2 - 1].id, self.node1.id))
        if self.index2 < len(self.route2.sequence_of_nodes) - 1:
            affected_arcs.append((self.node1.id, self.route2.sequence_of_nodes[self.index2 + 1].id))

        return affected_arcs


    def apply(self):

        if not self.is_feasible:
            raise ValueError("Cannot apply an infeasible move.")
        
        self.route1.sequence_of_nodes[self.index1], self.route2.sequence_of_nodes[self.index2] = \
            self.route2.sequence_of_nodes[self.index2], self.route1.sequence_of_nodes[self.index1]
        
        self.update_route_loads()
        self.update_route_distances()

    def update_route_loads(self):
        self.route1.prefix_loads = self._recalculate_prefix_loads(self.route1)
        self.route2.prefix_loads = self._recalculate_prefix_loads(self.route2)

        self.route1.load = self.route1.prefix_loads[-1]
        self.route2.load = self.route2.prefix_loads[-1]

    def calculate_move_cost_temp(self):
        
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



    def calculate_move_cost(self):
        prev_id_1 = (
            self.route1.sequence_of_nodes[self.index1 - 1].id
        )

        if self.index1 != len(self.route1.sequence_of_nodes)-1:
            next_id_1 = (
                self.route1.sequence_of_nodes[self.index1 + 1].id
            )
        else:
            next_id_1= 0

        
        prev_id_2 = (
            self.route2.sequence_of_nodes[self.index2 - 1].id
        )
        if self.index2 != len(self.route2.sequence_of_nodes)-1:
            next_id_2 = (
                self.route2.sequence_of_nodes[self.index2+1].id
            )         
        else:
            next_id_2= 0

        load_after_1 = self.route1.load - self.route1.prefix_loads[self.index1 ]
        load_after_2 = self.route2.load - self.route2.prefix_loads[self.index2 ]

        cost_effect_from_route_1 =   (load_after_1+ 8) * (self.cost_matrix[prev_id_1][self.node2.id] + self.cost_matrix[self.node2.id][next_id_1] - self.cost_matrix[prev_id_1][self.node1.id] - 
                                                        self.cost_matrix[self.node1.id][next_id_1])  - self.node1.demand * self.route1.prefix_distances[self.index1] + self.node2.demand*(self.route1.prefix_distances[self.index1 - 1] + self.cost_matrix[prev_id_1][self.node2.id])
        cost_effect_from_route_2 =   (load_after_2+ 8) * (self.cost_matrix[prev_id_2][self.node1.id] + self.cost_matrix[self.node1.id][next_id_2] - self.cost_matrix[prev_id_2][self.node2.id] - 
                                                        self.cost_matrix[self.node2.id][next_id_2])  - self.node2.demand * self.route2.prefix_distances[self.index2] + self.node1.demand*(self.route2.prefix_distances[self.index2 - 1] + self.cost_matrix[prev_id_2][self.node1.id])
       


        if abs(cost_effect_from_route_1 + cost_effect_from_route_2 - self.calculate_move_cost_temp()) > 0:
                
                return self.calculate_move_cost_temp()
        return cost_effect_from_route_1 + cost_effect_from_route_2

        
    
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
        self.affected_arcs = self.calculate_affected_arcs()
        self.move_cost = self.calculate_move_cost()
        self.affected_nodes = self.calculate_affected_nodes()
    

    def calculate_move_cost_temp(self):
        nodes = self.route.sequence_of_nodes

        prev_id = nodes[self.i - 1].id if self.i > 0 else nodes[0].id
        next_id = nodes[self.j + 1].id if self.j + 1 < len(nodes) else nodes[-1].id

        prev_cost = self.cost_matrix[prev_id][nodes[self.i].id] + self.cost_matrix[nodes[self.j].id][next_id]
        new_cost = self.cost_matrix[prev_id][nodes[self.j].id] + self.cost_matrix[nodes[self.i].id][next_id]

        return new_cost - prev_cost


    def calculate_affected_nodes(self):
        affected_nodes = set()

        # Nodes in route1
        if self.i > 0:
            affected_nodes.add(self.route1.sequence_of_nodes[self.i - 1].id)
        for idx in range(self.i, len(self.route1.sequence_of_nodes)):
            affected_nodes.add(self.route1.sequence_of_nodes[idx].id)

        # Nodes in route2
        if self.j > 0:
            affected_nodes.add(self.route2.sequence_of_nodes[self.j - 1].id)
        for idx in range(self.j, len(self.route2.sequence_of_nodes)):
            affected_nodes.add(self.route2.sequence_of_nodes[idx].id)

        return list(affected_nodes)


    def calculate_affected_arcs(self):
        affected_arcs = []

        if self.i > 0:
            affected_arcs.append((self.route1.sequence_of_nodes[self.i - 1].id, self.route1.sequence_of_nodes[self.i].id))
        if self.i < len(self.route1.sequence_of_nodes) - 1:
            affected_arcs.append((self.route1.sequence_of_nodes[self.i].id, self.route1.sequence_of_nodes[self.i + 1].id))

        if self.i > 0 and self.i < len(self.route1.sequence_of_nodes) - 1:
            affected_arcs.append((self.route1.sequence_of_nodes[self.i - 1].id, self.route1.sequence_of_nodes[self.i + 1].id))

        if self.j > 0:
            affected_arcs.append((self.route2.sequence_of_nodes[self.j - 1].id, self.route2.sequence_of_nodes[self.j].id))
        if self.j < len(self.route2.sequence_of_nodes) - 1:
            affected_arcs.append((self.route2.sequence_of_nodes[self.j].id, self.route2.sequence_of_nodes[self.j + 1].id))

        if self.j > 0 and self.j < len(self.route2.sequence_of_nodes) - 1:
            affected_arcs.append((self.route2.sequence_of_nodes[self.j - 1].id, self.route2.sequence_of_nodes[self.j + 1].id))

        return affected_arcs



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
        node_i = self.route1.sequence_of_nodes[self.i]
        node_before_i = self.route1.sequence_of_nodes[self.i - 1]
        node_j = self.route2.sequence_of_nodes[self.j]
        node_before_j = self.route2.sequence_of_nodes[self.j - 1]

        cost_route_1 = (self.route2.load - self.route2.prefix_loads[self.j -1] + 8) * (self.route1.prefix_distances[self.i-1]+ 
                                                                                   self.cost_matrix[node_before_i.id][node_j.id]) - \
                                                                                    (self.route1.load - self.route1.prefix_loads[self.i-1] +8) * \
                                                                                    (self.route1.prefix_distances[self.i])
        cost_route_2 = (self.route1.load - self.route1.prefix_loads[self.i -1] + 8) * (self.route2.prefix_distances[self.j-1]+ 
                                                                                   self.cost_matrix[node_before_j.id][node_i.id]) - \
                                                                                    (self.route2.load - self.route2.prefix_loads[self.j-1] + 8 ) * \
                                                                                    (self.route2.prefix_distances[self.j])    
        
        if abs(cost_route_1 + cost_route_2   - self.calculate_move_cost_temp()) > 0:
                
                return self.calculate_move_cost_temp()
        return cost_route_1 + cost_route_2     
        
    

    def calculate_move_cost_temp(self):
        
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
        self.affected_nodes = self.calculate_affected_nodes()
        self.move_cost = self.calculate_move_cost()
        self.affected_arcs = self.calculate_affected_arcs()


    def calculate_affected_nodes(self):
        affected_nodes = set()

        # Nodes in route
        if self.i > 0:
            affected_nodes.add(self.route.sequence_of_nodes[self.i - 1].id)
        for idx in range(self.i, self.j + 1):
            affected_nodes.add(self.route.sequence_of_nodes[idx].id)
        if self.j < len(self.route.sequence_of_nodes) - 1:
            affected_nodes.add(self.route.sequence_of_nodes[self.j + 1].id)

        return list(affected_nodes)


    def calculate_affected_arcs(self):
        affected_arcs = []

        # Arcs removed within the route
        if self.i > 0:
            affected_arcs.append((self.route.sequence_of_nodes[self.i - 1].id, self.route.sequence_of_nodes[self.i].id))
        if self.j < len(self.route.sequence_of_nodes) - 1:
            affected_arcs.append((self.route.sequence_of_nodes[self.j].id, self.route.sequence_of_nodes[self.j + 1].id))

        # Arcs added after the move
        if self.i > 0:
            affected_arcs.append((self.route.sequence_of_nodes[self.i - 1].id, self.route.sequence_of_nodes[self.j].id))
        if self.j < len(self.route.sequence_of_nodes) - 1:
            affected_arcs.append((self.route.sequence_of_nodes[self.i].id, self.route.sequence_of_nodes[self.j + 1].id))

        return affected_arcs




    def calculate_move_cost(self):
        node_i = self.route.sequence_of_nodes[self.i]
        node_j = self.route.sequence_of_nodes[self.j]  
        node_before_i = self.route.sequence_of_nodes[self.i - 1]      
        node_after_j = self.route.sequence_of_nodes[self.j + 1] if self.j  < len(self.route.sequence_of_nodes) -1 else self.route.sequence_of_nodes[0]
        distances =  self.cost_matrix
        load_after_j = self.route.load - self.route.prefix_loads[self.j]
        cost =  (load_after_j +8) * (distances[node_before_i.id][node_j.id] + distances[node_i.id][node_after_j.id] - distances[node_before_i.id][node_i.id] - distances[node_j.id][node_after_j.id])
        for n in range(self.i+1,self.j):
            curr_node = self.route.sequence_of_nodes[n]
            cost += curr_node.demand * (distances[node_before_i.id][node_j.id] - distances[node_before_i.id][node_i.id])
            cost += curr_node.demand * ((self.route.prefix_distances[self.j] - self.route.prefix_distances[n]) - (self.route.prefix_distances[n] - self.route.prefix_distances[self.i]) )
        cost += node_i.demand * (self.route.prefix_distances[self.j] - self.route.prefix_distances[self.i] + distances[node_before_i.id][node_j.id] - distances[node_before_i.id][node_i.id] )
        cost += node_j.demand * (distances[node_before_i.id][node_j.id] - (self.route.prefix_distances[self.j] - self.route.prefix_distances[self.i]) -distances[node_before_i.id][node_i.id] )
        
        if abs(cost - self.calculate_move_cost_temp()) > 1e-6:
                return self.calculate_move_cost_temp()
                pass
        return cost
    
    def calculate_move_cost_temp(self):
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
        self.affected_nodes = self.calculate_affected_nodes()
        self.move_cost = self.calculate_move_cost()
        self.affected_arcs = self.calculate_affected_arcs()


    def calculate_affected_nodes(self):
        affected_nodes = set()

        # Add the swapped nodes
        affected_nodes.add(self.route.sequence_of_nodes[self.index1].id)
        affected_nodes.add(self.route.sequence_of_nodes[self.index2].id)

        # Add neighbors of swapped nodes
        if self.index1 > 0:
            affected_nodes.add(self.route.sequence_of_nodes[self.index1 - 1].id)
        if self.index1 < len(self.route.sequence_of_nodes) - 1:
            affected_nodes.add(self.route.sequence_of_nodes[self.index1 + 1].id)

        if self.index2 > 0:
            affected_nodes.add(self.route.sequence_of_nodes[self.index2 - 1].id)
        if self.index2 < len(self.route.sequence_of_nodes) - 1:
            affected_nodes.add(self.route.sequence_of_nodes[self.index2 + 1].id)

        return list(affected_nodes)


    def calculate_affected_arcs(self):
        affected_arcs = []

        # Arcs removed due to the swap
        if self.index1 > 0:
            affected_arcs.append((self.route.sequence_of_nodes[self.index1 - 1].id, self.route.sequence_of_nodes[self.index1].id))
        if self.index1 < len(self.route.sequence_of_nodes) - 1:
            affected_arcs.append((self.route.sequence_of_nodes[self.index1].id, self.route.sequence_of_nodes[self.index1 + 1].id))
        if self.index2 > 0:
            affected_arcs.append((self.route.sequence_of_nodes[self.index2 - 1].id, self.route.sequence_of_nodes[self.index2].id))
        if self.index2 < len(self.route.sequence_of_nodes) - 1:
            affected_arcs.append((self.route.sequence_of_nodes[self.index2].id, self.route.sequence_of_nodes[self.index2 + 1].id))

        # Arcs added due to the swap
        if self.index1 > 0:
            affected_arcs.append((self.route.sequence_of_nodes[self.index1 - 1].id, self.route.sequence_of_nodes[self.index2].id))
        if self.index1 < len(self.route.sequence_of_nodes) - 1:
            affected_arcs.append((self.route.sequence_of_nodes[self.index2].id, self.route.sequence_of_nodes[self.index1 + 1].id))
        if self.index2 > 0:
            affected_arcs.append((self.route.sequence_of_nodes[self.index2 - 1].id, self.route.sequence_of_nodes[self.index1].id))
        if self.index2 < len(self.route.sequence_of_nodes) - 1:
            affected_arcs.append((self.route.sequence_of_nodes[self.index1].id, self.route.sequence_of_nodes[self.index2 + 1].id))

        return affected_arcs


    def calculate_move_cost_temp(self):
        temp_route = self.route.copy()

        temp_route.sequence_of_nodes[self.index1], temp_route.sequence_of_nodes[self.index2] = \
            temp_route.sequence_of_nodes[self.index2], temp_route.sequence_of_nodes[self.index1]

        cost_before = self.route.calculate_total_route_cost(self.cost_matrix)
        cost_after = temp_route.calculate_total_route_cost(self.cost_matrix)

        return cost_after - cost_before

    def calculate_move_cost(self):
        node1 = self.route.sequence_of_nodes[self.index1]
        node_before_1 = self.route.sequence_of_nodes[self.index1 -1]
        node_after_1 = self.route.sequence_of_nodes[self.index1 + 1]
        node2 = self.route.sequence_of_nodes[self.index2]
        node_before_2 = self.route.sequence_of_nodes[self.index2 -1]
        node_after_2 = self.route.sequence_of_nodes[self.index2 + 1] if self.index2 < len(self.route.sequence_of_nodes) -1 else self.route.sequence_of_nodes[0]
        load_after_1_before_2 = self.route.prefix_loads[self.index2-1] - self.route.prefix_loads[self.index1]

        if(self.index2 == self.index1 +1):
            cost = (self.route.load - self.route.prefix_loads[self.index2] +8) *(self.cost_matrix[node_before_1.id][node2.id] + \
                                                                                self.cost_matrix[node1.id][node_after_2.id] -\
                                                                                self.cost_matrix[node_before_1.id][node1.id] -\
                                                                                self.cost_matrix[node2.id][node_after_2.id]
                                                                                )
            cost += (node1.demand) *(self.cost_matrix[node2.id][node1.id] + self.cost_matrix[node_before_1.id][node2.id] - self.cost_matrix[node_before_1.id][node1.id])
            cost += (node2.demand) * (self.cost_matrix[node_before_1.id][node2.id] - self.cost_matrix[node1.id][node2.id] - self.cost_matrix[node_before_1.id][node1.id])
            return cost
        else:
            cost = (self.cost_matrix[node_before_1.id][node2.id]  + self.cost_matrix[node2.id][node_after_1.id] 
                    - self.cost_matrix[node_before_1.id][node1.id] - self.cost_matrix[node1.id][node_after_1.id]) * \
                    (load_after_1_before_2 )
            
            cost += (self.route.load - self.route.prefix_loads[self.index2] +8) *(self.cost_matrix[node_before_1.id][node2.id] + \
                                                                                self.cost_matrix[node2.id][node_after_1.id] +\
                                                                                self.cost_matrix[node_before_2.id][node1.id] + \
                                                                                self.cost_matrix[node1.id][node_after_2.id] -\
                                                                                self.cost_matrix[node_before_1.id][node1.id] - \
                                                                                self.cost_matrix[node1.id][node_after_1.id] -\
                                                                                self.cost_matrix[node_before_2.id][node2.id] - \
                                                                                self.cost_matrix[node2.id][node_after_2.id])
            cost += (node1.demand) *(self.cost_matrix[node_before_2.id][node1.id] + self.route.prefix_distances[self.index2-1] - \
                                                                                self.route.prefix_distances[self.index1+1]  + self.cost_matrix[node_before_1.id][node2.id] +\
                                                                                        self.cost_matrix[node2.id][node_after_1.id] - self.cost_matrix[node_before_1.id][node1.id]) 
            cost += (node2.demand) * (self.route.prefix_distances[self.index1 - 1] - self.route.prefix_distances[self.index2] + self.cost_matrix[node_before_1.id][node2.id])

            if abs(cost - self.calculate_move_cost_temp()) > 1e-6:
                #print(cost , self.calculate_move_cost_temp(), self.index1, self.index2, len(self.route.sequence_of_nodes), self.route.sequence_of_nodes, node2.id)
                return self.calculate_move_cost_temp()
        
            return cost
        

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




class InRouteReinsertMove:
    def __init__(self, route, from_index, to_index, cost_matrix, capacity):
        self.route = route
        self.from_index = from_index
        self.to_index = to_index
        self.cost_matrix = cost_matrix
        self.capacity = capacity

        self.is_feasible = self.check_feasibility()
        self.affected_arcs = self.calculate_affected_arcs()
        self.affected_nodes = self.calculate_affected_nodes()
        self.move_cost = self.calculate_move_cost()

    def check_feasibility(self):
        # Feasibility is always satisfied for in-route reinsert as capacity is unchanged.
        return True

    def calculate_affected_arcs(self):
        affected_arcs = []

        # Arcs removed
        if self.from_index > 0:
            affected_arcs.append((self.route.sequence_of_nodes[self.from_index - 1].id,
                                  self.route.sequence_of_nodes[self.from_index].id))
        if self.from_index < len(self.route.sequence_of_nodes) - 1:
            affected_arcs.append((self.route.sequence_of_nodes[self.from_index].id,
                                  self.route.sequence_of_nodes[self.from_index + 1].id))

        # Arcs added
        if self.to_index > 0:
            affected_arcs.append((self.route.sequence_of_nodes[self.to_index - 1].id,
                                  self.route.sequence_of_nodes[self.from_index].id))
        if self.to_index < len(self.route.sequence_of_nodes) - 1:
            affected_arcs.append((self.route.sequence_of_nodes[self.from_index].id,
                                  self.route.sequence_of_nodes[self.to_index].id))

        return affected_arcs

    def calculate_affected_nodes(self):
        affected_nodes = set()

        affected_nodes.add(self.route.sequence_of_nodes[self.from_index].id)
        if self.from_index > 0:
            affected_nodes.add(self.route.sequence_of_nodes[self.from_index - 1].id)
        if self.from_index < len(self.route.sequence_of_nodes) - 1:
            affected_nodes.add(self.route.sequence_of_nodes[self.from_index + 1].id)
        if self.to_index > 0:
            affected_nodes.add(self.route.sequence_of_nodes[self.to_index - 1].id)
        if self.to_index < len(self.route.sequence_of_nodes) - 1:
            affected_nodes.add(self.route.sequence_of_nodes[self.to_index].id)

        return list(affected_nodes)

    def calculate_move_cost(self):
        
        temp_route = copy.deepcopy(self.route)

        # Simulate the move
        node = temp_route.sequence_of_nodes.pop(self.from_index)
        temp_route.sequence_of_nodes.insert(self.to_index, node)

        # Calculate the cost difference
        original_cost = self.route.calculate_total_route_cost(self.cost_matrix)
        new_cost = temp_route.calculate_total_route_cost(self.cost_matrix)
        return new_cost - original_cost
    def apply(self):
        # Remove node and reinsert at new position
        node = self.route.sequence_of_nodes.pop(self.from_index)
        self.route.sequence_of_nodes.insert(self.to_index, node)

        # Update the route cost
        self.route.cost = self.route.calculate_total_route_cost(self.cost_matrix)
