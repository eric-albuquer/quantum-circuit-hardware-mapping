import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from qiskit import QuantumCircuit
from qiskit.transpiler import CouplingMap

from analysis.benchmark_mappers import (
    ALGORITHMS,
    CIRCUIT_FAMILIES,
    DEFAULT_CIRCUIT_FAMILIES,
    DEFAULT_TOPOLOGY_FAMILIES,
    DEFAULT_EXACT_MAX_QUBITS,
    DEFAULT_QUBIT_COUNTS,
    _run_local_algorithm,
    _run_sabre,
    _qubit_count,
    _should_run_exact,
    benchmark,
    default_cases,
)
from src.circuit_graph.graph import CircuitEdge, CircuitGraph
from src.mapping_common import RoutingResult
from src.topology_graph.graph import TopologyEdge, TopologyGraph


class BenchmarkExactSearchTests(unittest.TestCase):
    def test_exact_search_requires_qubit_and_placement_limits(self):
        circuit = CircuitGraph(
            [CircuitEdge("test", "test", 2, 0, 0, "cx", 0, 1)]
        )
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.01, 0.99),
                TopologyEdge(1, 0, 0.01, 0.99),
                TopologyEdge(1, 2, 0.01, 0.99),
                TopologyEdge(2, 1, 0.01, 0.99),
            ]
        )

        self.assertTrue(_should_run_exact(circuit, topology, 6, 2))
        self.assertFalse(_should_run_exact(circuit, topology, 5, 2))
        self.assertFalse(_should_run_exact(circuit, topology, 6, 1))


