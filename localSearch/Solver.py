import heapq
from VRP_Model import *
import random


class Solution:
    def __init__(self):
        self.cost = 0.0
        self.routes = []


class Saving:
    def __init__(self, n1, n2, sav):
        self.n1 = n1
        self.n2 = n2
        self.score = sav

    def __lt__(self, other):
        # Compare Savings based on the score
        return self.score < other.score


class RelocationMove(object):
    def __init__(self):
        self.originRoutePosition = None
        self.targetRoutePosition = None
        self.originNodePosition = None
        self.targetNodePosition = None
        self.costChangeOriginRt = None
        self.costChangeTargetRt = None
        self.moveCost = None

    def Initialize(self):
        self.originRoutePosition = None
        self.targetRoutePosition = None
        self.originNodePosition = None
        self.targetNodePosition = None
        self.costChangeOriginRt = None
        self.costChangeTargetRt = None
        self.moveCost = 10 ** 9


class SwapMove(object):
    def __init__(self):
        self.positionOfFirstRoute = None
        self.positionOfSecondRoute = None
        self.positionOfFirstNode = None
        self.positionOfSecondNode = None
        self.costChangeFirstRt = None
        self.costChangeSecondRt = None
        self.moveCost = None

    def Initialize(self):
        self.positionOfFirstRoute = None
        self.positionOfSecondRoute = None
        self.positionOfFirstNode = None
        self.positionOfSecondNode = None
        self.costChangeFirstRt = None
        self.costChangeSecondRt = None
        self.moveCost = 10 ** 9


class TwoOptMove(object):
    def __init__(self):
        self.positionOfFirstRoute = None
        self.positionOfSecondRoute = None
        self.positionOfFirstNode = None
        self.positionOfSecondNode = None
        self.moveCost = None

    def Initialize(self):
        self.positionOfFirstRoute = None
        self.positionOfSecondRoute = None
        self.positionOfFirstNode = None
        self.positionOfSecondNode = None
        self.moveCost = 10 ** 9


