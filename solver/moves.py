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
        node1 = self.route1.sequence_of_nodes[self.index1]
        node2 = self.route2.sequence_of_nodes[self.index2]

        self.route1.sequence_of_nodes[self.index1] = node2
        self.route2.sequence_of_nodes[self.index2] = node1

        self.update_route_loads()

    def update_route_loads(self):
        self.route1.load = sum(node.demand for node in self.route1.sequence_of_nodes)
        self.route2.load = sum(node.demand for node in self.route2.sequence_of_nodes)

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


class InRouteSwapMove:
    def __init__(self, route, index1, index2, cost_matrix):
        self.route = route
        self.index1 = index1
        self.index2 = index2
        self.cost_matrix = cost_matrix

        self.move_cost = self.calculate_move_cost()

    def calculate_move_cost(self):
        """
        Calculate the cost impact of swapping two nodes within the same route using a temporary route.
        :return: The net cost difference (negative indicates improvement).
        """
        # Create a temporary copy of the route
        temp_route = self.route.copy()

        # Simulate the swap on the temporary route
        temp_route.sequence_of_nodes[self.index1], temp_route.sequence_of_nodes[self.index2] = \
            temp_route.sequence_of_nodes[self.index2], temp_route.sequence_of_nodes[self.index1]

        # Calculate the cost before and after the move
        cost_before = self.route.calculate_total_route_cost(self.cost_matrix)
        cost_after = temp_route.calculate_total_route_cost(self.cost_matrix)

        # Return the difference in costs
        return cost_after - cost_before



    def apply(self):
        
        self.route.sequence_of_nodes[self.index1], self.route.sequence_of_nodes[self.index2] = \
            self.route.sequence_of_nodes[self.index2], self.route.sequence_of_nodes[self.index1]

        self.route.cost = self.route.calculate_total_route_cost(self.cost_matrix)
