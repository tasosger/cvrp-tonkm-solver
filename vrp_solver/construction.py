"""Clarke-Wright savings construction heuristic: builds an initial feasible solution.

Starts every customer on its own route, then repeatedly merges the pair of
routes with the best "saving" (randomized among the top-3 candidates each
step, for some construction diversity across `Solver` iterations), subject to
capacity and the classic Clarke-Wright first/last-node merge rule.
"""

import heapq
import random

from .model import EMPTY_VEHICLE_WEIGHT, Route
from .solution import Solution


class Saving:
    def __init__(self, n1, n2, sav):
        self.n1 = n1
        self.n2 = n2
        self.score = sav

    def __lt__(self, other):
        return self.score > other.score


class ClarkeWrightConstructor:
    def __init__(self, depot, cost_matrix, capacity, customers, empty_vehicle_weight=EMPTY_VEHICLE_WEIGHT):
        self.depot = depot
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.empty_vehicle_weight = empty_vehicle_weight
        self.customers = customers
        self.sol = None

    def build(self):
        self.sol = self.create_initial_routes()
        self.calculate_savings_with_pq()

        while self.savings_heap:
            top_savings = [heapq.heappop(self.savings_heap) for _ in range(min(3, len(self.savings_heap)))]

            _, selected_saving = random.choice(top_savings)

            for saving in top_savings:
                if saving != (_, selected_saving):
                    heapq.heappush(self.savings_heap, saving)

            n1, n2 = selected_saving.n1, selected_saving.n2
            rt1, rt2 = n1.route, n2.route

            if rt1 == rt2 or self.not_first_or_last(rt1, n1) or self.not_first_or_last(rt2, n2):
                continue
            if rt1.load + rt2.load > self.capacity:
                continue

            self.merge_routes(n1, n2)
        return self.sol

    def create_initial_routes(self):
        s = Solution(self.cost_matrix)
        for customer in self.customers:
            rt = Route(self.depot, self.capacity)

            customer.route = rt
            customer.position_in_route = 1
            rt.sequence_of_nodes.append(customer)
            rt.prefix_loads = [0, customer.demand]
            rt.prefix_distances = [0, self.cost_matrix[self.depot.id][customer.id]]
            rt.load = customer.demand
            rt.cost = (rt.load + self.empty_vehicle_weight) * self.cost_matrix[self.depot.id][customer.id]
            s.routes.append(rt)
            s.cost += rt.cost
            rt.length = self.cost_matrix[self.depot.id][customer.id]
        return s

    def not_first_or_last(self, rt, n):
        return not (n.position_in_route == 1 or n.position_in_route == len(rt.sequence_of_nodes) - 1)

    def merge_routes(self, n1, n2):
        rt1, rt2 = n1.route, n2.route

        if n1.position_in_route == 1 and n2.position_in_route == len(rt2.sequence_of_nodes) - 1:
            self._merge_case1(rt1, rt2, n1, n2)
        elif n1.position_in_route == len(rt1.sequence_of_nodes) - 1 and n2.position_in_route == 1:
            self._merge_case2(rt1, rt2, n1, n2)
        else:
            return

        rt1.load += rt2.load
        for node in rt2.sequence_of_nodes:
            node.route = rt1

        self.sol.routes.remove(rt2)
        rt1.update_route_customers()
        self.sol.update_solution_cost()
        self.recalculate_savings_for_route(rt1)

    def _merge_case1(self, rt1, rt2, n1, n2):

        rt1.sequence_of_nodes[1:1] = rt2.sequence_of_nodes[1:]
        rt1.length += rt2.length - self.cost_matrix[self.depot.id][n1.id] + self.cost_matrix[n2.id][n1.id]

        if rt2.prefix_loads:
            offset = rt2.prefix_loads[-1]
            rt1.prefix_loads = (
                rt2.prefix_loads[:] + [offset + load for load in rt1.prefix_loads[1:]]
            )

        if rt2.prefix_distances:
            offset_distance = rt2.prefix_distances[-1]

            distance_between_n1_n2 = self.cost_matrix[n1.id][n2.id]
            offset_distance += distance_between_n1_n2

            additional_distances = []
            cumulative_distance = offset_distance
            for i in range(2, len(rt1.prefix_distances)):
                prev_node_id = rt1.sequence_of_nodes[len(rt2.sequence_of_nodes) + i - 2].id
                curr_node_id = rt1.sequence_of_nodes[len(rt2.sequence_of_nodes) + i - 1].id
                cumulative_distance += self.cost_matrix[prev_node_id][curr_node_id]
                additional_distances.append(cumulative_distance)

            rt1.prefix_distances = rt2.prefix_distances[:] + [offset_distance] + additional_distances

    def _merge_case2(self, rt1, rt2, n1, n2):

        rt1.sequence_of_nodes.extend(rt2.sequence_of_nodes[1:])
        rt1.length += rt2.length - self.cost_matrix[self.depot.id][n2.id] + self.cost_matrix[n1.id][n2.id]

        last_load_rt1 = rt1.prefix_loads[-1]
        rt1.prefix_loads.extend([last_load_rt1 + load for load in rt2.prefix_loads[1:]])

        last_distance_rt1 = rt1.prefix_distances[-1] if rt1.prefix_distances else 0
        distance_between_n1_n2 = self.cost_matrix[n1.id][n2.id]

        offset_distance = last_distance_rt1 + distance_between_n1_n2
        rt1.prefix_distances.extend([offset_distance])
        additional_distances = []
        cumulative_distance = offset_distance
        for i in range(2, len(rt2.sequence_of_nodes)):
            prev_node = rt2.sequence_of_nodes[i - 1]
            curr_node = rt2.sequence_of_nodes[i]
            cumulative_distance += self.cost_matrix[prev_node.id][curr_node.id]
            additional_distances.append(cumulative_distance)

        rt1.prefix_distances.extend(additional_distances)

    def recalculate_savings_for_route(self, updated_route):
        new_edge_nodes = {updated_route.sequence_of_nodes[1], updated_route.sequence_of_nodes[-1]}
        merged_nodes = set(updated_route.sequence_of_nodes)

        self.savings_heap = [
            (priority, sav) for priority, sav in self.savings_heap
            if sav.n1 not in merged_nodes and sav.n2 not in merged_nodes
        ]
        heapq.heapify(self.savings_heap)

        for node1 in new_edge_nodes:
            if node1.id == 0:
                continue
            for route in self.sol.routes:
                if route == updated_route:
                    continue
                first_node, last_node = route.sequence_of_nodes[1], route.sequence_of_nodes[-1]

                if node1 == first_node or node1 == last_node:
                    continue

                if node1 == updated_route.sequence_of_nodes[-1]:
                    self._add_saving(node1, first_node)
                elif node1 == updated_route.sequence_of_nodes[1]:
                    self._add_saving(last_node, node1)

    def _add_saving(self, node1, node2):
        score = self.calculate_saving_score(node1, node2)
        if score > 0:
            heapq.heappush(self.savings_heap, (-score, Saving(node1, node2, score)))

    def calculate_savings_with_pq(self):
        self.savings_heap = []
        for i in range(len(self.customers)):
            n1 = self.customers[i]
            for j in range(i + 1, len(self.customers)):
                n2 = self.customers[j]
                if n1.demand + n2.demand > self.capacity:
                    continue

                score = self.calculate_saving_score(n1, n2)
                if score > 0:
                    sav = Saving(n1, n2, score)
                    heapq.heappush(self.savings_heap, (-score, sav))

    def calculate_saving_score(self, node1, node2):
        rt2 = node2.route
        rt1 = node1.route

        saving = ((self.empty_vehicle_weight + rt2.load) * self.cost_matrix[self.depot.id][node2.id]
                  - (rt2.load * rt1.length)
                  - (rt2.load + self.empty_vehicle_weight) * self.cost_matrix[node1.id][node2.id])
        return saving
