from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# [IA] Claude Code (Claude Opus 5.5) – importação da página de apresentação
from analysis.labels import dataset_label
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
# [IA] Claude Code (Claude Sonnet 5.5) – limite de tamanho para execução ao vivo
LIVE_WORK_LIMIT = 500  # qubits lógicos × qubits físicos; acima disso o multi-start passa de ~12 s por execução
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


# [IA] Claude Code (Claude Sonnet 5.5) – checkboxes só dos algoritmos disponíveis, sem coluna vazia à esquerda
def _select_algorithms(available: list[str], key_prefix: str) -> list[str]:
    options = [
        (index, option)
        for index, option in enumerate(ALGORITHM_OPTIONS)
        if option[0] in available
    ]
    if not options:
        return []
    columns = st.columns(len(options))
    selected = []
    for column, (index, (algorithm, label, help_text)) in zip(columns, options):
        if column.checkbox(
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


def _labelled(table: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    """Cópia da tabela com nomes de datasets legíveis nas colunas indicadas."""
    table = table.copy()
    for column in columns:
        if column in table:
            table[column] = table[column].map(dataset_label)
    return table


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
    with circuit_column.container(border=True):
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

    with topology_column.container(border=True):
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
            degree_column, interactions_column = st.columns(2, gap="large")
            with degree_column:
                st.markdown("**Grau (vizinhos distintos)**")
                _bar_chart(
                    details["logical_qubits"],
                    x="Qubit lógico",
                    y="Grau",
                    height=220,
                    bar_color=LIGHT_BLUE,
                    value_axis=True,
                    axis_color=QUBIT_AXIS_GRAY,
                    axis_line_color=QUBIT_AXIS_LINE_GRAY,
                )
            with interactions_column:
                st.markdown("**Interações de 2 qubits**")
                _bar_chart(
                    details["logical_qubits"],
                    x="Qubit lógico",
                    y="Interações de 2 qubits",
                    height=220,
                    bar_color=DARK_BLUE,
                    value_axis=True,
                    axis_color=QUBIT_AXIS_GRAY,
                    axis_line_color=QUBIT_AXIS_LINE_GRAY,
                )
            st.markdown("#### Pares de interação")
            st.dataframe(
                details["interaction_pairs"],
                width="stretch",
                hide_index=True,
            )
        with physical_tab:
            physical_metrics = (
                "Grau",
                "Erro adjacente médio (%)",
                "Distância média",
                "Erro médio dos caminhos (%)",
            )
            chart_column, _ = st.columns(2, gap="large")  # mesma largura de antes
            with chart_column:
                metric_tabs = st.tabs(list(physical_metrics))
                for tab, column in zip(metric_tabs, physical_metrics):
                    with tab:
                        _bar_chart(
                            details["physical_qubits"],
                            x="Qubit físico",
                            y=column,
                            height=300,
                            bar_color=LIGHT_BLUE,
                            value_axis=True,
                            axis_color=QUBIT_AXIS_GRAY,
                            axis_line_color=QUBIT_AXIS_LINE_GRAY,
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


LIGHT_BLUE = "#8EC5F0"
QUBIT_AXIS_GRAY = "#6B7280"
QUBIT_AXIS_LINE_GRAY = "#9CA3AF"
DARK_BLUE = "#1D4E89"
SABRE_GRAY = "#9AA0A6"
METHOD_COLORS = {
    "Busca exata": "#F58518",
    "Multi-start": LIGHT_BLUE,
    "Fluxo min-cost": "#4C78A8",
    "Qiskit SABRE": SABRE_GRAY,
}
FALLBACK_COLOR = "#72B7B2"
# [IA] Claude Code (Claude Sonnet 5.5) – tradução dos nomes dos métodos para a legenda em inglês
ENGLISH_METHOD_LABELS = {
    "Busca exata": "Exact search",
    "Fluxo min-cost": "Min-cost flow",
}
ENGLISH_METHOD_LABEL_EXPR = (
    f"{json.dumps(ENGLISH_METHOD_LABELS)}[datum.label] || datum.label"
)
VALUE_LABEL_COLOR = "black"


def _method_color_scale(methods) -> alt.Scale:
    """Cor fixa por método: Multi-start em azul claro e SABRE em cinza."""
    domain = list(dict.fromkeys(methods))
    colors = [METHOD_COLORS.get(method, FALLBACK_COLOR) for method in domain]
    return alt.Scale(domain=domain, range=colors)


# [IA] Claude Code (Claude Sonnet 5.5) – gráfico de barras com valores sobre as barras e rótulos horizontais
MAX_LABELLED_BARS = 40  # acima disso os valores se sobrepõem e são omitidos (ficam no tooltip)


def _bar_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    height: int = 300,
    bar_gap: float = 0.1,
    bar_color: str | None = None,
    horizontal: bool = False,
    sort_by_value: bool = False,
    color_scale: alt.Scale | None = None,
    max_labelled: int = MAX_LABELLED_BARS,
    value_axis: bool = False,
    axis_color: str = VALUE_LABEL_COLOR,
    axis_line_color: str = "#374151",
    value_format: str = ".3~g",
    english_legend: bool = False,
) -> None:
    """Barras com o valor escrito na ponta de cada uma.

    ``x`` é a coluna de categorias e ``y`` a de valores. Não há eixo de valores
    nem grade, pois o número está na barra; o eixo de categorias mantém só os
    nomes, sem título, marcas nem linha.

    ``bar_gap`` é a fração de espaço entre as barras (maior = barras mais
    finas) e ``bar_color`` fixa a cor quando não há ``color``. Com ``color`` as
    barras ficam agrupadas, uma por categoria de cor. Com ``horizontal`` as
    categorias ficam no eixo vertical e as barras crescem para a direita. Com
    muitas barras os valores são omitidos para não se sobreporem; eles
    continuam no tooltip (o limite é ``max_labelled``). Com ``sort_by_value``
    as categorias ficam do maior para o menor valor. ``color_scale`` fixa as
    cores de cada valor de ``color``. Com ``value_axis`` o eixo dos valores
    aparece só com os números e as duas linhas de borda (esquerda e base), sem grade nem marcas.
    ``axis_color`` e ``axis_line_color`` colorem os números e as linhas dos eixos.
    """
    # [IA] Claude Code (Claude Sonnet 5.5) – nomes das categorias (grid, heavy-hex, linear, anel…) em preto
    category_axis = alt.Axis(
        labelAngle=0,
        labelOverlap="greedy",
        ticks=False,
        domain=value_axis,  # com eixo de valores, a linha de base também aparece
        domainColor=axis_line_color,
        labelColor=VALUE_LABEL_COLOR,  # nomes das categorias sempre em preto
    )
    # Ordem explícita (maior primeiro): a ordenação por canal do Altair ("-x")
    # não foi aplicada de forma confiável quando o gráfico tem camada de texto.
    category_order = (
        data.groupby(x, sort=False)[y].max().sort_values(ascending=False).index.tolist()
        if sort_by_value
        else None
    )
    category_scale = alt.Scale(paddingInner=bar_gap, paddingOuter=0.05)
    if value_axis:
        integer_values = bool((data[y] == data[y].round()).all())
        axis_options = {"tickMinStep": 1} if integer_values else {}
        value_axis_encoding = alt.Axis(
            title=None,
            grid=False,
            domain=True,
            domainColor=axis_line_color,
            ticks=False,
            labelColor=axis_color,
            **axis_options,
        )
    else:
        value_axis_encoding = None
    value_encoding_args = {
        "axis": value_axis_encoding,
        "scale": alt.Scale(domainMax=max(float(data[y].max()) * 1.18, 1e-12)),
    }
    category_channel, value_channel = ("y", "x") if horizontal else ("x", "y")
    offset_channel = "yOffset" if horizontal else "xOffset"
    category_class = alt.Y if horizontal else alt.X
    value_class = alt.X if horizontal else alt.Y
    offset_class = alt.YOffset if horizontal else alt.XOffset

    encodings: dict[str, object] = {
        category_channel: category_class(
            f"{x}:N", title=None, sort=category_order, axis=category_axis,
            scale=category_scale,
        ),
        value_channel: value_class(f"{y}:Q", **value_encoding_args),
        "tooltip": [x, y] + ([color] if color else []),
    }
    if color:
        if color_scale is None:
            color_scale = (
                _method_color_scale(data[color])
                if color == "Método"
                else alt.Undefined
            )
        # [IA] Claude Code (Claude Sonnet 5.5) – legenda de métodos à esquerda do gráfico de barras
        encodings["color"] = alt.Color(
            f"{color}:N",
            title=color,
            scale=color_scale,
            legend=(
                # [IA] Claude Code (Claude Sonnet 5.5) – legenda de métodos em inglês (título e nomes)
                alt.Legend(
                    orient="left",
                    title="Method",
                    labelExpr=ENGLISH_METHOD_LABEL_EXPR,
                )
                if english_legend
                else alt.Legend(orient="left")
            ),
        )
        # Só agrupa em subbarras quando a cor é diferente da categoria; se for a
        # mesma, uma barra por categoria ocupa a faixa toda e fica alinhada ao nome.
        if color != x:
            encodings[offset_channel] = offset_class(
                f"{color}:N", scale=alt.Scale(paddingInner=0.05)
            )
    mark_options = {"color": bar_color} if bar_color and not color else {}
    bars = alt.Chart(data).mark_bar(**mark_options).encode(**encodings)
    layers = [bars]
    if len(data) <= max_labelled:
        # [IA] Claude Code (Claude Sonnet 5.5) – valores sem negrito, centralizados sobre a ponta de cada barra
        if horizontal:
            text_mark = bars.mark_text(
                align="left", baseline="middle", dx=4, fontSize=11,
                color=VALUE_LABEL_COLOR,
            )
        else:
            text_mark = bars.mark_text(
                align="center", baseline="bottom", dy=-3, fontSize=11,
                color=VALUE_LABEL_COLOR,
            )
        # O texto herda a cor da barra; fixa a cor para os valores ficarem pretos.
        text_encodings: dict[str, object] = {
            "text": alt.Text(f"{y}:Q", format=value_format),
            "color": alt.value(VALUE_LABEL_COLOR),
        }
        if color and color != x:
            # No texto, o deslocamento de barras agrupadas vale para o início
            # da subfaixa; bandPosition=0.5 centraliza o valor sobre a barra.
            text_encodings[offset_channel] = offset_class(
                f"{color}:N",
                scale=alt.Scale(paddingInner=0.05),
                bandPosition=0.5,
            )
        layers.append(text_mark.encode(**text_encodings))
    st.altair_chart(
        alt.layer(*layers).properties(height=height),
        width="stretch",
    )


# [IA] Claude Code (Claude Sonnet 5.5) – matriz de desempenho (SWAPs × erro) com quadrantes
QUADRANT_LABEL_COLOR = "#6B7280"


def _star_path(points: int = 5, inner_ratio: float = 0.42) -> str:
    """Caminho SVG de uma estrela num quadrado de -1 a 1, como o Vega espera."""
    vertices = []
    for index in range(points * 2):
        radius = 1.0 if index % 2 == 0 else inner_ratio
        angle = -math.pi / 2 + index * math.pi / points
        vertices.append(f"{radius * math.cos(angle):.3f},{radius * math.sin(angle):.3f}")
    return "M" + "L".join(vertices) + "Z"


# Formato do ponto de cada método na matriz de desempenho.
METHOD_SHAPES = {
    "Fluxo min-cost": "circle",
    "Multi-start": _star_path(),
    "Qiskit SABRE": "triangle-up",
    "Busca exata": "square",
}


def _method_shape_scale(methods) -> alt.Scale:
    domain = list(dict.fromkeys(methods))
    return alt.Scale(
        domain=domain,
        range=[METHOD_SHAPES.get(method, "diamond") for method in domain],
    )


def _padded_domain(values: pd.Series) -> tuple[float, float]:
    """Intervalo do eixo com folga, para os pontos não colarem nas bordas."""
    low, high = float(values.min()), float(values.max())
    pad = max((high - low) * 0.25, abs(high) * 0.05, 0.5 if high == low else 0.0)
    return max(low - pad, 0.0), high + pad


def _quadrant_matrix(summary: pd.DataFrame) -> None:
    """Um ponto por método: SWAPs (x) × erro estimado (y), dividido na média.

    O quadrante inferior esquerdo reúne os métodos com menos SWAPs e menos erro
    que a média dos métodos comparados.
    """
    x_label, y_label = CHART_METRICS[0], CHART_METRICS[1]
    data = summary[["Método", x_label, y_label]].copy()
    x_low, x_high = _padded_domain(data[x_label])
    y_low, y_high = _padded_domain(data[y_label])
    x_mid, y_mid = float(data[x_label].mean()), float(data[y_label].mean())

    axis_style = {"labelColor": VALUE_LABEL_COLOR, "titleColor": VALUE_LABEL_COLOR}
    x_encoding = alt.X(
        f"{x_label}:Q",
        scale=alt.Scale(domain=[x_low, x_high], nice=False),
        axis=alt.Axis(grid=True, gridColor="#E5E7EB", tickMinStep=1, **axis_style),
    )
    y_encoding = alt.Y(
        f"{y_label}:Q",
        scale=alt.Scale(domain=[y_low, y_high], nice=False),
        axis=alt.Axis(grid=True, gridColor="#E5E7EB", **axis_style),
    )
    color_encoding = alt.Color(
        "Método:N",
        scale=_method_color_scale(data["Método"]),
        legend=None,
    )
    points = (
        alt.Chart(data)
        .mark_point(filled=True, size=320, opacity=1)
        .encode(
            x=x_encoding,
            y=y_encoding,
            color=color_encoding,
            shape=alt.Shape(
                "Método:N",
                scale=_method_shape_scale(data["Método"]),
                legend=None,
            ),
            tooltip=["Método", x_label, y_label],
        )
    )
    names = (
        alt.Chart(data)
        .mark_text(align="left", dx=12, fontSize=12, color=VALUE_LABEL_COLOR)
        .encode(x=x_encoding, y=y_encoding, text="Método:N")
    )
    cross = alt.layer(
        alt.Chart(pd.DataFrame({"v": [x_mid]})).mark_rule(color="#1F2937").encode(
            x=alt.X("v:Q", axis=None, scale=alt.Scale(domain=[x_low, x_high], nice=False))
        ),
        alt.Chart(pd.DataFrame({"v": [y_mid]})).mark_rule(color="#1F2937").encode(
            y=alt.Y("v:Q", axis=None, scale=alt.Scale(domain=[y_low, y_high], nice=False))
        ),
    )
    corners = (
        (x_low, y_low, "left", "bottom", ["Melhores", "poucos SWAPs, erro baixo"]),
        (x_low, y_high, "left", "top", ["Poucos SWAPs,", "erro alto"]),
        (x_high, y_low, "right", "bottom", ["Muitos SWAPs,", "erro baixo"]),
        (x_high, y_high, "right", "top", ["Piores", "muitos SWAPs, erro alto"]),
    )
    quadrant_labels = alt.layer(
        *[
            alt.Chart(pd.DataFrame({"x": [cx], "y": [cy]}))
            .mark_text(
                align=align,
                baseline=baseline,
                dx=6 if align == "left" else -6,
                dy=-6 if baseline == "bottom" else 6,
                fontStyle="italic",
                fontSize=12,
                color=QUADRANT_LABEL_COLOR,
                lineBreak="\n",
            )
            .encode(
                x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[x_low, x_high], nice=False)),
                y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[y_low, y_high], nice=False)),
                text=alt.value("\n".join(text)),
            )
            for cx, cy, align, baseline, text in corners
        ]
    )
    st.altair_chart(
        alt.layer(cross, quadrant_labels, points, names).properties(height=360),
        width="stretch",
    )


