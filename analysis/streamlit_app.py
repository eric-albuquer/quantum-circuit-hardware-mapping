from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from analysis.presentation import show_presentation
from analysis.visualize_avd import (
    generate,
    load_circuits,
    load_topologies,
    save_graph_metrics,
)
from src.circuit_graph.loader import load_circuit_graph
from src.topology_graph.loader import load_topology_graph


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "out" / "parte2"
METRICS_PATH = OUTPUT / "metricas_grafos.csv"
BENCHMARK_PATH = OUTPUT / "mapping_benchmarks.csv"
ALGORITHM_OPTIONS = (
    (
        "Busca exata",
        "Busca exata",
        "Referência ótima; disponível só nos casos pequenos.",
    ),
    (
        "Heurística multi-start",
        "Multi-start",
        "Busca várias colocações iniciais.",
    ),
    (
        "Fluxo min-cost + hill climb",
        "Fluxo min-cost",
        "Atribuição por fluxo, seguida de refinamento local.",
    ),
    ("Qiskit SABRE", "Qiskit SABRE", "Baseline de roteamento do Qiskit."),
)
REQUIRED_METRIC_COLUMNS = {
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
}

st.set_page_config(
    page_title="Mapeamento de circuitos quânticos",
    page_icon="🧭",
    layout="wide",
)


@st.cache_data
def _read_csv(path: str, modified_at: int) -> pd.DataFrame:
    del modified_at
    return pd.read_csv(path)


