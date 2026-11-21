from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from src.circuit_graph.graph import CircuitEdge, CircuitGraph
from src.topology_graph.graph import TopologyEdge, TopologyGraph


COLORS = {
    "blue": "#2878B5",
    "orange": "#E07A32",
    "green": "#3A936A",
    "red": "#C84C4C",
    "purple": "#7D65A5",
    "gray": "#77808A",
    "light": "#DCE6EF",
    "ink": "#243447",
}


@dataclass
class CircuitData:
    name: str
    algorithm: str
    qubit_count: int
    interaction_count: int
    pair_counts: Counter[tuple[int, int]]
    degrees: list[int]
    dependency_depth: int
    depth_pressure: float
    qubit_interactions: list[int]
    interaction_matrix: list[list[int]]
    interaction_pairs: list[tuple[int, int, int]]
    max_qubit_degree: int
    max_qubit_interactions: int

    @property
    def density(self) -> float:
        possible_pairs = self.qubit_count * (self.qubit_count - 1) / 2
        return len(self.pair_counts) / possible_pairs if possible_pairs else 0.0


@dataclass
class TopologyData:
    name: str
    architecture: str
    qubit_count: int
    arcs: list[tuple[int, int, float]]
    links: dict[tuple[int, int], float]
    in_degrees: list[int]
    out_degrees: list[int]
    adjacent_errors: dict[int, float]
    qubit_degree: dict[int, int]
    global_adjacent_error: float
    mean_distance: dict[int, float]
    mean_path_error: dict[int, float]
    max_mean_distance: float
    max_mean_path_error: float

    @property
    def directed_density(self) -> float:
        possible_arcs = self.qubit_count * (self.qubit_count - 1)
        return len(self.arcs) / possible_arcs if possible_arcs else 0.0

    @property
    def link_density(self) -> float:
        possible_links = self.qubit_count * (self.qubit_count - 1) / 2
        return len(self.links) / possible_links if possible_links else 0.0


def _qubit_count_from_name(name: str) -> int:
    match = re.search(r"_(\d+)qubits", name)
    if not match:
        raise ValueError(f"Could not determine qubit count from filename: {name}")
    return int(match.group(1))


