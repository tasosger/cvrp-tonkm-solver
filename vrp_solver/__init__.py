"""vrp_solver: a capacitated VRP solver minimizing ton-km (distance x load carried).

Quick start -- a single algorithm:

    from vrp_solver import Solver
    from vrp_solver.io_utils import load_model

    model = load_model("data/instance_300.txt")
    solution = Solver(model).solve(algorithm="vns")

Or chain algorithms into a pipeline (each stage refines the previous
stage's solution, PyTorch `nn.Sequential`-style):

    from vrp_solver import Solver, Stage
    from vrp_solver.io_utils import load_model

    model = load_model("data/instance_300.txt")
    solution = Solver(model).solve(algorithm=[
        "local_search",
        Stage("tabu", tabu_tenure=20, max_iterations=200),
        "vns",
    ])

See README.md for the problem statement, the list of available algorithms,
and how to add a new one.
"""

from .algorithms import ALGORITHMS
from .model import VrpModel
from .pipeline import Pipeline, Stage
from .solver import Solver

__all__ = ["Solver", "VrpModel", "ALGORITHMS", "Pipeline", "Stage"]
