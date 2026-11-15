from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import os
import random
import time
import math

from src.circuit_graph.graph import CircuitGraph
from src.topology_graph.graph import TopologyGraph


_WORKER_CIRCUIT: CircuitGraph | None = None
_WORKER_TOPOLOGY: TopologyGraph | None = None


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


def _initialize_placement_worker(
    circuit: CircuitGraph,
    topology: TopologyGraph,
) -> None:
    global _WORKER_CIRCUIT, _WORKER_TOPOLOGY
    _WORKER_CIRCUIT = circuit
    _WORKER_TOPOLOGY = topology


def _improve_placement_worker(
    mapping: dict[int, int],
) -> tuple[dict[int, int], tuple[float, int]]:
    if _WORKER_CIRCUIT is None or _WORKER_TOPOLOGY is None:
        raise RuntimeError("Placement worker was not initialized")
    return _improve_placement(_WORKER_CIRCUIT, _WORKER_TOPOLOGY, mapping)


def _optimal_map_worker(
    first_physical: int,
) -> tuple[float, int, tuple[int, ...]] | None:
    if _WORKER_CIRCUIT is None or _WORKER_TOPOLOGY is None:
        raise RuntimeError("Placement worker was not initialized")
    return _optimal_map_for_prefix(
        _WORKER_CIRCUIT,
        _WORKER_TOPOLOGY,
        (first_physical,),
    )


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
    if not logical_pairs:
        return _degree_initial_placement(circuit, topology)

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
    remaining_logical = sorted(
        (logical for logical in range(circuit.qubit_count) if logical not in mapping),
        key=lambda logical: (
            -weighted_degrees[logical],
            -degrees[logical],
            logical,
        ),
    )
    remaining_physical = sorted(
        (physical for physical in topology.graph if physical not in mapping.values()),
        key=lambda physical: (
            -len(topology.graph[physical]),
            sum(
                topology.error_matrix[physical][target]
                for target in topology.graph
            ),
            physical,
        ),
    )
    mapping.update(zip(remaining_logical, remaining_physical))
    return mapping


