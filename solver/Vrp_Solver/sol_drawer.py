import matplotlib
matplotlib.use('Agg')  # Set non-interactive Agg backend
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
import csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Node:
    def __init__(self, id: int, x: float, y: float, demand: float):
        self.id = id
        self.x = x
        self.y = y
        self.demand = demand
        
    def distance_to(self, other: 'Node') -> float:
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

class Route:
    def __init__(self, sequence_of_nodes: List[Node], capacity: float = float('inf')):
        self.sequence = sequence_of_nodes
        self.capacity = capacity
        
    @property
    def total_demand(self) -> float:
        return sum(node.demand for node in self.sequence)
    
    @property
    def total_distance(self) -> float:
        if len(self.sequence) < 2:
            return 0
        
        distance = 0
        for i in range(len(self.sequence) - 1):
            distance += self.sequence[i].distance_to(self.sequence[i + 1])
        return distance

def parse_instance_file(filename: str) -> Tuple[Dict[int, Node], float]:
    
    nodes = {}
    capacity = None
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            
            for line in lines:
                if line.startswith('CAPACITY'):
                    capacity = float(line.strip().split(',')[1])
                    break
            
            start_index = next(i for i, line in enumerate(lines) if 'ID,XCOORD,YCOORD,DEMAND' in line)
            
            for line in lines[start_index + 1:]:
                if line.strip(): 
                    parts = line.strip().split(',')
                    if len(parts) == 4: 
                        try:
                            node_id = int(parts[0])
                            x = float(parts[1])
                            y = float(parts[2])
                            demand = float(parts[3])
                            nodes[node_id] = Node(node_id, x, y, demand)
                        except ValueError as e:
                            logger.warning(f"Invalid data format: {line.strip()} - {e}")
                    
    except FileNotFoundError:
        logger.error(f"Instance file not found: {filename}")
        raise
    
    logger.info(f"Successfully parsed {len(nodes)} nodes")
    return nodes, capacity

def parse_output_file(filename: str) -> List[List[int]]:
   
    routes = []
    try:
        with open(filename, 'r') as file:
            for line_num, line in enumerate(file, 1):
                if line.strip().startswith("0,"):  
                    try:
                        route = [int(x) for x in line.strip().split(',')]
                        routes.append(route)
                    except ValueError as e:
                        logger.warning(f"Line {line_num}: Invalid route format - {e}")
    except FileNotFoundError:
        logger.error(f"Output file not found: {filename}")
        raise
    
    logger.info(f"Successfully parsed {len(routes)} routes")
    return routes

def draw_solution(
    routes: List[List[int]], 
    nodes: Dict[int, Node], 
    title: str = "Solution Visualization",
    figsize: tuple = (12, 10),
    save_path: Optional[str] = None,
    capacity: Optional[float] = None
) -> None:
    
    plt.figure(figsize=figsize)
    
    colors = plt.cm.tab20(np.linspace(0, 1, len(routes)))
    
    depot = nodes[0]
    plt.scatter(depot.x, depot.y, c="red", s=150, marker="s", label="Depot")
    plt.annotate("Depot", (depot.x, depot.y), xytext=(5, 5), 
                textcoords='offset points', color="red", fontweight='bold')

    total_distance = 0
    total_demand = 0
    
    for idx, route in enumerate(routes):
        route_nodes = [nodes[node_id] for node_id in route if node_id in nodes]
        if not route_nodes:
            continue
            
        route_obj = Route(route_nodes, capacity)
        route_distance = route_obj.total_distance
        route_demand = route_obj.total_demand
        total_distance += route_distance
        total_demand += route_demand
        
        x_coords = [node.x for node in route_nodes]
        y_coords = [node.y for node in route_nodes]
        
        x_coords = x_coords
        y_coords = y_coords
        
        color = colors[idx]
        route_label = f"Route {idx + 1}\n(Dist: {route_distance:.1f}, Demand: {route_demand:.1f})"
        if capacity:
            route_label += f"\n(Capacity: {(route_demand/capacity)*100:.1f}%)"
        plt.plot(x_coords, y_coords, marker="o", label=route_label, color=color)
        
        for node in route_nodes:
            size = max(50, node.demand * 10) 
            plt.scatter(node.x, node.y, c=[color], s=size, alpha=0.6)
            plt.annotate(f"{node.id}\n({node.demand})", (node.x, node.y),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8, color=color[:-1])  

    stats_title = f"{title}\nTotal Distance: {total_distance:.1f}, Total Demand: {total_demand:.1f}"
    if capacity:
        stats_title += f"\nVehicle Capacity: {capacity}"
    plt.title(stats_title)
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        logger.info(f"Visualization saved to {save_path}")
    else:
        plt.show()
    
    plt.close()

def main():
    
    instance_file = "Instance.txt"
    output_file = "output.txt"
    
    try:
        nodes, capacity = parse_instance_file(instance_file)
        routes = parse_output_file(output_file)
        
        draw_solution(
            routes, 
            nodes, 
            title="Vehicle Routing Solution",
            save_path="route_visualization.png",
            capacity=capacity
        )
        
    except Exception as e:
        logger.error(f"Error during visualization: {e}")
        raise

if __name__ == "__main__":
    main()