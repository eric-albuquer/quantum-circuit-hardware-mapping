from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.circuit_graph.graph import CircuitGraph
from src.topology_graph.graph import TopologyGraph


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
    """Route ordered interactions and return the final placement and route metrics."""
    validate_mapping(circuit, topology, mapping)
    final_mapping = mapping.copy()
    physical_to_logical = {
        physical: logical for logical, physical in mapping.items()
    }
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
