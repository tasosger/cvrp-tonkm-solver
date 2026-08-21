"""vrp_solver: a capacitated VRP solver minimizing ton-km (distance x load carried).

Quick start:

    from vrp_solver import Solver
    from vrp_solver.io_utils import load_model

    model = load_model("data/instance_300.txt")
    solution = Solver(model).solve(algorithm="vns")

See README.md for the problem statement, the list of available algorithms,
and how to add a new one.
"""

from .algorithms import ALGORITHMS
from .model import VrpModel
from .solver import Solver

__all__ = ["Solver", "VrpModel", "ALGORITHMS"]
