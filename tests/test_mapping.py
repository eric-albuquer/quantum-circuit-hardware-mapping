import random
import unittest
from unittest.mock import patch

from src.circuit_graph.graph import CircuitEdge, CircuitGraph
from src.mapping import (
    RoutingResult,
    _interaction_pair_initial_placement,
    _improve_placement,
    _initial_placement_candidates,
    count_possible_mappings,
    heuristic_map,
    map_and_route,
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


def routed_placement_cost(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    mapping: dict[int, int],
) -> tuple[float, int]:
    result = route_circuit(circuit, topology, mapping)
    return result.expected_error_rate, result.swap_count


class MappingTests(unittest.TestCase):
    def test_count_possible_mappings_uses_injective_placements(self):
        circuit = make_circuit(2, [(0, 1)])
        topology = make_topology([(0, 1), (1, 2)], 3)

        self.assertEqual(count_possible_mappings(circuit, topology), 6)

    @patch("src.mapping.heuristic_map")
    @patch("src.mapping.optimal_map")
    def test_main_mapping_flow_selects_exact_search_below_limit(
        self,
        optimal_map_mock,
        heuristic_map_mock,
    ):
        circuit = make_circuit(2, [(0, 1)])
        topology = make_topology([(0, 1), (1, 2)], 3)
        optimal_map_mock.return_value = {0: 0, 1: 1}

        result = map_and_route(circuit, topology, exact_search_limit=7)

        self.assertEqual(result.solution_count, 6)
        self.assertEqual(result.algorithm, "exact")
        self.assertEqual(result.routing.swap_count, 0)
        optimal_map_mock.assert_called_once()
        heuristic_map_mock.assert_not_called()

    @patch("src.mapping.heuristic_map")
    @patch("src.mapping.optimal_map")
    def test_main_mapping_flow_selects_heuristic_at_limit(
        self,
        optimal_map_mock,
        heuristic_map_mock,
    ):
        circuit = make_circuit(2, [(0, 1)])
        topology = make_topology([(0, 1), (1, 2)], 3)
        heuristic_map_mock.return_value = {0: 0, 1: 1}

        result = map_and_route(circuit, topology, exact_search_limit=6)

        self.assertEqual(result.algorithm, "heuristic")
        self.assertEqual(result.routing.swap_count, 0)
        heuristic_map_mock.assert_called_once()
        optimal_map_mock.assert_not_called()

    def test_count_possible_mappings_rejects_too_few_physical_qubits(self):
        circuit = make_circuit(2, [(0, 1)])
        topology = make_topology([], 1)

        with self.assertRaises(ValueError):
            count_possible_mappings(circuit, topology)

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
        optimal_error = route_circuit(
            circuit,
            topology,
            optimal_mapping,
        ).expected_error_rate

        self.assertAlmostEqual(heuristic_cost[0], 1.0 - 0.9**2)
        self.assertAlmostEqual(optimal_error, 1.0 - 0.9**2)

    def test_hill_climbing_scores_the_complete_routed_result(self):
        circuit = make_circuit(2, [(0, 1)])
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 1.0, 0.0),
                TopologyEdge(1, 0, 1.0, 0.0),
            ]
        )

        mapping, cost = _improve_placement(circuit, topology, {0: 0, 1: 1})

        self.assertEqual(mapping, {0: 0, 1: 1})
        self.assertEqual(cost, (1.0, 0))

    def test_hill_climb_returns_a_local_minimum_of_routed_cost(self):
        circuit = make_circuit(4, [(0, 1), (0, 1), (0, 2), (1, 3), (2, 3)])
        topology = make_topology([(0, 1), (1, 2), (2, 3), (3, 4)], 5)

        mapping, delta_cost = _improve_placement(
            circuit,
            topology,
            {0: 0, 1: 2, 2: 3, 3: 4},
        )
        full_cost = routed_placement_cost(circuit, topology, mapping)
        self.assertAlmostEqual(delta_cost[0], full_cost[0])
        self.assertEqual(delta_cost[1], full_cost[1])

        logical_qubits = list(range(circuit.qubit_count))
        for index, logical_1 in enumerate(logical_qubits):
            for logical_2 in logical_qubits[index + 1 :]:
                mapping[logical_1], mapping[logical_2] = (
                    mapping[logical_2],
                    mapping[logical_1],
                )
                self.assertGreaterEqual(
                    routed_placement_cost(circuit, topology, mapping),
                    full_cost,
                )
                mapping[logical_1], mapping[logical_2] = (
                    mapping[logical_2],
                    mapping[logical_1],
                )

        unused_physical = set(topology.graph) - set(mapping.values())
        for logical in logical_qubits:
            original_physical = mapping[logical]
            for physical in unused_physical:
                mapping[logical] = physical
                self.assertGreaterEqual(
                    routed_placement_cost(circuit, topology, mapping),
                    full_cost,
                )
            mapping[logical] = original_physical

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

        first = heuristic_map(
            circuit,
            topology,
            initial_candidates=8,
            seed=7,
            max_workers=1,
        )
        second = heuristic_map(
            circuit,
            topology,
            initial_candidates=8,
            seed=7,
            max_workers=1,
        )

        self.assertEqual(first, second)
        self.assertEqual(set(first), set(range(4)))
        self.assertEqual(len(set(first.values())), 4)
        routed_result = route_circuit(circuit, topology, first)
        self.assertGreaterEqual(routed_result.expected_error_rate, 0.0)
        self.assertLessEqual(routed_result.expected_error_rate, 1.0)

    def test_parallel_hill_climbing_matches_sequential_result(self):
        circuit = make_circuit(4, [(0, 1), (0, 1), (0, 2), (1, 3)])
        topology = make_topology([(0, 1), (1, 2), (2, 3), (3, 4)], 5)

        sequential = heuristic_map(
            circuit,
            topology,
            initial_candidates=8,
            seed=7,
            max_workers=1,
        )
        parallel = heuristic_map(
            circuit,
            topology,
            initial_candidates=8,
            seed=7,
            max_workers=2,
        )

        self.assertEqual(parallel, sequential)

    def test_optimal_map_minimizes_routed_error_including_swaps(self):
        circuit = make_circuit(3, [(0, 2), (1, 2), (0, 1), (0, 2)])
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.002, 0.998),
                TopologyEdge(1, 0, 0.002, 0.998),
                TopologyEdge(1, 2, 0.04, 0.96),
                TopologyEdge(2, 1, 0.04, 0.96),
                TopologyEdge(2, 3, 0.008, 0.992),
                TopologyEdge(3, 2, 0.008, 0.992),
            ]
        )

        candidates = [
            {0: physical_0, 1: physical_1, 2: physical_2}
            for physical_0 in range(4)
            for physical_1 in range(4)
            for physical_2 in range(4)
            if len({physical_0, physical_1, physical_2}) == 3
        ]
        best_score = min(
            (
                result.expected_error_rate,
                result.swap_count,
                tuple(mapping[logical] for logical in range(3)),
            )
            for mapping in candidates
            for result in [route_circuit(circuit, topology, mapping)]
        )

        mapping = optimal_map(circuit, topology)
        result = route_circuit(circuit, topology, mapping)
        self.assertEqual(
            (
                result.expected_error_rate,
                result.swap_count,
                tuple(mapping[logical] for logical in range(3)),
            ),
            best_score,
        )

    def test_parallel_optimal_map_matches_sequential_result(self):
        circuit = make_circuit(4, [(0, 1), (0, 1), (0, 2), (1, 3)])
        topology = make_topology([(0, 1), (1, 2), (2, 3), (3, 4)], 5)

        sequential = optimal_map(circuit, topology, max_workers=1)
        parallel = optimal_map(circuit, topology, max_workers=2)

        self.assertEqual(parallel, sequential)

    def test_optimal_map_rejects_nonpositive_worker_count(self):
        circuit = make_circuit(2, [(0, 1)])
        topology = make_topology([(0, 1)], 2)

        with self.assertRaisesRegex(ValueError, "max_workers must be at least 1"):
            optimal_map(circuit, topology, max_workers=0)

    def test_interaction_pair_start_places_most_frequent_pair_adjacent(self):
        circuit = make_circuit(4, [(0, 1), (0, 1), (0, 1), (0, 2), (2, 3)])
        topology = make_topology([(0, 1), (1, 2), (2, 3), (3, 4)], 5)

        placement = _interaction_pair_initial_placement(circuit, topology)

        self.assertEqual(len(set(placement.values())), 4)
        self.assertEqual(
            len(topology.path_matrix[placement[0]][placement[1]]),
            2,
        )

    def test_thousand_initial_candidates_are_balanced_and_reproducible(self):
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
        self.assertEqual(sum(is_initial for _, is_initial, _ in first), 3)
        strategy_counts = {
            strategy: 0 for strategy in ("random", "degree", "interaction_pair")
        }
        for strategy, _, _ in first:
            strategy_counts[strategy] += 1
        self.assertEqual(
            strategy_counts,
            {
                "random": 334,
                "degree": 333,
                "interaction_pair": 333,
            },
        )
        for _, _, candidate in first:
            self.assertEqual(set(candidate), set(range(4)))
            self.assertEqual(len(set(candidate.values())), 4)

    def test_non_divisible_candidate_count_distributes_remainder_deterministically(self):
        circuit = make_circuit(3, [(0, 1), (1, 2)])
        topology = make_topology([(0, 1), (1, 2)], 3)

        candidates = _initial_placement_candidates(
            circuit,
            topology,
            9,
            random.Random(7),
        )

        self.assertEqual(len(candidates), 9)
        self.assertEqual(
            [strategy for strategy, _, _ in candidates],
            [
                "random",
                "random",
                "random",
                "degree",
                "degree",
                "degree",
                "interaction_pair",
                "interaction_pair",
                "interaction_pair",
            ],
        )

    def test_single_candidate_budget_uses_random_placement_strategy(self):
        circuit = make_circuit(2, [(0, 1)])
        topology = make_topology([(0, 1), (1, 2)], 3)

        candidates = _initial_placement_candidates(
            circuit,
            topology,
            1,
            random.Random(7),
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0][0], "random")
        self.assertTrue(candidates[0][1])
        self.assertEqual(set(candidates[0][2]), {0, 1})
        self.assertEqual(len(set(candidates[0][2].values())), 2)

    def test_unperturbed_strategy_starts_are_preserved_for_routing(self):
        circuit = make_circuit(4, [(0, 1), (0, 1), (0, 2), (1, 3)])
        topology = make_topology([(0, 1), (1, 2), (2, 3), (3, 4)], 5)
        initial_candidates = _initial_placement_candidates(
            circuit,
            topology,
            8,
            random.Random(7),
        )
        routed_mappings = []

        def discard_start_with_local_improvement(circuit, topology, mapping):
            improved = {logical: logical for logical in range(circuit.qubit_count)}
            return improved, (0.0, 0)

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
            heuristic_map(
                circuit,
                topology,
                initial_candidates=8,
                seed=7,
                max_workers=1,
            )

        routed_keys = {
            tuple(mapping[logical] for logical in range(4))
            for mapping in routed_mappings
        }
        expected_routed_keys = {
            tuple(candidate[logical] for logical in range(4))
            for strategy, is_initial, candidate in initial_candidates
            if is_initial
        }
        expected_routed_keys.add(tuple(range(4)))
        self.assertEqual(routed_keys, expected_routed_keys)

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