def _read_if_present(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return _read_csv(str(path), path.stat().st_mtime_ns)


def _read_graph_metrics() -> pd.DataFrame:
    metrics = _read_if_present(METRICS_PATH)
    if not REQUIRED_METRIC_COLUMNS.issubset(metrics.columns):
        with st.spinner("Atualizando métricas dos circuitos e topologias..."):
            METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
            circuits_data = load_circuits(ROOT / "datasets")
            topologies_data = load_topologies(ROOT / "datasets")
            save_graph_metrics(
                circuits_data,
                topologies_data,
                METRICS_PATH,
            )
        metrics = _read_if_present(METRICS_PATH)
    return metrics


def _available_graph_rows(
    graphs: pd.DataFrame,
    source_root: Path,
    suffix: str,
) -> pd.DataFrame:
    available = [
        (source_root / str(row.categoria) / f"{row.grafo}{suffix}").is_file()
        for row in graphs.itertuples()
    ]
    return graphs.loc[available].copy()


def _reset_stale_selection(key: str, options: list[str]) -> None:
    if key in st.session_state and st.session_state[key] not in options:
        del st.session_state[key]


def _mapping_label(serialized_mapping: str) -> str:
    mapping = json.loads(serialized_mapping)
    return ", ".join(
        f"L{logical} → P{physical}"
        for logical, physical in sorted(
            mapping.items(),
            key=lambda item: int(item[0]),
        )
    )


def _select_algorithms(available: list[str], key_prefix: str) -> list[str]:
    columns = st.columns(len(ALGORITHM_OPTIONS))
    selected = []
    for index, (algorithm, label, help_text) in enumerate(ALGORITHM_OPTIONS):
        if algorithm not in available:
            continue
        if columns[index].checkbox(
            label,
            value=algorithm != "Busca exata",
            help=help_text,
            key=f"{key_prefix}_{index}",
        ):
            selected.append(algorithm)
    return selected


@st.cache_data
def _load_graph_details(
    circuit_path: str,
    circuit_modified_at: float,
    topology_path: str,
    topology_modified_at: float,
) -> dict[str, object]:
    del circuit_modified_at, topology_modified_at
    circuit = load_circuit_graph(circuit_path)
    topology = load_topology_graph(topology_path)
    logical_ids = list(range(circuit.qubit_count))
    logical_labels = [f"L{logical}" for logical in logical_ids]
    physical_ids = sorted(topology.graph)
    physical_labels = [f"P{physical}" for physical in physical_ids]

    logical_qubits = pd.DataFrame(
        {
            "Qubit lógico": logical_labels,
            "Grau": circuit.qubit_degree,
            "Interações de 2 qubits": circuit.qubit_interactions,
        }
    )
    physical_qubits = pd.DataFrame(
        {
            "Qubit físico": physical_labels,
            "Grau": [
                topology.qubit_degree[physical] for physical in physical_ids
            ],
            "Erro adjacente médio (%)": [
                topology.mean_adjacent_error[physical] * 100
                for physical in physical_ids
            ],
            "Distância média": [
                topology.mean_distance[physical] for physical in physical_ids
            ],
            "Erro médio dos caminhos (%)": [
                topology.mean_path_error[physical] * 100
                for physical in physical_ids
            ],
        }
    )
    interaction_matrix = pd.DataFrame(
        circuit.iteraction_matrix,
        index=logical_labels,
        columns=logical_labels,
    )
    path_lengths = [
        [
            len(path) - 1 if path else None
            for path in topology.path_matrix[source]
        ]
        for source in physical_ids
    ]
    path_errors = [
        [
            error if error != float("inf") else None
            for error in topology.error_matrix[source]
        ]
        for source in physical_ids
    ]
    directed_arcs = sum(
        source != target
        for source, neighbors in topology.graph.items()
        for target in neighbors
    )
    physical_links = {
        (min(source, target), max(source, target))
        for source, neighbors in topology.graph.items()
        for target in neighbors
        if source != target
    }
    physical_qubit_count = topology.qubit_count
    return {
        "circuit_summary": {
            "qubits": circuit.qubit_count,
            "interactions": circuit.two_qubit_interaction_count,
            "interaction_pairs": len(circuit.interaction_pairs),
            "dependency_depth": circuit.dependency_depth,
            "depth_pressure": circuit.depth_pressure,
            "max_qubit_degree": circuit.max_qubit_degree,
            "max_qubit_interactions": circuit.max_qubit_interactions,
        },
        "topology_summary": {
            "qubits": physical_qubit_count,
            "directed_arcs": directed_arcs,
            "physical_links": len(physical_links),
            "directed_density": (
                directed_arcs / (physical_qubit_count * (physical_qubit_count - 1))
                if physical_qubit_count > 1
                else 0.0
            ),
            "global_adjacent_error": topology.global_adjacent_error,
            "max_mean_distance": topology.max_mean_distance,
            "max_mean_path_error": topology.max_mean_path_error,
            "max_degree": max(topology.qubit_degree.values(), default=0),
        },
        "logical_qubits": logical_qubits,
        "physical_qubits": physical_qubits,
        "interaction_pairs": pd.DataFrame(
            circuit.interaction_pairs,
            columns=[
                "Qubit lógico 1",
                "Qubit lógico 2",
                "Interações",
            ],
        ),
        "interaction_matrix": interaction_matrix,
        "path_lengths": pd.DataFrame(
            path_lengths,
            index=physical_labels,
            columns=physical_labels,
        ),
        "path_errors": pd.DataFrame(
            path_errors,
            index=physical_labels,
            columns=physical_labels,
        ),
    }


def _show_graph_metrics(details: dict[str, object]) -> None:
    circuit = details["circuit_summary"]
    topology = details["topology_summary"]

    st.subheader("Métricas pré-computadas dos grafos")
    circuit_column, topology_column = st.columns(2)
    with circuit_column:
        st.markdown("**Circuito lógico**")
        first_row = st.columns(3)
        first_row[0].metric("Qubits", circuit["qubits"])
        first_row[1].metric(
            "Gates de 2 qubits",
            circuit["interactions"],
        )
        first_row[2].metric("Pares distintos", circuit["interaction_pairs"])
        second_row = st.columns(3)
        second_row[0].metric(
            "Profundidade",
            circuit["dependency_depth"],
        )
        second_row[1].metric(
            "Maior grau",
            circuit["max_qubit_degree"],
        )
        second_row[2].metric(
            "Maior interações/qubit",
            circuit["max_qubit_interactions"],
        )
        st.caption(
            f"Pressão de profundidade: {circuit['depth_pressure']:.3f} "
            "(0 = mais paralelizável; 1 = dependências em série)."
        )

    with topology_column:
        st.markdown("**Topologia física**")
        first_row = st.columns(3)
        first_row[0].metric("Qubits", topology["qubits"])
        first_row[1].metric("Arcos direcionados", topology["directed_arcs"])
        first_row[2].metric("Links físicos", topology["physical_links"])
        second_row = st.columns(3)
        second_row[0].metric("Maior grau", topology["max_degree"])
        second_row[1].metric(
            "Erro médio dos links",
            f"{topology['global_adjacent_error'] * 100:.3f}%",
        )
        second_row[2].metric(
            "Densidade",
            f"{topology['directed_density']:.3f}",
        )
        st.caption(
            f"Maior distância média: {topology['max_mean_distance']:.2f} hops; "
            "maior erro médio de caminho: "
            f"{topology['max_mean_path_error'] * 100:.3f}%."
        )

    with st.expander("Explorar métricas por qubit e matrizes de caminhos"):
        logical_tab, physical_tab, matrix_tab = st.tabs(
            ["Qubits lógicos", "Qubits físicos", "Matrizes"]
        )
        with logical_tab:
            st.dataframe(
                details["logical_qubits"],
                width="stretch",
                hide_index=True,
            )
            st.bar_chart(
                details["logical_qubits"],
                x="Qubit lógico",
                y="Grau",
                height=300,
            )
            st.bar_chart(
                details["logical_qubits"],
                x="Qubit lógico",
                y="Interações de 2 qubits",
                height=300,
            )
            with st.expander("Pares de interação e frequências"):
                st.dataframe(
                    details["interaction_pairs"],
                    width="stretch",
                    hide_index=True,
                )
        with physical_tab:
            st.dataframe(
                details["physical_qubits"],
                width="stretch",
                hide_index=True,
            )
            physical_metrics = (
                ("Grau", "Grau"),
                ("Erro adjacente médio (%)", "Erro adjacente médio (%)"),
                ("Distância média", "Distância média"),
                (
                    "Erro médio dos caminhos (%)",
                    "Erro médio dos caminhos (%)",
                ),
            )
            metric_tabs = st.tabs([label for _, label in physical_metrics])
            for tab, (column, label) in zip(metric_tabs, physical_metrics):
                with tab:
                    st.bar_chart(
                        details["physical_qubits"],
                        x="Qubit físico",
                        y=column,
                        height=320,
                    )
        with matrix_tab:
            matrix_tabs = st.tabs(
                [
                    "Interações lógicas",
                    "Distâncias físicas",
                    "Erros de caminho",
                ]
            )
            matrices = (
                details["interaction_matrix"],
                details["path_lengths"],
                details["path_errors"],
            )
            for tab, matrix in zip(matrix_tabs, matrices):
                with tab:
                    st.dataframe(
                        matrix.style.background_gradient(
                            cmap="Blues",
                            axis=None,
                        ).format(na_rep="—"),
                        width="stretch",
                    )


def _show_figures(names: tuple[str, ...]) -> None:
    for offset in range(0, len(names), 2):
        columns = st.columns(2)
        for column, filename in zip(columns, names[offset : offset + 2]):
            image_path = OUTPUT / filename
            if image_path.is_file():
                column.image(
                    str(image_path),
                    caption=filename.removesuffix(".png").replace("_", " "),
                    width="stretch",
                )
            else:
                column.info(
                    f"Figura ausente: `{filename}`. "
                    "Execute `python -m analysis.visualize_avd`."
                )


def _summary_by_mapper(results: pd.DataFrame) -> pd.DataFrame:
    summary = results.groupby("algorithm", as_index=False).agg(
        runs=("run", "count"),
        tempo_mediano_s=("elapsed_seconds", "median"),
        tempo_medio_s=("elapsed_seconds", "mean"),
        swaps_medianos=("swap_count", "median"),
        erro_estimado_mediano=("expected_error_rate", "median"),
    )
    summary["erro_estimado_mediano_%"] = summary.pop(
        "erro_estimado_mediano"
    ) * 100
    return summary


def _show_algorithm_charts(
    results: pd.DataFrame,
    by_topology: bool = False,
) -> None:
    grouping = ["algorithm"]
    x_axis = "metodo"
    if by_topology:
        grouping.insert(0, "topology_category")
        x_axis = "Topologia"
    summary = results.groupby(grouping, as_index=False).agg(
        swaps_medianos=("swap_count", "median"),
        erro_estimado_mediano=("expected_error_rate", "median"),
        tempo_mediano_s=("elapsed_seconds", "median"),
    )
    summary["erro_estimado_mediano_%"] = (
        summary.pop("erro_estimado_mediano") * 100
    )
    summary["metodo"] = summary["algorithm"].map(
        {
            "Busca exata": "Busca exata",
            "Heurística multi-start": "Multi-start",
            "Fluxo min-cost + hill climb": "Fluxo min-cost",
            "Qiskit SABRE": "SABRE",
        }
    )
    summary = summary.rename(
        columns={
            "topology_category": "Topologia",
            "swaps_medianos": "SWAPs medianos",
            "erro_estimado_mediano_%": "Erro estimado mediano (%)",
            "tempo_mediano_s": "Tempo mediano (s)",
        }
    )
    chart_tabs = st.tabs(["SWAPs", "Erro estimado", "Tempo"])
    chart_specs = (
        "SWAPs medianos",
        "Erro estimado mediano (%)",
        "Tempo mediano (s)",
    )
    for tab, label in zip(chart_tabs, chart_specs):
        with tab:
            st.caption(f"{label} por algoritmo; valores menores são melhores.")
            st.bar_chart(
                summary,
                x=x_axis,
                y=label,
                color="metodo",
                stack=False,
                height=360,
            )


def _show_mapping_results(results: pd.DataFrame) -> None:
    if results.empty:
        st.info(
            "Não há benchmark para esta combinação. Execute "
            "`python -m analysis.benchmark_mappers`."
        )
        return

    summary = _summary_by_mapper(results)
    summary_for_display = summary[
        [
            "algorithm",
            "runs",
            "swaps_medianos",
            "tempo_mediano_s",
            "erro_estimado_mediano_%",
        ]
    ].rename(
        columns={
            "algorithm": "Algoritmo",
            "runs": "Execuções",
            "swaps_medianos": "SWAPs medianos",
            "tempo_mediano_s": "Tempo mediano (s)",
            "erro_estimado_mediano_%": "Erro estimado mediano (%)",
        }
    )
    st.subheader("Resumo numérico por algoritmo")
    st.dataframe(summary_for_display, width="stretch", hide_index=True)
    st.subheader("Comparação visual do caso")
    st.caption(
        "Cada barra mostra a mediana das execuções selecionadas; valores menores "
        "indicam menos SWAPs, menor erro estimado ou menor tempo."
    )
    _show_algorithm_charts(results)

    best_runs = (
        results.sort_values(
            ["expected_error_rate", "swap_count", "elapsed_seconds"]
        )
        .groupby("algorithm", as_index=False)
        .first()
    )
    best_runs = best_runs.assign(
        erro_estimado_percentual=best_runs["expected_error_rate"] * 100,
        mapeamento_inicial=best_runs["initial_mapping"].map(_mapping_label),
        mapeamento_final=best_runs["final_mapping"].map(_mapping_label),
    )
    st.subheader("Mapeamento escolhido por método")
    st.caption(
        "Uma linha por algoritmo: melhor execução segundo erro estimado, "
        "SWAPs e tempo, nessa ordem. L = qubit lógico; P = qubit físico."
    )
    st.dataframe(
        best_runs[
            [
                "algorithm",
                "run",
                "elapsed_seconds",
                "swap_count",
                "erro_estimado_percentual",
                "mapeamento_inicial",
                "mapeamento_final",
            ]
        ],
        width="stretch",
        hide_index=True,
    )
    with st.expander("Mapeamentos e métricas de todas as execuções"):
        all_runs = results.assign(
            erro_estimado_percentual=results["expected_error_rate"] * 100,
            mapeamento_inicial=results["initial_mapping"].map(_mapping_label),
            mapeamento_final=results["final_mapping"].map(_mapping_label),
        )
        st.dataframe(
            all_runs[
                [
                    "algorithm",
                    "run",
                    "seed",
                    "elapsed_seconds",
                    "swap_count",
                    "erro_estimado_percentual",
                    "mapeamento_inicial",
                    "mapeamento_final",
                    "implementation_version",
                ]
            ],
            width="stretch",
            hide_index=True,
        )


st.title(":blue[Mapeamento de circuitos quânticos]")
st.caption(
    "Compare grafos pré-computados, estratégias locais de mapeamento e "
    "Qiskit SABRE em condições controladas."
)

metrics = _read_graph_metrics()
benchmarks = _read_if_present(BENCHMARK_PATH)
if metrics.empty:
    st.warning(
        "Ainda não há métricas de grafo. Gere-as com "
        "`python -m analysis.visualize_avd`."
    )
    st.stop()

circuits = metrics[metrics["tipo"].str.startswith("simples")].copy()
topologies = metrics[metrics["tipo"].str.startswith("direcionado")].copy()
circuits = _available_graph_rows(
    circuits,
    ROOT / "datasets" / "interaction_order" / "algorithms",
    "_ordered_interactions.csv",
)
topologies = _available_graph_rows(
    topologies,
    ROOT / "datasets" / "topologies",
    "_weighted_edges.csv",
)
if circuits.empty or topologies.empty:
    st.error(
        "Não encontrei arquivos de circuitos ou topologias. Verifique "
        "`datasets/` e atualize as métricas com `python -m analysis.visualize_avd`."
    )
    st.stop()
circuits = circuits[circuits["vertices"] <= topologies["vertices"].max()]
if circuits.empty:
    st.error(
        "Nenhum circuito cabe nas topologias disponíveis. Atualize os dados "
        "ou gere topologias com mais qubits."
    )
    st.stop()

if not benchmarks.empty:
    available_circuits = set(zip(circuits["categoria"], circuits["grafo"]))
    available_topologies = set(zip(topologies["categoria"], topologies["grafo"]))
    benchmark_rows = [
        (row.circuit_category, row.circuit) in available_circuits
        and (row.topology_category, row.topology) in available_topologies
        for row in benchmarks.itertuples()
    ]
    benchmarks = benchmarks.loc[benchmark_rows].copy()

tab_overview, tab_case, tab_comparison = st.tabs(
    ["Apresentação", "Caso selecionado", "Comparação de algoritmos"]
)

with tab_overview:
    show_presentation(circuits, topologies, benchmarks)
    with st.expander("Explorar os conjuntos de circuitos e topologias"):
        circuit_category = st.selectbox(
            "Filtrar tabela de circuitos por categoria",
            ["Todas"] + sorted(circuits["categoria"].dropna().unique()),
            key="overview_circuit_category",
        )
        topology_category = st.selectbox(
            "Filtrar tabela de topologias por arquitetura",
            ["Todas"] + sorted(topologies["categoria"].dropna().unique()),
            key="overview_topology_category",
        )
        left, right = st.columns(2)
        filtered_circuits = circuits
        if circuit_category != "Todas":
            filtered_circuits = circuits[circuits["categoria"] == circuit_category]
        with left:
            st.subheader("Circuitos")
            st.caption(
                "Interações contam gates de dois qubits; grau conta vizinhos "
                "distintos; pressão de profundidade resume dependências seriais."
            )
            st.dataframe(
                filtered_circuits[
                    [
                        "grafo",
                        "categoria",
                        "vertices",
                        "interacoes_dois_qubits",
                        "arestas_nao_direcionadas",
                        "densidade_nao_direcionada",
                        "grau_medio",
                        "profundidade_dependencia",
                        "pressao_profundidade",
                        "grau_maximo_qubit",
                        "interacoes_maximo_qubit",
                    ]
                ].rename(
                    columns={
                        "grafo": "Circuito",
                        "categoria": "Família",
                        "vertices": "Qubits",
                        "interacoes_dois_qubits": "Gates de 2 qubits",
                        "arestas_nao_direcionadas": "Pares conectados",
                        "densidade_nao_direcionada": "Densidade de interação",
                        "grau_medio": "Grau médio",
                        "profundidade_dependencia": "Profundidade",
                        "pressao_profundidade": "Pressão de profundidade",
                        "grau_maximo_qubit": "Maior grau por qubit",
                        "interacoes_maximo_qubit": "Máximo de interações/qubit",
                    }
                ),
                width="stretch",
                hide_index=True,
            )
        filtered_topologies = topologies
        if topology_category != "Todas":
            filtered_topologies = topologies[
                topologies["categoria"] == topology_category
            ]
        with right:
            st.subheader("Topologias")
            st.caption(
                "Erro e distância são médias do melhor caminho entre qubits; "
                "densidade e graus descrevem a conectividade física."
            )
            topology_table = filtered_topologies[
                [
                    "grafo",
                    "categoria",
                    "vertices",
                    "arcos_direcionados",
                    "arestas_nao_direcionadas",
                    "densidade_direcionada",
                    "densidade_nao_direcionada",
                    "grau_medio_entrada",
                    "grau_medio_saida",
                    "erro_adjacente_global",
                    "distancia_media_maxima",
                    "erro_caminho_medio_maximo",
                    "grau_maximo_fisico",
                    "erro_adjacente_maximo",
                ]
            ].copy()
            for column in (
                "erro_adjacente_global",
                "erro_caminho_medio_maximo",
                "erro_adjacente_maximo",
            ):
                topology_table[column] *= 100
            st.dataframe(
                topology_table.rename(
                    columns={
                        "grafo": "Topologia",
                        "categoria": "Arquitetura",
                        "vertices": "Qubits físicos",
                        "arcos_direcionados": "Arcos direcionados",
                        "arestas_nao_direcionadas": "Links físicos",
                        "densidade_direcionada": "Densidade direcionada",
                        "densidade_nao_direcionada": "Densidade de links",
                        "grau_medio_entrada": "Grau médio de entrada",
                        "grau_medio_saida": "Grau médio de saída",
                        "erro_adjacente_global": "Erro médio dos links (%)",
                        "distancia_media_maxima": "Maior distância média",
                        "erro_caminho_medio_maximo": (
                            "Maior erro médio de caminho (%)"
                        ),
                        "grau_maximo_fisico": "Maior grau físico",
                        "erro_adjacente_maximo": "Maior erro médio de link (%)",
                    }
                ),
                width="stretch",
                hide_index=True,
            )

with tab_case:
    st.header("Caso selecionado: circuito, hardware e mapeamentos")
    controls_left, controls_right = st.columns(2)

    circuit_categories = sorted(circuits["categoria"].dropna().unique())
    _reset_stale_selection("case_circuit_category", circuit_categories)
    with controls_left:
        selected_circuit_category = st.selectbox(
            "Categoria do circuito",
            circuit_categories,
            index=(
                circuit_categories.index("modular_adder")
                if "modular_adder" in circuit_categories
                else 0
            ),
            key="case_circuit_category",
        )
        category_circuits = circuits[
            circuits["categoria"] == selected_circuit_category
        ].sort_values(["vertices", "grafo"])
        available_circuits = category_circuits["grafo"].tolist()
        circuit_key = f"case_circuit_{selected_circuit_category}"
        _reset_stale_selection(circuit_key, available_circuits)
        benchmarked_circuits = (
            set(benchmarks["circuit"].dropna())
            if not benchmarks.empty
            else set()
        )
        preferred_circuit = (
            "modular_adder_6qubits"
            if "modular_adder_6qubits" in available_circuits
            else next(
                (
                    circuit
                    for circuit in available_circuits
                    if circuit in benchmarked_circuits
                ),
                available_circuits[0],
            )
        )
        selected_circuit = st.selectbox(
            "Circuito",
            available_circuits,
            index=available_circuits.index(preferred_circuit),
            key=circuit_key,
        )

    circuit_row = circuits[circuits["grafo"] == selected_circuit].iloc[0]
    logical_qubits = int(circuit_row["vertices"])
    compatible_topologies = topologies[
        topologies["vertices"] >= logical_qubits
    ]
    architecture_categories = sorted(
        compatible_topologies["categoria"].dropna().unique()
    )
    _reset_stale_selection(
        "case_topology_category",
        architecture_categories,
    )
    with controls_right:
        selected_topology_category = st.selectbox(
            "Categoria da topologia",
            architecture_categories,
            index=(
                architecture_categories.index("line")
                if "line" in architecture_categories
                else 0
            ),
            key="case_topology_category",
        )
        category_topologies = compatible_topologies[
            compatible_topologies["categoria"] == selected_topology_category
        ].sort_values(["vertices", "grafo"])
        default_topology = f"line_{logical_qubits}qubits"
        topology_options = category_topologies["grafo"].tolist()
        topology_key = (
            f"case_topology_{selected_topology_category}_{logical_qubits}"
        )
        _reset_stale_selection(topology_key, topology_options)
        selected_topology = st.selectbox(
            "Topologia (qubits físicos)",
            topology_options,
            index=(
                topology_options.index(default_topology)
                if default_topology in topology_options
                else 0
            ),
            key=topology_key,
        )

    circuit_path = (
        ROOT
        / "datasets"
        / "interaction_order"
        / "algorithms"
        / selected_circuit_category
        / f"{selected_circuit}_ordered_interactions.csv"
    )
    topology_path = (
        ROOT
        / "datasets"
        / "topologies"
        / selected_topology_category
        / f"{selected_topology}_weighted_edges.csv"
    )
    graph_details = _load_graph_details(
        str(circuit_path),
        circuit_path.stat().st_mtime,
        str(topology_path),
        topology_path.stat().st_mtime,
    )
    _show_graph_metrics(graph_details)

    st.subheader("Algoritmos para este caso")
    st.caption(
        "Os três métodos principais ficam selecionados por padrão. "
        "Ative busca exata para incluí-la nos casos pequenos."
    )
    selected_methods = _select_algorithms(
        sorted(benchmarks["algorithm"].dropna().unique())
        if not benchmarks.empty
        else [],
        "case_method",
    )
    st.caption(
        f"Circuito: {logical_qubits} qubits, "
        f"{int(circuit_row['arestas_nao_direcionadas'])} pares conectados, "
        f"{circuit_row['densidade_nao_direcionada']:.3f} de densidade. "
        "Topologias incompatíveis (menos qubits físicos que lógicos) são ocultadas."
    )

    if st.button("Gerar grafos para este caso"):
        with st.spinner("Atualizando os grafos do circuito e da topologia..."):
            generate(
                ROOT / "datasets",
                OUTPUT,
                selected_circuit,
                selected_topology,
            )
        st.session_state["generated_case"] = (
            selected_circuit,
            selected_topology,
        )
        st.success("Grafo de interações e topologia atualizados.")

    generated_case = st.session_state.get("generated_case")
    if generated_case == (selected_circuit, selected_topology):
        _show_figures(("05_grafo_interacoes.png", "06_grafo_topologia.png"))
    else:
        st.info(
            "Clique em “Gerar grafos para este caso” para produzir as "
            "visualizações correspondentes à seleção."
        )

    case_results = benchmarks
    if not benchmarks.empty:
        case_results = benchmarks[
            (benchmarks["circuit"] == selected_circuit)
            & (benchmarks["topology"] == selected_topology)
            & (benchmarks["algorithm"].isin(selected_methods))
        ]
        st.subheader("Resultados e erro estimado por algoritmo")
        st.caption(
            "Erro estimado pelo modelo de taxas de erro dos links do dataset "
            "(sintético), não uma medição de hardware real. O SABRE é avaliado "
            "sobre as operações de dois qubits roteadas; cada SWAP conta como "
            "três gates de dois qubits."
        )
        _show_mapping_results(case_results)

with tab_comparison:
    st.header("Comparação por categoria e condição")
    st.caption(
        "Resultados pré-computados para GHZ, adição modular, QFT e QAOA com 4, "
        "6, 8, 10 e 12 qubits, mapeados em topologias lineares, em anel e "
        "completas, grids, heavy-hex e heavy-square."
    )
    if benchmarks.empty:
        st.info("Execute `python -m analysis.benchmark_mappers` para gerar a matriz.")
    else:
        filter_circuit, filter_topology, filter_size, filter_case = st.columns(4)
        circuit_categories = sorted(
            benchmarks["circuit_category"].dropna().unique()
        )
        topology_categories = sorted(
            benchmarks["topology_category"].dropna().unique()
        )
        qubit_counts = sorted(benchmarks["logical_qubits"].dropna().unique())
        algorithms = sorted(benchmarks["algorithm"].dropna().unique())
        with filter_circuit:
            selected_circuit_categories = st.multiselect(
                "Categorias de circuitos",
                circuit_categories,
                default=circuit_categories,
            )
        with filter_topology:
            selected_topology_categories = st.multiselect(
                "Categorias de topologias",
                topology_categories,
                default=topology_categories,
            )
        with filter_size:
            selected_qubit_counts = st.multiselect(
                "Qubits lógicos",
                qubit_counts,
                default=qubit_counts,
            )
        topology_options = sorted(benchmarks["topology"].dropna().unique())
        with filter_case:
            selected_topology = st.selectbox(
                "Topologia específica (opcional)",
                ["Todas"] + topology_options,
                help=(
                    "Refine a comparação para um dispositivo; por padrão, "
                    "inclui todas as topologias selecionadas acima."
                ),
                key="comparison_specific_topology",
            )
        st.markdown("**Algoritmos para comparar**")
        st.caption(
            "Selecione os métodos desejados; busca exata é uma referência "
            "opcional e só existe para casos pequenos."
        )
        selected_algorithm_categories = _select_algorithms(
            algorithms,
            "comparison_method",
        )

        filtered_results = benchmarks[
            benchmarks["circuit_category"].isin(selected_circuit_categories)
            & benchmarks["topology_category"].isin(selected_topology_categories)
            & benchmarks["logical_qubits"].isin(selected_qubit_counts)
            & (
                benchmarks["topology"].eq(selected_topology)
                | (selected_topology == "Todas")
            )
            & benchmarks["algorithm"].isin(selected_algorithm_categories)
        ]
        if filtered_results.empty:
            st.warning("Nenhum resultado corresponde aos filtros selecionados.")
        else:
            summary = filtered_results.groupby(
                [
                    "circuit_category",
                    "circuit",
                    "topology_category",
                    "topology",
                    "algorithm",
                ],
                as_index=False,
            ).agg(
                execucoes=("run", "count"),
                tempo_mediano_s=("elapsed_seconds", "median"),
                tempo_medio_s=("elapsed_seconds", "mean"),
                swaps_medianos=("swap_count", "median"),
                erro_estimado_mediano=("expected_error_rate", "median"),
            )
            summary["erro_estimado_mediano_%"] = (
                summary.pop("erro_estimado_mediano") * 100
            )

            scalable_results = filtered_results[
                filtered_results["algorithm"] != "Busca exata"
            ]
            architecture_tab, scaling_tab, distribution_tab, detail_tab, info_tab = (
                st.tabs(
                    [
                        "Por topologia",
                        "Por qubits lógicos",
                        "Por execução",
                        "Dados detalhados",
                        "Como interpretar",
                    ]
                )
            )
            with architecture_tab:
                st.subheader("Comparação agregada por topologia")
                st.caption(
                    "Cada barra resume os cenários filtrados de cada arquitetura. "
                    "As métricas mostram medianas; valores menores são melhores."
                )
                if scalable_results.empty:
                    st.info(
                        "Selecione SABRE, fluxo min-cost ou multi-start para "
                        "comparar os métodos de roteamento. Busca exata é uma "
                        "referência apenas para casos pequenos."
                    )
                else:
                    _show_algorithm_charts(scalable_results, by_topology=True)

            with scaling_tab:
                st.subheader("Comportamento por tamanho do circuito")
                if scalable_results.empty:
                    st.info(
                        "Selecione um algoritmo de roteamento para ver a escala."
                    )
                else:
                    scaling = scalable_results.groupby(
                        ["logical_qubits", "algorithm"],
                        as_index=False,
                    ).agg(
                        swaps_medianos=("swap_count", "median"),
                        erro_estimado_mediano=(
                            "expected_error_rate",
                            "median",
                        ),
                        tempo_mediano_s=("elapsed_seconds", "median"),
                    )
                    scaling["erro_estimado_mediano_%"] = (
                        scaling.pop("erro_estimado_mediano") * 100
                    )
                    if scaling["logical_qubits"].nunique() > 1:
                        scaling["metodo"] = scaling["algorithm"].map(
                            {
                                "Heurística multi-start": "Multi-start",
                                "Fluxo min-cost + hill climb": "Fluxo min-cost",
                                "Qiskit SABRE": "SABRE",
                            }
                        )
                        scaling = scaling.rename(
                            columns={
                                "logical_qubits": "Qubits lógicos",
                                "swaps_medianos": "SWAPs medianos",
                                "erro_estimado_mediano_%": (
                                    "Erro estimado mediano (%)"
                                ),
                                "tempo_mediano_s": "Tempo mediano (s)",
                            }
                        )
                        scaling_tabs = st.tabs(
                            ["SWAPs", "Erro estimado", "Tempo"]
                        )
                        scaling_specs = (
                            "SWAPs medianos",
                            "Erro estimado mediano (%)",
                            "Tempo mediano (s)",
                        )
                        for tab, label in zip(scaling_tabs, scaling_specs):
                            with tab:
                                st.caption(
                                    f"{label} por número de qubits lógicos."
                                )
                                st.line_chart(
                                    scaling,
                                    x="Qubits lógicos",
                                    y=label,
                                    color="metodo",
                                    height=360,
                                )
                    else:
                        st.info(
                            "Selecione mais de um tamanho de circuito para "
                            "comparar as curvas de escala."
                        )

            with distribution_tab:
                st.subheader("Tempo × erro estimado por execução")
                st.caption(
                    "Cada ponto representa uma execução; a cor indica a "
                    "arquitetura e o tamanho representa a quantidade de SWAPs."
                )
                selected_algorithm_names = set(
                    filtered_results["algorithm"].dropna().unique()
                )
                scatter_algorithms = [
                    (algorithm, label)
                    for algorithm, label, _ in ALGORITHM_OPTIONS
                    if algorithm in selected_algorithm_names
                ]
                scatter_tabs = st.tabs(
                    [label for _, label in scatter_algorithms]
                )
                for tab, (algorithm, label) in zip(
                    scatter_tabs,
                    scatter_algorithms,
                ):
                    with tab:
                        algorithm_results = filtered_results[
                            filtered_results["algorithm"] == algorithm
                        ]
                        metric_columns = st.columns(3)
                        metric_columns[0].metric(
                            "SWAPs medianos",
                            f"{algorithm_results['swap_count'].median():.1f}",
                        )
                        metric_columns[1].metric(
                            "Erro estimado mediano",
                            f"{algorithm_results['expected_error_rate'].median() * 100:.3f}%",
                        )
                        metric_columns[2].metric(
                            "Tempo mediano",
                            f"{algorithm_results['elapsed_seconds'].median():.4f} s",
                        )
                        chart_data = algorithm_results.assign(
                            erro_estimado_percentual=(
                                algorithm_results["expected_error_rate"] * 100
                            )
                        ).rename(
                            columns={
                                "elapsed_seconds": "Tempo (s)",
                                "erro_estimado_percentual": "Erro estimado (%)",
                                "swap_count": "SWAPs",
                                "topology_category": "Topologia",
                            }
                        )
                        st.scatter_chart(
                            chart_data,
                            x="Tempo (s)",
                            y="Erro estimado (%)",
                            color="Topologia",
                            size="SWAPs",
                            height=440,
                        )

            with detail_tab:
                st.subheader("Resumo detalhado por circuito e topologia")
                st.dataframe(summary, width="stretch", hide_index=True)

            with info_tab:
                st.subheader("O que é medido e o que é referência de mercado")
                st.markdown(
                    """
                    - **Busca exata**: enumera colocações injetivas e roteia cada
                      uma; é a referência ótima para o objetivo do roteador
                      local, com custo fatorial. No benchmark padrão, fica
                      restrita aos casos de até quatro qubits.
                    - **Heurística multi-start**: combina inícios aleatórios,
                      por grau e por par de interação, refinados por hill
                      climbing; não garante ótimo.
                    - **Fluxo min-cost + hill climb**: encontra uma atribuição
                      guiada por grau, distância e erros, depois otimiza o custo
                      roteado.
                    - **Qiskit SABRE**: baseline de mercado medida nesta
                      matriz. Usa layout e roteamento SABRE com seeds fixas;
                      veja a documentação do
                      [SabreLayout](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.transpiler.passes.SabreLayout).
                    - **VF2Layout**: referência de layout usada por
                      transpilers; procura embedding sem SWAP quando existe
                      subgrafo compatível. Não é incluída como roteador quando
                      não há embedding perfeito. Consulte
                      [VF2Layout](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.transpiler.passes.VF2Layout).

                    Para o baseline SABRE, os CSVs contêm apenas interações de
                    dois qubits; os gates são representados como `cx`,
                    mantendo os pares e a ordem. Portanto, os resultados
                    comparam as estratégias de mapeamento sobre a mesma carga
                    estrutural, não uma compilação semântica integral do QASM.
                    """
                )
