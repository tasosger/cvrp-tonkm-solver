"""Compose improvement algorithms into a pipeline, PyTorch `nn.Sequential`-style:
each stage takes the `Solution` produced by the previous stage and refines it
further, instead of picking a single algorithm to run in isolation.

    from vrp_solver.pipeline import Pipeline, Stage

    pipeline = Pipeline([
        "local_search",                                  # quick descent first
        Stage("tabu", tabu_tenure=20, max_iterations=200),  # then a configured stage
        "vns",                                            # then a final polish
    ])
    solution = pipeline(initial_solution, cost_matrix, capacity)

Every stage is just an entry from `algorithms.ALGORITHMS` (by name) or any
`run(solution, cost_matrix, capacity, **kwargs) -> Solution` callable you
wrote yourself — a pipeline stage doesn't have to be registered to be used.
`Solver.solve(algorithm=...)` accepts a `Pipeline`, or a plain list of
stages (which it wraps in a `Pipeline` for you), anywhere it accepts a
registered algorithm name.
"""

from .algorithms import ALGORITHMS


class Stage:
    """One pipeline step: an algorithm (by name or callable) plus fixed kwargs.

    Wrap an algorithm in a `Stage` when it needs non-default kwargs; a bare
    string or callable is enough when the defaults are fine.
    """

    def __init__(self, algorithm, **kwargs):
        if isinstance(algorithm, str):
            if algorithm not in ALGORITHMS:
                available = ", ".join(sorted(ALGORITHMS))
                raise ValueError(f"Unknown algorithm {algorithm!r}. Available: {available}")
            self.name = algorithm
            self.run = ALGORITHMS[algorithm]
        else:
            self.name = getattr(algorithm, "__name__", repr(algorithm))
            self.run = algorithm
        self.kwargs = kwargs

    def __call__(self, solution, cost_matrix, capacity):
        return self.run(solution, cost_matrix, capacity, **self.kwargs)

    def __repr__(self):
        return f"Stage({self.name!r}, {self.kwargs})" if self.kwargs else f"Stage({self.name!r})"


class Pipeline:
    """A sequence of `Stage`s, each applied to the previous stage's output."""

    def __init__(self, stages):
        self.stages = [stage if isinstance(stage, Stage) else Stage(stage) for stage in stages]
        if not self.stages:
            raise ValueError("Pipeline needs at least one stage.")

    def __call__(self, initial_solution, cost_matrix, capacity):
        solution = initial_solution
        for stage in self.stages:
            solution = stage(solution, cost_matrix, capacity)
        return solution

    def __len__(self):
        return len(self.stages)

    def __getitem__(self, index):
        return self.stages[index]

    def __iter__(self):
        return iter(self.stages)

    def __repr__(self):
        body = ",\n  ".join(repr(stage) for stage in self.stages)
        return f"Pipeline([\n  {body}\n])"