def _initial_placement_candidates(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    initial_candidates: int,
    rng: random.Random,
) -> list[tuple[str, bool, dict[int, int]]]:
    strategies = [
        ("degree", _degree_initial_placement(circuit, topology)),
        ("interaction_pair", _interaction_pair_initial_placement(circuit, topology)),
    ]
    base_count, remainder = divmod(initial_candidates, len(strategies))
    strategy_counts = [
        base_count + (1 if index < remainder else 0)
        for index in range(len(strategies))
    ]
    candidates: list[tuple[str, bool, dict[int, int]]] = []

    for (strategy, initial), count in zip(strategies, strategy_counts):
        for index in range(count):
            candidate = initial.copy()
            if index:
                _perturb_placement(candidate, topology, rng)
            candidates.append((strategy, index == 0, candidate))

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
    paths = topology.path_matrix
    errors = topology.error_matrix
    incident_interactions: list[list[int]] = [
        [] for _ in range(circuit.qubit_count)
    ]
    physical_pair_costs: dict[tuple[int, int], tuple[bool, float, int]] = {}
    for interaction_index, (logical_1, logical_2, _) in enumerate(interactions):
        incident_interactions[logical_1].append(interaction_index)
        incident_interactions[logical_2].append(interaction_index)

    def interaction_cost(
        interaction_index: int,
    ) -> tuple[bool, float, int]:
        logical_1, logical_2, count = interactions[interaction_index]
        physical_1 = mapping[logical_1]
        physical_2 = mapping[logical_2]
        physical_pair = (physical_1, physical_2)
        pair_cost = physical_pair_costs.get(physical_pair)
        if pair_cost is None:
            path = paths[physical_1][physical_2]
            if not path:
                raise ValueError(
                    "Mapped interacting qubits are disconnected in the topology"
                )
            error = errors[physical_1][physical_2]
            pair_cost = (
                error == 1.0,
                0.0 if error == 1.0 else math.log1p(-error),
                len(path) - 1,
            )
            physical_pair_costs[physical_pair] = pair_cost

        certain_error, log_success_per_gate, hops_per_gate = pair_cost
        return (
            certain_error,
            count * log_success_per_gate,
            count * hops_per_gate,
        )

    interaction_costs = [
        interaction_cost(interaction_index)
        for interaction_index in range(len(interactions))
    ]
    total_log_success = sum(
        log_success
        for certain_error, log_success, _ in interaction_costs
        if not certain_error
    )
    certain_error_count = sum(
        certain_error for certain_error, _, _ in interaction_costs
    )
    total_hops = sum(hops for _, _, hops in interaction_costs)
    logical_qubits = list(range(circuit.qubit_count))
    logical_swaps = [
        (
            logical_1,
            logical_2,
            sorted(
                set(incident_interactions[logical_1])
                | set(incident_interactions[logical_2])
            ),
        )
        for index, logical_1 in enumerate(logical_qubits)
        for logical_2 in logical_qubits[index + 1 :]
    ]

    def cost_from_totals(
        log_success: float,
        certain_errors: int,
        hops: int,
    ) -> tuple[float, int]:
        error_rate = (
            1.0
            if certain_errors
            else -math.expm1(log_success)
        )
        return error_rate, hops

    def evaluate_affected(
        affected: list[int],
    ) -> tuple[
        tuple[float, int],
        tuple[float, int, int],
    ]:
        candidate_log_success = total_log_success
        candidate_certain_errors = certain_error_count
        candidate_hops = total_hops
        for interaction_index in affected:
            old_cost = interaction_costs[interaction_index]
            new_cost = interaction_cost(interaction_index)

            old_certain, old_log_success, old_hops = old_cost
            new_certain, new_log_success, new_hops = new_cost
            candidate_certain_errors += int(new_certain) - int(old_certain)
            if not old_certain:
                candidate_log_success -= old_log_success
            if not new_certain:
                candidate_log_success += new_log_success
            candidate_hops += new_hops - old_hops

        totals = (
            candidate_log_success,
            candidate_certain_errors,
            candidate_hops,
        )
        return (
            cost_from_totals(*totals),
            totals,
        )

    current_cost = cost_from_totals(
        total_log_success,
        certain_error_count,
        total_hops,
    )

    while True:
        best_cost = current_cost
        best_move: tuple[str, int, int] | None = None
        best_affected: list[int] = []
        best_totals = (total_log_success, certain_error_count, total_hops)

        # swaping 2 logical qubits to local minimize
        for logical_1, logical_2, affected in logical_swaps:
            mapping[logical_1], mapping[logical_2] = (
                mapping[logical_2],
                mapping[logical_1],
            )
            candidate_cost, totals = evaluate_affected(affected)
            mapping[logical_1], mapping[logical_2] = (
                mapping[logical_2],
                mapping[logical_1],
            )
            if candidate_cost < best_cost:
                best_cost = candidate_cost
                best_move = ("swap", logical_1, logical_2)
                best_affected = affected
                best_totals = totals

        # swap 2 physical qubits to local minimize
        unused_physical = set(topology.graph) - set(mapping.values())
        for logical in logical_qubits:
            original_physical = mapping[logical]
            for physical in unused_physical:
                mapping[logical] = physical
                affected = incident_interactions[logical]
                candidate_cost, totals = evaluate_affected(affected)
                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_move = ("move", logical, physical)
                    best_affected = affected
                    best_totals = totals
            mapping[logical] = original_physical

        if best_move is None:
            break
        move_type, first, second = best_move
        if move_type == "swap":
            mapping[first], mapping[second] = mapping[second], mapping[first]
        else:
            mapping[first] = second
        current_cost = best_cost
        for interaction_index in best_affected:
            interaction_costs[interaction_index] = interaction_cost(
                interaction_index
            )
        total_log_success, certain_error_count, total_hops = best_totals

    return mapping, current_cost


def _optimal_map_for_prefix(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    prefix: tuple[int, ...],
) -> tuple[float, int, tuple[int, ...]] | None:
    current_physic = list(prefix)
    best_score: tuple[float, int, tuple[int, ...]] | None = None
    used_physic = [False] * topology.qubit_count
    for physical in prefix:
        used_physic[physical] = True

    def dfs_physic():
        nonlocal best_score
        if len(current_physic) == circuit.qubit_count:
            mapping = dict(enumerate(current_physic))
            routing_result = route_circuit(circuit, topology, mapping)
            score = (
                routing_result.expected_error_rate,
                routing_result.swap_count,
                tuple(current_physic),
            )
            if best_score is None or score < best_score:
                best_score = score
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
    return best_score


