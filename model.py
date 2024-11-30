import random
import math


def calc_dist(n1: 'Node', n2: 'Node'):
    return math.sqrt(math.pow(n1.x - n2.x, 2) + math.pow(n1.y - n2.y, 2))

class VrpModel:

    def __init__(self):
        self.all_nodes = []
        self.customers = []
        self.dist_matrix = []
        self.capacity = -1

    def build_model(self, s: int, depot_x: int, depot_y : int, customers: int, capacity: int, x_dim :int, y_dim: int, max_dim: int):
        random.seed(s)
        depot = Node(0, depot_x, depot_y, 0)
        self.capacity = capacity
        total_customers = customers
        for i in range(0, total_customers):
            x = random.randint(0, x_dim)
            y = random.randint(0, y_dim)
            dem = random.randint(1,max_dim)
            cust = Node(i+1, x, y, dem)
            self.allNodes.append(cust)
            self.customers.append(cust)
        rows = len(self.allNodes)
        self.matrix = [[0.0 for x in range(rows)] for y in range(rows)]

        for i in range (0,  len(self.allNodes)):
            for j in range(i, len(self.allNodes)):
                a = self.allNodes[i]
                b = self.allNodes[j]
                dist = calc_dist(a,b)
                self.matrix[i][j] = dist
                self.matrix[j][i] = dist


class Node:
    def __init__(self, idd, xx, yy, dem):
        self.x = xx
        self.y = yy
        self.id = idd
        self.demand = dem
        self.is_routed = False

class Route:
    def __init__(self, dp, cap):
        self.sequence_of_nodes = []
        self.sequence_of_nodes.append(dp)
        self.cost = 0
        self.capacity = cap
        self.load = 0

        
