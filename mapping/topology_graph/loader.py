from mapping.topology_graph.graph import *
import csv

def load_dependency_graph(topologies_path: str):
    edges = []
    with open(topologies_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        next(reader, None)

        for line in reader:
            edges.append(TopologyEdge(*line))

    return TopologyGraph(edges)

if __name__ == "__main__":
    ig = load_dependency_graph("/Users/ega/Desktop/codigos/python/quantum-circuit-hardware-mapping/datasets/topologies/full/full_3qubits_weighted_edges.csv")
    for key, value in ig.graph.items():
        print(key, value)