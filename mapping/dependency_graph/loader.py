from mapping.dependency_graph.graph import *
import csv

def load_dependency_graph(interaction_order_path: str):
    edges = []
    with open(interaction_order_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        next(reader, None)

        for line in reader:
            edges.append(DependencyEdge(*line))

    return DependencyGraph(edges)

if __name__ == "__main__":
    dg = load_dependency_graph("/Users/ega/Desktop/codigos/python/quantum-circuit-hardware-mapping/datasets/interaction_order/algorithms/bmw_quark_cardinality/bmw_quark_cardinality_3qubits_ordered_interactions.csv")

    for key, value in dg.graph.items():
        print(key, value)