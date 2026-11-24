import heapq

from src.circuit_graph.graph import CircuitGraph
from src.mapping_common import (
    RoutingResult,
    hill_climb_placement as _hill_climb_placement,
    validate_mapping,
    route_circuit,
)
from src.topology_graph.graph import TopologyGraph

hill_climb_placement = _hill_climb_placement

SHALLOW_WEIGHTS = (0.2, 0.2, 0.6)
DEEP_WEIGHTS = (0.45, 0.35, 0.2)
ADJACENT_ERROR_WEIGHT = 0.7
DISTANCE_ERROR_WEIGHT = 0.3


def mapping_cost_weights(circuit: CircuitGraph) -> tuple[float, float, float]:
    """Interpolate cost weights from noise-focused to topology-focused."""
    pressure = circuit.depth_pressure
    return tuple(
        shallow + pressure * (deep - shallow)
        for shallow, deep in zip(SHALLOW_WEIGHTS, DEEP_WEIGHTS)
    )


def build_min_cost_max_flow_graph(
    circuit: CircuitGraph,
    topology: TopologyGraph,
) -> dict[str, dict[str, float]]:
    def normalize(value: float, maximum: float) -> float:
        return min(1.0, value / maximum) if maximum else 0.0

    logic_qubit_importance = [
        0.5 * normalize(circuit.qubit_degree[qubit], circuit.max_qubit_degree)
        + 0.5
        * normalize(
            circuit.qubit_interactions[qubit],
            circuit.max_qubit_interactions,
        )
        for qubit in range(circuit.qubit_count)
    ]
    weight_degree, weight_distance, weight_error = mapping_cost_weights(circuit)

    flow_graph: dict[str, dict[str, float]] = {"s": {}}

    for physical_qubit in topology.graph:
        key = f"t{physical_qubit}"
        flow_graph[key] = {}
        flow_graph[key]["t"] = 0.0

    for logical_qubit in range(circuit.qubit_count):
        lkey = f"l{logical_qubit}"
        flow_graph["s"][lkey] = 0.0
        flow_graph[lkey] = {}

        for physical_qubit in topology.graph:
            p_degree = normalize(
                max(
                    0,
                    circuit.qubit_degree[logical_qubit]
                    - topology.qubit_degree[physical_qubit],
                ),
                circuit.max_qubit_degree,
            )
            p_dist = logic_qubit_importance[logical_qubit] * normalize(
                topology.mean_distance[physical_qubit],
                topology.max_mean_distance,
            )
            p_error = logic_qubit_importance[logical_qubit] * (
                ADJACENT_ERROR_WEIGHT
                * normalize(
                    topology.mean_adjacent_error[physical_qubit],
                    topology.global_adjacent_error,
                )
                + DISTANCE_ERROR_WEIGHT
                * normalize(
                    topology.mean_path_error[physical_qubit],
                    topology.max_mean_path_error,
                )
            )
            cost = (
                weight_degree * p_degree
                + weight_distance * p_dist
                + weight_error * p_error
            )

            tkey = f"t{physical_qubit}"
            flow_graph[lkey][tkey] = cost

    return flow_graph


def compute_max_flow_min_cost(
    flow_graph: dict[str, dict[str, float]],
    source: str,
    sink: str,
) -> tuple[float, float, dict[str, dict[str, list[float]]]]:
    residual_graph: dict[str, dict[str, list[float]]] = {}

    for q0, adj in flow_graph.items():
        if q0 not in residual_graph:
            residual_graph[q0] = {}

        for q1, cost in adj.items():
            if q1 not in residual_graph:
                residual_graph[q1] = {}

            residual_graph[q0][q1] = [1.0, cost]
            residual_graph[q1][q0] = [0.0, -cost]

    residual_graph.setdefault(source, {})
    residual_graph.setdefault(sink, {})

    max_flow = 0.0
    min_cost = 0.0
    potentials = {node: 0.0 for node in residual_graph}

    while True:
        dist = {node: float("inf") for node in residual_graph}
        parent = {node: None for node in residual_graph}

        dist[source] = 0.0
        pq = [(0.0, source)]

        while pq:
            d, u = heapq.heappop(pq)
            
            if d > dist[u]:
                continue

            for v, (cap, cost) in residual_graph[u].items():
                if cap > 0:
                    reduced_cost = cost + potentials[u] - potentials[v]
                    if reduced_cost < -1e-12:
                        raise RuntimeError(
                            "Negative reduced cost violates Dijkstra's invariant"
                        )
                    if reduced_cost < 0:
                        reduced_cost = 0.0
                    if dist[u] + reduced_cost < dist[v]:
                        dist[v] = dist[u] + reduced_cost
                        parent[v] = u
                        heapq.heappush(pq, (dist[v], v))

        if dist[sink] == float("inf"):
            break

        for node in residual_graph:
            if dist[node] < float("inf"):
                potentials[node] += dist[node]

        max_flow += 1
        curr = sink
        while curr != source:
            p = parent[curr]
            edge_cost = residual_graph[p][curr][1]

            residual_graph[p][curr][0] -= 1
            residual_graph[curr][p][0] += 1

            min_cost += edge_cost
            curr = p

    return max_flow, min_cost, residual_graph


