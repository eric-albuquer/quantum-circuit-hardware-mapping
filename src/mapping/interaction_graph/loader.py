from src.mapping.interaction_graph.graph import *
import csv

def load_interaction_graph(interaction_analysis_path: str):
    edges = []
    with open(interaction_analysis_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        next(reader, None)

        for line in reader:
            edges.append(InteractionEdge(*line))

    return InteractionGraph(edges)

if __name__ == "__main__":
    ig = load_interaction_graph("/Users/ega/Desktop/codigos/python/quantum-circuit-hardware-mapping/datasets/interaction_analysis/algorithms/bmw_quark_cardinality/pair_interactions_4qubits.csv")

    for key, value in ig.graph.items():
        print(key, value)