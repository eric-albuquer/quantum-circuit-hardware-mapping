from __future__ import annotations

from dataclasses import dataclass
import random
import time
import math

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


def _placement_error_rate(
    interactions: list[tuple[int, int, int]],
    topology: TopologyGraph,
    mapping: dict[int, int],
) -> float:
    success_probability = 1.0
    for logical_1, logical_2, count in interactions:
        error = topology.error_matrix[mapping[logical_1]][mapping[logical_2]]
        success_probability *= (1.0 - error) ** count
    return 1.0 - success_probability


def _validate_mapping(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    mapping: dict[int, int],
) -> None:
    expected_logical = set(range(circuit.qubit_count))
    if set(mapping) != expected_logical:
        raise ValueError("Mapping must contain exactly the circuit's logical qubits")
    if len(set(mapping.values())) != len(mapping):
        raise ValueError(
            "Mapping must assign each logical qubit to a distinct physical qubit"
        )
    if not set(mapping.values()).issubset(topology.graph):
        raise ValueError("Mapping refers to a physical qubit absent from the topology")


def estimate_placement_cost(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    mapping: dict[int, int],
) -> tuple[float, int]:
    """Return cumulative interaction error rate and weighted hardware hop distance."""
    _validate_mapping(circuit, topology, mapping)

    interactions = _interaction_pairs(circuit)
    distance = 0
    for logical_1, logical_2, count in interactions:
        path = topology.path_matrix[mapping[logical_1]][mapping[logical_2]]
        if not path:
            raise ValueError(
                "Mapped interacting qubits are disconnected in the topology"
            )
        distance += count * (len(path) - 1)
    error_rate = _placement_error_rate(interactions, topology, mapping)
    return error_rate, distance


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


