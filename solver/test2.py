from model import Route, Node, VrpModel
import math
from solver import Solver
def calc_dist(n1: 'Node', n2: 'Node'):
    return math.sqrt(math.pow(n1.x - n2.x, 2) + math.pow(n1.y - n2.y, 2))

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


n0 = Node(0,0,0,0)
n1 = Node(1,2,2,3)
n2 = Node(2,4,4,4)
n3 = Node(3,4,5,1)
n4 = Node(4,2,3,2)
n5 = Node(5,1,7,3)
nodes = [n0,n1,n2,n3,n4,n5]
model = VrpModel()
model = build_vrp_model(nodes, 5) 
solver =  Solver(model)
print(solver.solve().cost)