def extract_mapping_from_residual_graph(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    residual_graph: dict[str, dict[str, list[float]]],
) -> dict[int, int]:
    """Extract and validate the logical-to-physical assignment from the flow."""
    mapping = {}
    for logical_qubit in range(circuit.qubit_count):
        logical_key = f"l{logical_qubit}"
        for physical_qubit in topology.graph:
            physical_key = f"t{physical_qubit}"
            if residual_graph[logical_key][physical_key][0] == 0.0:
                mapping[logical_qubit] = physical_qubit

    if len(mapping) != circuit.qubit_count:
        raise RuntimeError("The min-cost flow did not produce a complete mapping")

    validate_mapping(circuit, topology, mapping)
    return mapping


def main() -> None:
    import argparse
    from pathlib import Path

    from src.circuit_graph.loader import load_circuit_graph
    from src.topology_graph.loader import load_topology_graph

    repository_root = Path(__file__).resolve().parents[1]
    default_circuit = (
        repository_root
        / "datasets"
        / "interaction_order"
        / "algorithms"
        / "bmw_quark_copula"
        / "bmw_quark_copula_6qubits_ordered_interactions.csv"
    )
    default_topology = (
        repository_root
        / "datasets"
        / "topologies"
        / "full"
        / "full_12qubits_weighted_edges.csv"
    )
    parser = argparse.ArgumentParser(
        description="Map and route a quantum circuit onto a hardware topology."
    )
    parser.add_argument(
        "--circuit",
        type=Path,
        default=default_circuit,
        help="CSV file with ordered circuit interactions.",
    )
    parser.add_argument(
        "--topology",
        type=Path,
        default=default_topology,
        help="CSV file with weighted hardware edges.",
    )
    parser.add_argument(
        "--exact-search-limit",
        type=int,
        default=100_000_000,
        help="Use exact search only when the solution count is below this limit.",
    )
    parser.add_argument(
        "--initial-candidates",
        type=int,
        default=1000,
        help="Number of starting placements used by the heuristic.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Maximum worker processes; use 1 to disable multiprocessing.",
    )
    args = parser.parse_args()
    for input_path in (args.circuit, args.topology):
        if not input_path.is_file():
            parser.error(f"Input file does not exist: {input_path}")

    circuit = load_circuit_graph(str(args.circuit))
    topology = load_topology_graph(str(args.topology))
    flow_graph = build_min_cost_max_flow_graph(circuit, topology)
    max_flow, _, residual_graph = compute_max_flow_min_cost(
        flow_graph,
        "s",
        "t",
    )

    if max_flow != circuit.qubit_count:
        raise ValueError(
            "Could not assign every logical qubit to a distinct physical qubit"
        )

    initial_mapping = extract_mapping_from_residual_graph(
        circuit,
        topology,
        residual_graph,
    )

    routed_results: dict[tuple[int, ...], RoutingResult] = {}

    def cached_route(
        candidate_circuit: CircuitGraph,
        candidate_topology: TopologyGraph,
        candidate_mapping: dict[int, int],
    ) -> RoutingResult:
        key = tuple(
            candidate_mapping[logical]
            for logical in range(candidate_circuit.qubit_count)
        )
        if key not in routed_results:
            routed_results[key] = route_circuit(
                candidate_circuit,
                candidate_topology,
                candidate_mapping,
            )
        return routed_results[key]

    mapped, placement_cost = _hill_climb_placement(
        circuit,
        topology,
        initial_mapping,
        router=cached_route,
    )
    print(f"Initial mapping: {initial_mapping}")
    print(f"Hill-climbing mapping: {mapped}")
    print(f"Hill-climbing routed cost (error, SWAPs): {placement_cost}")

if __name__ == "__main__":
    main()
