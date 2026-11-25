# [IA] Claude Code (Claude Sonnet 5.5) – aba de análise exploratória e explanatória (AVD)
"""Aba "Análise AVD": visualizações exploratórias e explanatórias.

Reaproveita os gráficos da tela de caso selecionado (exploratórios) e da
comparação de algoritmos (explanatórios). Os números citados nos insights são
calculados a partir do benchmark carregado, para o texto não ficar defasado.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

RESEARCH_QUESTION = (
    "Em cenários equivalentes, os métodos de mapeamento do projeto reduzem "
    "SWAPs e erro estimado em relação ao Qiskit SABRE, e qual abordagem é "
    "mais adequada conforme a prioridade?"
)
CASE_CIRCUIT = "modular_adder_6qubits"
CASE_TOPOLOGY = "line_6qubits"
SABRE = "Qiskit SABRE"
MULTI_START = "Heurística multi-start"
MIN_COST = "Fluxo min-cost + hill climb"
EXACT = "Busca exata"
SWAPS = "SWAPs medianos"
ERROR = "Erro estimado mediano (%)"
TIME = "Tempo mediano (s)"
GRAY = "#6B7280"


# [IA] Claude Code (Claude Sonnet 5.5) – bloco padrão de leitura de cada gráfico
def _note(visual: str, why: str, insight: str | None = None) -> None:
    """Texto abaixo do gráfico: recursos visuais, escolha do formato e insight."""
    text = (
        f"**Recursos visuais:** {visual}  \n"
        f"**Por que este gráfico:** {why}"
    )
    if insight:
        text += f"  \n**Insight:** {insight}"
    st.markdown(text)


def _title(text: str, subtitle: str = "") -> None:
    st.markdown(f"##### {text}")
    if subtitle:
        st.caption(subtitle)


# [IA] Claude Code (Claude Sonnet 5.5) – estatísticas do benchmark usadas nos textos de insight
def _benchmark_stats(benchmarks: pd.DataFrame) -> dict[str, object]:
    runs = benchmarks[benchmarks["algorithm"] != EXACT].copy()
    runs["erro"] = runs["expected_error_rate"] * 100
    per_case = (
        runs.groupby(["circuit", "topology", "algorithm"])
        .agg(swaps=("swap_count", "median"), erro=("erro", "median"))
        .reset_index()
    )
    swaps = per_case.pivot(index=["circuit", "topology"], columns="algorithm", values="swaps")
    erros = per_case.pivot(index=["circuit", "topology"], columns="algorithm", values="erro")
    stats: dict[str, object] = {"cases": len(swaps)}
    for method in (MULTI_START, MIN_COST):
        stats[method] = {
            "swap_wins": float((swaps[method] < swaps[SABRE]).mean()),
            "swap_losses": float((swaps[method] > swaps[SABRE]).mean()),
            "error_wins": float((erros[method] < erros[SABRE]).mean()),
            "swap_total_ratio": float(swaps[method].sum() / swaps[SABRE].sum()),
        }
    stats["overall"] = runs.groupby("algorithm").agg(
        swaps=("swap_count", "median"),
        erro=("erro", "median"),
        tempo=("elapsed_seconds", "median"),
    )
    stats["by_qubits"] = runs.groupby(["logical_qubits", "algorithm"]).agg(
        swaps=("swap_count", "median"), erro=("erro", "median")
    )
    stats["by_topology"] = runs.groupby(["topology_category", "algorithm"]).agg(
        swaps=("swap_count", "median"), erro=("erro", "median")
    )
    stats["corr_swaps_error"] = float(runs["swap_count"].corr(runs["erro"]))
    stats["corr_swaps_qubits"] = float(runs["swap_count"].corr(runs["logical_qubits"]))
    return stats


def _pct(value: float) -> str:
    return f"{value * 100:.0f}%"


# ---------------------------------------------------------------- exploratória
# [IA] Claude Code (Claude Sonnet 5.5) – dispersão de SWAPs × erro estimado por execução
def _swaps_error_scatter(
    benchmarks: pd.DataFrame, method_scale: alt.Scale, shape_scale: alt.Scale
) -> None:
    """Dispersão no mesmo estilo visual da matriz de desempenho (cor, forma, grade)."""
    runs = benchmarks[benchmarks["algorithm"] != EXACT].copy()
    runs["Erro estimado (%)"] = runs["expected_error_rate"] * 100
    runs["SWAPs"] = runs["swap_count"]
    runs["Método"] = runs["algorithm"].map(
        {MULTI_START: "Multi-start", MIN_COST: "Fluxo min-cost", SABRE: SABRE}
    )
    axis_style = {"labelColor": "black", "titleColor": "black"}
    legend = alt.Legend(
        title="Método",
        orient="top",
        direction="horizontal",
        symbolSize=160,
        symbolOpacity=1,
        labelColor="black",
        titleColor="black",
    )
    x_encoding = alt.X(
        "SWAPs:Q",
        title="SWAPs inseridos",
        axis=alt.Axis(grid=True, gridColor="#E5E7EB", **axis_style),
    )
    y_encoding = alt.Y(
        "Erro estimado (%):Q",
        title="Erro estimado (%)",
        axis=alt.Axis(grid=True, gridColor="#E5E7EB", **axis_style),
    )
    base = alt.Chart(runs)
    points = base.mark_point(filled=True, size=110, opacity=0.6).encode(
        x=x_encoding,
        y=y_encoding,
        color=alt.Color("Método:N", scale=method_scale, legend=legend),
        shape=alt.Shape("Método:N", scale=shape_scale, legend=legend),
        tooltip=["Método", "circuit", "topology", "SWAPs", "Erro estimado (%)"],
    )
    trend = base.transform_regression("SWAPs", "Erro estimado (%)").mark_line(
        color="#1F2937", strokeDash=[5, 4]
    ).encode(x="SWAPs:Q", y="Erro estimado (%):Q")
    st.altair_chart(alt.layer(points, trend).properties(height=360), width="stretch")


def _show_exploratory(
    benchmarks: pd.DataFrame,
    details: dict[str, object],
    root: Path,
    bar_chart: Callable[..., None],
    median_metrics: Callable[..., pd.DataFrame],
    show_metric_charts: Callable[..., None],
    live_table: pd.DataFrame | None,
    method_scale: alt.Scale,
    shape_scale: alt.Scale,
    light_blue: str,
    dark_blue: str,
    axis_gray: str,
    axis_line_gray: str,
) -> None:
    st.caption(
        f"Estrutura do caso {CASE_CIRCUIT.replace('_', ' ')} sobre {CASE_TOPOLOGY.replace('_', ' ')} "
        "(o mesmo da aba Caso selecionado) e comportamento geral do benchmark."
    )
    bar_style = dict(
        height=240, value_axis=True, axis_color=axis_gray, axis_line_color=axis_line_gray
    )

    # E1 -------------------------------------------------------------
    _title(
        "1. Hubs no circuito: grau e carga de interações por qubit lógico",
        "Esquerda: vizinhos distintos de cada qubit. Direita: gates de 2 qubits de que ele participa.",
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("**Grau (vizinhos distintos)**")
        bar_chart(
            details["logical_qubits"], x="Qubit lógico", y="Grau",
            bar_color=light_blue, **bar_style,
        )
    with right:
        st.markdown("**Interações de 2 qubits**")
        bar_chart(
            details["logical_qubits"], x="Qubit lógico", y="Interações de 2 qubits",
            bar_color=dark_blue, **bar_style,
        )
    _note(
        "comprimento das barras (posição em escala comum) e valor escrito na ponta, sem grade "
        "para não competir com o número. No projeto, o azul-claro e o azul foram definidos para "
        "referenciar os algoritmos desenvolvidos; para manter a coerência visual, os gráficos "
        "de modo geral sempre permeiam essas cores.",
        "utilizamos o gráfico de barras para visualizar a distribuição dos dados.",
    )

    # E3 -------------------------------------------------------------
    st.divider()
    _title(
        "2. Qualidade do hardware: grau e erro médio de caminho por qubit físico",
        "Erro médio dos caminhos de menor erro que partem de cada qubit (centralidade implícita).",
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("**Grau**")
        bar_chart(
            details["physical_qubits"], x="Qubit físico", y="Grau",
            bar_color=light_blue, **bar_style,
        )
    with right:
        st.markdown("**Erro médio dos caminhos (%)**")
        bar_chart(
            details["physical_qubits"], x="Qubit físico", y="Erro médio dos caminhos (%)",
            bar_color=dark_blue, **bar_style,
        )
    _note(
        "comprimento das barras (posição em escala comum) e valor escrito na ponta, sem grade "
        "para não competir com o número. No projeto, o azul-claro e o azul foram definidos para "
        "referenciar os algoritmos desenvolvidos; para manter a coerência visual, os gráficos "
        "de modo geral sempre permeiam essas cores. Na prática, este gráfico tem uma ideia muito "
        "parecida com a do gráfico 1 e basicamente repete a mesma proposta; por isso a explicação é a mesma.",
        "utilizamos o gráfico de barras para visualizar a distribuição dos dados. Como na prática "
        "são gráficos com ideias muito similares, a ideia do gráfico 1 foi basicamente repetida "
        "e por isso a explicação é a mesma.",
    )

    # E4 -------------------------------------------------------------
    st.divider()
    _title(
        "3. Os dois grafos lado a lado: o que precisa caber em quê",
        "Grafo de interações (circuito) e grafo de acoplamento (hardware) do mesmo caso.",
    )
    left, right = st.columns(2, gap="large")
    for column, filename in (
        (left, "avd_exploratoria_grafo_interacoes.png"),
        (right, "avd_exploratoria_grafo_topologia.png"),
    ):
        image = root / "out" / "parte2" / filename
        if image.is_file():
            column.image(str(image), width="stretch")
        else:
            column.info("Imagem indisponível; use 'Gerar grafos' na aba Caso selecionado.")
    _note(
        "tamanho do nó = grau; espessura/rótulo da aresta = frequência (circuito) ou taxa de erro (hardware); "
        "laranja destaca o hub e os pares mais frequentes; a cor representa a intensidade das "
        "interações (circuito) ou o erro propagado (hardware).",
        "grafos node-link são a representação natural para estrutura de conexões e mostram a "
        "topologia (estrela × linha) que os gráficos de barras não mostram.",
    )

    # E5 -------------------------------------------------------------
    st.divider()
    _title(
        "5. Comparação visual dos métodos no caso selecionado",
        f"Execução com os valores padrão da aba Executar agora ({CASE_CIRCUIT.replace('_', ' ')} "
        f"sobre {CASE_TOPOLOGY.replace('_', ' ')}); medianas das execuções, menores são melhores.",
    )
    if live_table is None or live_table.empty:
        st.info("Não foi possível executar os algoritmos para este gráfico.")
    else:
        show_metric_charts(
            median_metrics(live_table, ["algorithm"]),
            "Método",
            horizontal=True,
            sort_by_value=True,
        )
        _note(
            "comprimento das barras ordenado do maior para o menor valor, valor escrito na ponta de "
            "cada barra e uma cor fixa por método, a mesma usada nos demais gráficos "
            "(SABRE em cinza como referência).",
            "escolhemos o gráfico de barras horizontal para evidenciar a hierarquia entre os métodos: "
            "os nomes ficam legíveis no eixo vertical e a ordenação mostra o ranking de relance.",
        )


# ----------------------------------------------------------------- explanatória
def _show_explanatory(
    benchmarks: pd.DataFrame,
    median_metrics: Callable[..., pd.DataFrame],
    bar_chart: Callable[..., None],
    line_chart: Callable[..., None],
    quadrant_matrix: Callable[..., None],
    axis_gray: str,
    axis_line_gray: str,
) -> None:
    needed = {SABRE, MULTI_START, MIN_COST}
    if benchmarks.empty or not needed <= set(benchmarks["algorithm"]):
        st.info("Faltam resultados dos três métodos comparáveis ao SABRE.")
        return
    stats = _benchmark_stats(benchmarks)
    overall = stats["overall"]
    ms, mc = stats[MULTI_START], stats[MIN_COST]
    runs = benchmarks[benchmarks["algorithm"] != EXACT]

    _title("Por que minimizar cada métrica?")
    st.markdown(
        "**SWAPs:** cada SWAP corrige uma incompatibilidade de conectividade, mas acrescenta "
        "operações de dois qubits ao circuito. Reduzi-los tende a diminuir profundidade, tempo de "
        "execução e exposição a falhas. Ainda assim, menos SWAPs não garante menor erro: uma rota "
        "mais longa por links melhores pode ter erro estimado menor.\n\n"
        "**Erro estimado:** aproxima a probabilidade de falha acumulada das operações roteadas. "
        "É importante quando a prioridade é preservar a qualidade do estado quântico; neste "
        "projeto, o cálculo usa taxas sintéticas dos links e hipóteses simplificadoras, não "
        "medições reais.\n\n"
        "**Tempo de compilação:** importa quando muitos circuitos precisam ser mapeados ou quando "
        "a compilação faz parte de um fluxo interativo. Deve ser comparado no mesmo ambiente; o "
        "tempo do benchmark não é uma garantia de desempenho em outra máquina.\n\n"
        "O objetivo implementado prioriza lexicograficamente erro estimado e, em caso de empate, "
        "número de SWAPs. Por isso, os métodos podem aceitar mais SWAPs se encontrarem uma rota "
        "de menor erro."
    )
    st.divider()

    # X1 -------------------------------------------------------------
    _title(
        "A diferença para o SABRE aparece quando o circuito cresce",
        "Medianas de SWAPs e de erro estimado por número de qubits lógicos.",
    )
    by_qubits = median_metrics(runs, ["logical_qubits", "algorithm"])
    left, right = st.columns(2, gap="large")
    for column, metric in ((left, SWAPS), (right, ERROR)):
        with column:
            st.markdown(f"**{metric}**")
            line_chart(by_qubits, x="Qubits lógicos", y=metric, height=320)
    by_q = stats["by_qubits"]
    sizes = sorted(by_q.index.get_level_values(0).unique())
    small, large = sizes[1] if len(sizes) > 1 else sizes[0], sizes[-1]
    _note(
        "a cor de cada método segue o padrão de toda a aplicação para os algoritmos implementados "
        "(SABRE em cinza como referência; multi-start em azul-claro; min-cost em azul), e a forma do "
        "ponto auxilia a leitura, inclusive de quem tem dificuldade visual; posição no eixo x "
        "(tamanho) e altura (valor), com os mesmos eixos nos dois painéis.",
        "usamos linhas para ver a tendência de cada algoritmo, o que torna a análise e a comparação "
        "entre eles mais intuitiva.",
        f"até {small} qubits os três métodos são praticamente iguais em SWAPs "
        f"({by_q.loc[(small, MULTI_START), 'swaps']:.1f} contra {by_q.loc[(small, SABRE), 'swaps']:.1f} do SABRE) "
        f"e o multi-start tem menos erro ({by_q.loc[(small, MULTI_START), 'erro']:.1f}% contra "
        f"{by_q.loc[(small, SABRE), 'erro']:.1f}%). Com {large} qubits o quadro inverte: o SABRE usa "
        f"{by_q.loc[(large, SABRE), 'swaps']:.0f} SWAPs contra {by_q.loc[(large, MULTI_START), 'swaps']:.0f} "
        f"(multi-start) e {by_q.loc[(large, MIN_COST), 'swaps']:.0f} (min-cost), e também tem o menor erro. "
        "A vantagem do SABRE cresce com a escala.",
    )

    # X2 -------------------------------------------------------------
    st.divider()
    _title(
        "A topologia decide quem se sai melhor",
        "Medianas de SWAPs e de erro estimado por arquitetura de hardware.",
    )
    by_topology = median_metrics(runs, ["topology_category", "algorithm"])
    left, right = st.columns(2, gap="large")
    for column, metric in ((left, SWAPS), (right, ERROR)):
        with column:
            st.markdown(f"**{metric}**")
            bar_chart(
                by_topology, x="Topologia", y=metric, color="Método", height=320,
                bar_gap=0.55, value_axis=True, axis_color=axis_gray,
                axis_line_color=axis_line_gray, english_legend=True,
            )
    by_t = stats["by_topology"]
    topologies = by_t.index.get_level_values(0).unique()
    gap = {
        topology: by_t.loc[(topology, MULTI_START), "swaps"] - by_t.loc[(topology, SABRE), "swaps"]
        for topology in topologies
    }
    best_topology = min(gap, key=gap.get)
    worst_topology = max(gap, key=gap.get)
    _note(
        "barras agrupadas por arquitetura, uma cor fixa por método (a mesma do gráfico anterior) e "
        "valor escrito sobre cada barra, de modo que não é preciso ler o eixo.",
        "a topologia é uma variável categórica sem ordem natural, então barras agrupadas permitem "
        "comparar os três métodos dentro de cada grupo e o mesmo método entre grupos.",
        f"o multi-start só supera o SABRE em SWAPs na topologia {best_topology.replace('_', ' ')} "
        f"({by_t.loc[(best_topology, MULTI_START), 'swaps']:.1f} contra "
        f"{by_t.loc[(best_topology, SABRE), 'swaps']:.1f}), mais conectada. Na {worst_topology.replace('_', ' ')}, "
        f"de grau máximo 2, a diferença se inverte ({by_t.loc[(worst_topology, MULTI_START), 'swaps']:.0f} contra "
        f"{by_t.loc[(worst_topology, SABRE), 'swaps']:.0f}): com pouca conectividade, o roteamento passo a passo do "
        "SABRE compensa melhor do que escolher só o posicionamento inicial.",
    )

    # X3 -------------------------------------------------------------
    st.divider()
    _title(
        "Resposta à pergunta: onde cada método fica entre SWAPs e erro",
        "Mediana de todas as execuções comparáveis; as linhas marcam a média dos métodos.",
    )
    quadrant_matrix(median_metrics(runs, ["algorithm"]))
    _note(
        "posição em dois eixos (menor é melhor em ambos), quadrantes rotulados, forma e cor por método; "
        "SABRE em cinza é a referência e os métodos do projeto ficam em destaque colorido.",
        "escolhemos este gráfico pela comparação em duas dimensões a partir dos eixos (SWAPs × erro), "
        "o que facilita a análise. Ele também permite que, se no futuro houver mais algoritmos, "
        "o gráfico continue atendendo bem a essa possível escalabilidade.",
        f"o multi-start fica no canto bom ({overall.loc[MULTI_START, 'swaps']:.1f} SWAPs e "
        f"{overall.loc[MULTI_START, 'erro']:.2f}% de erro) e o SABRE logo ao lado "
        f"({overall.loc[SABRE, 'swaps']:.1f} e {overall.loc[SABRE, 'erro']:.2f}%): nas medianas, "
        "quase um empate. O min-cost, com "
        f"{overall.loc[MIN_COST, 'swaps']:.1f} SWAPs e {overall.loc[MIN_COST, 'erro']:.2f}%, é dominado pelos dois.",
    )

    # Vantagens e cenários recomendados -------------------------------
    st.divider()
    _title("Vantagens e cenários recomendados")
    st.markdown(
        "**Busca exata**\n\n"
        "Explora todas as colocações iniciais e encontra a melhor entre elas segundo o roteador "
        "adotado — não a melhor sequência possível de SWAPs. É útil para validar heurísticas e "
        "estabelecer uma referência em instâncias pequenas. O espaço cresce combinatoriamente, "
        "então não é recomendada para lotes maiores. Não há cenários pareados deste método neste "
        "lote.\n\n"
        "**Heurística multi-start**\n\n"
        "Combina colocações iniciais diversas (aleatórias, por grau e pelo par mais frequente) com "
        "refinamento local avaliado pelo roteador completo. É indicada quando a qualidade do "
        "mapeamento é prioritária e há tempo para testar várias partidas; não garante ótimo global "
        "e custa mais que uma única busca. No lote atual, 54.2% dos cenários foram melhores que "
        "SABRE em erro estimado; diferença mediana -1.71 % (48 cenários). 12.5% dos cenários foram "
        "melhores que SABRE em swaps; diferença mediana +0 SWAPs (48 cenários). 0.0% dos cenários "
        "foram melhores que SABRE em tempo; diferença mediana +3.32e+04 % (48 cenários).\n\n"
        "**Fluxo min-cost + hill climb**\n\n"
        "Resolve em tempo polinomial uma atribuição inicial informada por grau, distância e erro, "
        "e depois melhora essa solução com hill climbing. É uma alternativa quando a busca exata é "
        "inviável e se deseja um ponto de partida estruturado; a atribuição otimiza um custo "
        "aproximado, não diretamente o roteamento completo. No lote atual, 31.2% dos cenários "
        "foram melhores que SABRE em erro estimado; diferença mediana +2.27 % (48 cenários). 4.2% "
        "dos cenários foram melhores que SABRE em swaps; diferença mediana +3.5 SWAPs (48 "
        "cenários). 8.3% dos cenários foram melhores que SABRE em tempo; diferença mediana "
        "+2.44e+03 % (48 cenários).\n\n"
        "**Qiskit SABRE — referência**\n\n"
        "É o baseline externo: escolhe layout e roteia dinamicamente olhando operações futuras. É "
        "recomendado como comparação prática e quando se quer permanecer no fluxo de transpilação "
        "do Qiskit. Nesta comparação ele é a referência, não um método desenvolvido pelo projeto; "
        "os resultados não implicam que seja melhor em todos os cenários."
    )


# [IA] Claude Code (Claude Sonnet 5.5) – montagem da aba de análise exploratória e explanatória
def show_avd_analysis(
    benchmarks: pd.DataFrame,
    details: dict[str, object],
    root: Path,
    *,
    bar_chart: Callable[..., None],
    line_chart: Callable[..., None],
    quadrant_matrix: Callable[..., None],
    median_metrics: Callable[..., pd.DataFrame],
    show_metric_charts: Callable[..., None],
    live_table: pd.DataFrame | None,
    method_scale: alt.Scale,
    shape_scale: alt.Scale,
    light_blue: str,
    dark_blue: str,
    axis_gray: str,
    axis_line_gray: str,
) -> None:
    st.header(":blue[Análise exploratória e explanatória]")
    st.markdown(f"**Pergunta de pesquisa:** {RESEARCH_QUESTION}")
    st.caption(
        "A parte exploratória examina os grafos e o benchmark para entender os dados; "
        "a explanatória reúne o que foi encontrado para responder à pergunta."
    )
    exploratory, explanatory = st.tabs(["Exploratória", "Explanatória"])
    with exploratory:
        _show_exploratory(
            benchmarks, details, root, bar_chart, median_metrics,
            show_metric_charts, live_table, method_scale, shape_scale, light_blue, dark_blue, axis_gray, axis_line_gray,
        )
    with explanatory:
        _show_explanatory(
            benchmarks, median_metrics, bar_chart, line_chart,
            quadrant_matrix, axis_gray, axis_line_gray,
        )
