import unittest

from src.circuit_graph.graph import CircuitEdge, CircuitGraph
from src.mapping import estimate_placement_cost, map, route_circuit
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
        self.assertAlmostEqual(topology.error_matrix[0][2], 0.1)
        self.assertAlmostEqual(topology.error_matrix[0][1], 0.05)

    def test_multi_start_mapping_is_reproducible_and_injective(self):
        circuit = make_circuit(4, [(0, 1), (0, 1), (0, 2), (1, 3)])
        topology = make_topology([(0, 1), (1, 2), (2, 3), (3, 4)], 5)

        first = map(circuit, topology, restarts=8, seed=7)
        second = map(circuit, topology, restarts=8, seed=7)

        self.assertEqual(first, second)
        self.assertEqual(set(first), set(range(4)))
        self.assertEqual(len(set(first.values())), 4)
        self.assertLessEqual(
            estimate_placement_cost(circuit, topology, first),
            estimate_placement_cost(circuit, topology, {0: 0, 1: 4, 2: 1, 3: 3}),
        )

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
            map(circuit, topology)


if __name__ == "__main__":
    unittest.main()
