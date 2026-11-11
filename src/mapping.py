from __future__ import annotations

from dataclasses import dataclass
import random

from src.circuit_graph.graph import CircuitGraph
from src.topology_graph.graph import TopologyGraph


@dataclass(frozen=True)
class RoutingResult:
    swap_count: int
    expected_error_rate: float
    final_mapping: dict[int, int]


def _interaction_pairs(circuit: CircuitGraph) -> list[tuple[int, int, int]]:
    return [
        (logical_1, logical_2, circuit.iteraction_matrix[logical_1][logical_2])
        for logical_1 in range(circuit.qubit_count)
        for logical_2 in range(logical_1 + 1, circuit.qubit_count)
        if circuit.iteraction_matrix[logical_1][logical_2] > 0
    ]


def _validate_mapping(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    mapping: dict[int, int],
) -> None:
    expected_logical = set(range(circuit.qubit_count))
    if set(mapping) != expected_logical:
        raise ValueError("Mapping must contain exactly the circuit's logical qubits")
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("Mapping must assign each logical qubit to a distinct physical qubit")
    if not set(mapping.values()).issubset(topology.graph):
        raise ValueError("Mapping refers to a physical qubit absent from the topology")


def estimate_placement_cost(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    mapping: dict[int, int],
) -> int:
    """Return interaction-count-weighted undirected hardware hop distance."""
    _validate_mapping(circuit, topology, mapping)

    cost = 0
    for logical_1, logical_2, count in _interaction_pairs(circuit):
        path = topology.path_matrix[mapping[logical_1]][mapping[logical_2]]
        if not path:
            raise ValueError("Mapped interacting qubits are disconnected in the topology")
        cost += count * (len(path) - 1)
    return cost


def route_circuit(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    mapping: dict[int, int],
) -> RoutingResult:
    """Route ordered two-qubit interactions using shortest paths and SWAPs.

    Each required SWAP moves the first operand along the topology's precomputed
    shortest path until the operands are adjacent.
    """
    _validate_mapping(circuit, topology, mapping)
    final_mapping = mapping.copy()
    physical_to_logical = {physical: logical for logical, physical in mapping.items()}
    swap_count = 0
    success_probability = 1.0

    def link_error_rate(physical_a: int, physical_b: int) -> float:
        rate = topology.link_error_rate(physical_a, physical_b)
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"Invalid two-qubit gate error rate: {rate}")
        return rate

    for interaction in circuit.fpga:
        physical_1 = final_mapping[interaction.qubit_1]
        physical_2 = final_mapping[interaction.qubit_2]
        path = topology.path_matrix[physical_1][physical_2]
        if not path:
            raise ValueError("Interacting qubits are disconnected in the topology")

        for index in range(len(path) - 2):
            physical_a = path[index]
            physical_b = path[index + 1]
            logical_a = physical_to_logical.get(physical_a)
            logical_b = physical_to_logical.get(physical_b)

            if logical_a is not None:
                final_mapping[logical_a] = physical_b
            if logical_b is not None:
                final_mapping[logical_b] = physical_a
            physical_to_logical.pop(physical_a, None)
            physical_to_logical.pop(physical_b, None)
            if logical_b is not None:
                physical_to_logical[physical_a] = logical_b
            if logical_a is not None:
                physical_to_logical[physical_b] = logical_a
            swap_gate_error = link_error_rate(physical_a, physical_b)
            success_probability *= (1.0 - swap_gate_error) ** 3
            swap_count += 1

        interaction_error = link_error_rate(
            final_mapping[interaction.qubit_1],
            final_mapping[interaction.qubit_2],
        )
        success_probability *= 1.0 - interaction_error

    return RoutingResult(
        swap_count=swap_count,
        expected_error_rate=1.0 - success_probability,
        final_mapping=final_mapping,
    )


def _initial_placement(
    circuit: CircuitGraph,
    topology: TopologyGraph,
) -> dict[int, int]:
    logical_qubits = []
    weighted_degree = 0.0
    for logical in range(circuit.qubit_count):
        weighted_degree = 0
        degree = 0
        for i in range(circuit.qubit_count):
            interactions_pair = circuit.iteraction_matrix[logical][i]
            if interactions_pair == 0: continue
            weighted_degree += interactions_pair
            degree += 1
        logical_qubits.append((logical, degree, weighted_degree))
    logical_qubits.sort(key=lambda item: (-item[1], -item[2], item[0]))

    physical_qubits = []
    for physical in topology.graph:
        average_hops = sum(
            len(topology.path_matrix[physical][target]) - 1
            for target in topology.graph
        ) / topology.qubit_count
        average_error = sum(
            topology.error_matrix[physical][target]
            for target in topology.graph
        ) / topology.qubit_count
        physical_qubits.append(
            (physical, len(topology.graph[physical]), average_hops, average_error)
        )
    physical_qubits.sort(key=lambda item: (-item[1], item[3], item[2], item[0]))
    return {
        logical: physical_qubits[index][0]
        for index, (logical, _, _) in enumerate(logical_qubits)
    }


