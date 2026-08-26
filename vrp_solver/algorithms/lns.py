"""Large Neighborhood Search: destroy a slice of the solution and repair it.

Each iteration removes the customers sitting on the most expensive edges
(the ones most likely to be there because of a poor assignment, not because
they had to be), then reinserts them with regret-k insertion: the customer
whose best-vs-next-best insertion cost gap ("regret") is largest is placed
first, since it has the most to lose from being left for later once cheap
slots are taken. Optionally accepts a worse candidate with a simulated-
annealing probability that cools over the run, so the search can escape a
local optimum instead of only ever taking improving destroy/repair cycles.
"""

import copy
import math
import random

from ..model import Route


class LargeNeighborhoodSearch:
    def __init__(
        self,
        initial_solution,
        cost_matrix,
        capacity,
        removal_percentage=0.15,
        regret_k=2,
        max_iterations=200,
        use_simulated_annealing=True,
        initial_temperature=50.0,
        cooling_rate=0.98,
        seed=None,
    ):
        self.sol = copy.deepcopy(initial_solution)
        self.best_solution = copy.deepcopy(initial_solution)
        self.cost_matrix = cost_matrix
        self.capacity = capacity
        self.depot = self.sol.routes[0].sequence_of_nodes[0]
        self.removal_percentage = removal_percentage
        self.regret_k = regret_k
        self.max_iterations = max_iterations
        self.use_simulated_annealing = use_simulated_annealing
        self.temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.rng = random.Random(seed)

    def search(self):
        current = self.sol

        for _ in range(self.max_iterations):
            candidate = copy.deepcopy(current)
            removed = self._edge_based_removal(candidate)
            self._regret_k_reinsertion(candidate, removed)
            candidate.update_solution_cost()

            accept = candidate.cost < current.cost
            if not accept and self.use_simulated_annealing and self.temperature > 1e-6:
                accept = self.rng.random() < self._acceptance_probability(current.cost, candidate.cost)

            if accept:
                current = candidate
            if current.cost < self.best_solution.cost:
                self.best_solution = copy.deepcopy(current)

            self.temperature *= self.cooling_rate

        return self.best_solution

    def _acceptance_probability(self, current_cost, candidate_cost):
        return math.exp((current_cost - candidate_cost) / self.temperature)

    def _edge_based_removal(self, solution):
        num_customers = sum(len(route.sequence_of_nodes) - 1 for route in solution.routes)
        num_to_remove = max(1, int(num_customers * self.removal_percentage))

        edges = []
        for route in solution.routes:
            nodes = route.sequence_of_nodes
            for i in range(len(nodes) - 1):
                edges.append((self.cost_matrix[nodes[i].id][nodes[i + 1].id], nodes[i + 1]))
        edges.sort(key=lambda e: e[0], reverse=True)

        removed = []
        removed_ids = set()
        for _, node in edges:
            if len(removed_ids) >= num_to_remove:
                break
            if node.id not in removed_ids:
                removed.append(node)
                removed_ids.add(node.id)

        for node in removed:
            route = next(r for r in solution.routes if node in r.sequence_of_nodes)
            route.sequence_of_nodes.remove(node)
            route.load -= node.demand
            route.cost = route.calculate_total_route_cost(self.cost_matrix)

        return removed

    def _regret_k_reinsertion(self, solution, removed_customers):
        remaining = list(removed_customers)

        while remaining:
            best_customer = best_route = best_position = None
            best_regret = float("-inf")
            best_cost_increase = float("inf")

            for customer in remaining:
                insertion_costs = []
                for route in solution.routes:
                    if route.load + customer.demand > self.capacity:
                        continue
                    for position in range(1, len(route.sequence_of_nodes)):
                        insertion_costs.append((self._insertion_cost(route, customer, position), route, position))

                if not insertion_costs:
                    continue

                insertion_costs.sort(key=lambda c: c[0])
                k = min(self.regret_k, len(insertion_costs))
                cost_increase, route, position = insertion_costs[0]
                regret = sum(c[0] for c in insertion_costs[1:k]) - cost_increase * (k - 1)

                if regret > best_regret or (regret == best_regret and cost_increase < best_cost_increase):
                    best_customer, best_route, best_position = customer, route, position
                    best_regret, best_cost_increase = regret, cost_increase

            if best_customer is None:
                # No route has room for any remaining customer: open a fresh one
                # rather than dropping the customer from the solution.
                customer = remaining.pop(0)
                route = Route(self.depot, self.capacity)
                route.sequence_of_nodes.append(customer)
                route.load = customer.demand
                route.cost = route.calculate_total_route_cost(self.cost_matrix)
                solution.routes.append(route)
                continue

            best_route.sequence_of_nodes.insert(best_position, best_customer)
            best_route.load += best_customer.demand
            best_route.cost = best_route.calculate_total_route_cost(self.cost_matrix)
            remaining.remove(best_customer)

    def _insertion_cost(self, route, customer, position):
        temp_route = route.copy()
        temp_route.sequence_of_nodes.insert(position, customer)
        cost_before = route.calculate_total_route_cost(self.cost_matrix)
        cost_after = temp_route.calculate_total_route_cost(self.cost_matrix)
        return cost_after - cost_before


def run(
    initial_solution,
    cost_matrix,
    capacity,
    removal_percentage=0.15,
    regret_k=2,
    max_iterations=200,
    use_simulated_annealing=True,
    initial_temperature=50.0,
    cooling_rate=0.98,
    seed=None,
    **_ignored,
):
    """Registry entry point: uniform `run(initial, cost_matrix, capacity, **kwargs)` signature."""
    search = LargeNeighborhoodSearch(
        initial_solution=initial_solution,
        cost_matrix=cost_matrix,
        capacity=capacity,
        removal_percentage=removal_percentage,
        regret_k=regret_k,
        max_iterations=max_iterations,
        use_simulated_annealing=use_simulated_annealing,
        initial_temperature=initial_temperature,
        cooling_rate=cooling_rate,
        seed=seed,
    )
    return search.search()
