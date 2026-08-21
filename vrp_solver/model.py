"""Core domain objects for the ton-km CVRP: nodes, distance, and routes."""

import math

# The instance's EMPTY_VEHICLE_WEIGHT (see data/instance_300.txt): a vehicle's
# base weight is added to whatever it's carrying, so an empty leg still costs
# something. Named here instead of the bare "8" that used to be scattered
# across model/construction/moves.
EMPTY_VEHICLE_WEIGHT = 8


def calc_dist(n1: "Node", n2: "Node") -> float:
    return math.sqrt(math.pow(n1.x - n2.x, 2) + math.pow(n1.y - n2.y, 2))


class Node:
    def __init__(self, idd, xx, yy, dem):
        self.x = xx
        self.y = yy
        self.id = idd
        self.demand = dem
        self.is_routed = False

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.id == other.id

    def __lt__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.id < other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"Node(id={self.id}, demand={self.demand})"


class Route:
    def __init__(self, dp, cap):
        self.sequence_of_nodes = [dp]
        self.cost = 0
        self.capacity = cap
        self.load = 0
        self.length = 0
        self.prefix_loads = []
        self.prefix_distances = []

    def copy(self):
        new_route = Route(self.sequence_of_nodes[0], self.capacity)
        new_route.sequence_of_nodes = self.sequence_of_nodes[:]
        new_route.cost = self.cost
        new_route.load = self.load
        new_route.length = self.length
        return new_route

    def update_route_customers(self):
        for i, n in enumerate(self.sequence_of_nodes):
            n.position_in_route = i

    def calculate_total_route_cost(self, cost_matrix):
        nodes_sequence = self.sequence_of_nodes
        tot_load = EMPTY_VEHICLE_WEIGHT + sum(n.demand for n in nodes_sequence)
        route_cost = 0
        for i in range(len(nodes_sequence) - 1):
            from_node = nodes_sequence[i]
            to_node = nodes_sequence[i + 1]
            distance = cost_matrix[from_node.id][to_node.id]
            route_cost += distance * tot_load
            tot_load -= to_node.demand
        return route_cost


class VrpModel:
    """Holds the parsed instance: nodes, distance matrix, and vehicle capacity.

    Populated by `vrp_solver.io_utils.build_vrp_model` from an instance file.
    """

    def __init__(self):
        self.all_nodes = []
        self.customers = []
        self.dist_matrix = []
        self.capacity = -1