def _line_chart(data: pd.DataFrame, x: str, y: str, height: int = 360) -> None:
    """Linhas por método com as mesmas cores e formas da matriz de desempenho."""
    methods = data["Método"]
    axis_style = {"labelColor": VALUE_LABEL_COLOR, "titleColor": VALUE_LABEL_COLOR}
    legend = alt.Legend(
        title="Método",
        orient="top",
        direction="horizontal",
        symbolSize=160,
        symbolOpacity=1,
        labelColor=VALUE_LABEL_COLOR,
        titleColor=VALUE_LABEL_COLOR,
    )
    base = alt.Chart(data).encode(
        x=alt.X(
            f"{x}:O",
            axis=alt.Axis(labelAngle=0, grid=False, **axis_style),
            sort=sorted(data[x].unique()),
        ),
        y=alt.Y(
            f"{y}:Q",
            axis=alt.Axis(grid=True, gridColor="#E5E7EB", **axis_style),
        ),
        color=alt.Color(
            "Método:N",
            scale=_method_color_scale(methods),
            legend=legend,
        ),
    )
    lines = base.mark_line(strokeWidth=2.5)
    points = base.mark_point(filled=True, size=160, opacity=1).encode(
        shape=alt.Shape(
            "Método:N", scale=_method_shape_scale(methods), legend=legend
        ),
        tooltip=["Método", x, y],
    )
    st.altair_chart(
        alt.layer(lines, points).properties(height=height),
        width="stretch",
    )


