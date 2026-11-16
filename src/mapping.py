from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import math
import os
import random
import time
from typing import Literal

from src.circuit_graph.graph import CircuitGraph
from src.mapping_common import (
    RoutingResult,
    hill_climb_placement,
    interaction_pairs,
    route_circuit,
    validate_mapping,
)
from src.topology_graph.graph import TopologyGraph


_WORKER_CIRCUIT: CircuitGraph | None = None
_WORKER_TOPOLOGY: TopologyGraph | None = None


@dataclass(frozen=True)
class MappingRoutingResult:
    solution_count: int
    algorithm: Literal["exact", "heuristic"]
    initial_mapping: dict[int, int]
    routing: RoutingResult
    elapsed_seconds: float


def count_possible_mappings(
    circuit: CircuitGraph,
    topology: TopologyGraph,
) -> int:
    """Return the number of injective logical-to-physical placements."""
    if topology.qubit_count < circuit.qubit_count:
        raise ValueError(
            f"Incompatible topology for this circuit: "
            f"t: {topology.qubit_count} < c: {circuit.qubit_count}"
        )
    return math.perm(topology.qubit_count, circuit.qubit_count)


_interaction_pairs = interaction_pairs


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


_validate_mapping = validate_mapping


def _degree_initial_placement(
    circuit: CircuitGraph,
    topology: TopologyGraph,
) -> dict[int, int]:
    logical_qubits = [
        (logical, circuit.qubit_degree[logical], circuit.qubit_interactions[logical])
        for logical in range(circuit.qubit_count)
    ]
    logical_qubits.sort(key=lambda item: (-item[1], -item[2], item[0]))

    physical_qubits = []
    for physical in topology.graph:
        physical_qubits.append(
            (
                physical,
                topology.qubit_degree[physical],
                topology.mean_distance[physical],
                topology.mean_path_error[physical],
            )
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
    weighted_degrees = circuit.qubit_interactions
    degrees = circuit.qubit_degree
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
            -(
                topology.qubit_degree[pair[0]]
                + topology.qubit_degree[pair[1]]
            ),
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
        topology.qubit_degree[physical_1],
        -physical_1,
    ) < (
        topology.qubit_degree[physical_2],
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
            -topology.qubit_degree[physical],
            topology.mean_path_error[physical],
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
    strategies: list[tuple[str, dict[int, int] | None]] = [
        ("random", None),
        ("degree", _degree_initial_placement(circuit, topology)),
        ("interaction_pair", _interaction_pair_initial_placement(circuit, topology)),
    ]
    physical_qubits = sorted(topology.graph)
    base_count, remainder = divmod(initial_candidates, len(strategies))
    strategy_counts = [
        base_count + (1 if index < remainder else 0)
        for index in range(len(strategies))
    ]
    candidates: list[tuple[str, bool, dict[int, int]]] = []

    for (strategy, initial), count in zip(strategies, strategy_counts):
        for index in range(count):
            if strategy == "random":
                candidate = dict(
                    zip(
                        range(circuit.qubit_count),
                        rng.sample(physical_qubits, circuit.qubit_count),
                    )
                )
            else:
                if initial is None:
                    raise RuntimeError(f"Missing initial placement for {strategy}")
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
    return hill_climb_placement(
        circuit,
        topology,
        mapping,
        router=route_circuit,
    )


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
    """Find a placement with multi-start hill climbing over routed outcomes.

    Every neighborhood candidate is routed in circuit order and scored by
    expected error rate before SWAP count. Distinct local minima and preserved
    strategy starts are ranked by the same routed objective.
    Initial candidates are split evenly across random, degree-based, and
    most-frequent interaction-pair starts. The first random placement and the
    unperturbed start from each deterministic strategy are preserved for
    routing alongside every distinct placement found by hill climbing.
    Hill climbing runs in separate processes by default; set
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
    candidates: dict[tuple[int, ...], dict[int, int]] = {}

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

    for (_, is_initial, initial_candidate), (candidate, _) in zip(
        initial_starts,
        improved_candidates,
    ):
        initial_key = tuple(initial_candidate[logical] for logical in logical_qubits)
        if is_initial:
            candidates.setdefault(initial_key, initial_candidate.copy())

        key = tuple(candidate[logical] for logical in logical_qubits)
        candidates.setdefault(key, candidate.copy())

    routed_finalists = [
        (route_circuit(circuit, topology, placement), placement)
        for placement in candidates.values()
    ]
    best_candidate = min(
        routed_finalists,
        key=lambda item: (
            item[0].expected_error_rate,
            item[0].swap_count,
            tuple(item[1][logical] for logical in logical_qubits),
        ),
    )
    return best_candidate[1]


def map_and_route(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    exact_search_limit: int = 100_000_000,
    initial_candidates: int = 1000,
    seed: int | None = 42,
    max_workers: int | None = None,
) -> MappingRoutingResult:
    """Choose exact or heuristic placement, then route the circuit."""
    if exact_search_limit < 0:
        raise ValueError("exact_search_limit must be non-negative")

    solution_count = count_possible_mappings(circuit, topology)
    start_time = time.perf_counter()
    if solution_count < exact_search_limit:
        algorithm: Literal["exact", "heuristic"] = "exact"
        initial_mapping = optimal_map(circuit, topology, max_workers=max_workers)
    else:
        algorithm = "heuristic"
        initial_mapping = heuristic_map(
            circuit,
            topology,
            initial_candidates=initial_candidates,
            seed=seed,
            max_workers=max_workers,
        )
    routing = route_circuit(circuit, topology, initial_mapping)
    return MappingRoutingResult(
        solution_count=solution_count,
        algorithm=algorithm,
        initial_mapping=initial_mapping,
        routing=routing,
        elapsed_seconds=time.perf_counter() - start_time,
    )


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
        default=1_000_000,
        help="Use exact search only when the solution count is below this limit.",
    )
    parser.add_argument(
        "--initial-candidates",
        type=int,
        default=10,
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
    result = map_and_route(
        circuit,
        topology,
        exact_search_limit=args.exact_search_limit,
        initial_candidates=args.initial_candidates,
        seed=args.seed,
        max_workers=args.max_workers,
    )

    algorithm_name = (
        "Exact placement search (optimal_map; shortest-risk-path routing)"
        if result.algorithm == "exact"
        else "Heuristic placement search (heuristic_map; shortest-risk-path routing)"
    )
    print(f"Possible placements: {result.solution_count:.3e}")
    print(f"Method used: {algorithm_name}")
    print(f"Initial mapping: {result.initial_mapping}")
    print(f"Routing result: {result.routing}")
    print(f"Expected routed error: {result.routing.expected_error_rate}")
    print(f"Total time: {result.elapsed_seconds:.2f}s")


if __name__ == "__main__":
    main()
