import random
import unittest
from collections import Counter
from unittest.mock import patch

from src.circuit_graph.graph import CircuitEdge, CircuitGraph
from src.mapping import (
    RoutingResult,
    _interaction_pair_initial_placement,
    _locality_initial_placement,
    _improve_placement,
    _initial_placement_candidates,
    estimate_placement_cost,
    heuristic_map,
    optimal_map,
    route_circuit,
)
from src.topology_graph.graph import TopologyEdge, TopologyGraph


def make_circuit(qubit_count: int, interactions: list[tuple[int, int]]) -> CircuitGraph:
    edges = [
        CircuitEdge(
            "test",
            "test",
            qubit_count,
            index,
            index,
            "cx",
            logical_1,
            logical_2,
        )
        for index, (logical_1, logical_2) in enumerate(interactions)
    ]
    return CircuitGraph(edges)


def make_topology(links: list[tuple[int, int]], qubit_count: int) -> TopologyGraph:
    edges = []
    for source, target in links:
        edges.append(TopologyEdge(source, target, 0.01, 1.0))
        edges.append(TopologyEdge(target, source, 0.01, 1.0))
    for qubit in range(qubit_count):
        if not any(edge.qubit_1 == qubit for edge in edges):
            edges.append(TopologyEdge(qubit, qubit, 0.01, 1.0))
    return TopologyGraph(edges)


