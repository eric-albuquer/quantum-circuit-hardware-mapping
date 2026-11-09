from src.mapping.dependency_graph.graph import *
from src.mapping.interaction_graph.graph import *
from src.mapping.topology_graph.graph import *

import heapq

def map(circuit: InteractionGraph, dependency: DependencyGraph, topology: TopologyGraph) -> list[tuple[int, int]]:
    topology_dist_matrix = [[float("inf") for _ in range(len(topology.graph))] for _ in range(len(topology.graph))]
    topology_path_matrix = [[[] for _ in range(len(topology.graph))] for _ in range(len(topology.graph))]

    # multi dijkstra pass
    for start_q in topology.graph:
        heap = [(0.0, start_q)]
        prev_map = {start_q: None}
        topology_dist_matrix[start_q][start_q] = 0.0

        while heap:
            error, q = heapq.heappop(heap)

            if error > topology_dist_matrix[start_q][q]:
                continue

            current_q = q
            reverse_path = []

            while current_q is not None:
                reverse_path.append(current_q)
                current_q = prev_map[current_q]

            topology_path_matrix[start_q][q] = reverse_path[::-1]

            for new_q, new_error in topology.graph[q].items():
                new_error += error

                if new_error >= topology_dist_matrix[start_q][new_q]:
                    continue

                topology_dist_matrix[start_q][new_q] = new_error
                prev_map[new_q] = q
                heapq.heappush(heap, (new_error, new_q))

    for line in topology_dist_matrix:
        print(line)

    for line in topology_path_matrix:
        print(line)

if __name__ == "__main__":
    from src.mapping.dependency_graph.loader import *
    from src.mapping.interaction_graph.loader import *
    from src.mapping.topology_graph.loader import *

    dg = load_dependency_graph("/Users/ega/Desktop/codigos/python/quantum-circuit-hardware-mapping/datasets/interaction_order/algorithms/bmw_quark_cardinality/bmw_quark_cardinality_3qubits_ordered_interactions.csv")
    ig = load_interaction_graph("/Users/ega/Desktop/codigos/python/quantum-circuit-hardware-mapping/datasets/interaction_analysis/algorithms/bmw_quark_cardinality/pair_interactions_3qubits.csv")
    tg = load_topology_graph("/Users/ega/Desktop/codigos/python/quantum-circuit-hardware-mapping/datasets/topologies/line/line_3qubits_weighted_edges.csv")

    map(dg, ig, tg)