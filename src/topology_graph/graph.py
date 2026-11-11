import heapq
import math

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
        self.error_matrix: list[list[float]] = [
            [float("inf") for _ in range(self.qubit_count)]
            for _ in range(self.qubit_count)
        ]
        self.path_matrix = [
            [[] for _ in range(self.qubit_count)]
            for _ in range(self.qubit_count)
        ]

        for start_q in self.graph:
            previous: dict[int, int | None] = {start_q: None}
            distances = {start_q: (0.0, 0)}
            pending = [(0.0, 0, start_q)]
            self.error_matrix[start_q][start_q] = 0.0
            self.path_matrix[start_q][start_q] = [start_q]

            while pending:
                log_success_loss, hop_count, q = heapq.heappop(pending)
                if (log_success_loss, hop_count) != distances[q]:
                    continue

                reverse_path = []
                current_q: int | None = q
                while current_q is not None:
                    reverse_path.append(current_q)
                    current_q = previous[current_q]
                self.path_matrix[start_q][q] = reverse_path[::-1]

                for new_q in sorted(self.graph[q]):
                    link_error = self.link_error_rate(q, new_q)
                    link_log_loss = (
                        float("inf")
                        if link_error == 1.0
                        else -math.log1p(-link_error)
                    )
                    candidate = (log_success_loss + link_log_loss, hop_count + 1)
                    if new_q in distances and candidate >= distances[new_q]:
                        continue

                    distances[new_q] = candidate
                    previous[new_q] = q
                    cumulative_error = -math.expm1(-candidate[0])
                    self.error_matrix[start_q][new_q] = cumulative_error
                    heapq.heappush(
                        pending,
                        (candidate[0], candidate[1], new_q),
                    )

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
        rate = sum(rates) / len(rates)
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"Invalid two-qubit gate error rate: {rate}")
        return rate