def optimal_map(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    max_workers: int | None = None,
) -> dict[int, int]:
    """Return the exact best placement, parallelizing the exhaustive search."""
    if max_workers is not None and max_workers < 1:
        raise ValueError("max_workers must be at least 1")

    prefixes = list(range(topology.qubit_count))
    worker_count = min(
        max_workers if max_workers is not None else (os.cpu_count() or 1),
        len(prefixes),
    )
    if worker_count > 1:
        with ProcessPoolExecutor(
            max_workers=worker_count,
            initializer=_initialize_placement_worker,
            initargs=(circuit, topology),
        ) as executor:
            scores = executor.map(_optimal_map_worker, prefixes)
            best_score = min(
                (score for score in scores if score is not None),
                default=None,
            )
    else:
        scores = (
            _optimal_map_for_prefix(circuit, topology, (prefix,))
            for prefix in prefixes
        )
        best_score = min(
            (score for score in scores if score is not None),
            default=None,
        )

    if best_score is None:
        raise ValueError("No valid placement exists for this circuit and topology")
    return {logical: physical for logical, physical in enumerate(best_score[2])}


def heuristic_map(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    initial_candidates: int = 100,
    seed: int | None = 0,
    max_workers: int | None = None,
) -> dict[int, int]:
    """Find a placement with multiple initial candidates and local search.

    Local search prioritizes proxy error rate, then weighted hop distance.
    All distinct locally improved candidates and the preserved strategy starts
    are routed in circuit order and ranked by exact expected error rate before
    SWAP count.
    Initial candidates are split evenly across degree-based and most-frequent
    interaction-pair starts. The unperturbed start from each strategy is
    preserved for routing alongside every distinct placement found by hill
    climbing. Hill climbing runs in separate processes by default; set
    ``max_workers=1`` to run it sequentially. A fixed seed makes the starts
    reproducible.
    """
    if initial_candidates < 1:
        raise ValueError("initial_candidates must be at least 1")
    if max_workers is not None and max_workers < 1:
        raise ValueError("max_workers must be at least 1")

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

    initial_starts = _initial_placement_candidates(
        circuit,
        topology,
        initial_candidates,
        rng,
    )
    worker_count = min(
        max_workers if max_workers is not None else (os.cpu_count() or 1),
        len(initial_starts),
    )
    if worker_count > 1:
        with ProcessPoolExecutor(
            max_workers=worker_count,
            initializer=_initialize_placement_worker,
            initargs=(circuit, topology),
        ) as executor:
            improved_starts = executor.map(
                _improve_placement_worker,
                (candidate.copy() for _, _, candidate in initial_starts),
            )
            improved_candidates = list(improved_starts)
    else:
        improved_candidates = [
            _improve_placement(circuit, topology, candidate.copy())
            for _, _, candidate in initial_starts
        ]

    for (_, is_initial, initial_candidate), (candidate, score) in zip(
        initial_starts,
        improved_candidates,
    ):
        initial_key = tuple(
            initial_candidate[logical] for logical in logical_qubits
        )
        if is_initial:
            candidates.setdefault(
                initial_key,
                (
                    score,
                    initial_candidate,
                ),
            )

        key = tuple(candidate[logical] for logical in logical_qubits)
        existing = candidates.get(key)
        if existing is None or score < existing[0]:
            candidates[key] = (score, candidate.copy())

    routed_finalists = [
        (
            route_circuit(circuit, topology, placement),
            score,
            placement,
        )
        for score, placement in candidates.values()
    ]
    best_candidate = min(
        routed_finalists,
        key=lambda item: (
            item[0].expected_error_rate,
            item[0].swap_count,
            item[1][0],
            item[1][1],
            tuple(item[2][logical] for logical in logical_qubits),
        ),
    )
    return best_candidate[2]


if __name__ == "__main__":
    from src.circuit_graph.loader import load_circuit_graph
    from src.topology_graph.loader import load_topology_graph

    circuit = load_circuit_graph(
        r"E:\Cesar\Python\Grafos\projeto-parte2\datasets\interaction_order\algorithms\bmw_quark_copula\bmw_quark_copula_6qubits_ordered_interactions.csv"
    )
    topology = load_topology_graph(
        r"E:\Cesar\Python\Grafos\projeto-parte2\datasets\topologies\full\full_14qubits_weighted_edges.csv"
    )

    iteractions = math.factorial(topology.qubit_count) // math.factorial(
        topology.qubit_count - circuit.qubit_count
    )
    print(f"Total solutions: {iteractions}")

    start_time = time.time()
    if iteractions < 100_000_000:
        print("CALCULATING OPTIMAL SOLUTION")
        placement = optimal_map(circuit, topology)
    else:
        print("CALCULATING HEURISTIC SOLUTION")
        placement = heuristic_map(
            circuit,
            topology,
            initial_candidates=1000,
            seed=42,
        )

    print(f"Mapping time: {time.time() - start_time:2f}s")

    routing_result = route_circuit(circuit, topology, placement)
    print("Routing result:", routing_result)

    print("Expected routed error:", routing_result.expected_error_rate)