# [IA] Claude Code (Claude Opus 5.5) – gráficos padronizados de SWAPs, erro e tempo
def _show_metric_charts(
    data: pd.DataFrame,
    x_axis: str,
    chart: str = "bar",
    horizontal: bool = False,
    sort_by_value: bool = False,
    bar_gap: float = 0.1,
    value_axis: bool = False,
    english_legend: bool = False,
) -> None:
    """Mostra SWAPs, erro e tempo em abas com o mesmo formato."""
    chart_tabs = st.tabs(list(CHART_METRICS))
    plot_height = 30 + 52 * len(data) if horizontal else 360
    for tab, label in zip(chart_tabs, CHART_METRICS):
        with tab:
            # Contêiner de altura fixa: as abas ocupam o mesmo espaço e a página
            # não se move ao trocar de métrica.
            with st.container(height=plot_height + 110, border=False):
                if chart == "line":
                    _line_chart(data, x=x_axis, y=label, height=plot_height)
                else:
                    _bar_chart(
                        data,
                        x=x_axis,
                        y=label,
                        color="Método",
                        height=plot_height,
                        horizontal=horizontal,
                        sort_by_value=sort_by_value,
                        bar_gap=bar_gap,
                        value_axis=value_axis,
                        axis_color=QUBIT_AXIS_GRAY,
                        axis_line_color=QUBIT_AXIS_LINE_GRAY,
                        # [IA] Claude Code (Claude Sonnet 5.5) – tempo mediano com no máximo 3 casas decimais sobre as barras
                        value_format=(
                            ".3~f" if label == "Tempo mediano (s)" else ".3~g"
                        ),
                        english_legend=english_legend,
                    )