def _improve_placement(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    mapping: dict[int, int],
) -> tuple[dict[int, int], tuple[float, int]]:
    interactions = _interaction_pairs(circuit)
    incident: dict[int, list[tuple[int, int, int]]] = {
        logical: [] for logical in range(circuit.qubit_count)
    }
    for interaction in interactions:
        logical_1, logical_2, _ = interaction
        incident[logical_1].append(interaction)
        incident[logical_2].append(interaction)

    def cost_for(edges: set[tuple[int, int, int]]) -> tuple[float, int]:
        total_hops = 0
        total_error = 0.0
        for logical_1, logical_2, count in edges:
            physical_1 = mapping[logical_1]
            physical_2 = mapping[logical_2]
            path = topology.path_matrix[physical_1][physical_2]
            if not path:
                raise ValueError("Mapped interacting qubits are disconnected in the topology")
            total_hops += count * (len(path) - 1)
            total_error += count * topology.error_matrix[physical_1][physical_2]
        return total_error, total_hops

    current_cost = cost_for(set(interactions))
    logical_qubits = list(range(circuit.qubit_count))

    while True:
        best_cost = current_cost
        best_move: tuple[str, int, int] | None = None

        # swaping 2 logical qubits to local minimize
        for index, logical_1 in enumerate(logical_qubits):
            for logical_2 in logical_qubits[index + 1:]:
                affected = set(incident[logical_1]) | set(incident[logical_2])
                previous_cost = cost_for(affected)
                mapping[logical_1], mapping[logical_2] = (
                    mapping[logical_2],
                    mapping[logical_1],
                )
                updated_cost = cost_for(affected)
                candidate_cost = (
                    current_cost[0] - previous_cost[0] + updated_cost[0],
                    current_cost[1] - previous_cost[1] + updated_cost[1],
                )
                mapping[logical_1], mapping[logical_2] = (
                    mapping[logical_2],
                    mapping[logical_1],
                )
                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_move = ("swap", logical_1, logical_2)

        # swap 2 physical qubits to local minimize
        unused_physical = set(topology.graph) - set(mapping.values())
        for logical in logical_qubits:
            affected = set(incident[logical])
            previous_cost = cost_for(affected)
            original_physical = mapping[logical]
            for physical in unused_physical:
                mapping[logical] = physical
                updated_cost = cost_for(affected)
                candidate_cost = (
                    current_cost[0] - previous_cost[0] + updated_cost[0],
                    current_cost[1] - previous_cost[1] + updated_cost[1],
                )
                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_move = ("move", logical, physical)
            mapping[logical] = original_physical

        if best_move is None:
            break
        move_type, first, second = best_move
        if move_type == "swap":
            mapping[first], mapping[second] = mapping[second], mapping[first]
        else:
            mapping[first] = second
        current_cost = best_cost

    return mapping, current_cost


def map(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    restarts: int = 100,
    seed: int | None = 0,
    route_candidates: int = 5,
) -> dict[int, int]:
    """Find a placement with shuffled multi-start local search.

    Search prioritizes estimated error rate, then weighted hop distance. The
    best proxy candidates are routed in circuit order and ranked by estimated
    error rate before SWAP count.
    A fixed seed makes randomized starts reproducible.
    """
    if restarts < 1:
        raise ValueError("restarts must be at least 1")
    if route_candidates < 1:
        raise ValueError("route_candidates must be at least 1")

    if len(topology.graph) < circuit.qubit_count:
        raise ValueError(
            f"Incompatible topology for this circuit: "
            f"t: {len(topology.graph)} < c: {circuit.qubit_count}"
        )
    if any(
        not topology.path_matrix[source][target]
        for source in topology.graph
        for target in topology.graph
    ):
        raise ValueError("Topology must be connected to route this circuit")

    rng = random.Random(seed)
    baseline = _initial_placement(circuit, topology)
    logical_qubits = list(range(circuit.qubit_count))
    candidates: dict[
        tuple[int, ...],
        tuple[tuple[float, int], dict[int, int]],
    ] = {}

    for restart in range(restarts):
        candidate = baseline.copy()
        if restart:
            physical_to_logical = {
                physical: logical for logical, physical in candidate.items()
            }
            for _ in range(rng.randint(1, max(1, circuit.qubit_count))):
                logical = rng.choice(logical_qubits)
                physical = rng.choice(list(topology.graph))
                current_logical = physical_to_logical.get(physical)
                old_physical = candidate[logical]
                candidate[logical] = physical
                physical_to_logical.pop(old_physical, None)
                if current_logical is not None:
                    candidate[current_logical] = old_physical
                    physical_to_logical[old_physical] = current_logical
                physical_to_logical[physical] = logical

        candidate, score = _improve_placement(
            circuit,
            topology,
            candidate,
        )
        key = tuple(candidate[logical] for logical in logical_qubits)
        candidates[key] = (score, candidate.copy())

    finalists = sorted(
        candidates.values(),
        key=lambda item: (
            item[0],
            tuple(item[1][logical] for logical in logical_qubits),
        ),
    )[:route_candidates]
    routed_finalists = [
        (
            route_circuit(circuit, topology, placement),
            score,
            placement,
        )
        for score, placement in finalists
    ]
    return min(
        routed_finalists,
        key=lambda item: (
            item[0].expected_error_rate,
            item[0].swap_count,
            item[1][0],
            item[1][1],
            tuple(item[2][logical] for logical in logical_qubits),
        ),
    )[2]


if __name__ == "__main__":
    from src.circuit_graph.loader import load_circuit_graph
    from src.topology_graph.loader import load_topology_graph

    circuit = load_circuit_graph(
        "datasets/interaction_order/algorithms/bmw_quark_cardinality/"
        "bmw_quark_cardinality_3qubits_ordered_interactions.csv"
    )
    topology = load_topology_graph(
        "datasets/topologies/heavy_hex/heavy_hex_19qubits_weighted_edges.csv"
    )
    placement = map(circuit, topology, 1000, 45, route_candidates=1000)
    print("Routed SWAPs:", route_circuit(circuit, topology, placement))
