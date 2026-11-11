import tempfile
import unittest
from pathlib import Path

from analysis.interactions import analyze_ordered_interactions


class OrderedInteractionTests(unittest.TestCase):
    def test_expands_multi_qubit_gate_and_preserves_source_instruction_index(self):
        qasm = """\
OPENQASM 2.0;
include "qelib1.inc";
gate oracle a,b,c {
    cx a,c;
    cx b,c;
}
qreg q[3];
x q[0];
oracle q[0],q[1],q[2];
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "composite.qasm"
            path.write_text(qasm, encoding="utf-8")

            qubit_count, interactions = analyze_ordered_interactions(path)

        self.assertEqual(qubit_count, 3)
        self.assertEqual(
            interactions,
            [
                (0, 1, "cx", 0, 2),
                (1, 1, "cx", 1, 2),
            ],
        )


if __name__ == "__main__":
    unittest.main()
