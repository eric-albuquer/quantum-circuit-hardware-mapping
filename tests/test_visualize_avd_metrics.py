import csv
import tempfile
import unittest
from pathlib import Path

from analysis.visualize_avd import (
    _top_pair_labels,
    load_circuits,
    load_topologies,
    save_graph_metrics,
)


class TopPairLegendTests(unittest.TestCase):
    def test_lists_up_to_six_most_frequent_pairs(self):
        pairs = [(index, index + 1) for index in range(6)]

        summary, legend_label = _top_pair_labels(pairs)

        self.assertIn("q0–q1", summary)
        self.assertIn("q5–q6", summary)
        self.assertEqual(legend_label, f"Pares mais recorrentes: {summary}")

    def test_hides_pair_names_when_more_than_six_are_tied(self):
        pairs = [(index, index + 1) for index in range(7)]

        summary, legend_label = _top_pair_labels(pairs)

        self.assertEqual(summary, "7 pares")
        self.assertEqual(legend_label, "Pares mais recorrentes (7 pares)")
        self.assertNotIn("q0–q1", legend_label)


class GraphMetricsExportTests(unittest.TestCase):
    def test_exports_precomputed_circuit_and_topology_metrics(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_root = Path(temporary_directory)
            circuit_dir = (
                data_root / "interaction_order" / "algorithms" / "test"
            )
            topology_dir = data_root / "topologies" / "line"
            circuit_dir.mkdir(parents=True)
            topology_dir.mkdir(parents=True)

            circuit_path = (
                circuit_dir / "test_3qubits_ordered_interactions.csv"
            )
            with circuit_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "algorithm",
                        "circuit",
                        "num_qubits",
                        "interaction_index",
                        "instruction_index",
                        "gate",
                        "qubit_1",
                        "qubit_2",
                    ],
                )
                writer.writeheader()
                for index, (qubit_1, qubit_2) in enumerate(
                    [(0, 1), (0, 1), (1, 2)]
                ):
                    writer.writerow(
                        {
                            "algorithm": "test",
                            "circuit": "test_3qubits",
                            "num_qubits": 3,
                            "interaction_index": index,
                            "instruction_index": index,
                            "gate": "cx",
                            "qubit_1": qubit_1,
                            "qubit_2": qubit_2,
                        }
                    )

            topology_path = (
                topology_dir / "line_3qubits_weighted_edges.csv"
            )
            with topology_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "source_qubit",
                        "target_qubit",
                        "gate_error_rate",
                        "gate_fidelity",
                    ],
                )
                writer.writeheader()
                for source, target, error in (
                    (0, 1, 0.01),
                    (1, 0, 0.01),
                    (1, 2, 0.02),
                    (2, 1, 0.02),
                ):
                    writer.writerow(
                        {
                            "source_qubit": source,
                            "target_qubit": target,
                            "gate_error_rate": error,
                            "gate_fidelity": 1.0 - error,
                        }
                    )

            circuits = load_circuits(data_root)
            topologies = load_topologies(data_root)
            output_path = data_root / "metricas_grafos.csv"
            save_graph_metrics(circuits, topologies, output_path)

            self.assertEqual(circuits[0].dependency_depth, 3)
            self.assertEqual(circuits[0].depth_pressure, 1.0)
            self.assertEqual(circuits[0].qubit_interactions, [2, 3, 1])
            self.assertEqual(circuits[0].interaction_pairs, [(0, 1, 2), (1, 2, 1)])
            self.assertAlmostEqual(
                topologies[0].global_adjacent_error,
                0.015,
            )
            self.assertAlmostEqual(topologies[0].max_mean_distance, 1.5)

            with output_path.open(encoding="utf-8-sig", newline="") as file:
                rows = {
                    row["tipo"]: row for row in csv.DictReader(file)
                }
            circuit_row = rows["simples, nao direcionado e ponderado"]
            topology_row = rows["direcionado e ponderado"]
            self.assertEqual(circuit_row["interacoes_dois_qubits"], "3")
            self.assertEqual(circuit_row["profundidade_dependencia"], "3")
            self.assertEqual(circuit_row["grau_maximo_qubit"], "2")
            self.assertAlmostEqual(
                float(topology_row["erro_adjacente_global"]),
                0.015,
            )
            self.assertEqual(topology_row["grau_maximo_fisico"], "2")


if __name__ == "__main__":
    unittest.main()
