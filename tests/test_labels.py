import unittest

from analysis.labels import dataset_label


class DatasetLabelTests(unittest.TestCase):
    def test_family_uses_spaces_and_capitals(self):
        self.assertEqual(dataset_label("modular_adder"), "Modular Adder")
        self.assertEqual(dataset_label("heavy_hex"), "Heavy Hex")

    def test_acronyms_and_joined_names(self):
        self.assertEqual(dataset_label("ghz"), "GHZ")
        self.assertEqual(dataset_label("cdkm_ripple_carry_adder"), "CDKM Ripple Carry Adder")
        self.assertEqual(dataset_label("qpeexact"), "QPE Exact")
        self.assertEqual(dataset_label("graphstate"), "Graph State")

    def test_circuit_and_topology_sizes(self):
        self.assertEqual(dataset_label("modular_adder_14qubits"), "Modular Adder · 14 qubits")
        self.assertEqual(dataset_label("grid_3x3_9qubits"), "Grid 3x3 · 9 qubits")
        self.assertEqual(dataset_label("heavy_square_21qubits"), "Heavy Square · 21 qubits")

    def test_random_circuit_shows_depth_without_id(self):
        self.assertEqual(
            dataset_label("random_4qubits_depth10_id0"),
            "Random · 4 qubits · profundidade 10",
        )

    def test_already_readable_or_non_text_values_pass_through(self):
        self.assertEqual(dataset_label("Todas"), "Todas")
        self.assertEqual(dataset_label(12), "12")


if __name__ == "__main__":
    unittest.main()