def _degree_initial_placement(
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
            if interactions_pair == 0:
                continue
            weighted_degree += interactions_pair
            degree += 1
        logical_qubits.append((logical, degree, weighted_degree))
    logical_qubits.sort(key=lambda item: (-item[1], -item[2], item[0]))

    physical_qubits = []
    for physical in topology.graph:
        average_hops = (
            sum(
                len(topology.path_matrix[physical][target]) - 1
                for target in topology.graph
            )
            / topology.qubit_count
        )
        success_probability = 1.0
        for target in topology.graph:
            success_probability *= 1.0 - topology.error_matrix[physical][target]
        average_error = 1.0 - success_probability
        physical_qubits.append(
            (physical, len(topology.graph[physical]), average_hops, average_error)
        )
    physical_qubits.sort(key=lambda item: (-item[1], item[3], item[2], item[0]))
    return {
        logical: physical_qubits[index][0]
        for index, (logical, _, _) in enumerate(logical_qubits)
    }


def _interaction_pair_initial_placement(
    circuit: CircuitGraph,
    topology: TopologyGraph,
) -> dict[int, int]:
    weighted_degrees = [sum(row) for row in circuit.iteraction_matrix]
    degrees = [
        sum(weight > 0 for weight in row)
        for row in circuit.iteraction_matrix
    ]
    logical_pairs = _interaction_pairs(circuit)
    logical_1, logical_2, _ = min(
        logical_pairs,
        key=lambda pair: (
            -pair[2],
            -(weighted_degrees[pair[0]] + weighted_degrees[pair[1]]),
            pair[0],
            pair[1],
        ),
    )
    physical_edges = {
        tuple(sorted((physical, neighbor)))
        for physical, neighbors in topology.graph.items()
        for neighbor in neighbors
        if physical != neighbor
    }
    physical_1, physical_2 = min(
        physical_edges,
        key=lambda pair: (
            topology.link_error_rate(*pair),
            -(len(topology.graph[pair[0]]) + len(topology.graph[pair[1]])),
            pair[0],
            pair[1],
        ),
    )
    if (
        weighted_degrees[logical_1],
        degrees[logical_1],
        -logical_1,
    ) < (
        weighted_degrees[logical_2],
        degrees[logical_2],
        -logical_2,
    ):
        logical_1, logical_2 = logical_2, logical_1
    if (
        len(topology.graph[physical_1]),
        -physical_1,
    ) < (
        len(topology.graph[physical_2]),
        -physical_2,
    ):
        physical_1, physical_2 = physical_2, physical_1
    mapping = {logical_1: physical_1, logical_2: physical_2}
    return _grow_locality_initial_placement(circuit, topology, mapping)


def _locality_initial_placement(
    circuit: CircuitGraph,
    topology: TopologyGraph,
) -> dict[int, int]:
    weighted_degrees = [sum(row) for row in circuit.iteraction_matrix]
    degrees = [
        sum(weight > 0 for weight in row)
        for row in circuit.iteraction_matrix
    ]
    logical = min(
        range(circuit.qubit_count),
        key=lambda qubit: (-degrees[qubit], -weighted_degrees[qubit], qubit),
    )
    physical = min(
        topology.graph,
        key=lambda qubit: (
            -len(topology.graph[qubit]),
            sum(
                len(topology.path_matrix[qubit][target]) - 1
                for target in topology.graph
            ),
            sum(topology.error_matrix[qubit][target] for target in topology.graph),
            qubit,
        ),
    )
    return _grow_locality_initial_placement(
        circuit,
        topology,
        {logical: physical},
    )


def _grow_locality_initial_placement(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    mapping: dict[int, int],
) -> dict[int, int]:
    weighted_degrees = [sum(row) for row in circuit.iteraction_matrix]
    degrees = [
        sum(weight > 0 for weight in row)
        for row in circuit.iteraction_matrix
    ]
    while len(mapping) < circuit.qubit_count:
        logical = min(
            (qubit for qubit in range(circuit.qubit_count) if qubit not in mapping),
            key=lambda qubit: (
                -sum(circuit.iteraction_matrix[qubit][mapped] for mapped in mapping),
                -weighted_degrees[qubit],
                -degrees[qubit],
                qubit,
            ),
        )
        physical = min(
            set(topology.graph) - set(mapping.values()),
            key=lambda qubit: (
                sum(
                    circuit.iteraction_matrix[logical][mapped]
                    * topology.error_matrix[qubit][mapped_physical]
                    for mapped, mapped_physical in mapping.items()
                ),
                sum(
                    circuit.iteraction_matrix[logical][mapped]
                    * (len(topology.path_matrix[qubit][mapped_physical]) - 1)
                    for mapped, mapped_physical in mapping.items()
                ),
                qubit,
            ),
        )
        mapping[logical] = physical

    return mapping


def _random_initial_placement(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    rng: random.Random,
) -> dict[int, int]:
    physical_qubits = rng.sample(list(topology.graph), circuit.qubit_count)
    return dict(zip(range(circuit.qubit_count), physical_qubits))


def _initial_placement_candidates(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    restarts: int,
    rng: random.Random,
) -> list[tuple[str, bool, dict[int, int]]]:
    strategies = [
        ("degree", _degree_initial_placement(circuit, topology)),
        ("interaction_pair", _interaction_pair_initial_placement(circuit, topology)),
        ("locality", _locality_initial_placement(circuit, topology)),
    ]
    base_count, remainder = divmod(restarts, 4)
    strategy_counts = [base_count + (index < remainder) for index in range(4)]
    candidates: list[tuple[str, bool, dict[int, int]]] = []

    for (strategy, initial), count in zip(strategies, strategy_counts[:3]):
        for index in range(count):
            candidate = initial.copy()
            if index:
                _perturb_placement(candidate, topology, rng)
            candidates.append((strategy, index == 0, candidate))

    for index in range(strategy_counts[3]):
        candidates.append(
            ("random", index == 0, _random_initial_placement(circuit, topology, rng))
        )

    return candidates


def _perturb_placement(
    mapping: dict[int, int],
    topology: TopologyGraph,
    rng: random.Random,
) -> None:
    physical_to_logical = {physical: logical for logical, physical in mapping.items()}
    logical_qubits = list(mapping)
    physical_qubits = list(topology.graph)
    for _ in range(rng.randint(1, max(1, len(logical_qubits)))):
        logical = rng.choice(logical_qubits)
        physical = rng.choice(physical_qubits)
        current_logical = physical_to_logical.get(physical)
        old_physical = mapping[logical]
        mapping[logical] = physical
        physical_to_logical.pop(old_physical, None)
        if current_logical is not None:
            mapping[current_logical] = old_physical
            physical_to_logical[old_physical] = current_logical
        physical_to_logical[physical] = logical


def _improve_placement(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    mapping: dict[int, int],
) -> tuple[dict[int, int], tuple[float, int]]:
    interactions = _interaction_pairs(circuit)

    def cost_for() -> tuple[float, int]:
        total_hops = 0
        for logical_1, logical_2, count in interactions:
            physical_1 = mapping[logical_1]
            physical_2 = mapping[logical_2]
            path = topology.path_matrix[physical_1][physical_2]
            if not path:
                raise ValueError(
                    "Mapped interacting qubits are disconnected in the topology"
                )
            total_hops += count * (len(path) - 1)
        return _placement_error_rate(interactions, topology, mapping), total_hops

    current_cost = cost_for()
    logical_qubits = list(range(circuit.qubit_count))

    while True:
        best_cost = current_cost
        best_move: tuple[str, int, int] | None = None

        # swaping 2 logical qubits to local minimize
        for index, logical_1 in enumerate(logical_qubits):
            for logical_2 in logical_qubits[index + 1 :]:
                mapping[logical_1], mapping[logical_2] = (
                    mapping[logical_2],
                    mapping[logical_1],
                )
                candidate_cost = cost_for()
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
            original_physical = mapping[logical]
            for physical in unused_physical:
                mapping[logical] = physical
                candidate_cost = cost_for()
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


def optimal_map(circuit: CircuitGraph, topology: TopologyGraph):
    current_physic = []

    pairs = _interaction_pairs(circuit)

    def estimate_error() -> float:
        mapping = dict(enumerate(current_physic))
        return _placement_error_rate(pairs, topology, mapping)

    min_error = float("inf")
    best_map = None

    used_physic = [False] * topology.qubit_count

    def dfs_physic():
        nonlocal min_error, best_map
        if len(current_physic) == circuit.qubit_count:
            total_error = estimate_error()
            if total_error < min_error:
                min_error = total_error
                best_map = [p for p in current_physic]
            return
        for i in range(topology.qubit_count):
            if used_physic[i]:
                continue
            used_physic[i] = True
            current_physic.append(i)
            dfs_physic()
            used_physic[i] = False
            current_physic.pop()

    dfs_physic()
    mapped = {l: p for l, p in enumerate(best_map)}

    return mapped


def heuristic_map(
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
    logical_qubits = list(range(circuit.qubit_count))
    candidates: dict[
        tuple[int, ...],
        tuple[tuple[float, int], dict[int, int]],
    ] = {}

    preserved_initial_keys: list[tuple[int, ...]] = []
    for _, is_initial, candidate in _initial_placement_candidates(
        circuit,
        topology,
        restarts,
        rng,
    ):
        if is_initial:
            initial_key = tuple(candidate[logical] for logical in logical_qubits)
            preserved_initial_keys.append(initial_key)
            candidates[initial_key] = (
                estimate_placement_cost(circuit, topology, candidate),
                candidate.copy(),
            )

        candidate, score = _improve_placement(
            circuit,
            topology,
            candidate,
        )
        key = tuple(candidate[logical] for logical in logical_qubits)
        candidates[key] = (score, candidate.copy())

    sorted_candidates = sorted(
        candidates.values(),
        key=lambda item: (
            item[0],
            tuple(item[1][logical] for logical in logical_qubits),
        ),
    )
    preserved_initial_keys = list(dict.fromkeys(preserved_initial_keys))
    finalists_by_key = {
        key: candidates[key]
        for key in preserved_initial_keys
    }
    finalist_limit = max(route_candidates, len(finalists_by_key))
    for score, placement in sorted_candidates:
        key = tuple(placement[logical] for logical in logical_qubits)
        if key not in finalists_by_key and len(finalists_by_key) < finalist_limit:
            finalists_by_key[key] = (score, placement)
    finalists = list(finalists_by_key.values())
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
        r"E:\Cesar\Python\Grafos\projeto-parte2\datasets\interaction_order\algorithms\bmw_quark_cardinality\bmw_quark_cardinality_6qubits_ordered_interactions.csv"
    )
    topology = load_topology_graph(
        r"E:\Cesar\Python\Grafos\projeto-parte2\datasets\topologies\grid\grid_10x10_100qubits_weighted_edges.csv"
    )

    iteractions = math.factorial(topology.qubit_count) // math.factorial(
        topology.qubit_count - circuit.qubit_count
    )
    print(f"Total solutions: {iteractions}")

    start_time = time.time()
    if iteractions < 10_000_000:
        print("CALCULATING OPTIMAL SOLUTION")
        placement = optimal_map(circuit, topology)
    else:
        print("CALCULATING HEURISTIC SOLUTION")
        placement = heuristic_map(circuit, topology, 1000, 45, route_candidates=1000)

    print(f"Mapping time: {time.time() - start_time:2f}s")

    routing_result = route_circuit(circuit, topology, placement)
    print("Routed SWAPs:", routing_result)

    print(
        "Estimated error and distance:",
        estimate_placement_cost(circuit, topology, routing_result.final_mapping),
    )