# [IA] Claude Code (Claude Opus 5.5) – cálculo das medianas para os gráficos
def _median_metrics(results: pd.DataFrame, grouping: list[str]) -> pd.DataFrame:
    summary = results.groupby(grouping, as_index=False).agg(
        swaps=("swap_count", "median"),
        erro=("expected_error_rate", "median"),
        tempo=("elapsed_seconds", "median"),
    )
    summary["erro"] *= 100
    summary = _labelled(summary, ("topology_category",))
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

    summary = _median_metrics(results, ["algorithm"])
    chart_column, matrix_column = st.columns(2, gap="large")
    with chart_column:
        st.markdown("#### Comparação visual")
        st.caption("Medianas das execuções; valores menores são melhores.")
        _show_metric_charts(
            summary,
            "Método",
            horizontal=True,
            sort_by_value=True,
        )
    with matrix_column:
        st.markdown("#### Matriz de desempenho")
        st.caption(
            "SWAPs × erro estimado (medianas). As linhas marcam a média dos "
            "métodos comparados; quanto mais perto do canto inferior esquerdo, "
            "melhor."
        )
        _quadrant_matrix(summary)

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


# [IA] Claude Code (Claude Sonnet 5.5) – chamada do subprocesso que executa os algoritmos
def _run_case_in_subprocess(
    circuit_path: Path,
    topology_path: Path,
    runs: int,
    initial_candidates: int,
    seed: int,
    max_exact_placements: int,
    on_progress,
) -> list[dict[str, object]]:
    """Roda `analysis.live_run` e devolve os registros, avisando o progresso."""
    command = [
        sys.executable, "-m", "analysis.live_run",
        "--circuit", str(circuit_path),
        "--topology", str(topology_path),
        "--runs", str(runs),
        "--initial-candidates", str(initial_candidates),
        "--seed", str(seed),
        "--max-exact-placements", str(max_exact_placements),
    ]
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    records = None
    try:
        for line in process.stdout:
            message = json.loads(line)
            if "progress" in message:
                on_progress(message["progress"], message["total"])
            elif "records" in message:
                records = message["records"]
        _, errors = process.communicate()
    finally:
        if process.poll() is None:
            process.kill()
    if process.returncode != 0 or records is None:
        details = (errors or "").strip().splitlines()
        raise RuntimeError(
            details[-1] if details else f"o processo terminou com código {process.returncode}"
        )
    return records


