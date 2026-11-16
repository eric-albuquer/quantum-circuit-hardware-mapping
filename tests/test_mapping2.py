import math
import unittest

from src.circuit_graph.graph import CircuitEdge, CircuitGraph
from src.mapping2 import hill_climb_placement, map2, mapping_cost_weights
from src.topology_graph.graph import TopologyEdge, TopologyGraph


def make_circuit() -> CircuitGraph:
    return CircuitGraph(
        [
            CircuitEdge("test", "test", 2, 0, 0, "cx", 0, 1),
        ]
    )


def make_interaction_circuit(
    interactions: list[tuple[int, int]],
    qubit_count: int,
) -> CircuitGraph:
    return CircuitGraph(
        [
            CircuitEdge("test", "test", qubit_count, index, index, "cx", q1, q2)
            for index, (q1, q2) in enumerate(interactions)
        ]
    )


class Mapping2Tests(unittest.TestCase):
    def test_graphs_precompute_mapping_metrics(self):
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.1, 0.9),
                TopologyEdge(1, 0, 0.1, 0.9),
                TopologyEdge(1, 2, 0.1, 0.9),
                TopologyEdge(2, 1, 0.1, 0.9),
            ]
        )
        circuit = make_circuit()

        self.assertEqual(circuit.max_qubit_degree, 1)
        self.assertEqual(circuit.max_qubit_interactions, 1)
        self.assertEqual(topology.qubit_degree, {0: 1, 1: 2, 2: 1})
        self.assertEqual(topology.mean_adjacent_error, {0: 0.1, 1: 0.1, 2: 0.1})
        self.assertEqual(topology.mean_distance, {0: 1.5, 1: 1.0, 2: 1.5})
        self.assertAlmostEqual(topology.global_adjacent_error, 0.1)
        self.assertAlmostEqual(topology.mean_path_error[0], 0.29 / 2)
        self.assertAlmostEqual(topology.mean_path_error[1], 0.2 / 2)

    def test_cost_weights_adapt_to_dependency_graph_depth(self):
        shallow = make_interaction_circuit([(0, 1), (2, 3), (4, 5)], 6)
        intermediate = make_interaction_circuit(
            [(0, 1), (2, 3), (1, 2)],
            4,
        )
        deep = make_interaction_circuit([(0, 1), (0, 1), (0, 1)], 2)

        self.assertEqual(shallow.depth_pressure, 0.0)
        self.assertEqual(intermediate.depth_pressure, 0.5)
        self.assertEqual(deep.depth_pressure, 1.0)
        self.assertEqual(mapping_cost_weights(shallow), (0.2, 0.2, 0.6))
        self.assertEqual(mapping_cost_weights(intermediate), (0.325, 0.275, 0.4))
        self.assertEqual(mapping_cost_weights(deep), (0.45, 0.35, 0.2))

    def test_map2_returns_cost_edges_and_handles_zero_error_rates(self):
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.0, 1.0),
                TopologyEdge(1, 0, 0.0, 1.0),
            ]
        )

        flux_graph = map2(make_circuit(), topology)

        self.assertEqual(flux_graph["s"], {"l0": 0.0, "l1": 0.0})
        self.assertEqual(flux_graph["t0"], {"t": 0.0})
        self.assertEqual(flux_graph["t1"], {"t": 0.0})
        for logical_qubit in ("l0", "l1"):
            for cost in flux_graph[logical_qubit].values():
                self.assertTrue(math.isfinite(cost))
                self.assertGreaterEqual(cost, 0.0)

    def test_disconnected_hardware_links_get_a_finite_penalty(self):
        topology = TopologyGraph(
            [
                TopologyEdge(0, 0, 0.0, 1.0),
                TopologyEdge(1, 1, 0.0, 1.0),
            ]
        )

        self.assertEqual(topology.mean_distance, {0: 2.0, 1: 2.0})
        self.assertEqual(topology.mean_path_error, {0: 1.0, 1: 1.0})
        flux_graph = map2(make_circuit(), topology)
        for logical_qubit in ("l0", "l1"):
            for cost in flux_graph[logical_qubit].values():
                self.assertTrue(math.isfinite(cost))

    def test_hill_climbing_improves_the_initial_mapping(self):
        circuit = make_circuit()
        topology = TopologyGraph(
            [
                TopologyEdge(source, target, 0.01, 0.99)
                for source, target in (
                    (0, 1),
                    (1, 0),
                    (1, 2),
                    (2, 1),
                    (2, 3),
                    (3, 2),
                )
            ]
        )
        initial_mapping = {0: 0, 1: 3}

        improved_mapping, improved_cost = hill_climb_placement(
            circuit,
            topology,
            initial_mapping,
        )

        self.assertEqual(initial_mapping, {0: 0, 1: 3})
        self.assertEqual(set(improved_mapping), {0, 1})
        self.assertEqual(len(set(improved_mapping.values())), 2)
        self.assertLess(improved_cost[1], 3)


if __name__ == "__main__":
    unittest.main()
