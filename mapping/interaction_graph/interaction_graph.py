from typing import NamedTuple

class InteractionEdge:
    def __init__(self, algorithm, circuit, num_qubits, qubit_1, qubit_2, interaction_count):
        self.algorithm = algorithm
        self.circuit = circuit
        self.num_qubits = int(num_qubits)
        self.qubit_1 = int(qubit_1)
        self.qubit_2 = int(qubit_2)
        self.interaction_count = int(interaction_count)

class InteractionGraph:
    def __init__(self, edges: list[InteractionEdge]):
        self.graph: dict[int, dict[int, int]] = {}
                        # q1 -> { q2 -> count}

        for e in edges:
            q1 = e.qubit_1
            q2 = e.qubit_2
            count = e.interaction_count

            if q1 not in self.graph:
                self.graph[q1] = {}

            if q2 not in self.graph:
                self.graph[q2] = {}

            self.graph[q1][q2] = count
            self.graph[q2][q1] = count