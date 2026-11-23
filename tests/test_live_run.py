import json
import subprocess
import sys
import unittest
from pathlib import Path

from analysis.benchmark_mappers import ALGORITHMS, run_case

ROOT = Path(__file__).resolve().parents[1]
CIRCUIT = (
    ROOT / "datasets/interaction_order/algorithms/modular_adder"
    / "modular_adder_6qubits_ordered_interactions.csv"
)
TOPOLOGY = ROOT / "datasets/topologies/line/line_6qubits_weighted_edges.csv"


class RunCaseTests(unittest.TestCase):
    def test_runs_all_four_methods_with_one_seed_per_run(self):
        progress = []
        records = run_case(
            CIRCUIT, TOPOLOGY, runs=2, initial_candidates=3, seed=7,
            on_run=lambda done, total: progress.append((done, total)),
        )
        self.assertEqual(progress, [(1, 2), (2, 2)])
        self.assertEqual(len(records), 2 * len(ALGORITHMS))
        self.assertEqual({r["algorithm"] for r in records}, set(ALGORITHMS))
        self.assertEqual({(r["run"], r["seed"]) for r in records}, {(1, 7), (2, 8)})

    def test_exact_search_is_skipped_above_the_placement_limit(self):
        records = run_case(
            CIRCUIT, TOPOLOGY, runs=1, initial_candidates=3,
            max_exact_placements=10,
        )
        self.assertNotIn("Busca exata", {r["algorithm"] for r in records})

    def test_rejects_invalid_arguments(self):
        with self.assertRaises(ValueError):
            run_case(CIRCUIT, TOPOLOGY, runs=0)
        with self.assertRaises(ValueError):
            run_case(CIRCUIT, TOPOLOGY, initial_candidates=0)


class LiveRunProcessTests(unittest.TestCase):
    def test_subprocess_keeps_stdout_as_json_lines(self):
        result = subprocess.run(
            [
                sys.executable, "-m", "analysis.live_run",
                "--circuit", str(CIRCUIT), "--topology", str(TOPOLOGY),
                "--runs", "1", "--initial-candidates", "3",
            ],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        messages = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(messages[0], {"progress": 1, "total": 1})
        self.assertEqual(len(messages[-1]["records"]), len(ALGORITHMS))


if __name__ == "__main__":
    unittest.main()
