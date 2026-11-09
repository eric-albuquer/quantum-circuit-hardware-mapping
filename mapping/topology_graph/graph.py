from typing import NamedTuple

class TopologyEdge:
    def __init__(self, source_qubit, target_qubit, gate_error_rate, _):
        self.qubit_1 = int(source_qubit)
        self.qubit_2 = int(target_qubit)
        self.gate_error_rate = float(gate_error_rate)

class TopologyGraph:
    def __init__(self, edges: list[TopologyEdge]):
        self.graph: dict[int, dict[int, float]] = {} # q1 -> { q2 -> error}

        for e in edges:
            q1 = e.qubit_1
            q2 = e.qubit_2

            error = e.gate_error_rate

            if q1 not in self.graph:
                self.graph[q1] = {}

            self.graph[q1][q2] = error