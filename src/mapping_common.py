from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Callable

from src.circuit_graph.graph import CircuitEdge, CircuitGraph
from src.topology_graph.graph import TopologyGraph


_ROUTING_LOOKAHEAD = 3
_ROUTING_BEAM_WIDTH = 8


@dataclass(frozen=True)
class RoutingResult:
    swap_count: int
    expected_error_rate: float
    final_mapping: dict[int, int]


def interaction_pairs(circuit: CircuitGraph) -> list[tuple[int, int, int]]:
    return circuit.interaction_pairs


def validate_mapping(
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
    """Route interactions with error-aware paths and bounded lookahead."""
    validate_mapping(circuit, topology, mapping)
    logical_qubits = tuple(range(circuit.qubit_count))
    current_mapping = tuple(mapping[logical] for logical in logical_qubits)
    operations = [
        interaction
        for interaction in circuit.fpga
        if interaction.qubit_1 != interaction.qubit_2
    ]
    physical_neighbors = {physical: set() for physical in topology.graph}
    for physical, neighbors in topology.graph.items():
        for neighbor in neighbors:
            if neighbor != physical:
                physical_neighbors[physical].add(neighbor)
                physical_neighbors[neighbor].add(physical)

    edge_risk_cache: dict[tuple[int, int], float] = {}

    def link_risk(physical_a: int, physical_b: int) -> float:
        edge = (min(physical_a, physical_b), max(physical_a, physical_b))
        if edge not in edge_risk_cache:
            rate = topology.link_error_rate(physical_a, physical_b)
            if not 0.0 <= rate <= 1.0:
                raise ValueError(f"Invalid two-qubit gate error rate: {rate}")
            edge_risk_cache[edge] = (
                float("inf") if rate == 1.0 else -math.log1p(-rate)
            )
        return edge_risk_cache[edge]

    path_cache: dict[
        tuple[int, int],
        tuple[dict[int, tuple[float, int]], dict[int, int]],
    ] = {}

    def shortest_swap_paths(
        origin: int,
        blocked: int,
    ) -> tuple[dict[int, tuple[float, int]], dict[int, int]]:
        cache_key = (origin, blocked)
        if cache_key in path_cache:
            return path_cache[cache_key]

        distances = {origin: (0.0, 0)}
        previous: dict[int, int] = {}
        pending = [(0.0, 0, origin)]
        while pending:
            risk, hops, physical = heapq.heappop(pending)
            if (risk, hops) != distances[physical]:
                continue
            for neighbor in sorted(physical_neighbors[physical]):
                if neighbor == blocked:
                    continue
                candidate = (risk + 3.0 * link_risk(physical, neighbor), hops + 1)
                previous_distance = distances.get(neighbor)
                if previous_distance is not None and candidate >= previous_distance:
                    continue
                distances[neighbor] = candidate
                previous[neighbor] = physical
                heapq.heappush(pending, (candidate[0], candidate[1], neighbor))

        result = (distances, previous)
        path_cache[cache_key] = result
        return result

    def route_options(
        placement: tuple[int, ...],
        interaction: CircuitEdge,
    ) -> list[tuple[tuple[int, ...], float, int]]:
        logical_1 = interaction.qubit_1
        logical_2 = interaction.qubit_2
        physical_1 = placement[logical_1]
        physical_2 = placement[logical_2]
        physical_to_logical = {
            physical: logical for logical, physical in enumerate(placement)
        }
        options: dict[tuple[int, ...], tuple[float, int]] = {}

        def add_direction(origin: int, blocked: int) -> None:
            distances, previous = shortest_swap_paths(origin, blocked)
            for adjacent in sorted(physical_neighbors[blocked]):
                if adjacent not in distances:
                    continue
                path = [adjacent]
                while path[-1] != origin:
                    path.append(previous[path[-1]])
                path.reverse()

                next_placement = list(placement)
                next_physical_to_logical = physical_to_logical.copy()
                for physical_a, physical_b in zip(path, path[1:]):
                    logical_a = next_physical_to_logical.pop(physical_a, None)
                    logical_b = next_physical_to_logical.pop(physical_b, None)
                    if logical_b is not None:
                        next_placement[logical_b] = physical_a
                        next_physical_to_logical[physical_a] = logical_b
                    if logical_a is not None:
                        next_placement[logical_a] = physical_b
                        next_physical_to_logical[physical_b] = logical_a

                added_risk = distances[adjacent][0] + link_risk(
                    next_placement[logical_1],
                    next_placement[logical_2],
                )
                next_placement_tuple = tuple(next_placement)
                score = (added_risk, len(path) - 1)
                previous_score = options.get(next_placement_tuple)
                if previous_score is None or score < previous_score:
                    options[next_placement_tuple] = score

        add_direction(physical_1, physical_2)
        add_direction(physical_2, physical_1)
        if not options:
            raise ValueError("Interacting qubits are disconnected in the topology")
        return [
            (next_placement, risk, swaps)
            for next_placement, (risk, swaps) in options.items()
        ]

    total_log_risk = 0.0
    swap_count = 0
    for operation_index, interaction in enumerate(operations):
        beam = [(current_mapping, total_log_risk, swap_count, None, 0.0, 0)]
        lookahead = operations[
            operation_index : operation_index + _ROUTING_LOOKAHEAD
        ]
        for future_interaction in lookahead:
            expanded = []
            for (
                placement,
                cumulative_risk,
                cumulative_swaps,
                first_mapping,
                first_risk,
                first_swaps,
            ) in beam:
                for next_placement, added_risk, added_swaps in route_options(
                    placement,
                    future_interaction,
                ):
                    expanded.append(
                        (
                            next_placement,
                            cumulative_risk + added_risk,
                            cumulative_swaps + added_swaps,
                            next_placement if first_mapping is None else first_mapping,
                            added_risk if first_mapping is None else first_risk,
                            added_swaps if first_mapping is None else first_swaps,
                        )
                    )
            beam = sorted(
                expanded,
                key=lambda state: (state[1], state[2]),
            )[:_ROUTING_BEAM_WIDTH]

        best_state = min(beam, key=lambda state: (state[1], state[2]))
        current_mapping = best_state[3]
        total_log_risk += best_state[4]
        swap_count += best_state[5]

    return RoutingResult(
        swap_count=swap_count,
        expected_error_rate=-math.expm1(-total_log_risk),
        final_mapping=dict(zip(logical_qubits, current_mapping)),
    )


def hill_climb_placement(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    mapping: dict[int, int],
    router: Callable[
        [CircuitGraph, TopologyGraph, dict[int, int]],
        RoutingResult,
    ] = route_circuit,
) -> tuple[dict[int, int], tuple[float, int]]:
    """Find a local minimum using complete routed error and SWAP count."""
    validate_mapping(circuit, topology, mapping)
    current_mapping = mapping.copy()
    logical_qubits = list(range(circuit.qubit_count))
    score_cache: dict[tuple[int, ...], tuple[float, int]] = {}

    def routed_score(candidate: dict[int, int]) -> tuple[float, int]:
        key = tuple(candidate[logical] for logical in logical_qubits)
        if key not in score_cache:
            result = router(circuit, topology, candidate)
            score_cache[key] = (result.expected_error_rate, result.swap_count)
        return score_cache[key]

    current_score = routed_score(current_mapping)
    while True:
        best_mapping: dict[int, int] | None = None
        best_score = current_score

        for index, logical_1 in enumerate(logical_qubits):
            for logical_2 in logical_qubits[index + 1 :]:
                candidate = current_mapping.copy()
                candidate[logical_1], candidate[logical_2] = (
                    candidate[logical_2],
                    candidate[logical_1],
                )
                candidate_score = routed_score(candidate)
                if candidate_score < best_score:
                    best_mapping = candidate
                    best_score = candidate_score

        unused_physical = set(topology.graph) - set(current_mapping.values())
        for logical in logical_qubits:
            for physical in sorted(unused_physical):
                candidate = current_mapping.copy()
                candidate[logical] = physical
                candidate_score = routed_score(candidate)
                if candidate_score < best_score:
                    best_mapping = candidate
                    best_score = candidate_score

        if best_mapping is None:
            return current_mapping, current_score
        current_mapping = best_mapping
        current_score = best_score