class BenchmarkScenarioTests(unittest.TestCase):
    def test_batch_defaults_use_three_runs_and_disable_exact_search(self):
        self.assertEqual(DEFAULT_QUBIT_COUNTS, (4, 8, 12, 16))
        self.assertEqual(DEFAULT_CIRCUIT_FAMILIES, ("ghz", "qft", "qaoa"))
        self.assertEqual(
            DEFAULT_TOPOLOGY_FAMILIES,
            ("line", "ring", "grid", "heavy_hex"),
        )
        self.assertEqual(DEFAULT_EXACT_MAX_QUBITS, 0)

    def test_local_algorithm_runner_dispatches_multi_start_and_flow(self):
        circuit = CircuitGraph(
            [CircuitEdge("test", "test", 2, 0, 0, "cx", 0, 1)]
        )
        topology = TopologyGraph(
            [
                TopologyEdge(0, 1, 0.01, 0.99),
                TopologyEdge(1, 0, 0.01, 0.99),
            ]
        )
        mapping = {0: 0, 1: 1}
        routing = RoutingResult(0, 0.0, mapping)

        with patch(
            "analysis.benchmark_mappers.heuristic_map",
            return_value=mapping,
        ) as multi_start, patch(
            "analysis.benchmark_mappers.route_circuit",
            return_value=routing,
        ):
            result = _run_local_algorithm(
                ALGORITHMS[1],
                circuit,
                topology,
                initial_candidates=4,
                seed=11,
            )

        multi_start.assert_called_once_with(
            circuit,
            topology,
            initial_candidates=4,
            seed=11,
            max_workers=1,
        )
        self.assertEqual(result, (mapping, routing))

        with patch(
            "analysis.benchmark_mappers.build_min_cost_max_flow_graph",
            return_value={"s": {}},
        ), patch(
            "analysis.benchmark_mappers.compute_max_flow_min_cost",
            return_value=(circuit.qubit_count, 0.0, {}),
        ), patch(
            "analysis.benchmark_mappers.extract_mapping_from_residual_graph",
            return_value=mapping,
        ), patch(
            "analysis.benchmark_mappers.hill_climb_placement",
            return_value=(mapping, (0.0, 0)),
        ) as flow_hill_climb, patch(
            "analysis.benchmark_mappers.route_circuit",
            return_value=routing,
        ):
            result = _run_local_algorithm(
                ALGORITHMS[2],
                circuit,
                topology,
                initial_candidates=4,
                seed=11,
            )

        flow_args, flow_kwargs = flow_hill_climb.call_args
        self.assertEqual(flow_args, (circuit, topology, mapping))
        self.assertTrue(callable(flow_kwargs["router"]))
        self.assertEqual(result, (mapping, routing))

        with self.assertRaisesRegex(ValueError, "Unsupported local mapping"):
            _run_local_algorithm(
                ALGORITHMS[0],
                circuit,
                topology,
                initial_candidates=4,
                seed=11,
            )

    def test_benchmark_accepts_three_runs_and_rejects_fewer(self):
        with TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "benchmark.csv"
            cases = [(Path("circuit.csv"), Path("topology.csv"))]
            with patch("analysis.benchmark_mappers._benchmark_case", return_value=[]):
                benchmark(cases, output_path, runs=3)
                self.assertTrue(output_path.is_file())
                with self.assertRaisesRegex(ValueError, "três execuções"):
                    benchmark(cases, output_path, runs=2)

    def test_default_cases_include_each_family_at_compatible_sizes(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            expected_counts = set(DEFAULT_QUBIT_COUNTS)
            for family in CIRCUIT_FAMILIES:
                for qubit_count in expected_counts:
                    directory = (
                        root
                        / "datasets"
                        / "interaction_order"
                        / "algorithms"
                        / family
                    )
                    directory.mkdir(parents=True, exist_ok=True)
                    (
                        directory
                        / f"{family}_{qubit_count}qubits_ordered_interactions.csv"
                    ).touch()
            for family in ("line", "ring"):
                directory = root / "datasets" / "topologies" / family
                directory.mkdir(parents=True, exist_ok=True)
                for qubit_count in (4, 8, 12, 16, 17, 18):
                    (
                        directory
                        / f"{family}_{qubit_count}qubits_weighted_edges.csv"
                    ).touch()
            non_uniform_topologies = {
                "grid": (9, 16, 25),
                "heavy_hex": (19, 57),
            }
            for family, topology_sizes in non_uniform_topologies.items():
                directory = root / "datasets" / "topologies" / family
                directory.mkdir(parents=True, exist_ok=True)
                for qubit_count in topology_sizes:
                    (
                        directory
                        / f"{family}_{qubit_count}qubits_weighted_edges.csv"
                    ).touch()

            cases = default_cases(root)

        expected_case_count = (
            len(DEFAULT_CIRCUIT_FAMILIES)
            * len(expected_counts)
            * len(DEFAULT_TOPOLOGY_FAMILIES)
            * 2
        )
        self.assertEqual(len(cases), expected_case_count)
        observed_counts = {
            int(
                circuit.stem.removesuffix("_ordered_interactions")
                .rsplit("_", 1)[1]
                .removesuffix("qubits")
            )
            for circuit, _ in cases
        }
        observed_topologies = {topology.parent.name for _, topology in cases}
        self.assertEqual(observed_counts, expected_counts)
        self.assertEqual(observed_topologies, set(DEFAULT_TOPOLOGY_FAMILIES))
        self.assertEqual(
            {circuit.parent.name for circuit, _ in cases},
            set(DEFAULT_CIRCUIT_FAMILIES),
        )
        for circuit, topology in cases:
            circuit_qubits = int(
                circuit.stem.removesuffix("_ordered_interactions")
                .rsplit("_", 1)[1]
                .removesuffix("qubits")
            )
            topology_qubits = int(
                topology.stem.removesuffix("_weighted_edges")
                .rsplit("_", 1)[1]
                .removesuffix("qubits")
            )
            self.assertGreaterEqual(topology_qubits, circuit_qubits)

        available_sizes = {
            "line": (4, 8, 12, 16, 17, 18),
            "ring": (4, 8, 12, 16, 17, 18),
            "grid": (9, 16, 25),
            "heavy_hex": (19, 57),
        }
        for circuit in {circuit for circuit, _ in cases}:
            circuit_qubits = int(
                circuit.stem.removesuffix("_ordered_interactions")
                .rsplit("_", 1)[1]
                .removesuffix("qubits")
            )
            for family in DEFAULT_TOPOLOGY_FAMILIES:
                family_topologies = sorted(
                    (
                        topology
                        for candidate, topology in cases
                        if candidate == circuit and topology.parent.name == family
                    ),
                    key=_qubit_count,
                )
                self.assertEqual(len(family_topologies), 2)
                self.assertEqual(
                    [_qubit_count(topology) for topology in family_topologies],
                    [
                        size
                        for size in available_sizes[family]
                        if size >= circuit_qubits
                    ][:2],
                )

    def test_sabre_can_route_to_a_larger_physical_topology(self):
        circuit = CircuitGraph(
            [CircuitEdge("test", "test", 2, 0, 0, "cx", 0, 1)]
        )
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
        quantum_circuit = QuantumCircuit(2)
        quantum_circuit.cx(0, 1)
        coupling_map = CouplingMap(
            couplinglist=[
                [source, target]
                for source, neighbors in topology.graph.items()
                for target in neighbors
                if source != target
            ]
        )

        swap_count, _, initial_mapping, final_mapping = _run_sabre(
            circuit,
            quantum_circuit,
            coupling_map,
            topology,
            seed=42,
        )

        self.assertGreaterEqual(swap_count, 0)
        self.assertEqual(len(initial_mapping), circuit.qubit_count)
        self.assertEqual(len(set(initial_mapping.values())), circuit.qubit_count)
        self.assertEqual(len(final_mapping), circuit.qubit_count)
        self.assertEqual(len(set(final_mapping.values())), circuit.qubit_count)


if __name__ == "__main__":
    unittest.main()