# [IA] Claude Code (Claude Sonnet 5.5) – execução dos quatro métodos na hora, sem usar o CSV pré-computado
def _show_live_run(
    circuit_path: Path,
    topology_path: Path,
    circuit_name: str,
    topology_name: str,
    logical_qubits: int,
    physical_qubits: int,
) -> None:
    st.caption(
        "Roda agora os quatro métodos no circuito e na topologia escolhidos, "
        "sem ler o CSV pré-computado. Cada execução usa uma seed diferente "
        "(seed inicial + número da execução − 1)."
    )
    columns = st.columns(4)
    runs = columns[0].number_input(
        "Execuções", min_value=1, max_value=20, value=5, key="live_runs",
        help="Use 5 ou mais para uma média de tempo confiável.",
    )
    candidates = columns[1].number_input(
        "Inícios do multi-start", min_value=1, max_value=200, value=10,
        key="live_candidates",
        help="Quanto maior, mais lento é o multi-start.",
    )
    seed = columns[2].number_input(
        "Seed inicial", min_value=0, value=42, key="live_seed"
    )
    exact_limit = columns[3].number_input(
        "Limite da busca exata (placements)", min_value=0, value=100_000,
        step=10_000, key="live_exact_limit",
        help="A busca exata só roda se o número de placements couber aqui.",
    )

    work = logical_qubits * physical_qubits
    too_large = work > LIVE_WORK_LIMIT
    allow_large = False
    if too_large:
        st.warning(
            f"Este caso tem {logical_qubits} qubits lógicos e {physical_qubits} "
            "físicos. O multi-start pode levar vários minutos por execução. "
            "Para uma resposta rápida, use os resultados pré-computados."
        )
        allow_large = st.checkbox(
            "Executar mesmo assim (pode travar o app por muito tempo)",
            key="live_allow_large",
        )

    signature = (
        circuit_name, topology_name, int(runs), int(candidates), int(seed),
        int(exact_limit),
    )
    if st.button(
        "Executar os 4 algoritmos agora",
        disabled=too_large and not allow_large,
        key="live_run_button",
    ):
        progress = st.progress(0.0, text="Preparando a execução...")

        def _update(done: int, total: int) -> None:
            progress.progress(done / total, text=f"Execução {done} de {total}")

        started = time.perf_counter()
        try:
            records = _run_case_in_subprocess(
                circuit_path,
                topology_path,
                int(runs),
                int(candidates),
                int(seed),
                int(exact_limit),
                _update,
            )
        except Exception as error:  # noqa: BLE001 - mostra qualquer falha ao usuário
            progress.empty()
            st.error(f"Não foi possível executar os algoritmos: {error}")
            st.session_state.pop("live_results", None)
        else:
            progress.empty()
            st.session_state["live_results"] = {
                "signature": signature,
                "table": pd.DataFrame(records),
                "seconds": time.perf_counter() - started,
            }

    live = st.session_state.get("live_results")
    if not live or live["signature"][:2] != (circuit_name, topology_name):
        st.caption("Clique em “Executar” para calcular os resultados deste caso.")
        return
    table = live["table"]
    st.success(
        f"{len(table):,} execuções calculadas em {live['seconds']:.1f} s "
        f"(seed inicial {live['signature'][4]}, {live['signature'][2]} execuções)."
    )
    if "Busca exata" not in set(table["algorithm"]):
        placements = int(table["possible_mappings"].iloc[0])
        st.info(
            f"A busca exata não rodou: este caso tem {placements:,} placements "
            f"possíveis, acima do limite de {live['signature'][5]:,}."
        )
    _show_mapping_results(table)


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
            format_func=dataset_label,
            key="overview_circuit_category",
        )
        topology_category = st.selectbox(
            "Filtrar tabela de topologias por arquitetura",
            ["Todas"] + sorted(topologies["categoria"].dropna().unique()),
            format_func=dataset_label,
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
                _labelled(filtered_circuits, ("grafo", "categoria"))[
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
            topology_table = _labelled(filtered_topologies, ("grafo", "categoria"))[
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
            format_func=dataset_label,
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
            format_func=dataset_label,
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
            format_func=dataset_label,
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
            format_func=dataset_label,
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

    st.divider()
    _show_graph_metrics(graph_details)

    st.divider()
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
    precomputed_tab, live_tab = st.tabs(
        ["Resultados pré-computados", "Executar agora"]
    )
    topology_summary_qubits = graph_details["topology_summary"]["qubits"]
    with precomputed_tab:
        st.caption(
            "Erro estimado pelo modelo de taxas sintéticas dos links, não uma "
            "medição em hardware real. Cada SWAP conta como três portas de dois "
            "qubits."
        )
        # [IA] Claude Code (Claude Sonnet 5.5) – botões de métodos mais estreitos, junto à borda esquerda
        methods_column, _ = st.columns([2, 3], gap="large")
        with methods_column:
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

    with live_tab:
        _show_live_run(
            circuit_path,
            topology_path,
            selected_circuit,
            selected_topology,
            logical_qubits,
            int(topology_summary_qubits),
        )

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
                format_func=dataset_label,
            )
        with filter_topology:
            selected_topology_categories = st.multiselect(
                "Arquiteturas",
                topology_categories,
                default=topology_categories,
                format_func=dataset_label,
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
                format_func=dataset_label,
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
            architecture_tab, scaling_tab, matrix_tab, detail_tab = st.tabs(
                [
                    "Por topologia",
                    "Por qubits lógicos",
                    "Matriz de desempenho",
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
                        bar_gap=0.65,
                        value_axis=True,
                        english_legend=True,
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

            with matrix_tab:
                if scalable_results.empty:
                    st.info(
                        "Selecione multi-start, fluxo min-cost ou SABRE para "
                        "ver a matriz de desempenho."
                    )
                else:
                    st.caption(
                        "SWAPs × erro estimado (medianas de todos os casos "
                        "filtrados). As linhas marcam a média dos métodos "
                        "comparados; quanto mais perto do canto inferior "
                        "esquerdo, melhor."
                    )
                    _quadrant_matrix(
                        _median_metrics(scalable_results, ["algorithm"])
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
                detail = _labelled(
                    detail,
                    ("circuit_category", "circuit", "topology_category", "topology"),
                )
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
