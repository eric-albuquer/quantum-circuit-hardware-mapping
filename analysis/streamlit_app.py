from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

# [IA] Claude Code (Claude Opus 5.5) – importação da página de apresentação
from analysis.presentation import (
    show_comparative_summary,
    show_eda,
    show_presentation,
)
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
# [IA] Claude Code (Claude Opus 5.5) – constantes compartilhadas de nomes curtos e métricas dos gráficos
SHORT_NAMES = {
    algorithm: label for algorithm, label, _ in ALGORITHM_OPTIONS
}
CHART_METRICS = ("SWAPs medianos", "Erro estimado mediano (%)", "Tempo mediano (s)")
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


# [IA] Claude Code (Claude Opus 5.5) – padronização dos títulos de seção
def _section(title: str) -> None:
    """Abre uma seção com a mesma hierarquia visual da tela inicial."""
    st.divider()
    st.subheader(f":blue[{title}]")


# [IA] Claude Code (Claude Opus 5.5) – nome curto dos algoritmos
def _short_name(algorithm: str) -> str:
    return SHORT_NAMES.get(algorithm, algorithm)


# [IA] Claude Code (Claude Opus 5.5) – reorganização visual das métricas dos grafos
def _show_graph_metrics(details: dict[str, object]) -> None:
    circuit = details["circuit_summary"]
    topology = details["topology_summary"]

    circuit_column, topology_column = st.columns(2, gap="large")
    with circuit_column:
        st.markdown("#### Circuito lógico")
        first_row = st.columns(3)
        first_row[0].metric("Qubits", circuit["qubits"])
        first_row[1].metric("Gates de 2 qubits", circuit["interactions"])
        first_row[2].metric("Pares distintos", circuit["interaction_pairs"])
        second_row = st.columns(3)
        second_row[0].metric("Profundidade", circuit["dependency_depth"])
        second_row[1].metric("Maior grau", circuit["max_qubit_degree"])
        second_row[2].metric(
            "Maior interações/qubit",
            circuit["max_qubit_interactions"],
        )
        st.caption(
            f"Pressão de profundidade: {circuit['depth_pressure']:.3f} "
            "(0 = paralelizável; 1 = totalmente serial)."
        )

    with topology_column:
        st.markdown("#### Topologia física")
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
            f"Maior distância média: {topology['max_mean_distance']:.2f} saltos. "
            "Maior erro médio de caminho: "
            f"{topology['max_mean_path_error'] * 100:.3f}%."
        )

    with st.expander("Detalhes por qubit e matrizes de caminhos"):
        logical_tab, physical_tab, matrix_tab = st.tabs(
            ["Qubits lógicos", "Qubits físicos", "Matrizes"]
        )
        with logical_tab:
            st.dataframe(
                details["logical_qubits"],
                width="stretch",
                hide_index=True,
            )
            degree_column, interactions_column = st.columns(2)
            with degree_column:
                st.bar_chart(
                    details["logical_qubits"],
                    x="Qubit lógico",
                    y="Grau",
                    height=280,
                )
            with interactions_column:
                st.bar_chart(
                    details["logical_qubits"],
                    x="Qubit lógico",
                    y="Interações de 2 qubits",
                    height=280,
                )
            st.markdown("#### Pares de interação")
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
                "Grau",
                "Erro adjacente médio (%)",
                "Distância média",
                "Erro médio dos caminhos (%)",
            )
            metric_tabs = st.tabs(list(physical_metrics))
            for tab, column in zip(metric_tabs, physical_metrics):
                with tab:
                    st.bar_chart(
                        details["physical_qubits"],
                        x="Qubit físico",
                        y=column,
                        height=300,
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


# [IA] Claude Code (Claude Opus 5.5) – exibição das figuras com legendas legíveis
def _show_figures(names: tuple[str, ...]) -> None:
    columns = st.columns(len(names))
    for column, (filename, caption) in zip(columns, names):
        image_path = OUTPUT / filename
        if image_path.is_file():
            column.image(str(image_path), caption=caption, width="stretch")
        else:
            column.info("Visualização indisponível. Gere os grafos novamente.")


# [IA] Claude Code (Claude Opus 5.5) – tabela de resumo com nomes de coluna em português
def _summary_by_mapper(results: pd.DataFrame) -> pd.DataFrame:
    summary = results.groupby("algorithm", as_index=False).agg(
        runs=("run", "count"),
        tempo_mediano_s=("elapsed_seconds", "median"),
        swaps_medianos=("swap_count", "median"),
        erro_estimado_mediano=("expected_error_rate", "median"),
    )
    summary["erro_estimado_mediano"] *= 100
    return summary.rename(
        columns={
            "algorithm": "Algoritmo",
            "runs": "Execuções",
            "swaps_medianos": "SWAPs medianos",
            "tempo_mediano_s": "Tempo mediano (s)",
            "erro_estimado_mediano": "Erro estimado mediano (%)",
        }
    )[
        [
            "Algoritmo",
            "Execuções",
            "SWAPs medianos",
            "Erro estimado mediano (%)",
            "Tempo mediano (s)",
        ]
    ]


# [IA] Claude Code (Claude Opus 5.5) – gráficos padronizados de SWAPs, erro e tempo
def _show_metric_charts(
    data: pd.DataFrame,
    x_axis: str,
    chart: str = "bar",
) -> None:
    """Mostra SWAPs, erro e tempo em abas com o mesmo formato."""
    chart_tabs = st.tabs(list(CHART_METRICS))
    for tab, label in zip(chart_tabs, CHART_METRICS):
        with tab:
            if chart == "line":
                st.line_chart(data, x=x_axis, y=label, color="Método", height=360)
            else:
                st.bar_chart(
                    data,
                    x=x_axis,
                    y=label,
                    color="Método",
                    stack=False,
                    height=360,
                )


# [IA] Claude Code (Claude Opus 5.5) – cálculo das medianas para os gráficos
def _median_metrics(results: pd.DataFrame, grouping: list[str]) -> pd.DataFrame:
    summary = results.groupby(grouping, as_index=False).agg(
        swaps=("swap_count", "median"),
        erro=("expected_error_rate", "median"),
        tempo=("elapsed_seconds", "median"),
    )
    summary["erro"] *= 100
    summary["Método"] = summary["algorithm"].map(_short_name)
    return summary.rename(
        columns={
            "topology_category": "Topologia",
            "logical_qubits": "Qubits lógicos",
            "swaps": CHART_METRICS[0],
            "erro": CHART_METRICS[1],
            "tempo": CHART_METRICS[2],
        }
    )


# [IA] Claude Code (Claude Opus 5.5) – tabela de execuções com nomes de coluna em português
def _runs_table(results: pd.DataFrame, include_details: bool = False) -> pd.DataFrame:
    table = results.assign(
        erro_percentual=results["expected_error_rate"] * 100,
        mapeamento_inicial=results["initial_mapping"].map(_mapping_label),
        mapeamento_final=results["final_mapping"].map(_mapping_label),
    )
    columns = {
        "algorithm": "Algoritmo",
        "run": "Execução",
        "elapsed_seconds": "Tempo (s)",
        "swap_count": "SWAPs",
        "erro_percentual": "Erro estimado (%)",
        "mapeamento_inicial": "Mapeamento inicial",
        "mapeamento_final": "Mapeamento final",
    }
    if include_details:
        columns = {
            "algorithm": "Algoritmo",
            "run": "Execução",
            "seed": "Seed",
            **{key: value for key, value in columns.items() if key not in {"algorithm", "run"}},
        }
    return table[list(columns)].rename(columns=columns)


# [IA] Claude Code (Claude Opus 5.5) – reorganização dos resultados por algoritmo
def _show_mapping_results(results: pd.DataFrame) -> None:
    if results.empty:
        st.info(
            "Não há resultados de benchmark para esta combinação de circuito, "
            "topologia e algoritmos."
        )
        return

    st.markdown("#### Resumo por algoritmo")
    st.dataframe(_summary_by_mapper(results), width="stretch", hide_index=True)

    st.markdown("#### Comparação visual")
    st.caption("Medianas das execuções; valores menores são melhores.")
    _show_metric_charts(_median_metrics(results, ["algorithm"]), "Método")

    st.markdown("#### Melhor mapeamento por algoritmo")
    st.caption(
        "Melhor execução por erro estimado, SWAPs e tempo, nessa ordem. "
        "L = qubit lógico; P = qubit físico."
    )
    best_runs = (
        results.sort_values(["expected_error_rate", "swap_count", "elapsed_seconds"])
        .groupby("algorithm", as_index=False)
        .first()
    )
    st.dataframe(_runs_table(best_runs), width="stretch", hide_index=True)
    with st.expander("Todas as execuções"):
        st.dataframe(
            _runs_table(results, include_details=True),
            width="stretch",
            hide_index=True,
        )


# [IA] Claude Code (Claude Opus 5.5) – título do app em azul
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

# [IA] Claude Code (Claude Opus 5.5) – aba de apresentação e tabelas de dados recolhidas
tab_overview, tab_eda, tab_case, tab_comparison = st.tabs(
    ["Apresentação", "EDA", "Caso selecionado", "Comparação de algoritmos"]
)

with tab_overview:
    show_presentation(circuits, topologies, benchmarks)

with tab_eda:
    show_eda(circuits, topologies, benchmarks)
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
            st.markdown("#### Circuitos")
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
            st.markdown("#### Topologias")
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

# [IA] Claude Code (Claude Opus 5.5) – refatoração visual da tela de caso selecionado
with tab_case:
    st.header(":blue[Caso selecionado]")
    st.caption(
        "Escolha um circuito e uma topologia para analisar os grafos e comparar "
        "os mapeamentos encontrados por cada algoritmo."
    )

    controls = st.columns(4)
    circuit_categories = sorted(circuits["categoria"].dropna().unique())
    _reset_stale_selection("case_circuit_category", circuit_categories)
    with controls[0]:
        selected_circuit_category = st.selectbox(
            "Família do circuito",
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
        set(benchmarks["circuit"].dropna()) if not benchmarks.empty else set()
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
    with controls[1]:
        selected_circuit = st.selectbox(
            "Circuito",
            available_circuits,
            index=available_circuits.index(preferred_circuit),
            key=circuit_key,
        )

    circuit_row = circuits[circuits["grafo"] == selected_circuit].iloc[0]
    logical_qubits = int(circuit_row["vertices"])
    compatible_topologies = topologies[topologies["vertices"] >= logical_qubits]
    architecture_categories = sorted(
        compatible_topologies["categoria"].dropna().unique()
    )
    _reset_stale_selection("case_topology_category", architecture_categories)
    with controls[2]:
        selected_topology_category = st.selectbox(
            "Arquitetura",
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
    topology_key = f"case_topology_{selected_topology_category}_{logical_qubits}"
    _reset_stale_selection(topology_key, topology_options)
    with controls[3]:
        selected_topology = st.selectbox(
            "Topologia",
            topology_options,
            index=(
                topology_options.index(default_topology)
                if default_topology in topology_options
                else 0
            ),
            key=topology_key,
        )
    st.caption(
        "Só aparecem topologias com pelo menos tantos qubits físicos quanto os "
        "qubits lógicos do circuito."
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

    _section("Métricas dos grafos")
    _show_graph_metrics(graph_details)

    _section("Visualização dos grafos")
    if st.button("Gerar grafos para este caso"):
        with st.spinner("Gerando os grafos do circuito e da topologia..."):
            generate(
                ROOT / "datasets",
                OUTPUT,
                selected_circuit,
                selected_topology,
            )
        st.session_state["generated_case"] = (selected_circuit, selected_topology)

    if st.session_state.get("generated_case") == (
        selected_circuit,
        selected_topology,
    ):
        _show_figures(
            (
                ("05_grafo_interacoes.png", "Grafo de interações do circuito"),
                ("06_grafo_topologia.png", "Grafo de acoplamento do hardware"),
            )
        )
    else:
        st.caption(
            "Clique no botão para desenhar o grafo de interações e a topologia "
            "do caso selecionado."
        )

    _section("Resultados dos algoritmos")
    st.caption(
        "Erro estimado pelo modelo de taxas sintéticas dos links, não uma "
        "medição em hardware real. Cada SWAP conta como três portas de dois "
        "qubits."
    )
    selected_methods = _select_algorithms(
        sorted(benchmarks["algorithm"].dropna().unique())
        if not benchmarks.empty
        else [],
        "case_method",
    )
    case_results = benchmarks
    if not benchmarks.empty:
        case_results = benchmarks[
            (benchmarks["circuit"] == selected_circuit)
            & (benchmarks["topology"] == selected_topology)
            & (benchmarks["algorithm"].isin(selected_methods))
        ]
    _show_mapping_results(case_results)

# [IA] Claude Code (Claude Opus 5.5) – refatoração visual da tela de comparação de algoritmos
with tab_comparison:
    st.header(":blue[Comparação de algoritmos]")
    st.caption(
        "Resultados pré-computados para GHZ, adição modular, QFT e QAOA com 4 a "
        "12 qubits, em topologias linear, anel, completa, grid, heavy-hex e "
        "heavy-square."
    )
    show_comparative_summary()
    if benchmarks.empty:
        st.info("Ainda não há resultados de benchmark para comparar.")
    else:
        _section("Filtros")
        filter_circuit, filter_topology, filter_size, filter_case = st.columns(4)
        circuit_categories = sorted(benchmarks["circuit_category"].dropna().unique())
        topology_categories = sorted(
            benchmarks["topology_category"].dropna().unique()
        )
        qubit_counts = sorted(benchmarks["logical_qubits"].dropna().unique())
        algorithms = sorted(benchmarks["algorithm"].dropna().unique())
        with filter_circuit:
            selected_circuit_categories = st.multiselect(
                "Famílias de circuitos",
                circuit_categories,
                default=circuit_categories,
            )
        with filter_topology:
            selected_topology_categories = st.multiselect(
                "Arquiteturas",
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
                "Topologia específica",
                ["Todas"] + topology_options,
                help="Opcional: restringe a comparação a um único dispositivo.",
                key="comparison_specific_topology",
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

        _section("Resultados")
        if filtered_results.empty:
            st.warning("Nenhum resultado corresponde aos filtros selecionados.")
        else:
            st.caption(
                "Medianas das execuções; valores menores são melhores. O SABRE "
                "recebe as mesmas interações de dois qubits, como `cx` e na "
                "mesma ordem. A busca exata só existe para casos pequenos e "
                "fica fora das visões por topologia e por tamanho."
            )
            scalable_results = filtered_results[
                filtered_results["algorithm"] != "Busca exata"
            ]
            architecture_tab, scaling_tab, distribution_tab, detail_tab = st.tabs(
                [
                    "Por topologia",
                    "Por qubits lógicos",
                    "Por execução",
                    "Dados detalhados",
                ]
            )
            with architecture_tab:
                if scalable_results.empty:
                    st.info(
                        "Selecione multi-start, fluxo min-cost ou SABRE para "
                        "comparar por topologia."
                    )
                else:
                    _show_metric_charts(
                        _median_metrics(
                            scalable_results,
                            ["topology_category", "algorithm"],
                        ),
                        "Topologia",
                    )

            with scaling_tab:
                if scalable_results.empty:
                    st.info(
                        "Selecione multi-start, fluxo min-cost ou SABRE para "
                        "ver a escala."
                    )
                elif scalable_results["logical_qubits"].nunique() < 2:
                    st.info("Selecione mais de um tamanho de circuito.")
                else:
                    _show_metric_charts(
                        _median_metrics(
                            scalable_results,
                            ["logical_qubits", "algorithm"],
                        ),
                        "Qubits lógicos",
                        chart="line",
                    )

            with distribution_tab:
                st.caption(
                    "Cada ponto é uma execução: a cor indica a arquitetura e o "
                    "tamanho, a quantidade de SWAPs."
                )
                selected_algorithm_names = set(
                    filtered_results["algorithm"].dropna().unique()
                )
                scatter_algorithms = [
                    (algorithm, label)
                    for algorithm, label, _ in ALGORITHM_OPTIONS
                    if algorithm in selected_algorithm_names
                ]
                scatter_tabs = st.tabs([label for _, label in scatter_algorithms])
                for tab, (algorithm, _) in zip(scatter_tabs, scatter_algorithms):
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
                            erro_percentual=(
                                algorithm_results["expected_error_rate"] * 100
                            )
                        ).rename(
                            columns={
                                "elapsed_seconds": "Tempo (s)",
                                "erro_percentual": "Erro estimado (%)",
                                "swap_count": "SWAPs",
                                "topology_category": "Arquitetura",
                            }
                        )
                        st.scatter_chart(
                            chart_data,
                            x="Tempo (s)",
                            y="Erro estimado (%)",
                            color="Arquitetura",
                            size="SWAPs",
                            height=440,
                        )

            with detail_tab:
                detail = filtered_results.groupby(
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
                    swaps=("swap_count", "median"),
                    erro=("expected_error_rate", "median"),
                    tempo=("elapsed_seconds", "median"),
                )
                detail["erro"] *= 100
                st.dataframe(
                    detail.rename(
                        columns={
                            "circuit_category": "Família",
                            "circuit": "Circuito",
                            "topology_category": "Arquitetura",
                            "topology": "Topologia",
                            "algorithm": "Algoritmo",
                            "execucoes": "Execuções",
                            "swaps": "SWAPs medianos",
                            "erro": "Erro estimado mediano (%)",
                            "tempo": "Tempo mediano (s)",
                        }
                    ),
                    width="stretch",
                    hide_index=True,
                )