def load_circuits(data_root: Path) -> list[CircuitData]:
    records: list[CircuitData] = []
    for path in sorted(
        (data_root / "interaction_order" / "algorithms").rglob(
            "*_ordered_interactions.csv"
        )
    ):
        pair_counts: Counter[tuple[int, int]] = Counter()
        edges: list[CircuitEdge] = []
        interaction_count = 0
        qubit_count = _qubit_count_from_name(path.name)
        with path.open("r", encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                qubit_count = int(row["num_qubits"])
                qubit_1 = int(row["qubit_1"])
                qubit_2 = int(row["qubit_2"])
                edges.append(
                    CircuitEdge(
                        row["algorithm"],
                        row["circuit"],
                        qubit_count,
                        row["interaction_index"],
                        row["instruction_index"],
                        row["gate"],
                        qubit_1,
                        qubit_2,
                    )
                )
                pair_counts[tuple(sorted((qubit_1, qubit_2)))] += 1
                interaction_count += 1

        circuit_graph = CircuitGraph(edges) if edges else None
        degrees = (
            circuit_graph.qubit_degree
            if circuit_graph is not None
            else [0] * qubit_count
        )
        qubit_interactions = (
            circuit_graph.qubit_interactions
            if circuit_graph is not None
            else [0] * qubit_count
        )

        name = path.name.removesuffix("_ordered_interactions.csv")
        records.append(
            CircuitData(
                name=name,
                algorithm=path.parent.name,
                qubit_count=qubit_count,
                interaction_count=interaction_count,
                pair_counts=pair_counts,
                degrees=degrees,
                dependency_depth=(
                    circuit_graph.dependency_depth
                    if circuit_graph is not None
                    else 0
                ),
                depth_pressure=(
                    circuit_graph.depth_pressure
                    if circuit_graph is not None
                    else 0.0
                ),
                qubit_interactions=qubit_interactions,
                interaction_matrix=(
                    circuit_graph.iteraction_matrix
                    if circuit_graph is not None
                    else [[0] * qubit_count for _ in range(qubit_count)]
                ),
                interaction_pairs=(
                    circuit_graph.interaction_pairs
                    if circuit_graph is not None
                    else []
                ),
                max_qubit_degree=(
                    circuit_graph.max_qubit_degree
                    if circuit_graph is not None
                    else 0
                ),
                max_qubit_interactions=(
                    circuit_graph.max_qubit_interactions
                    if circuit_graph is not None
                    else 0
                ),
            )
        )
    if not records:
        raise FileNotFoundError(
            f"No ordered interaction CSV files found under {data_root}"
        )
    return records


def load_topologies(data_root: Path) -> list[TopologyData]:
    records: list[TopologyData] = []
    for path in sorted((data_root / "topologies").rglob("*_weighted_edges.csv")):
        qubit_count = _qubit_count_from_name(path.name)
        arcs: list[tuple[int, int, float]] = []
        graph_edges: list[TopologyEdge] = []
        rates_by_link: dict[tuple[int, int], list[float]] = defaultdict(list)
        incoming = [0] * qubit_count
        outgoing = [0] * qubit_count
        with path.open("r", encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                source = int(row["source_qubit"])
                target = int(row["target_qubit"])
                error = float(row["gate_error_rate"])
                graph_edges.append(
                    TopologyEdge(source, target, error, 1.0 - error)
                )
                if source == target:
                    continue
                arcs.append((source, target, error))
                outgoing[source] += 1
                incoming[target] += 1
                rates_by_link[tuple(sorted((source, target)))].append(error)

        links = {
            pair: sum(rates) / len(rates)
            for pair, rates in rates_by_link.items()
        }
        topology_graph = TopologyGraph(graph_edges)
        adjacent_errors = topology_graph.mean_adjacent_error
        records.append(
            TopologyData(
                name=path.stem.removesuffix("_weighted_edges"),
                architecture=path.parent.name,
                qubit_count=qubit_count,
                arcs=arcs,
                links=links,
                in_degrees=incoming,
                out_degrees=outgoing,
                adjacent_errors=adjacent_errors,
                qubit_degree=topology_graph.qubit_degree,
                global_adjacent_error=topology_graph.global_adjacent_error,
                mean_distance=topology_graph.mean_distance,
                mean_path_error=topology_graph.mean_path_error,
                max_mean_distance=topology_graph.max_mean_distance,
                max_mean_path_error=topology_graph.max_mean_path_error,
            )
        )
    if not records:
        raise FileNotFoundError(f"No weighted topology CSV files found under {data_root}")
    return records


def save_graph_metrics(
    circuits: list[CircuitData],
    topologies: list[TopologyData],
    output_path: Path,
) -> None:
    fields = [
        "grafo",
        "categoria",
        "tipo",
        "vertices",
        "arcos_direcionados",
        "arestas_nao_direcionadas",
        "densidade_direcionada",
        "densidade_nao_direcionada",
        "grau_medio",
        "grau_medio_entrada",
        "grau_medio_saida",
        "interacoes_dois_qubits",
        "profundidade_dependencia",
        "pressao_profundidade",
        "grau_maximo_qubit",
        "interacoes_maximo_qubit",
        "erro_adjacente_global",
        "distancia_media_maxima",
        "erro_caminho_medio_maximo",
        "grau_maximo_fisico",
        "erro_adjacente_maximo",
        "origem_peso",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for circuit in circuits:
            mean_degree = (
                sum(circuit.degrees) / circuit.qubit_count
                if circuit.qubit_count
                else 0.0
            )
            possible_pairs = circuit.qubit_count * (circuit.qubit_count - 1) / 2
            writer.writerow(
                {
                    "grafo": circuit.name,
                    "categoria": circuit.algorithm,
                    "tipo": "simples, nao direcionado e ponderado",
                    "vertices": circuit.qubit_count,
                    "arcos_direcionados": "",
                    "arestas_nao_direcionadas": len(circuit.pair_counts),
                    "densidade_direcionada": "",
                    "densidade_nao_direcionada": circuit.density,
                    "grau_medio": mean_degree,
                    "grau_medio_entrada": "",
                    "grau_medio_saida": mean_degree,
                    "interacoes_dois_qubits": circuit.interaction_count,
                    "profundidade_dependencia": circuit.dependency_depth,
                    "pressao_profundidade": circuit.depth_pressure,
                    "grau_maximo_qubit": circuit.max_qubit_degree,
                    "interacoes_maximo_qubit": (
                        circuit.max_qubit_interactions
                    ),
                    "erro_adjacente_global": "",
                    "distancia_media_maxima": "",
                    "erro_caminho_medio_maximo": "",
                    "grau_maximo_fisico": "",
                    "erro_adjacente_maximo": "",
                    "origem_peso": (
                        f"contagem de gates de dois qubits; "
                        f"{int(possible_pairs)} pares possiveis"
                    ),
                }
            )
        for topology in topologies:
            writer.writerow(
                {
                    "grafo": topology.name,
                    "categoria": topology.architecture,
                    "tipo": "direcionado e ponderado",
                    "vertices": topology.qubit_count,
                    "arcos_direcionados": len(topology.arcs),
                    "arestas_nao_direcionadas": len(topology.links),
                    "densidade_direcionada": topology.directed_density,
                    "densidade_nao_direcionada": topology.link_density,
                    "grau_medio": (
                        sum(topology.out_degrees) / topology.qubit_count
                        if topology.qubit_count
                        else 0.0
                    ),
                    "grau_medio_entrada": (
                        sum(topology.in_degrees) / topology.qubit_count
                        if topology.qubit_count
                        else 0.0
                    ),
                    "grau_medio_saida": (
                        sum(topology.out_degrees) / topology.qubit_count
                        if topology.qubit_count
                        else 0.0
                    ),
                    "interacoes_dois_qubits": "",
                    "profundidade_dependencia": "",
                    "pressao_profundidade": "",
                    "grau_maximo_qubit": "",
                    "interacoes_maximo_qubit": "",
                    "erro_adjacente_global": (
                        topology.global_adjacent_error
                    ),
                    "distancia_media_maxima": topology.max_mean_distance,
                    "erro_caminho_medio_maximo": (
                        topology.max_mean_path_error
                    ),
                    "grau_maximo_fisico": max(
                        topology.qubit_degree.values(),
                        default=0,
                    ),
                    "erro_adjacente_maximo": max(
                        topology.adjacent_errors.values(),
                        default=0.0,
                    ),
                    "origem_peso": (
                        "taxa de erro sintetica do gate de dois qubits; "
                        "CSV preserva arcos direcionados"
                    ),
                }
            )


def _prepare_axes(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=COLORS["light"], linewidth=0.8)
    ax.set_axisbelow(True)


def _save(fig, output_dir: Path, filename: str) -> None:
    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_circuit_scaling(circuits: list[CircuitData], output_dir: Path) -> str:
    fig, ax = plt.subplots(figsize=(10.5, 6))
    qubit_counts = sorted({circuit.qubit_count for circuit in circuits})
    for index, circuit in enumerate(circuits):
        ax.scatter(
            circuit.qubit_count,
            circuit.interaction_count,
            color=COLORS["blue"],
            alpha=0.24,
            s=24,
            edgecolors="none",
            label="Circuito" if index == 0 else None,
        )
    medians = [
        float(
            np.median(
                [
                    circuit.interaction_count
                    for circuit in circuits
                    if circuit.qubit_count == qubit_count
                ]
            )
        )
        for qubit_count in qubit_counts
    ]
    ax.plot(
        qubit_counts,
        medians,
        color=COLORS["orange"],
        marker="o",
        linewidth=2.2,
        markersize=5,
        label="Mediana por número de qubits",
    )
    ax.set(
        title="O volume de interações cresce de forma desigual entre circuitos",
        xlabel="Qubits lógicos",
        ylabel="Instruções de dois qubits",
    )
    ax.legend(frameon=False)
    _prepare_axes(ax)
    _save(fig, output_dir, "01_escala_circuitos.png")
    return (
        "Mostra o número de instruções de dois qubits por circuito em função do "
        "número de qubits. Cada ponto é um CSV pré-computado; a linha laranja "
        "resume a mediana em cada tamanho. A dispersão entre pontos de mesmo "
        "tamanho mostra que o número de qubits, sozinho, não explica o custo "
        "de roteamento. O diagrama de dispersão é adequado para observar escala "
        "e variabilidade sem ocultar circuitos individuais."
    )


def plot_circuit_relations(circuits: list[CircuitData], output_dir: Path) -> str:
    fig, ax = plt.subplots(figsize=(10.5, 6))
    densities = [circuit.density for circuit in circuits]
    norm = Normalize(vmin=min(densities, default=0), vmax=max(densities, default=1))
    scatter = ax.scatter(
        [circuit.dependency_depth for circuit in circuits],
        [circuit.interaction_count for circuit in circuits],
        c=densities,
        cmap="viridis",
        norm=norm,
        s=42,
        alpha=0.78,
        edgecolors="white",
        linewidths=0.35,
    )
    for circuit in sorted(
        circuits,
        key=lambda item: item.interaction_count,
        reverse=True,
    )[:5]:
        ax.annotate(
            circuit.name,
            (circuit.dependency_depth, circuit.interaction_count),
            xytext=(5, 4),
            textcoords="offset points",
            fontsize=7,
            color=COLORS["ink"],
        )
    fig.colorbar(scatter, ax=ax, label="Densidade do grafo de interações")
    ax.legend(
        handles=[
            Line2D(
                [0], [0], marker="o", linestyle="none", color=COLORS["blue"],
                label="Circuito (cor = densidade)",
            )
        ],
        frameon=False,
    )
    ax.set(
        title="Interações, dependência temporal e densidade do circuito",
        xlabel="Profundidade de dependência (somente gates de 2 qubits)",
        ylabel="Instruções de dois qubits",
    )
    _prepare_axes(ax)
    _save(fig, output_dir, "02_relacao_interacoes_profundidade.png")
    return (
        "Relaciona quantidade de interações com a profundidade de dependência "
        "derivada da ordem dos gates de dois qubits; a cor representa a densidade "
        "do grafo lógico. Os cinco circuitos com mais interações são identificados "
        "para facilitar a investigação de casos extremos. Profundidade aqui não "
        "inclui gates de um qubit, medições ou barreiras porque esses atributos "
        "não estão nos CSVs de interações. O espalhamento multivariado permite "
        "ver relações e exceções sem presumir linearidade."
    )


def plot_topology_structure(
    topologies: list[TopologyData],
    output_dir: Path,
) -> str:
    fig, ax = plt.subplots(figsize=(10.5, 6))
    architectures = sorted({topology.architecture for topology in topologies})
    palette = dict(
        zip(
            architectures,
            [
                COLORS["blue"],
                COLORS["orange"],
                COLORS["green"],
                COLORS["red"],
                COLORS["purple"],
                COLORS["gray"],
            ],
        )
    )
    markers = {
        "full": "o",
        "grid": "s",
        "heavy_hex": "^",
        "heavy_square": "D",
        "line": "v",
        "ring": "P",
    }
    for architecture in architectures:
        group = [
            topology
            for topology in topologies
            if topology.architecture == architecture
        ]
        ax.scatter(
            [topology.qubit_count for topology in group],
            [topology.link_density for topology in group],
            label=architecture,
            color=palette[architecture],
            marker=markers.get(architecture, "o"),
            s=36,
            alpha=0.78,
            edgecolors="white",
            linewidths=0.35,
        )
    ax.set(
        title="Tamanho e conectividade das topologias de hardware",
        xlabel="Qubits físicos (|V|)",
        ylabel="Densidade de links físicos |E| / possíveis pares",
        ylim=(-0.03, 1.03),
    )
    ax.legend(title="Arquitetura", frameon=False, ncol=2)
    _prepare_axes(ax)
    _save(fig, output_dir, "03_estrutura_topologias.png")
    return (
        "Cada ponto representa uma topologia pré-computada; a densidade trata "
        "como link físico um par conectado por pelo menos um arco direcionado. "
        "A comparação entre famílias existentes (full, grid, heavy-hex, "
        "heavy-square, line e ring) evidencia o compromisso entre quantidade "
        "de qubits e conectividade. Topologias com tamanhos diferentes não são "
        "comparações controladas de desempenho; o gráfico descreve estrutura, "
        "não qualidade do mapeamento."
    )


def plot_error_outliers(topologies: list[TopologyData], output_dir: Path) -> str:
    architectures = sorted({topology.architecture for topology in topologies})
    samples = [
        [
            error * 100
            for topology in topologies
            if topology.architecture == architecture
            for _, _, error in topology.arcs
        ]
        for architecture in architectures
    ]
    all_errors = [value for sample in samples for value in sample]
    q1, q3 = np.percentile(all_errors, [25, 75])
    iqr = q3 - q1
    lower_fence, upper_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    fig, ax = plt.subplots(figsize=(10.5, 6))
    box = ax.boxplot(
        samples,
        tick_labels=architectures,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": COLORS["ink"], "linewidth": 1.8},
        whiskerprops={"color": COLORS["gray"]},
        capprops={"color": COLORS["gray"]},
    )
    colors = [
        COLORS["blue"],
        COLORS["orange"],
        COLORS["green"],
        COLORS["red"],
        COLORS["purple"],
        COLORS["gray"],
    ]
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
    for index, sample in enumerate(samples, start=1):
        outliers = [
            error
            for error in sample
            if error < lower_fence or error > upper_fence
        ]
        if outliers:
            jitter = np.linspace(-0.13, 0.13, len(outliers))
            ax.scatter(
                np.full(len(outliers), index) + jitter,
                outliers,
                color=COLORS["red"],
                s=17,
                alpha=0.76,
                label="Fora do limite IQR" if index == 1 else None,
                zorder=3,
            )
    ax.set(
        title="Distribuição das taxas de erro dos links direcionados",
        xlabel="Família da topologia",
        ylabel="Erro de gate de dois qubits (%)",
    )
    ax.legend(
        handles=[
            Patch(
                facecolor="#DCE6EF",
                edgecolor=COLORS["gray"],
                label="Mediana e intervalo interquartil",
            ),
            Line2D(
                [0], [0], marker="o", linestyle="none", color=COLORS["red"],
                label="Fora do limite IQR",
            ),
        ],
        frameon=False,
    )
    _prepare_axes(ax)
    _save(fig, output_dir, "04_erros_e_outliers.png")
    flagged = sum(
        value < lower_fence or value > upper_fence for value in all_errors
    )
    return (
        f"Compara taxas de erro por família de topologia; pontos vermelhos indicam "
        f"{flagged} observações fora dos limites de 1,5 × IQR calculados sobre "
        "todos os arcos. São sinalizações para inspeção, não erros a excluir: "
        "um link com erro alto pode ser um atributo físico real e relevante para "
        "o mapeamento. As taxas são sintéticas no dataset, portanto não devem "
        "ser interpretadas como calibrações de um dispositivo real. Boxplots "
        "resumem mediana, dispersão e caudas sem usar gráficos de pizza."
    )


def _find_circuit(circuits: list[CircuitData], requested_name: str) -> CircuitData:
    for circuit in circuits:
        if circuit.name == requested_name:
            return circuit
    available = ", ".join(circuit.name for circuit in circuits[:8])
    raise ValueError(
        f"Circuit '{requested_name}' not found in interaction data. "
        f"Examples: {available}"
    )


def _find_topology(
    topologies: list[TopologyData],
    requested_name: str,
) -> TopologyData:
    for topology in topologies:
        if topology.name == requested_name:
            return topology
    available = ", ".join(topology.name for topology in topologies[:8])
    raise ValueError(
        f"Topology '{requested_name}' not found. Examples: {available}"
    )


def _top_pair_labels(
    top_pairs: list[tuple[int, int]],
) -> tuple[str, str]:
    if not top_pairs:
        return "nenhum", "Sem pares recorrentes"
    if len(top_pairs) > 6:
        return (
            f"{len(top_pairs)} pares",
            f"Pares mais recorrentes ({len(top_pairs)} pares)",
        )
    pair_names = ", ".join(
        f"q{qubit_1}–q{qubit_2}" for qubit_1, qubit_2 in top_pairs
    )
    return pair_names, f"Pares mais recorrentes: {pair_names}"


def plot_circuit_graph(circuit: CircuitData, output_dir: Path) -> str:
    graph = nx.Graph()
    graph.add_nodes_from(range(circuit.qubit_count))
    for (qubit_1, qubit_2), weight in circuit.pair_counts.items():
        graph.add_edge(qubit_1, qubit_2, weight=weight)
    positions = nx.spring_layout(graph, seed=17, weight="weight")
    degrees = dict(graph.degree())
    node_sizes = [600 + 170 * degrees[node] for node in graph]
    weights = [graph[u][v]["weight"] for u, v in graph.edges()]
    max_weight = max(weights, default=1)
    top_weight = max(circuit.pair_counts.values(), default=0)
    top_pairs = [
        pair for pair, weight in circuit.pair_counts.items() if weight == top_weight
    ]
    top_pair_label, top_pair_legend_label = _top_pair_labels(top_pairs)
    hub_degree = max(degrees.values(), default=0)
    hubs = [node for node, degree in degrees.items() if degree == hub_degree]
    edge_widths = [1.0 + 4.0 * weight / max_weight for weight in weights]
    edge_colors = [
        COLORS["orange"]
        if graph[u][v]["weight"] == top_weight
        else "#9CB8CE"
        for u, v in graph.edges()
    ]
    fig, ax = plt.subplots(figsize=(9, 7))
    nx.draw_networkx_edges(
        graph,
        positions,
        ax=ax,
        width=edge_widths,
        edge_color=edge_colors,
        alpha=0.82,
    )
    nx.draw_networkx_nodes(
        graph,
        positions,
        ax=ax,
        node_size=node_sizes,
        node_color=[
            COLORS["orange"] if degrees[node] == hub_degree else COLORS["blue"]
            for node in graph
        ],
        edgecolors="white",
        linewidths=1.5,
    )
    nx.draw_networkx_labels(
        graph,
        positions,
        ax=ax,
        labels={node: f"q{node}" for node in graph},
        font_size=9,
        font_color=COLORS["ink"],
    )
    nx.draw_networkx_edge_labels(
        graph,
        positions,
        ax=ax,
        edge_labels={(u, v): graph[u][v]["weight"] for u, v in graph.edges()},
        font_size=8,
        font_color=COLORS["ink"],
        rotate=False,
        label_pos=0.55,
    )
    ax.set_title(
        f"Grafo de interações: {circuit.name}\n"
        f"Par(es) mais recorrente(s): {top_pair_label} ({top_weight} gates); "
        f"maior grau: {hubs} ({hub_degree})"
    )
    ax.axis("off")
    ax.legend(
        handles=[
            Line2D(
                [0], [0], color=COLORS["orange"], linewidth=3,
                label=top_pair_legend_label,
            ),
            Line2D(
                [0], [0], color="#9CB8CE", linewidth=2, label="Outros pares"
            ),
            Line2D(
                [0], [0], marker="o", color="w",
                markerfacecolor=COLORS["orange"], label="Maior grau",
            ),
        ],
        loc="upper left",
        frameon=False,
    )
    _save(fig, output_dir, "05_grafo_interacoes.png")
    return (
        f"Mostra o grafo lógico não direcionado de {circuit.name}: nós são "
        "qubits lógicos, tamanho do nó indica grau, o laranja destaca os qubits "
        "de maior grau e os pares mais recorrentes, e largura/rótulo da aresta indicam a "
        "frequência de interações. Par(es) mais recorrente(s): "
        f"{top_pair_label} ({top_weight} gates); o maior grau é "
        f"dos qubits {hubs} (grau {hub_degree}). A agregação perde ordem temporal "
        "e direção do gate, então o grafo explica afinidade estrutural, não uma "
        "rota nem um mapeamento."
    )


def plot_topology_graph(topology: TopologyData, output_dir: Path) -> str:
    graph = nx.Graph()
    graph.add_nodes_from(range(topology.qubit_count))
    graph.add_weighted_edges_from(
        (qubit_1, qubit_2, error)
        for (qubit_1, qubit_2), error in topology.links.items()
    )
    positions = nx.spring_layout(graph, seed=17, weight=None)
    edge_errors = [graph[u][v]["weight"] for u, v in graph.edges()]
    edge_errors_percent = [error * 100 for error in edge_errors]
    max_error = max(edge_errors_percent, default=0.0)
    fig, ax = plt.subplots(figsize=(10, 8))
    nx.draw_networkx_edges(
        graph,
        positions,
        ax=ax,
        width=[
            1.0 + 3.0 * error / max_error if max_error else 1.0
            for error in edge_errors_percent
        ],
        edge_color=edge_errors_percent,
        edge_cmap=plt.cm.Reds,
        edge_vmin=0,
        edge_vmax=max_error or 1.0,
        alpha=0.82,
    )
    nx.draw_networkx_nodes(
        graph,
        positions,
        ax=ax,
        node_size=[
            520 + 110 * graph.degree(node) for node in graph
        ],
        node_color=COLORS["blue"],
        edgecolors="white",
        linewidths=1.3,
    )
    nx.draw_networkx_labels(
        graph,
        positions,
        ax=ax,
        labels={node: str(node) for node in graph},
        font_size=9,
        font_color=COLORS["ink"],
    )
    worst_link = max(
        topology.links.items(),
        key=lambda item: item[1],
        default=((0, 0), 0.0),
    )
    best_link = min(
        topology.links.items(),
        key=lambda item: item[1],
        default=((0, 0), 0.0),
    )
    total_degrees = {
        node: topology.in_degrees[node] + topology.out_degrees[node]
        for node in range(topology.qubit_count)
    }
    hub_degree = max(total_degrees.values(), default=0)
    hubs = [node for node, degree in total_degrees.items() if degree == hub_degree]
    if len(graph.edges) <= 12:
        nx.draw_networkx_edge_labels(
            graph,
            positions,
            ax=ax,
            edge_labels={
                (u, v): f"{graph[u][v]['weight'] * 100:.2f}%"
                for u, v in graph.edges()
            },
            font_size=7,
            rotate=False,
            label_pos=0.5,
        )
    ax.set_title(
        f"Topologia física: {topology.name}\n"
        f"Maior erro: {worst_link[0]} ({worst_link[1] * 100:.2f}%) | "
        f"maior grau: {hubs} ({hub_degree})"
    )
    ax.axis("off")
    fig.colorbar(
        ScalarMappable(
            norm=Normalize(vmin=0, vmax=max_error or 1.0),
            cmap=plt.cm.Reds,
        ),
        ax=ax,
        fraction=0.046,
        pad=0.03,
        label="Erro médio do link (%)",
    )
    ax.legend(
        handles=[
            Line2D(
                [0], [0], marker="o", linestyle="none", color=COLORS["blue"],
                label="Qubit físico (tamanho = grau)",
            ),
            Line2D(
                [0], [0], color=COLORS["red"], linewidth=2,
                label="Link (cor = erro estimado)",
            ),
        ],
        loc="upper left",
        frameon=False,
    )
    _save(fig, output_dir, "06_grafo_topologia.png")
    return (
        f"Mostra a topologia física {topology.name}: tamanho do nó representa "
        "grau e cor/rótulo da aresta representa a taxa de erro média entre os "
        "arcos do par, em porcentagem (em topologias densas, os rótulos são omitidos para "
        "preservar legibilidade). "
        "O maior grau total é do qubit físico "
        f"{hubs} (entrada/saída por qubit: "
        + ", ".join(
            f"{node}={topology.in_degrees[node]}/{topology.out_degrees[node]}"
            for node in hubs
        )
        + "). O link com maior erro é "
        f"{worst_link[0]} ({worst_link[1] * 100:.3f}%) e o menor é "
        f"{best_link[0]} ({best_link[1] * 100:.3f}%). A visualização agrega "
        "arcos recíprocos para legibilidade; o CSV original e as métricas "
        "preservam graus e contagens direcionadas. Este contraste ajuda a "
        "formular hipóteses de posicionamento, mas não prova desempenho."
    )


def generate(
    data_root: Path,
    output_dir: Path,
    circuit_name: str,
    topology_name: str,
) -> None:
    circuits = load_circuits(data_root)
    topologies = load_topologies(data_root)
    selected_circuit = _find_circuit(circuits, circuit_name)
    selected_topology = _find_topology(topologies, topology_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titleweight": "bold",
            "axes.titlecolor": COLORS["ink"],
            "axes.labelcolor": COLORS["ink"],
            "xtick.color": COLORS["ink"],
            "ytick.color": COLORS["ink"],
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )

    notes = [
        plot_circuit_scaling(circuits, output_dir),
        plot_circuit_relations(circuits, output_dir),
        plot_topology_structure(topologies, output_dir),
        plot_error_outliers(topologies, output_dir),
        plot_circuit_graph(selected_circuit, output_dir),
        plot_topology_graph(selected_topology, output_dir),
    ]
    save_graph_metrics(
        circuits,
        topologies,
        output_dir / "metricas_grafos.csv",
    )
    note_path = output_dir / "notas_analiticas.md"
    with note_path.open("w", encoding="utf-8") as file:
        file.write("# Notas analíticas das visualizações\n\n")
        file.write(
            "Os gráficos usam os CSVs pré-computados em `datasets/`; não executam "
            "algoritmos de mapeamento nem estimam tempos de execução. Os pesos "
            "das interações são contagens de gates de dois qubits. Os pesos do "
            "hardware são taxas de erro sintéticas.\n\n"
        )
        for index, note in enumerate(notes, start=1):
            image_name = [
                "01_escala_circuitos.png",
                "02_relacao_interacoes_profundidade.png",
                "03_estrutura_topologias.png",
                "04_erros_e_outliers.png",
                "05_grafo_interacoes.png",
                "06_grafo_topologia.png",
            ][index - 1]
            file.write(f"## {index}. `{image_name}`\n\n{note}\n\n")
        file.write(
            "## Comparação com soluções existentes\n\n"
            "O repositório oferece `optimal_map` (busca exata), `heuristic_map` "
            "(busca multi-start) e uma inicialização por fluxo de custo mínimo "
            "seguida de hill climbing. `analysis/benchmark_mappers.py` mede "
            "multi-start, fluxo min-cost e Qiskit SABRE em 36 casos padrão "
            "(quatro famílias de circuito, três tamanhos e três topologias), "
            "com cinco execuções por método e caso. A busca exata é limitada "
            "aos 12 casos de quatro qubits. Consulte "
            "`out/parte2/mapping_benchmarks.csv` para tempos, SWAPs, "
            "mapeamentos iniciais/finais e erro estimado. SABRE é uma "
            "referência de mercado medida, enquanto VF2Layout é apenas uma "
            "referência qualitativa de layout: encontra embedding sem SWAP "
            "somente quando há subgrafo compatível. O erro do benchmark usa "
            "taxas sintéticas dos links e não representa hardware real. As "
            "figuras deste relatório continuam descritivas dos datasets e "
            "não alegam superioridade de algoritmo.\n"
        )
    print(
        f"Generated 6 figures, graph metrics, and analytical notes in {output_dir}"
    )


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Generate AVD figures from precomputed circuit and topology CSVs."
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=repository_root / "datasets",
        help="Root containing interaction_order/ and topologies/.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repository_root / "out" / "parte2",
        help="Directory for PNG figures, graph metrics, and analytical notes.",
    )
    parser.add_argument(
        "--circuit",
        default="modular_adder_6qubits",
        help="Circuit CSV basename without _ordered_interactions.csv.",
    )
    parser.add_argument(
        "--topology",
        default="line_6qubits",
        help="Topology CSV basename without _weighted_edges.csv.",
    )
    args = parser.parse_args()
    generate(args.data_root, args.output_dir, args.circuit, args.topology)


if __name__ == "__main__":
    main()