class Solver:
    def __init__(self, m):
        self.allNodes = m.allNodes
        self.customers = m.customers
        self.depot = m.allNodes[0]
        self.distanceMatrix = m.matrix
        self.capacity = m.capacity
        self.sol = None
        self.bestSolution = None
        self.emptyWeight = m.emptyWeight

    def solve(self):
        random.seed(5)
        num_restarts = 15
        best_solution = None
        best_cost = float('inf')

        for restart in range(num_restarts):
            print(f"Restart {restart + 1}/{num_restarts}")

            self.SetRoutedFlagToFalseForAllCustomers()
            self.Clarke_n_Wright(rcl_size=10)
            print(f"Solution cost after clarke and wright on restart {restart + 1}: {self.sol.cost}")

            print("Applying VND...")
            self.VND()

            print(f"Solution cost after restart {restart + 1}: {self.sol.cost}")

            if self.sol.cost < best_cost:
                best_solution = self.cloneSolution(self.sol)
                best_cost = self.sol.cost

        self.ReportSolution(best_solution)
        print(f"Overall best solution cost: {best_cost}")
        return best_solution

    def SetRoutedFlagToFalseForAllCustomers(self):
        for c in self.customers:
            c.isRouted = False

    def ReportSolution(self, sol):
        for i in range(0, len(sol.routes)):
            rt = sol.routes[i]
            for j in range(0, len(rt.sequenceOfNodes)):
                print(rt.sequenceOfNodes[j].ID, end=' ')
            print(rt.cost)
        print(self.sol.cost)

    def Clarke_n_Wright(self, rcl_size):
        self.sol = self.create_initial_routes()
        savings_heap = self.precalculate_savings()

        while savings_heap:
            rcl = []
            for _ in range(min(rcl_size, len(savings_heap))):
                rcl.append(heapq.heappop(savings_heap))

            chosen_saving = random.choice(rcl)
            _, saving = chosen_saving
            n1, n2 = saving.n1, saving.n2

            for entry in rcl:
                if entry != chosen_saving:
                    heapq.heappush(savings_heap, entry)

            if n1.route == n2.route:
                continue
            if self.not_first_or_last(n1.route, n1) or self.not_first_or_last(n2.route, n2):
                continue
            if n1.route.load + n2.route.load > self.capacity:
                continue

            self.merge_routes(n1, n2)

            savings_heap = self.update_savings_after_merge(savings_heap, n1.route)

        self.sol.cost = self.calculate_total_cost()

    def precalculate_savings(self):
        savings_heap = []
        for i in range(len(self.customers)):
            n1 = self.customers[i]
            for j in range(i + 1, len(self.customers)):
                n2 = self.customers[j]
                if n1.route == n2.route:
                    continue

                separate_routes_cost = n1.route.cost + n2.route.cost
                merged_routes_cost = self.calculate_cost_for_test_route(n1.route.sequenceOfNodes.copy(), n2.route.sequenceOfNodes.copy(), n1, n2)
                sav_score = separate_routes_cost - merged_routes_cost

                if sav_score > 0:
                    heapq.heappush(savings_heap, (-sav_score, Saving(n1, n2, sav_score)))
        return savings_heap

    def update_savings_after_merge(self, savings_heap, merged_route):
        new_heap = []
        for _, saving in savings_heap:
            n1, n2 = saving.n1, saving.n2

            if n1.route != merged_route and n2.route != merged_route:
                heapq.heappush(new_heap, (-saving.score, saving))
                continue

            if n1.route == merged_route or n2.route == merged_route:
                separate_routes_cost = n1.route.cost + n2.route.cost
                merged_routes_cost = self.calculate_cost_for_test_route(n1.route.sequenceOfNodes.copy(), n2.route.sequenceOfNodes.copy(), n1, n2)
                sav_score = separate_routes_cost - merged_routes_cost

                if sav_score > 0:
                    heapq.heappush(new_heap, (-sav_score, Saving(n1, n2, sav_score)))
        return new_heap

    def calculate_cost_for_route(self, routeNodes):
        tot_dem = sum(n.demand for n in routeNodes)
        tot_load = self.emptyWeight + tot_dem
        tn_km = 0
        for i in range(len(routeNodes) - 2):
            from_node = routeNodes[i]
            to_node = routeNodes[i + 1]
            tn_km += self.distanceMatrix[from_node.ID][to_node.ID] * tot_load
            tot_load -= to_node.demand
        return tn_km

    def calculate_total_cost(self):
        newCost = 0
        for rt in self.sol.routes:
            newCost += rt.cost
        return newCost

    def calculate_cost_for_test_route(self, rt1, rt2, n1, n2):

        if n1.position_in_route == 1 and n2.position_in_route == len(rt2) - 2:
            rt1[1:1] = rt2[1:len(rt2) - 1]
        elif n1.position_in_route == 1 and n2.position_in_route == 1:
            rt1[1:1] = rt2[len(rt2) - 2:0:-1]
        elif n1.position_in_route == len(rt1) - 2 and n2.position_in_route == 1:
            rt1[len(rt1) - 1:len(rt1) - 1] = rt2[1:len(rt2) - 1]
        elif n1.position_in_route == len(rt1) - 2 and n2.position_in_route == len(rt2) - 2:
            rt1[len(rt1) - 1:len(rt1) - 1] = rt2[len(rt2) - 2:0:-1]
        cost = self.calculate_cost_for_route(rt1)
        return cost

    def create_initial_routes(self):
        s = Solution()
        for i in range(0, len(self.customers)):
            n = self.customers[i]
            rt = Route(self.depot, self.capacity)
            n.route = rt
            n.position_in_route = 1
            rt.sequenceOfNodes.insert(1, n)
            rt.load = n.demand
            rt.cost = self.distanceMatrix[self.depot.ID][n.ID] * (self.emptyWeight + n.demand)
            s.routes.append(rt)
        return s

    def not_first_or_last(self, rt, n):
        if n.position_in_route != 1 and n.position_in_route != len(rt.sequenceOfNodes) - 2:
            return True
        return False

    def merge_routes(self, n1, n2):
        rt1 = n1.route
        rt2 = n2.route

        if n1.position_in_route == 1 and n2.position_in_route == len(rt2.sequenceOfNodes) - 2:
            rt1.sequenceOfNodes[1:1] = rt2.sequenceOfNodes[1:len(rt2.sequenceOfNodes) - 1]
        elif n1.position_in_route == 1 and n2.position_in_route == 1:
            rt1.sequenceOfNodes[1:1] = rt2.sequenceOfNodes[len(rt2.sequenceOfNodes) - 2:0:-1]
        elif n1.position_in_route == len(rt1.sequenceOfNodes) - 2 and n2.position_in_route == 1:
            rt1.sequenceOfNodes[len(rt1.sequenceOfNodes) - 1:len(rt1.sequenceOfNodes) - 1] = rt2.sequenceOfNodes[1:len(
                rt2.sequenceOfNodes) - 1]
        elif n1.position_in_route == len(rt1.sequenceOfNodes) - 2 and n2.position_in_route == len(
                rt2.sequenceOfNodes) - 2:
            rt1.sequenceOfNodes[len(rt1.sequenceOfNodes) - 1:len(rt1.sequenceOfNodes) - 1] = rt2.sequenceOfNodes[
                                                                                             len(rt2.sequenceOfNodes) - 2:0:-1]
        rt1.load += rt2.load
        rt1.cost = self.calculate_cost_for_route(rt1.sequenceOfNodes)
        self.sol.routes.remove(rt2)
        self.update_route_customers(rt1)

    def update_route_customers(self, rt):
        for i in range(1, len(rt.sequenceOfNodes) - 1):
            n = rt.sequenceOfNodes[i]
            n.route = rt
            n.position_in_route = i

    def VND(self):
        self.bestSolution = self.cloneSolution(self.sol)
        VNDIterator = 0
        kmax = 2
        rm = RelocationMove()
        sm = SwapMove()
        top = TwoOptMove()
        k = 0

        while k <= kmax:
            self.InitializeOperators(rm, sm, top)
            if k == 2:
                self.FindBestRelocationMove(rm)
                if rm.originRoutePosition is not None and rm.moveCost < 0:
                    self.ApplyRelocationMove(rm)
                    VNDIterator = VNDIterator + 1
                    k = 0
                else:
                    k += 1
            elif k == 1:
                self.FindBestSwapMove(sm)
                if sm.positionOfFirstRoute is not None and sm.moveCost < 0:
                    self.ApplySwapMove(sm)
                    VNDIterator = VNDIterator + 1
                    k = 0
                else:
                    k += 1
            elif k == 0:
                self.FindBestTwoOptMove(top)
                if top.positionOfFirstRoute is not None and top.moveCost < 0:
                    self.ApplyTwoOptMove(top)
                    VNDIterator = VNDIterator + 1
                    k = 0
                else:
                    k += 1

            if self.sol.cost < self.bestSolution.cost:
                self.bestSolution = self.cloneSolution(self.sol)

    def LocalSearch(self, operator):
        self.bestSolution = self.cloneSolution(self.sol)
        terminationCondition = False
        localSearchIterator = 0

        rm = RelocationMove()
        sm = SwapMove()
        top = TwoOptMove()

        while terminationCondition is False:

            self.InitializeOperators(rm, sm, top)

            # Relocations
            if operator == 0:
                #SolDrawer.draw(f"Relocation {localSearchIterator}", self.sol, self.allNodes)
                self.FindBestRelocationMove(rm)
                if rm.originRoutePosition is not None:
                    if rm.moveCost < 0:
                        self.ApplyRelocationMove(rm)
                    else:
                        terminationCondition = True
            # Swaps
            elif operator == 1:
                #SolDrawer.draw(f"Swap {localSearchIterator}", self.sol, self.allNodes)
                self.FindBestSwapMove(sm)
                if sm.positionOfFirstRoute is not None:
                    if sm.moveCost < 0:
                        self.ApplySwapMove(sm)
                    else:
                        terminationCondition = True
            elif operator == 2:
                #SolDrawer.draw(f"TwoOpt {localSearchIterator}", self.sol, self.allNodes)
                self.FindBestTwoOptMove(top)
                if top.positionOfFirstRoute is not None:
                    if top.moveCost < 0:
                        self.ApplyTwoOptMove(top)
                    else:
                        terminationCondition = True

            if self.sol.cost < self.bestSolution.cost:
                self.bestSolution = self.cloneSolution(self.sol)

            localSearchIterator = localSearchIterator + 1
            print(localSearchIterator, self.sol.cost)

        self.sol = self.bestSolution

    def cloneRoute(self, rt: Route):
        cloned = Route(self.depot, self.capacity)
        cloned.cost = rt.cost
        cloned.load = rt.load
        cloned.sequenceOfNodes = rt.sequenceOfNodes.copy()
        return cloned

    def cloneSolution(self, sol: Solution):
        cloned = Solution()
        for i in range(0, len(sol.routes)):
            rt = sol.routes[i]
            clonedRoute = self.cloneRoute(rt)
            cloned.routes.append(clonedRoute)
        cloned.cost = self.sol.cost
        return cloned

    def FindBestRelocationMove(self, rm):
        for originRouteIndex in range(0, len(self.sol.routes)):
            rt1: Route = self.sol.routes[originRouteIndex]
            for originNodeIndex in range(1, len(rt1.sequenceOfNodes) - 2):
                for targetRouteIndex in range(0, len(self.sol.routes)):
                    rt2: Route = self.sol.routes[targetRouteIndex]
                    for targetNodeIndex in range(0, len(rt2.sequenceOfNodes) - 2):

                        if originRouteIndex == targetRouteIndex and (
                                targetNodeIndex == originNodeIndex or targetNodeIndex == originNodeIndex - 1):
                            continue

                        A = rt1.sequenceOfNodes[originNodeIndex - 1]
                        B = rt1.sequenceOfNodes[originNodeIndex]
                        C = rt1.sequenceOfNodes[originNodeIndex + 1]

                        F = rt2.sequenceOfNodes[targetNodeIndex]
                        G = rt2.sequenceOfNodes[targetNodeIndex + 1]

                        if rt1 != rt2:
                            if rt2.load + B.demand > rt2.capacity:
                                continue

                        originalRt1Cost = rt1.cost
                        originalRt2Cost = rt2.cost

                        route1Candidate = rt1.sequenceOfNodes.copy()
                        if rt1 == rt2:
                            route2Candidate = route1Candidate
                        else:
                            route2Candidate = rt2.sequenceOfNodes.copy()
                        route1Candidate.remove(B)
                        route2Candidate.insert(route2Candidate.index(G), B)

                        newRt1Cost = self.calculate_cost_for_route(route1Candidate)
                        newRt2Cost = self.calculate_cost_for_route(route2Candidate)

                        moveCost = (newRt1Cost + newRt2Cost) - (originalRt1Cost + originalRt2Cost)
                        costChangeFirstRoute = newRt1Cost - originalRt1Cost
                        costChangeSecondRoute = newRt2Cost - originalRt2Cost

                        if rt1 == rt2:
                            moveCost = moveCost / 2

                        if moveCost < rm.moveCost:
                            self.StoreBestRelocationMove(originRouteIndex, targetRouteIndex, originNodeIndex,
                                                         targetNodeIndex, moveCost, costChangeFirstRoute,
                                                         costChangeSecondRoute, rm)

    def FindBestSwapMove(self, sm):
        for firstRouteIndex in range(0, len(self.sol.routes)):
            rt1: Route = self.sol.routes[firstRouteIndex]
            for secondRouteIndex in range(firstRouteIndex, len(self.sol.routes)):
                rt2: Route = self.sol.routes[secondRouteIndex]
                for firstNodeIndex in range(1, len(rt1.sequenceOfNodes) - 2):
                    startOfSecondNodeIndex = 1
                    if rt1 == rt2:
                        startOfSecondNodeIndex = firstNodeIndex + 1
                    for secondNodeIndex in range(startOfSecondNodeIndex, len(rt2.sequenceOfNodes) - 2):

                        a1 = rt1.sequenceOfNodes[firstNodeIndex - 1]
                        b1 = rt1.sequenceOfNodes[firstNodeIndex]
                        c1 = rt1.sequenceOfNodes[firstNodeIndex + 1]

                        a2 = rt2.sequenceOfNodes[secondNodeIndex - 1]
                        b2 = rt2.sequenceOfNodes[secondNodeIndex]
                        c2 = rt2.sequenceOfNodes[secondNodeIndex + 1]

                        if rt1 == rt2:
                            originalRtCost = rt1.cost
                            routeCandidate = rt1.sequenceOfNodes.copy()
                            routeCandidate[firstNodeIndex], routeCandidate[secondNodeIndex] = (
                                routeCandidate[secondNodeIndex],
                                routeCandidate[firstNodeIndex],
                            )
                            newRtCost = self.calculate_cost_for_route(routeCandidate)
                            moveCost = newRtCost - originalRtCost
                            costChangeFirstRoute = moveCost
                            costChangeSecondRoute = moveCost
                        else:
                            if rt1.load - b1.demand + b2.demand > self.capacity:
                                continue
                            if rt2.load - b2.demand + b1.demand > self.capacity:
                                continue
                            originalRt1Cost = rt1.cost
                            originalRt2Cost = rt2.cost
                            routeCandidate1 = rt1.sequenceOfNodes.copy()
                            routeCandidate2 = rt2.sequenceOfNodes.copy()
                            routeCandidate1[firstNodeIndex], routeCandidate2[secondNodeIndex] = (
                                routeCandidate2[secondNodeIndex],
                                routeCandidate1[firstNodeIndex],
                            )
                            newRt1Cost = self.calculate_cost_for_route(routeCandidate1)
                            newRt2Cost = self.calculate_cost_for_route(routeCandidate2)
                            costChangeFirstRoute = newRt1Cost - originalRt1Cost
                            costChangeSecondRoute = newRt2Cost - originalRt2Cost
                            moveCost = (newRt1Cost + newRt2Cost) - (originalRt1Cost + originalRt2Cost)

                        if moveCost < sm.moveCost:
                            self.StoreBestSwapMove(firstRouteIndex, secondRouteIndex, firstNodeIndex, secondNodeIndex,
                                                   moveCost, costChangeFirstRoute, costChangeSecondRoute, sm)

    def ApplyRelocationMove(self, rm: RelocationMove):

        oldCost = self.calculate_total_cost()

        originRt = self.sol.routes[rm.originRoutePosition]
        targetRt = self.sol.routes[rm.targetRoutePosition]

        B = originRt.sequenceOfNodes[rm.originNodePosition]

        if originRt == targetRt:
            del originRt.sequenceOfNodes[rm.originNodePosition]
            if rm.originNodePosition < rm.targetNodePosition:
                targetRt.sequenceOfNodes.insert(rm.targetNodePosition, B)
            else:
                targetRt.sequenceOfNodes.insert(rm.targetNodePosition + 1, B)

            originRt.cost += rm.moveCost
        else:
            del originRt.sequenceOfNodes[rm.originNodePosition]
            targetRt.sequenceOfNodes.insert(rm.targetNodePosition + 1, B)
            originRt.cost += rm.costChangeOriginRt
            targetRt.cost += rm.costChangeTargetRt
            originRt.load -= B.demand
            targetRt.load += B.demand

        self.sol.cost += rm.moveCost

        newCost = self.calculate_total_cost()
        # debuggingOnly
        if abs((newCost - oldCost) - rm.moveCost) > 0.0001:
            print('Cost Issue')

    def ApplySwapMove(self, sm):
        oldCost = self.calculate_total_cost()
        rt1 = self.sol.routes[sm.positionOfFirstRoute]
        rt2 = self.sol.routes[sm.positionOfSecondRoute]
        b1 = rt1.sequenceOfNodes[sm.positionOfFirstNode]
        b2 = rt2.sequenceOfNodes[sm.positionOfSecondNode]
        rt1.sequenceOfNodes[sm.positionOfFirstNode] = b2
        rt2.sequenceOfNodes[sm.positionOfSecondNode] = b1

        if rt1 == rt2:
            rt1.cost += sm.moveCost
        else:
            rt1.cost += sm.costChangeFirstRt
            rt2.cost += sm.costChangeSecondRt
            rt1.load = rt1.load - b1.demand + b2.demand
            rt2.load = rt2.load + b1.demand - b2.demand

        self.sol.cost += sm.moveCost

        newCost = self.calculate_total_cost()
        # debuggingOnly
        if abs((newCost - oldCost) - sm.moveCost) > 0.0001:
            print('Cost Issue')

    def StoreBestRelocationMove(self, originRouteIndex, targetRouteIndex, originNodeIndex, targetNodeIndex, moveCost,
                                originRtCostChange, targetRtCostChange, rm: RelocationMove):
        rm.originRoutePosition = originRouteIndex
        rm.originNodePosition = originNodeIndex
        rm.targetRoutePosition = targetRouteIndex
        rm.targetNodePosition = targetNodeIndex
        rm.costChangeOriginRt = originRtCostChange
        rm.costChangeTargetRt = targetRtCostChange
        rm.moveCost = moveCost

    def StoreBestSwapMove(self, firstRouteIndex, secondRouteIndex, firstNodeIndex, secondNodeIndex, moveCost,
                          costChangeFirstRoute, costChangeSecondRoute, sm):
        sm.positionOfFirstRoute = firstRouteIndex
        sm.positionOfSecondRoute = secondRouteIndex
        sm.positionOfFirstNode = firstNodeIndex
        sm.positionOfSecondNode = secondNodeIndex
        sm.costChangeFirstRt = costChangeFirstRoute
        sm.costChangeSecondRt = costChangeSecondRoute
        sm.moveCost = moveCost

    def InitializeOperators(self, rm, sm, top):
        rm.Initialize()
        sm.Initialize()
        top.Initialize()

    def FindBestTwoOptMove(self, top):
        for rtInd1 in range(0, len(self.sol.routes)):
            rt1: Route = self.sol.routes[rtInd1]
            for rtInd2 in range(rtInd1, len(self.sol.routes)):
                rt2: Route = self.sol.routes[rtInd2]
                for nodeInd1 in range(0, len(rt1.sequenceOfNodes) - 2):
                    start2 = 0
                    if rt1 == rt2:
                        start2 = nodeInd1 + 2
                    for nodeInd2 in range(start2, len(rt2.sequenceOfNodes) - 2):
                        moveCost = 10 ** 9

                        A = rt1.sequenceOfNodes[nodeInd1]
                        B = rt1.sequenceOfNodes[nodeInd1 + 1]
                        K = rt2.sequenceOfNodes[nodeInd2]
                        L = rt2.sequenceOfNodes[nodeInd2 + 1]

                        if rt1 == rt2:
                            if nodeInd1 == 0 and nodeInd2 == len(rt1.sequenceOfNodes) - 2:
                                continue
                            originalRtCost = rt1.cost
                            routeCandidate = rt1.sequenceOfNodes.copy()
                            routeCandidate[nodeInd1 + 1: nodeInd2 + 1] = (
                                reversed(routeCandidate[nodeInd1 + 1: nodeInd2 + 1]))
                            newRtCost = self.calculate_cost_for_route(routeCandidate)
                            moveCost = newRtCost - originalRtCost
                        else:
                            if nodeInd1 == 0 and nodeInd2 == 0:
                                continue
                            if nodeInd1 == len(rt1.sequenceOfNodes) - 2 and nodeInd2 == len(rt2.sequenceOfNodes) - 2:
                                continue
                            if self.CapacityIsViolated(rt1, nodeInd1, rt2, nodeInd2):
                                continue

                            originalRt1Cost = rt1.cost
                            originalRt2Cost = rt2.cost
                            routeCandidate1 = rt1.sequenceOfNodes.copy()
                            routeCandidate2 = rt2.sequenceOfNodes.copy()
                            routeCandidate1[nodeInd1 + 1:] = rt2.sequenceOfNodes[nodeInd2 + 1:]
                            routeCandidate2[nodeInd2 + 1:] = rt1.sequenceOfNodes[nodeInd1 + 1:]
                            newRt1Cost = self.calculate_cost_for_route(routeCandidate1)
                            newRt2Cost = self.calculate_cost_for_route(routeCandidate2)
                            moveCost = (newRt1Cost + newRt2Cost) - (originalRt1Cost + originalRt2Cost)

                        if moveCost < top.moveCost:
                            self.StoreBestTwoOptMove(rtInd1, rtInd2, nodeInd1, nodeInd2, moveCost, top)

    def CapacityIsViolated(self, rt1, nodeInd1, rt2, nodeInd2):

        rt1FirstSegmentLoad = 0
        for i in range(0, nodeInd1 + 1):
            n = rt1.sequenceOfNodes[i]
            rt1FirstSegmentLoad += n.demand
        rt1SecondSegmentLoad = rt1.load - rt1FirstSegmentLoad

        rt2FirstSegmentLoad = 0
        for i in range(0, nodeInd2 + 1):
            n = rt2.sequenceOfNodes[i]
            rt2FirstSegmentLoad += n.demand
        rt2SecondSegmentLoad = rt2.load - rt2FirstSegmentLoad

        if rt1FirstSegmentLoad + rt2SecondSegmentLoad > rt1.capacity:
            return True
        if rt2FirstSegmentLoad + rt1SecondSegmentLoad > rt2.capacity:
            return True

        return False

    def StoreBestTwoOptMove(self, rtInd1, rtInd2, nodeInd1, nodeInd2, moveCost, top):
        top.positionOfFirstRoute = rtInd1
        top.positionOfSecondRoute = rtInd2
        top.positionOfFirstNode = nodeInd1
        top.positionOfSecondNode = nodeInd2
        top.moveCost = moveCost

    def ApplyTwoOptMove(self, top):
        rt1: Route = self.sol.routes[top.positionOfFirstRoute]
        rt2: Route = self.sol.routes[top.positionOfSecondRoute]

        if rt1 == rt2:
            # reverses the nodes in the segment [positionOfFirstNode + 1,  top.positionOfSecondNode]
            reversedSegment = reversed(rt1.sequenceOfNodes[top.positionOfFirstNode + 1: top.positionOfSecondNode + 1])
            rt1.sequenceOfNodes[top.positionOfFirstNode + 1: top.positionOfSecondNode + 1] = reversedSegment
            rt1.cost += top.moveCost

        else:
            # slice with the nodes from position top.positionOfFirstNode + 1 onwards
            relocatedSegmentOfRt1 = rt1.sequenceOfNodes[top.positionOfFirstNode + 1:]

            # slice with the nodes from position top.positionOfFirstNode + 1 onwards
            relocatedSegmentOfRt2 = rt2.sequenceOfNodes[top.positionOfSecondNode + 1:]

            del rt1.sequenceOfNodes[top.positionOfFirstNode + 1:]
            del rt2.sequenceOfNodes[top.positionOfSecondNode + 1:]

            rt1.sequenceOfNodes.extend(relocatedSegmentOfRt2)
            rt2.sequenceOfNodes.extend(relocatedSegmentOfRt1)

            self.UpdateRouteCostAndLoad(rt1)
            self.UpdateRouteCostAndLoad(rt2)

        self.sol.cost += top.moveCost

    def UpdateRouteCostAndLoad(self, rt: Route):
        tot_dem = sum(n.demand for n in rt.sequenceOfNodes)
        tot_load = self.emptyWeight + tot_dem
        tn_km = 0
        for i in range(len(rt.sequenceOfNodes) - 2):
            from_node = rt.sequenceOfNodes[i]
            to_node = rt.sequenceOfNodes[i + 1]
            tn_km += self.distanceMatrix[from_node.ID][to_node.ID] * tot_load
            tot_load -= to_node.demand
        rt.cost = tn_km
        rt.load = tot_dem