class MappingTests(unittest.TestCase):
    def test_placement_searches_combine_interaction_errors_as_probabilities(self):
        circuit = make_circuit(2, [(0, 1), (0, 1)])
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.1, 0.9),
                TopologyEdge(1, 0, 0.1, 0.9),
            ]
        )

        _, heuristic_cost = _improve_placement(
            circuit,
            topology,
            {0: 0, 1: 1},
        )
        optimal_mapping = optimal_map(circuit, topology)
        optimal_error, _ = estimate_placement_cost(
            circuit,
            topology,
            optimal_mapping,
        )

        self.assertAlmostEqual(heuristic_cost[0], 1.0 - 0.9**2)
        self.assertAlmostEqual(optimal_error, 1.0 - 0.9**2)
        estimated_error, estimated_distance = estimate_placement_cost(
            circuit,
            topology,
            {0: 0, 1: 1},
        )
        self.assertAlmostEqual(estimated_error, 1.0 - 0.9**2)
        self.assertEqual(estimated_distance, 2)

    def test_topology_precomputes_minimum_error_paths_with_dijkstra(self):
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.05, 1.0),
                TopologyEdge(1, 0, 0.05, 1.0),
                TopologyEdge(1, 2, 0.05, 1.0),
                TopologyEdge(2, 1, 0.05, 1.0),
                TopologyEdge(0, 2, 0.9, 1.0),
                TopologyEdge(2, 0, 0.9, 1.0),
            ]
        )

        self.assertEqual(topology.path_matrix[0][2], [0, 1, 2])
        self.assertEqual(topology.path_matrix[0][1], [0, 1])
        self.assertAlmostEqual(topology.error_matrix[0][2], 1.0 - 0.95**2)
        self.assertAlmostEqual(topology.error_matrix[0][1], 0.05)

    def test_dijkstra_keeps_paths_with_certain_error_reachable(self):
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 1.0, 1.0),
                TopologyEdge(1, 0, 1.0, 1.0),
                TopologyEdge(1, 2, 0.0, 1.0),
                TopologyEdge(2, 1, 0.0, 1.0),
            ]
        )

        self.assertEqual(topology.path_matrix[0][2], [0, 1, 2])
        self.assertEqual(topology.error_matrix[0][2], 1.0)

    def test_multi_start_mapping_is_reproducible_and_injective(self):
        circuit = make_circuit(4, [(0, 1), (0, 1), (0, 2), (1, 3)])
        topology = make_topology([(0, 1), (1, 2), (2, 3), (3, 4)], 5)

        first = heuristic_map(circuit, topology, restarts=8, seed=7)
        second = heuristic_map(circuit, topology, restarts=8, seed=7)

        self.assertEqual(first, second)
        self.assertEqual(set(first), set(range(4)))
        self.assertEqual(len(set(first.values())), 4)
        self.assertLessEqual(
            estimate_placement_cost(circuit, topology, first)[1],
            estimate_placement_cost(
                circuit,
                topology,
                {0: 0, 1: 4, 2: 1, 3: 3},
            )[1],
        )

    def test_interaction_pair_start_places_most_frequent_pair_adjacent(self):
        circuit = make_circuit(4, [(0, 1), (0, 1), (0, 1), (0, 2), (2, 3)])
        topology = make_topology([(0, 1), (1, 2), (2, 3), (3, 4)], 5)

        placement = _interaction_pair_initial_placement(circuit, topology)

        self.assertEqual(len(set(placement.values())), 4)
        self.assertEqual(
            len(topology.path_matrix[placement[0]][placement[1]]),
            2,
        )

    def test_locality_start_uses_a_high_degree_physical_qubit_for_circuit_hub(self):
        circuit = make_circuit(4, [(0, 1), (0, 2), (0, 3), (1, 2)])
        topology = make_topology(
            [(0, 1), (1, 2), (1, 3), (3, 4)],
            5,
        )

        placement = _locality_initial_placement(circuit, topology)
        physical_degrees = [len(neighbors) for neighbors in topology.graph.values()]

        self.assertEqual(
            len(topology.graph[placement[0]]),
            max(physical_degrees),
        )
        self.assertEqual(len(set(placement.values())), 4)

    def test_thousand_initial_candidates_are_evenly_split_and_reproducible(self):
        circuit = make_circuit(4, [(0, 1), (0, 1), (0, 2), (1, 3)])
        topology = make_topology([(0, 1), (1, 2), (2, 3), (3, 4)], 5)

        first = _initial_placement_candidates(
            circuit,
            topology,
            1000,
            random.Random(7),
        )
        second = _initial_placement_candidates(
            circuit,
            topology,
            1000,
            random.Random(7),
        )

        self.assertEqual(first, second)
        self.assertEqual(len(first), 1000)
        self.assertEqual(
            Counter(strategy for strategy, _, _ in first),
            {
                "degree": 250,
                "interaction_pair": 250,
                "locality": 250,
                "random": 250,
            },
        )
        for _, _, candidate in first:
            self.assertEqual(set(candidate), set(range(4)))
            self.assertEqual(len(set(candidate.values())), 4)

    def test_non_divisible_restart_count_distributes_remainder_in_order(self):
        circuit = make_circuit(3, [(0, 1), (1, 2)])
        topology = make_topology([(0, 1), (1, 2)], 3)

        candidates = _initial_placement_candidates(
            circuit,
            topology,
            10,
            random.Random(7),
        )

        self.assertEqual(
            Counter(strategy for strategy, _, _ in candidates),
            {
                "degree": 3,
                "interaction_pair": 3,
                "locality": 2,
                "random": 2,
            },
        )

    def test_initial_candidate_from_each_strategy_is_preserved_for_routing(self):
        circuit = make_circuit(4, [(0, 1), (0, 1), (0, 2), (1, 3)])
        topology = make_topology([(0, 1), (1, 2), (2, 3), (3, 4)], 5)
        initial_candidates = _initial_placement_candidates(
            circuit,
            topology,
            8,
            random.Random(7),
        )
        initial_keys = {
            tuple(candidate[logical] for logical in range(4))
            for _, is_initial, candidate in initial_candidates
            if is_initial
        }
        routed_mappings = []

        def discard_start_with_local_improvement(circuit, topology, mapping):
            improved = {logical: logical for logical in range(circuit.qubit_count)}
            return improved, estimate_placement_cost(circuit, topology, improved)

        def record_routed_mapping(circuit, topology, mapping):
            routed_mappings.append(mapping.copy())
            return RoutingResult(0, 0.0, mapping.copy())

        with (
            patch(
                "src.mapping._improve_placement",
                side_effect=discard_start_with_local_improvement,
            ),
            patch(
                "src.mapping.route_circuit",
                side_effect=record_routed_mapping,
            ),
        ):
            heuristic_map(circuit, topology, restarts=8, seed=7, route_candidates=1)

        routed_keys = {
            tuple(mapping[logical] for logical in range(4))
            for mapping in routed_mappings
        }
        self.assertTrue(initial_keys.issubset(routed_keys))

    def test_routing_counts_swaps_and_updates_mapping(self):
        circuit = make_circuit(3, [(0, 2), (0, 1)])
        topology = make_topology([(0, 1), (1, 2)], 3)

        result = route_circuit(circuit, topology, {0: 0, 1: 1, 2: 2})

        self.assertEqual(result.swap_count, 1)
        self.assertEqual(result.final_mapping, {0: 1, 1: 0, 2: 2})
        self.assertAlmostEqual(result.expected_error_rate, 1.0 - 0.99**5)

    def test_unused_physical_qubits_can_be_used_during_routing(self):
        circuit = make_circuit(2, [(0, 1)])
        topology = make_topology([(0, 1), (1, 2)], 3)

        result = route_circuit(circuit, topology, {0: 0, 1: 2})

        self.assertEqual(result.swap_count, 1)
        self.assertEqual(result.final_mapping, {0: 1, 1: 2})
        self.assertAlmostEqual(result.expected_error_rate, 1.0 - 0.99**4)

    def test_link_error_uses_mean_of_available_directed_rates(self):
        circuit = make_circuit(2, [(0, 1)])
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.1, 0.9),
                TopologyEdge(1, 0, 0.2, 0.8),
            ]
        )

        result = route_circuit(circuit, topology, {0: 0, 1: 1})

        self.assertAlmostEqual(result.expected_error_rate, 0.15)

    def test_route_uses_edge_error_not_precomputed_path_error(self):
        circuit = make_circuit(2, [(0, 1)])
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.8, 1.0),
                TopologyEdge(1, 0, 0.8, 1.0),
                TopologyEdge(0, 2, 0.01, 1.0),
                TopologyEdge(2, 0, 0.01, 1.0),
                TopologyEdge(2, 1, 0.01, 1.0),
                TopologyEdge(1, 2, 0.01, 1.0),
            ]
        )

        result = route_circuit(circuit, topology, {0: 0, 1: 1})

        self.assertEqual(result.swap_count, 1)
        self.assertAlmostEqual(result.expected_error_rate, 1.0 - 0.99**4)

    def test_mapping_rejects_disconnected_topology(self):
        circuit = make_circuit(2, [(0, 1)])
        topology = make_topology([(0, 1), (2, 3)], 4)

        with self.assertRaisesRegex(ValueError, "must be connected"):
            heuristic_map(circuit, topology)


if __name__ == "__main__":
    unittest.main()
