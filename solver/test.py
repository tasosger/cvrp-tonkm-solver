import csv
from model import VrpModel, Node, calc_dist
from solver import  Solver
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


def solve_vrp_exact(dist_matrix, demands, capacity):
    solver = pywraplp.Solver.CreateSolver('CBC')
    if not solver:
        print("Solver not available!")
        return None

    num_nodes = len(dist_matrix)
    x = [[solver.BoolVar(f'x[{i},{j}]') for j in range(num_nodes)] for i in range(num_nodes)]
    u = [solver.NumVar(0, capacity, f'u[{i}]') for i in range(num_nodes)]
    z = [[solver.NumVar(0, capacity, f'z[{i},{j}]') for j in range(num_nodes)] for i in range(num_nodes)]

    objective_terms = []
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                objective_terms.append(dist_matrix[i][j] * z[i][j])
    solver.Minimize(solver.Sum(objective_terms))

    for i in range(num_nodes):
        if i != 0:
            solver.Add(solver.Sum(x[i][j] for j in range(num_nodes) if i != j) == 1)
            solver.Add(solver.Sum(x[j][i] for j in range(num_nodes) if i != j) == 1)
        else:
            solver.Add(solver.Sum(x[i][j] for j in range(num_nodes) if i != j) ==
                       solver.Sum(x[j][i] for j in range(num_nodes) if i != j))

    solver.Add(u[0] == capacity)
    for i in range(1, num_nodes):
        solver.Add(u[i] >= demands[i])
        solver.Add(u[i] <= capacity)

    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j and i != 0 and j != 0:
                solver.Add(u[j] >= u[i] - demands[j] - capacity * (1 - x[i][j]))
                solver.Add(u[j] <= u[i] - demands[j] + capacity * (1 - x[i][j]))
                solver.Add(z[i][j] <= u[i])
                solver.Add(z[i][j] <= capacity * x[i][j])
                solver.Add(z[i][j] >= u[i] - capacity * (1 - x[i][j]))

    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        print("Optimal solution found.")
        print("Optimal total ton * km cost:", solver.Objective().Value())
        for i in range(num_nodes):
            for j in range(num_nodes):
                if x[i][j].solution_value() > 0.5:
                    print(f"Arc: {i} -> {j}, Distance: {dist_matrix[i][j]}")
        return solver.Objective().Value()
    else:
        print("No optimal solution found.")
        return None


def main():
    file_path = 'Instance.txt'
    capacity, empty_vehicle_weight, customers, nodes = parse_input_file(file_path)
    vrp_model = build_vrp_model(nodes, capacity)
    solver = Solver(vrp_model)

    best =  solver.solve()

    write_solution_to_file(best)
    print("Best Solution Cost:", best.cost)

if __name__ == "__main__":
    main()
