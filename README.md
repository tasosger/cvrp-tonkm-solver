# vrp_solver

A capacitated Vehicle Routing Problem (CVRP) solver that minimizes **ton-km**:
total cost is distance traveled multiplied by the load carried on that leg
(an empty-but-moving vehicle still costs something — see
`EMPTY_VEHICLE_WEIGHT` below), not plain distance. Solutions are built with a
Clarke-Wright savings construction heuristic and then improved by one of
several interchangeable local-search-based metaheuristics.

## Install

The core package is pure standard library. Two algorithms pull in extra
dependencies:

- `adaptive_tabu` uses `numpy`.
- `visualization.draw_solution` (the optional `--plot` CLI flag) uses `matplotlib`.

```
pip install -r requirements.txt
```

## Quick start

```
python -m vrp_solver --instance data/instance_300.txt --algorithm vns --validate
```

```python
from vrp_solver import Solver
from vrp_solver.io_utils import load_model

model = load_model("data/instance_300.txt")
solution = Solver(model).solve(algorithm="vns")
print(solution.cost)
```

## Instance file format

See `data/instance_300.txt` (300 randomly generated customers):

```
CAPACITY,<vehicle capacity>
EMPTY_VEHICLE_WEIGHT,<empty vehicle weight>
CUSTOMERS,<customer count>
NODES INFO
ID,XCOORD,YCOORD,DEMAND
0,<depot x>,<depot y>,0
1,<x>,<y>,<demand>
...
```

## Architecture

```
vrp_solver/
    model.py          Node, Route, VrpModel, calc_dist, EMPTY_VEHICLE_WEIGHT
    solution.py        Solution (a set of routes + total cost)
    moves.py            The 6 move/neighborhood operators every algorithm searches
    construction.py      Clarke-Wright savings construction (builds the initial solution)
    algorithms/           One module per improvement algorithm; each exposes
                            `run(initial_solution, cost_matrix, capacity, **kwargs) -> Solution`
                            and is registered in `algorithms/__init__.py`'s ALGORITHMS dict
    solver.py             Solver: construct, then dispatch to the chosen algorithm
    io_utils.py             Instance file parsing + solution file writing
    validation.py             Feasibility/consistency checks
    visualization.py           Optional matplotlib route-map plotting
    __main__.py                 CLI (`python -m vrp_solver`)
```

Every algorithm searches the same 6 neighborhoods, defined once in
`moves.py`, so results are comparable and adding a neighborhood benefits
every algorithm at once:

| Move | Scope |
|---|---|
| `RelocationMove` | move one node to a different route |
| `SwapMove` | swap two nodes across different routes |
| `TwoOptMove` | swap the tails of two routes |
| `InRouteTwoOptMove` | reverse a segment within one route |
| `InRouteSwapMove` | swap two nodes within one route |
| `InRouteReinsertMove` | move a node to a different position within one route |

## Algorithms

Select with `--algorithm` (CLI) or `Solver.solve(algorithm=...)`:

| Name | What it is |
|---|---|
| `local_search` | VND-style steepest descent: each iteration takes the best move across all 6 neighborhoods; occasionally (20%) takes the second-best instead, as light diversification. |
| `tabu` | Tabu Search: forbids moves touching recently-changed nodes/arcs for a tenure that adapts to search progress, with an aspiration criterion and periodic random perturbation when stuck. |
| `adaptive_tabu` | A more elaborate, reactive Tabu Search: learns per-neighborhood operator weights from move success rate, keeps a short memory of good-but-unchosen moves to revisit, and falls back to plain `tabu` after `switch_depth` iterations without improvement. |
| `vns` | Variable Neighborhood Search: cycles the 6 neighborhoods in a fixed order, restarting from the first whenever a move improves the solution; move selection uses a penalized objective (load balance + capacity + compactness), not raw move cost. |
| `rvns` | Randomized VNS: samples which neighborhood to explore next by adaptive priority instead of a fixed cycle, and only evaluates a random subsample of each neighborhood for speed. |

All algorithm-specific tuning knobs (`tabu_tenure`, `max_iterations`,
`max_no_improvement`, `sample_size`, `switch_depth`) are keyword arguments on
each algorithm's `run()`, forwarded through `Solver.solve(**kwargs)`; the CLI
exposes the common ones (`--max-iterations`, `--tabu-tenure`).

## Adding a new algorithm

1. Create `algorithms/my_algorithm.py` exposing
   `run(initial_solution, cost_matrix, capacity, **kwargs) -> Solution`
   (reuse the move classes in `moves.py` — you don't need to reinvent them).
2. Register it in `algorithms/__init__.py`'s `ALGORITHMS` dict.

That's it — it's immediately selectable via `--algorithm my_algorithm` and
`Solver.solve(algorithm="my_algorithm")`.

## Testing

```
python tests/test_smoke.py   # or: pytest tests/
```

Runs every registered algorithm on a tiny hand-built instance and checks
feasibility (every customer visited exactly once, no route over capacity,
reported cost matches a fresh recalculation) via `validation.py`.

## Known limitations

This started as a set of experiments comparing optimization techniques for a
university assignment; the heuristics are not fine-tuned against each other
and some (notably the penalty terms in `vns`/`rvns`'s move evaluation) are
fairly ad hoc. `adaptive_tabu` in particular caches "good but unchosen"
moves for later replay against routes that keep mutating — `Solver.solve`
guards against the resulting stale-move corruption (see
`algorithms/adaptive_tabu_search.py`'s `_apply_move_safely`), but the
mechanism itself is more of an experiment than a polished technique. With
more time these could be tuned further; treat `local_search` and `tabu` as
the more predictable baselines and the others as experimental.
