import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from qiskit import QuantumCircuit
from qiskit.transpiler import CouplingMap

from analysis.benchmark_mappers import (
    CIRCUIT_FAMILIES,
    DEFAULT_QUBIT_COUNTS,
    TOPOLOGY_FAMILIES,
    _run_sabre,
    _should_run_exact,
    default_cases,
)
from src.circuit_graph.graph import CircuitEdge, CircuitGraph
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
            for family in ("line", "ring", "full"):
                directory = root / "datasets" / "topologies" / family
                directory.mkdir(parents=True, exist_ok=True)
                for qubit_count in expected_counts:
                    (
                        directory
                        / f"{family}_{qubit_count}qubits_weighted_edges.csv"
                    ).touch()
            non_uniform_topologies = {
                "grid": (9, 16),
                "heavy_hex": (19,),
                "heavy_square": (21,),
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
            len(CIRCUIT_FAMILIES)
            * len(expected_counts)
            * len(TOPOLOGY_FAMILIES)
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
        self.assertEqual(observed_topologies, set(TOPOLOGY_FAMILIES))
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
            if topology.parent.name in ("line", "ring", "full"):
                self.assertEqual(topology_qubits, circuit_qubits)

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
