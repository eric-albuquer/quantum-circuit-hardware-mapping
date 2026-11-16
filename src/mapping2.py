import heapq

from src.circuit_graph.graph import CircuitGraph
from src.mapping import _improve_placement, _validate_mapping
from src.topology_graph.graph import TopologyGraph

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


def map2(
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

    flux_graph: dict[str, dict[str, float]] = {"s": {}}

    for physical_qubit in topology.graph:
        key = f"t{physical_qubit}"
        flux_graph[key] = {}
        flux_graph[key]["t"] = 0.0

    for logical_qubit in range(circuit.qubit_count):
        lkey = f"l{logical_qubit}"
        flux_graph["s"][lkey] = 0.0
        flux_graph[lkey] = {}

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
            flux_graph[lkey][tkey] = cost

    return flux_graph


def hill_climb_placement(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    mapping: dict[int, int],
) -> tuple[dict[int, int], tuple[float, int]]:
    """Improve an initial placement with mapping.py's local-search objective."""
    _validate_mapping(circuit, topology, mapping)
    return _improve_placement(circuit, topology, mapping.copy())


def compute_max_flux_min_cost(
    flux_graph: dict[str, dict[str, float]], 
    source: str, 
    sink: str
) -> tuple[float, float, dict[str, dict[str, list[float]]]]:
    # Estrutura: reverse_flux_graph[u][v] = [capacidade_residual, custo]
    reverse_flux_graph: dict[str, dict[str, list[float]]] = {}

    # 1. Montagem da rede residual com dicionários aninhados
    for q0, adj in flux_graph.items():
        if q0 not in reverse_flux_graph:
            reverse_flux_graph[q0] = {}

        for q1, cost in adj.items():
            if q1 not in reverse_flux_graph:
                reverse_flux_graph[q1] = {}

            # Aresta direta: capacidade 1, custo positivo
            reverse_flux_graph[q0][q1] = [1.0, cost]
            # Aresta reversa: capacidade 0, custo negativo (para permitir desfazer fluxo)
            reverse_flux_graph[q1][q0] = [0.0, -cost]

    # Garante que source e sink existam no grafo caso sejam isolados
    reverse_flux_graph.setdefault(source, {})
    reverse_flux_graph.setdefault(sink, {})

    max_flow = 0.0
    min_cost = 0.0
    potentials = {node: 0.0 for node in reverse_flux_graph}

    # 2. Loop principal (Caminhos Mais Curtos Sucessivos)
    while True:
        dist = {node: float('inf') for node in reverse_flux_graph}
        parent = {node: None for node in reverse_flux_graph}
        
        dist[source] = 0.0
        pq = [(0.0, source)]

        # Dijkstra com custos reduzidos
        while pq:
            d, u = heapq.heappop(pq)
            
            if d > dist[u]:
                continue

            for v, (cap, cost) in reverse_flux_graph[u].items():
                if cap > 0:
                    reduced_cost = cost + potentials[u] - potentials[v]
                    if dist[u] + reduced_cost < dist[v]:
                        dist[v] = dist[u] + reduced_cost
                        parent[v] = u
                        heapq.heappush(pq, (dist[v], v))

        # Encerra se não houver mais caminho até o destino
        if dist[sink] == float('inf'):
            break

        # 3. Atualiza potenciais para manter os pesos >= 0 na próxima iteração
        for node in reverse_flux_graph:
            if dist[node] < float('inf'):
                potentials[node] += dist[node]

        # 4. Encontra o gargalo no caminho
        push_flow = float('inf')
        curr = sink
        while curr != source:
            p = parent[curr]
            cap = reverse_flux_graph[p][curr][0]
            push_flow = min(push_flow, cap)
            curr = p

        # 5. Atualiza capacidades residuais e soma o custo
        max_flow += push_flow
        curr = sink
        while curr != source:
            p = parent[curr]
            edge_cost = reverse_flux_graph[p][curr][1]

            reverse_flux_graph[p][curr][0] -= push_flow  # Consome capacidade direta
            reverse_flux_graph[curr][p][0] += push_flow  # Libera capacidade reversa
            
            min_cost += push_flow * edge_cost
            curr = p

    return max_flow, min_cost, reverse_flux_graph

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
    flux_graph = map2(circuit, topology)
    max_flow, _, reverse_flux_graph = compute_max_flux_min_cost(
        flux_graph,
        "s",
        "t",
    )

    if max_flow != circuit.qubit_count:
        raise ValueError(
            "Could not assign every logical qubit to a distinct physical qubit"
        )

    initial_mapping = {}
    for lq in range(circuit.qubit_count):
        lkey = f"l{lq}"

        for tq in topology.graph:
            tkey = f"t{tq}"

            if reverse_flux_graph[lkey][tkey][0] == 0.0:
                initial_mapping[lq] = tq

    if len(initial_mapping) != circuit.qubit_count:
        raise RuntimeError("The min-cost flow did not produce a complete mapping")

    mapped, placement_cost = hill_climb_placement(
        circuit,
        topology,
        initial_mapping,
    )
    print(f"Initial mapping: {initial_mapping}")
    print(f"Hill-climbing mapping: {mapped}")
    print(f"Hill-climbing proxy cost: {placement_cost}")

if __name__ == "__main__":
    main()
