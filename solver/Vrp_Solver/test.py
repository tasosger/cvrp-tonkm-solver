import csv
from model import VrpModel, Node, Route, calc_dist
from solver import  Solver
import math
import time
#from ortools.linear_solver import pywraplp

def parse_input_file(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        lines = list(reader)
    
    capacity = None
    empty_vehicle_weight = None
    customers = None
    nodes = []
    
    node_info_started = False
    for line in lines:
        if line[0] == 'CAPACITY':
            capacity = int(line[1])
        elif line[0] == 'EMPTY_VEHICLE_WEIGHT':
            empty_vehicle_weight = float(line[1])
        elif line[0] == 'CUSTOMERS':
            customers = int(line[1])
        elif line[0] == 'NODES INFO':
            node_info_started = True
            continue  
        elif node_info_started:
            if line[0] == 'ID':  
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
    vrp_model.depot = nodes[0]  

    vrp_model.dist_matrix = [
        [calc_dist(n1, n2) for n2 in vrp_model.all_nodes]
        for n1 in vrp_model.all_nodes
    ]
    
    
    return vrp_model


def write_solution_to_file(solution, file_name="output.txt"):
    with open(file_name, "w") as file:
        file.write(f"Cost:\n{solution.cost}\n")
        
        file.write("Routes:\n")
        file.write(f"{len(solution.routes)}\n")
        
        for route in solution.routes:
            route_ids = [node.id for node in route.sequence_of_nodes]
            file.write(",".join(map(str, route_ids)) + "\n")




def main():
    start =time.time()
    file_path = 'Instance.txt'
    capacity, empty_vehicle_weight, customers, nodes = parse_input_file(file_path)
    vrp_model = build_vrp_model(nodes, capacity)
    solver = Solver(vrp_model)
    
    best =  solver.solve_vns()

    write_solution_to_file(best)
    print("Best Solution Cost:", best.cost)
    end = time.time()
    execution_time = end - start
    print(f"Total Execution Time: {execution_time:.6f} seconds")
if __name__ == "__main__":
    main()
