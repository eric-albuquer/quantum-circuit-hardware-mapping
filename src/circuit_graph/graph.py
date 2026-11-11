from typing import NamedTuple

class CircuitEdge:
    def __init__(self, algorithm, circuit, num_qubits, interaction_index, instruction_index, gate, qubit_1, qubit_2):
        self.algorithm = algorithm
        self.circuit = circuit
        self.num_qubits = int(num_qubits)
        self.interaction_index = int(interaction_index)
        self.instruction_index = int(instruction_index)
        self.gate = gate
        self.qubit_1 = int(qubit_1)
        self.qubit_2 = int(qubit_2)

class CircuitVertice(NamedTuple):
    qubit_1: int
    qubit_2: int
    gate: str
    interaction_index: int

    def __repr__(self):
        return f"({self.qubit_1}, {self.qubit_2}, {self.gate}, {self.interaction_index})"

class CircuitGraph:
    def __init__(self, edges: list[CircuitEdge]):
        if len(edges) == 0:
            raise ValueError("Empty circuit")
        
        self.qubit_count = edges[0].num_qubits
        self.iteraction_matrix = [[0 for _ in range(self.qubit_count)] for _ in range(self.qubit_count)]
        self.fpga = edges

        self.dependency_graph: dict[CircuitVertice, set[CircuitVertice]] = {}
        last_qubit_vertice = {}

        for e in edges:
            q1 = e.qubit_1
            q2 = e.qubit_2

            self.iteraction_matrix[q1][q2] += 1
            self.iteraction_matrix[q2][q1] += 1

            v = CircuitVertice(q1, q2, e.gate, e.interaction_index)
            self.dependency_graph[v] = set()

            if q1 in last_qubit_vertice:
                v1 = last_qubit_vertice[q1]
                self.dependency_graph[v].add(v1)

            if q2 in last_qubit_vertice:
                v2 = last_qubit_vertice[q2]
                self.dependency_graph[v].add(v2)

            last_qubit_vertice[q1] = v
            last_qubit_vertice[q2] = v    