"""Command-line entry point: `python -m vrp_solver --algorithm vns ...`"""

import argparse
import sys
import time

from .algorithms import ALGORITHMS
from .io_utils import load_model, write_solution_to_file
from .solver import Solver
from .validation import validate_solution


def build_arg_parser():
    parser = argparse.ArgumentParser(prog="vrp_solver", description=__doc__)
    parser.add_argument("--instance", default="data/instance_300.txt", help="Path to an instance file.")
    parser.add_argument("--algorithm", choices=sorted(ALGORITHMS), default="local_search", help="Improvement algorithm to run.")
    parser.add_argument("--out", default="output.txt", help="Where to write the solution.")
    parser.add_argument("--iterations", type=int, default=1, help="Number of independent construction+improvement runs; the best is kept.")
    parser.add_argument("--max-iterations", type=int, default=None, help="Improvement algorithm's internal iteration budget (algorithm-specific default if omitted).")
    parser.add_argument("--tabu-tenure", type=int, default=None, help="Tabu tenure, for the tabu/adaptive_tabu algorithms.")
    parser.add_argument("--validate", action="store_true", help="Validate the solution (capacity, coverage, cost) before writing it.")
    parser.add_argument("--plot", metavar="PATH", default=None, help="Save a route-map PNG to PATH (requires matplotlib).")
    return parser


def main(argv=None):
    args = build_arg_parser().parse_args(argv)

    model = load_model(args.instance)
    solver = Solver(model)

    algorithm_kwargs = {}
    if args.max_iterations is not None:
        algorithm_kwargs["max_iterations"] = args.max_iterations
    if args.tabu_tenure is not None:
        algorithm_kwargs["tabu_tenure"] = args.tabu_tenure

    start = time.perf_counter()
    solution = solver.solve(algorithm=args.algorithm, num_iterations=args.iterations, **algorithm_kwargs)
    elapsed = time.perf_counter() - start

    print(f"[{args.algorithm}] cost={solution.cost:.2f} routes={len(solution.routes)} time={elapsed:.2f}s")

    if args.validate:
        is_valid, message = validate_solution(model, solution)
        print(("[valid] " if is_valid else "[INVALID] ") + message)
        if not is_valid:
            return 1

    write_solution_to_file(solution, args.out)
    print(f"Solution written to {args.out}")

    if args.plot:
        from .visualization import draw_solution

        draw_solution(model, solution, title=f"{args.algorithm} solution", save_path=args.plot)
        print(f"Route map written to {args.plot}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
