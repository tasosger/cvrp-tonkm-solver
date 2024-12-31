from VRP_Model import *
from SolutionDrawer import *


class Solution:
    def __init__(self):
        self.cost = 0.0
        self.routes = []


class Saving:
    def __init__(self, n1, n2, sav):
        self.n1 = n1
        self.n2 = n2
        self.score = sav


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
        self.SetRoutedFlagToFalseForAllCustomers()
        self.Clarke_n_Wright()
        print("Constructive solution:")
        self.ReportSolution(self.sol)
        SolDrawer.draw('Clark_n_Wright', self.sol, self.allNodes)
        print("\n\n\n")
        print("Swaps:")
        self.LocalSearch(1)
        self.ReportSolution(self.sol)
        print("\n\n\n")
        print("Two Opt Moves:")
        self.LocalSearch(2)
        self.ReportSolution(self.sol)
        print("\n\n\n")
        print("Relocations:")
        self.LocalSearch(0)
        self.ReportSolution(self.sol)
        return self.sol

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

    def Clarke_n_Wright(self):
        self.sol = self.create_initial_routes()
        savings: list = self.calculate_savings()
        savings.sort(key=lambda s: s.score, reverse=True)
        for i in range(0, len(savings)):
            sav = savings[i]
            n1 = sav.n1
            n2 = sav.n2
            rt1 = n1.route
            rt2 = n2.route

            if n1.route == n2.route:
                continue
            if self.not_first_or_last(rt1, n1) or self.not_first_or_last(rt2, n2):
                continue
            if rt1.load + rt2.load > self.capacity:
                continue
            if sav.score < 0:
                continue
            self.merge_routes(n1, n2)

        self.update_routes_cost()
        self.sol.cost = self.calculate_total_cost()

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
            routeCost = self.calculate_cost_for_route(rt.sequenceOfNodes)
            newCost += routeCost
        return newCost

    def update_routes_cost(self):
        for rt in self.sol.routes:
            routeCost = self.calculate_cost_for_route(rt.sequenceOfNodes)
            rt.cost = routeCost

    def calculate_savings(self):
        savings = []
        for i in range(0, len(self.customers)):
            n1 = self.customers[i]
            for j in range(i + 1, len(self.customers)):
                n2 = self.customers[j]

                separateRoutesCost = (self.distanceMatrix[self.depot.ID][n1.ID] * (self.emptyWeight + n1.demand) +
                                      self.distanceMatrix[self.depot.ID][n2.ID] * (self.emptyWeight + n2.demand))
                mergedRoutesCost = self.distanceMatrix[self.depot.ID][n1.ID] * (
                        self.emptyWeight + n1.demand + n2.demand) + self.distanceMatrix[n1.ID][n2.ID] * (
                                           self.emptyWeight + n2.demand)
                score = separateRoutesCost - mergedRoutesCost

                sav = Saving(n1, n2, score)
                savings.append(sav)

        return savings

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
        self.sol.routes.remove(rt2)
        self.update_route_customers(rt1)

    def update_route_customers(self, rt):
        for i in range(1, len(rt.sequenceOfNodes) - 1):
            n = rt.sequenceOfNodes[i]
            n.route = rt
            n.position_in_route = i

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
                SolDrawer.draw(f"Relocation {localSearchIterator}", self.sol, self.allNodes)
                self.FindBestRelocationMove(rm)
                if rm.originRoutePosition is not None:
                    if rm.moveCost < 0:
                        self.ApplyRelocationMove(rm)
                    else:
                        terminationCondition = True
            # Swaps
            elif operator == 1:
                SolDrawer.draw(f"Swap {localSearchIterator}", self.sol, self.allNodes)
                self.FindBestSwapMove(sm)
                if sm.positionOfFirstRoute is not None:
                    if sm.moveCost < 0:
                        self.ApplySwapMove(sm)
                    else:
                        terminationCondition = True
            elif operator == 2:
                SolDrawer.draw(f"TwoOpt {localSearchIterator}", self.sol, self.allNodes)
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
