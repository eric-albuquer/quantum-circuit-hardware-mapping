import math
import unittest

from src.circuit_graph.graph import CircuitEdge, CircuitGraph
from src.mapping_common import route_circuit
from mapping_flow import (
    build_min_cost_max_flow_graph,
    compute_max_flow_min_cost,
    extract_mapping_from_residual_graph,
    hill_climb_placement,
    mapping_cost_weights,
)
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


class MaxFlowMinCostMappingTests(unittest.TestCase):
    def test_single_qubit_operations_are_dependencies_not_routed_interactions(self):
        circuit = CircuitGraph(
            [
                CircuitEdge("test", "test", 2, 0, 0, "h", 0, 0),
                CircuitEdge("test", "test", 2, 1, 1, "cx", 0, 1),
            ]
        )
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.1, 0.9),
                TopologyEdge(1, 0, 0.1, 0.9),
            ]
        )

        routed = route_circuit(circuit, topology, {0: 0, 1: 1})

        self.assertEqual(circuit.iteraction_matrix, [[1, 1], [1, 0]])
        self.assertEqual(circuit.qubit_degree, [1, 1])
        self.assertEqual(circuit.qubit_interactions, [1, 1])
        self.assertEqual(circuit.two_qubit_interaction_count, 1)
        self.assertEqual(circuit.operation_count, 2)
        self.assertEqual(circuit.dependency_depth, 2)
        self.assertAlmostEqual(routed.expected_error_rate, 0.1)
        self.assertEqual(routed.swap_count, 0)

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

        self.assertEqual(circuit.interaction_pairs, [(0, 1, 1)])
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

    def test_flow_graph_has_cost_edges_and_handles_zero_error_rates(self):
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.0, 1.0),
                TopologyEdge(1, 0, 0.0, 1.0),
            ]
        )

        flow_graph = build_min_cost_max_flow_graph(make_circuit(), topology)

        self.assertEqual(flow_graph["s"], {"l0": 0.0, "l1": 0.0})
        self.assertEqual(flow_graph["t0"], {"t": 0.0})
        self.assertEqual(flow_graph["t1"], {"t": 0.0})
        for logical_qubit in ("l0", "l1"):
            for cost in flow_graph[logical_qubit].values():
                self.assertTrue(math.isfinite(cost))
                self.assertGreaterEqual(cost, 0.0)

    def test_compute_max_flow_min_cost_finds_minimum_cost_full_assignment(self):
        flow_graph = {
            "s": {"l0": 0.0, "l1": 0.0},
            "l0": {"t0": 1.0, "t1": 5.0},
            "l1": {"t0": 2.0, "t1": 3.0},
            "t0": {"t": 0.0},
            "t1": {"t": 0.0},
        }

        max_flow, min_cost, _ = compute_max_flow_min_cost(flow_graph, "s", "t")

        self.assertEqual(max_flow, 2.0)
        self.assertEqual(min_cost, 4.0)

    def test_compute_max_flow_min_cost_handles_float_rounding_ties(self):
        interactions = [(3, 2), (2, 1), (1, 0)]
        circuit = make_interaction_circuit(interactions, 4)
        link_errors = (
            (0, 1, 0.0013216868179469431),
            (1, 0, 0.003146675214765709),
            (1, 2, 0.0014916480464655913),
            (2, 1, 0.0006931236489664008),
            (2, 3, 0.0013124757662012173),
            (3, 2, 0.0020525941373089364),
        )
        topology = TopologyGraph(
            [
                TopologyEdge(source, target, error, 1.0 - error)
                for source, target, error in link_errors
            ]
        )
        flow_graph = build_min_cost_max_flow_graph(circuit, topology)

        max_flow, min_cost, residual_graph = compute_max_flow_min_cost(
            flow_graph,
            "s",
            "t",
        )

        self.assertEqual(max_flow, circuit.qubit_count)
        self.assertTrue(math.isfinite(min_cost))
        mapping = extract_mapping_from_residual_graph(
            circuit,
            topology,
            residual_graph,
        )
        self.assertEqual(len(set(mapping.values())), circuit.qubit_count)

    def test_extract_mapping_from_residual_graph(self):
        circuit = make_circuit()
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.1, 0.9),
                TopologyEdge(1, 0, 0.1, 0.9),
                TopologyEdge(1, 2, 0.1, 0.9),
                TopologyEdge(2, 1, 0.1, 0.9),
            ]
        )
        flow_graph = {
            "s": {"l0": 0.0, "l1": 0.0},
            "l0": {"t0": 1.0, "t1": 5.0, "t2": 6.0},
            "l1": {"t0": 2.0, "t1": 3.0, "t2": 4.0},
            "t0": {"t": 0.0},
            "t1": {"t": 0.0},
            "t2": {"t": 0.0},
        }
        max_flow, _, residual_graph = compute_max_flow_min_cost(
            flow_graph,
            "s",
            "t",
        )

        self.assertEqual(max_flow, circuit.qubit_count)
        self.assertEqual(
            extract_mapping_from_residual_graph(circuit, topology, residual_graph),
            {0: 0, 1: 1},
        )

    def test_disconnected_hardware_links_get_a_finite_penalty(self):
        topology = TopologyGraph(
            [
                TopologyEdge(0, 0, 0.0, 1.0),
                TopologyEdge(1, 1, 0.0, 1.0),
            ]
        )

        self.assertEqual(topology.mean_distance, {0: 2.0, 1: 2.0})
        self.assertEqual(topology.mean_path_error, {0: 1.0, 1: 1.0})
        flow_graph = build_min_cost_max_flow_graph(make_circuit(), topology)
        for logical_qubit in ("l0", "l1"):
            for cost in flow_graph[logical_qubit].values():
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
        routed_result = route_circuit(circuit, topology, improved_mapping)
        self.assertEqual(
            improved_cost,
            (routed_result.expected_error_rate, routed_result.swap_count),
        )


if __name__ == "__main__":
    unittest.main()
