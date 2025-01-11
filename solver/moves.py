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

        self.move_cost = self.calculate_move_cost()

    def apply(self):
        
        if not self.is_feasible:
            raise ValueError("Cannot apply an infeasible move.")

        self.from_route.sequence_of_nodes.pop(self.from_index)

        self.to_route.sequence_of_nodes.insert(self.to_index, self.node)

        self.update_route_loads()

    def update_route_loads(self):
        
        self.from_route.load -= self.node.demand
        self.to_route.load += self.node.demand

    def calculate_move_cost(self):
        
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




class SwapMove:
    

    def __init__(self, route1, route2, index1, index2, cost_matrix):
        self.route1 = route1
        self.route2 = route2
        self.index1 = index1
        self.index2 = index2
        self.cost_matrix = cost_matrix

        self.move_cost = self.calculate_move_cost()

    def apply(self):
        node1 = self.route1.sequence_of_nodes[self.index1]
        node2 = self.route2.sequence_of_nodes[self.index2]

        self.route1.sequence_of_nodes[self.index1] = node2
        self.route2.sequence_of_nodes[self.index2] = node1

        self.update_route_loads()

    def update_route_loads(self):
        self.route1.load = sum(node.demand for node in self.route1.sequence_of_nodes)
        self.route2.load = sum(node.demand for node in self.route2.sequence_of_nodes)

    def calculate_move_cost(self):
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


class TwoOptMove:

    def __init__(self, route, i, j, cost_matrix):
        self.route = route
        self.i = i
        self.j = j
        self.cost_matrix = cost_matrix

        self.move_cost = self.calculate_move_cost()

    def apply(self):
        self.route.sequence_of_nodes[self.i:self.j + 1] = reversed(self.route.sequence_of_nodes[self.i:self.j + 1])
        self.update_route_cost()

    def update_route_cost(self):
        self.route.cost = self.route.calculate_total_route_cost(self.cost_matrix)

    def calculate_move_cost(self):
        nodes = self.route.sequence_of_nodes

        prev_id = nodes[self.i - 1].id if self.i > 0 else nodes[0].id
        next_id = nodes[self.j + 1].id if self.j + 1 < len(nodes) else nodes[-1].id

        prev_cost = self.cost_matrix[prev_id][nodes[self.i].id] + self.cost_matrix[nodes[self.j].id][next_id]
        new_cost = self.cost_matrix[prev_id][nodes[self.j].id] + self.cost_matrix[nodes[self.i].id][next_id]

        return new_cost - prev_cost

