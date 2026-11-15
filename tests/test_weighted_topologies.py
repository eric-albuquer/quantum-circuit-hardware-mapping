import unittest

import numpy as np

from dataset_generation.weighted_topologies import (
    GATE_ERROR_MAX,
    GATE_ERROR_MIN,
    _generate_weighted_edges,
)


class WeightedTopologyGenerationTests(unittest.TestCase):
    def test_gate_error_rates_use_reduced_synthetic_range(self):
        edges = [(index, index + 1) for index in range(1000)]

        generated = _generate_weighted_edges(edges, np.random.default_rng(7))

        error_rates = [edge["gate_error_rate"] for edge in generated]
        self.assertGreaterEqual(min(error_rates), GATE_ERROR_MIN)
        self.assertLessEqual(max(error_rates), GATE_ERROR_MAX)
        for edge in generated:
            self.assertAlmostEqual(
                edge["gate_fidelity"],
                1.0 - edge["gate_error_rate"],
            )


if __name__ == "__main__":
    unittest.main()
