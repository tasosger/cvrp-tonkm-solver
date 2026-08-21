"""Smoke test: every registered algorithm must run to completion on a tiny
instance and produce a feasible solution (every customer visited exactly
once, no route over capacity, reported cost matches a fresh recalculation).

Run directly with `python tests/test_smoke.py`, or via `pytest tests/`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vrp_solver.algorithms import ALGORITHMS
from vrp_solver.io_utils import build_vrp_model
from vrp_solver.model import Node
from vrp_solver.pipeline import Stage
from vrp_solver.solver import Solver
from vrp_solver.validation import validate_solution


def build_tiny_model():
    nodes = [
        Node(0, 0, 0, 0),
        Node(1, 2, 2, 3),
        Node(2, 4, 4, 4),
        Node(3, 4, 5, 1),
        Node(4, 2, 3, 2),
        Node(5, 1, 7, 3),
    ]
    return build_vrp_model(nodes, capacity=5)


def _run_algorithm(name):
    model = build_tiny_model()
    solver = Solver(model)
    solution = solver.solve(algorithm=name, num_iterations=1)

    is_valid, message = validate_solution(model, solution)
    assert is_valid, f"{name}: {message}"
    assert solution.cost > 0, f"{name}: expected a positive cost, got {solution.cost}"


def test_local_search():
    _run_algorithm("local_search")


def test_tabu_search():
    _run_algorithm("tabu")


def test_adaptive_tabu_search():
    _run_algorithm("adaptive_tabu")


def test_vns():
    _run_algorithm("vns")


def test_rvns():
    _run_algorithm("rvns")


def test_pipeline_chains_algorithms():
    model = build_tiny_model()
    solver = Solver(model)
    solution = solver.solve(
        algorithm=["local_search", Stage("tabu", max_iterations=20), "vns"],
        num_iterations=1,
    )

    is_valid, message = validate_solution(model, solution)
    assert is_valid, f"pipeline: {message}"


def test_pipeline_rejects_ambiguous_kwargs():
    model = build_tiny_model()
    solver = Solver(model)
    try:
        solver.solve(algorithm=["local_search", "tabu"], max_iterations=20)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for algorithm_kwargs with a pipeline")


def main():
    for name in ALGORITHMS:
        _run_algorithm(name)
        print(f"OK: {name}")
    test_pipeline_chains_algorithms()
    print("OK: pipeline")
    test_pipeline_rejects_ambiguous_kwargs()
    print("OK: pipeline rejects ambiguous kwargs")
    print("All algorithms produced feasible solutions.")


if __name__ == "__main__":
    main()
