"""Reading instance files and writing solution files.

Instance file format (see data/instance_300.txt):

    CAPACITY,<vehicle capacity>
    EMPTY_VEHICLE_WEIGHT,<empty vehicle weight>
    CUSTOMERS,<customer count>
    NODES INFO
    ID,XCOORD,YCOORD,DEMAND
    0,<depot x>,<depot y>,0
    1,<x>,<y>,<demand>
    ...
"""

import csv

from .model import Node, VrpModel, calc_dist


def parse_input_file(file_path):
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        lines = list(reader)

    capacity = None
    empty_vehicle_weight = None
    customers = None
    nodes = []

    node_info_started = False
    for line in lines:
        if line[0] == "CAPACITY":
            capacity = int(line[1])
        elif line[0] == "EMPTY_VEHICLE_WEIGHT":
            empty_vehicle_weight = float(line[1])
        elif line[0] == "CUSTOMERS":
            customers = int(line[1])
        elif line[0] == "NODES INFO":
            node_info_started = True
            continue
        elif node_info_started:
            if line[0] == "ID":
                continue
            node_id = int(line[0])
            x_coord = float(line[1])
            y_coord = float(line[2])
            demand = float(line[3])
            nodes.append(Node(node_id, x_coord, y_coord, demand))

    return capacity, empty_vehicle_weight, customers, nodes


def build_vrp_model(nodes, capacity):
    vrp_model = VrpModel()
    vrp_model.capacity = capacity
    vrp_model.all_nodes = nodes
    vrp_model.customers = nodes[1:]

    vrp_model.dist_matrix = [
        [calc_dist(n1, n2) for n2 in vrp_model.all_nodes]
        for n1 in vrp_model.all_nodes
    ]

    return vrp_model


def load_model(file_path):
    """Parse an instance file straight into a ready-to-solve `VrpModel`."""
    capacity, _empty_vehicle_weight, _customers, nodes = parse_input_file(file_path)
    return build_vrp_model(nodes, capacity)


def write_solution_to_file(solution, file_name="output.txt"):
    with open(file_name, "w") as file:
        file.write(f"Cost:\n{solution.cost}\n")

        file.write("Routes:\n")
        file.write(f"{len(solution.routes)}\n")

        for route in solution.routes:
            route_ids = [node.id for node in route.sequence_of_nodes]
            file.write(",".join(map(str, route_ids)) + "\n")
