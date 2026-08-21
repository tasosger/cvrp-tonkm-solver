"""Feasibility/consistency checks for a solution: every customer visited
exactly once, no route over capacity, and the reported cost matches a fresh
recalculation.
"""

from .io_utils import parse_input_file
from .model import calc_dist


def validate_solution(model, solution, tolerance=1e-3):
    """Validate an in-memory Solution against its VrpModel.

    Returns (is_valid: bool, message: str).
    """
    times_visited = {node.id: 0 for node in model.customers}

    for route in solution.routes:
        load = sum(node.demand for node in route.sequence_of_nodes)
        if load > model.capacity + tolerance:
            return False, f"Capacity violation: a route has load {load} > capacity {model.capacity}"

        for node in route.sequence_of_nodes[1:]:
            if node.id not in times_visited:
                return False, f"Unknown customer id {node.id} in solution"
            times_visited[node.id] += 1

    recalculated_cost = sum(route.calculate_total_route_cost(model.dist_matrix) for route in solution.routes)
    if abs(recalculated_cost - solution.cost) > tolerance:
        return False, f"Cost inconsistency: reported {solution.cost}, recalculated {recalculated_cost}"

    for node_id, count in times_visited.items():
        if count != 1:
            return False, f"Customer {node_id} visited {count} times (expected exactly once)"

    return True, f"Solution OK. Total cost: {recalculated_cost}"


def validate_solution_file(instance_path, output_path, tolerance=1e-3):
    """Validate a written `output.txt` (see `io_utils.write_solution_to_file`)
    against its instance file. Returns (is_valid: bool, message: str).
    """
    capacity, empty_vehicle_weight, _customers, nodes = parse_input_file(instance_path)
    nodes_by_id = {node.id: node for node in nodes}

    with open(output_path, "r") as file:
        lines = [line.strip() for line in file.readlines()]

    reported_cost = float(lines[1])
    num_routes = int(lines[3])

    times_visited = {node.id: 0 for node in nodes if node.id != 0}
    recalculated_cost = 0.0

    for i in range(num_routes):
        route_ids = [int(x) for x in lines[4 + i].split(",")]
        route_nodes = [nodes_by_id[idd] for idd in route_ids]

        total_demand = sum(n.demand for n in route_nodes)
        if total_demand > capacity + tolerance:
            return False, f"Capacity violation: route {i} has load {total_demand} > capacity {capacity}"

        tot_load = empty_vehicle_weight + total_demand
        for j in range(len(route_nodes) - 1):
            recalculated_cost += calc_dist(route_nodes[j], route_nodes[j + 1]) * tot_load
            tot_load -= route_nodes[j + 1].demand

        for node in route_nodes[1:]:
            times_visited[node.id] += 1

    if abs(recalculated_cost - reported_cost) > tolerance:
        return False, f"Cost inconsistency: reported {reported_cost}, recalculated {recalculated_cost}"

    for node_id, count in times_visited.items():
        if count != 1:
            return False, f"Customer {node_id} visited {count} times (expected exactly once)"

    return True, f"Solution OK. Total cost: {recalculated_cost}"
