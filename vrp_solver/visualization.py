"""Optional route-map plotting. Requires matplotlib (`pip install matplotlib`);
importing this module without it raises a clear ImportError instead of
crashing the whole package.
"""

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover - exercised only when matplotlib is absent
    raise ImportError(
        "vrp_solver.visualization requires matplotlib. Install it with `pip install matplotlib`."
    ) from exc


def draw_solution(model, solution, title="VRP Solution", save_path=None, figsize=(12, 10)):
    """Plot every route in `solution` over the customer/depot coordinates in `model`.

    If `save_path` is given, the figure is saved there (any matplotlib-supported
    extension, e.g. .png); otherwise it's shown interactively.
    """
    plt.figure(figsize=figsize)

    colors = plt.cm.tab20(range(len(solution.routes) % 20 or 1))
    if len(solution.routes) > 20:
        import numpy as np

        colors = plt.cm.tab20(np.linspace(0, 1, len(solution.routes)))

    depot = model.all_nodes[0]
    plt.scatter(depot.x, depot.y, c="red", s=150, marker="s", label="Depot")
    plt.annotate("Depot", (depot.x, depot.y), xytext=(5, 5), textcoords="offset points", color="red", fontweight="bold")

    total_distance = 0.0
    total_demand = 0.0

    for idx, route in enumerate(solution.routes):
        nodes = route.sequence_of_nodes
        route_demand = sum(n.demand for n in nodes)
        route_distance = sum(
            ((nodes[i].x - nodes[i + 1].x) ** 2 + (nodes[i].y - nodes[i + 1].y) ** 2) ** 0.5
            for i in range(len(nodes) - 1)
        )
        total_distance += route_distance
        total_demand += route_demand

        color = colors[idx % len(colors)]
        label = f"Route {idx + 1}\n(Dist: {route_distance:.1f}, Demand: {route_demand:.1f})"
        plt.plot([n.x for n in nodes], [n.y for n in nodes], marker="o", label=label, color=color)

        for node in nodes[1:]:
            plt.scatter(node.x, node.y, c=[color], s=max(50, node.demand * 10), alpha=0.6)

    plt.title(f"{title}\nTotal Distance: {total_distance:.1f}, Total Demand: {total_demand:.1f}")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
    else:
        plt.show()

    plt.close()
