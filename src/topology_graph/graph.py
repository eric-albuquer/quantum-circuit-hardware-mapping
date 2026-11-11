import heapq

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

        self.qubit_count = len(self.graph)
        self.error_matrix = [
            [float("inf") for _ in range(self.qubit_count)]
            for _ in range(self.qubit_count)
        ]
        self.path_matrix = [
            [[] for _ in range(self.qubit_count)]
            for _ in range(self.qubit_count)
        ]

        for start_q in self.graph:
            previous: dict[int, int | None] = {start_q: None}
            pending = [(0.0, start_q)]
            self.error_matrix[start_q][start_q] = 0.0
            self.path_matrix[start_q][start_q] = [start_q]

            while pending:
                error, q = heapq.heappop(pending)
                if error > self.error_matrix[start_q][q]:
                    continue

                for new_q in sorted(self.graph[q]):
                    new_error = error + self.link_error_rate(q, new_q)
                    if new_error >= self.error_matrix[start_q][new_q]:
                        continue

                    previous[new_q] = q
                    self.error_matrix[start_q][new_q] = new_error
                    heapq.heappush(pending, (new_error, new_q))

                    reverse_path = []
                    current_q: int | None = new_q
                    while current_q is not None:
                        reverse_path.append(current_q)
                        current_q = previous[current_q]
                    self.path_matrix[start_q][new_q] = reverse_path[::-1]

    def link_error_rate(self, source: int, target: int) -> float:
        rates = [
            rate
            for rate in (
                self.graph.get(source, {}).get(target),
                self.graph.get(target, {}).get(source),
            )
            if rate is not None
        ]
        if not rates:
            raise ValueError(f"No hardware link between qubits {source} and {target}")
        return sum(rates) / len(rates)
