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

Algorithms can also be chained into a pipeline — each stage refines the
previous stage's solution, PyTorch `nn.Sequential`-style — instead of
picking just one:

```
python -m vrp_solver --instance data/instance_300.txt --pipeline local_search,tabu,vns --validate
```

```python
from vrp_solver import Solver, Stage
from vrp_solver.io_utils import load_model

model = load_model("data/instance_300.txt")
solution = Solver(model).solve(algorithm=[
    "local_search",                                     # cheap descent first
    Stage("tabu", tabu_tenure=20, max_iterations=200),     # then a configured stage
    "vns",                                               # then a final polish
])
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
    construction.py      Clarke-Wright savings construction, adapted for ton-km and
                            an incremental savings heap (see below)
    algorithms/           One module per improvement algorithm; each exposes
                            `run(initial_solution, cost_matrix, capacity, **kwargs) -> Solution`
                            and is registered in `algorithms/__init__.py`'s ALGORITHMS dict
    algorithms/lns.py         Large Neighborhood Search: edge-based removal +
                                regret-k reinsertion, optional SA acceptance
    algorithms/penalty_tabu_search.py  Tabu Search with GLS-style arc-penalty
                                          move selection (subclasses tabu_search.py)
    pipeline.py              Stage/Pipeline: chain algorithms in sequence (nn.Sequential-style)
    solver.py                 Solver: construct, then run the chosen algorithm or pipeline
    io_utils.py                 Instance file parsing + solution file writing
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

(`lns` is the one exception: it doesn't search these neighborhoods at all —
it directly removes and reinserts customers between routes. See below.)

## Construction: an incremental, ton-km-aware Clarke-Wright

`construction.py` isn't textbook Clarke-Wright — two changes matter:

- **Incremental savings heap, not full recomputation.** The classic algorithm
  recomputes every pairwise saving after each merge. Here, all pairwise
  savings are pushed into a `heapq` once up front, and after a merge only the
  savings touching the merged route's new endpoints are recalculated
  (`recalculate_savings_for_route`); stale entries referencing now-interior
  nodes are dropped from the heap instead of the heap being rebuilt. That's
  the difference between an O(n³)-ish construction and one that scales to the
  300-customer instance without construction dominating runtime.
- **Load-weighted saving score, not distance saving.** Since the objective is
  ton-km (see above), `calculate_saving_score` computes the saving in terms
  of `empty_vehicle_weight`-plus-load times distance, not raw distance —
  merging two routes only "saves" if it reduces weighted cost, which can
  differ from the plain-distance answer once loads are uneven.

(Separately, each step randomizes among the top-3 candidate savings rather
than always taking the best, for construction diversity across `Solver`'s
multi-start restarts — a diversity tweak, not a performance one.)

## Algorithms

Select with `--algorithm` (CLI) or `Solver.solve(algorithm=...)`:

| Name | What it is |
|---|---|
| `local_search` | VND-style steepest descent: each iteration takes the best move across all 6 neighborhoods; occasionally (20%) takes the second-best instead, as light diversification. |
| `tabu` | Tabu Search: forbids moves touching recently-changed nodes/arcs for a tenure that adapts to search progress, with an aspiration criterion and periodic random perturbation when stuck. |
| `adaptive_tabu` | A more elaborate, reactive Tabu Search: learns per-neighborhood operator weights from move success rate, keeps a short memory of good-but-unchosen moves to revisit, and falls back to plain `tabu` after `switch_depth` iterations without improvement. |
| `penalty_tabu` | Tabu Search with Guided-Local-Search-style move selection: reuses `tabu`'s neighborhoods and tabu bookkeeping, but scores each admissible candidate by move cost plus a decaying per-arc usage penalty (`lambda_factor`), and takes the best-scoring one instead of the first admissible one. Frequently-reused arcs get progressively less attractive even while still allowed. |
| `vns` | Variable Neighborhood Search: cycles the 6 neighborhoods in a fixed order, restarting from the first whenever a move improves the solution; move selection uses a penalized objective (load balance + capacity + compactness), not raw move cost. |
| `rvns` | Randomized VNS: samples which neighborhood to explore next by adaptive priority instead of a fixed cycle, and only evaluates a random subsample of each neighborhood for speed. |
| `lns` | Large Neighborhood Search: each iteration removes the customers on the most expensive edges (`removal_percentage`), then reinserts them with regret-k insertion — the customer with the largest gap between its best and next-best insertion cost goes first. Optionally wraps this in a simulated-annealing acceptance criterion (`use_simulated_annealing`) that cools over the run, so a temporarily worse solution can be kept to escape a local optimum. Doesn't use the shared move classes — it edits routes directly. |

All algorithm-specific tuning knobs (`tabu_tenure`, `max_iterations`,
`max_no_improvement`, `sample_size`, `switch_depth`, `lambda_factor`,
`removal_percentage`, `regret_k`, `use_simulated_annealing`) are keyword
arguments on each algorithm's `run()`, forwarded through
`Solver.solve(**kwargs)`; the CLI exposes the common ones
(`--max-iterations`, `--tabu-tenure`).

## Pipelines: chaining algorithms

Every algorithm's `run(solution, cost_matrix, capacity, **kwargs) -> Solution`
signature means one stage's output is exactly the next stage's input, so
`vrp_solver.pipeline.Pipeline` can chain any number of them — like stacking
layers in a `torch.nn.Sequential`. Pass `Solver.solve(algorithm=...)` a list
instead of a single name:

```python
solver.solve(algorithm=["local_search", "tabu", "vns"])
```

Wrap a stage in `Stage(name, **kwargs)` when it needs non-default settings:

```python
from vrp_solver import Stage

solver.solve(algorithm=[
    "local_search",
    Stage("tabu", tabu_tenure=20, max_iterations=200),
    Stage("vns", max_no_improvement=10),
])
```

A `Stage`'s `algorithm` doesn't have to be a registered name either — any
`run(solution, cost_matrix, capacity, **kwargs) -> Solution` callable works,
so you can drop in a one-off algorithm without registering it. Per-call
`algorithm_kwargs` on `Solver.solve` only apply to a single named algorithm
(there'd be no way to tell which stage they belonged to in a pipeline) — put
per-stage kwargs on each `Stage` instead. CLI equivalent: `--pipeline
local_search,tabu,vns` (stages use their default kwargs; use the Python API
for per-stage tuning).

## Adding a new algorithm

1. Create `algorithms/my_algorithm.py` exposing
   `run(initial_solution, cost_matrix, capacity, **kwargs) -> Solution`
   (reuse the move classes in `moves.py` — you don't need to reinvent them).
2. Register it in `algorithms/__init__.py`'s `ALGORITHMS` dict.

That's it — it's immediately selectable via `--algorithm my_algorithm`,
`Solver.solve(algorithm="my_algorithm")`, and as a pipeline stage.

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

None of the algorithms are fast on the full 300-customer instance —
`tabu`/`penalty_tabu`'s neighbor generation runs at roughly 10s/iteration
there, and `lns` at roughly 1-2s/iteration, so their default
`max_iterations` (1000 and 200 respectively) can take minutes to finish.
The tiny instance in the tests is unaffected; for the real instance, pass a
smaller `--max-iterations` if you just want to see it run.
