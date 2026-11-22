# [IA] Claude Code (Claude Opus 5.5) – módulo da página de apresentação do projeto
"""Página de apresentação do projeto no app Streamlit."""

from __future__ import annotations

import pandas as pd
import streamlit as st


# [IA] Claude Code (Claude Opus 5.5) – texto de introdução e tabela de modelagem em grafos
def _show_problem() -> None:
    st.header(":blue[Sobre o projeto]")
    st.markdown(
        """
        Um circuito quântico descreve operações entre :blue[**qubits lógicos**]; um
        processador oferece :blue[**qubits físicos**] ligados por uma topologia de
        acoplamento limitada. Uma porta de dois qubits só executa diretamente
        se os qubits físicos que recebem seus operandos forem vizinhos no
        hardware. Caso contrário, o compilador precisa inserir **SWAPs** para
        aproximar os estados, e cada SWAP adiciona portas e, portanto, erro.

        Este projeto estuda **como o padrão de interações do circuito e a
        conectividade/erro do hardware afetam o posicionamento (placement) e o
        roteamento**, e quais algoritmos em grafos sugerem mapeamentos com
        menos SWAPs e menor erro estimado.
        """
    )

    st.divider()
    st.subheader(":blue[Modelagem em grafos]")
    st.markdown(
        "O problema é representado por dois grafos com vértices de domínios "
        "diferentes. Só um mapeamento injetivo lógico → físico relaciona os dois."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Característica": "Vértices",
                    "Grafo de interações (circuito)": "Qubits lógicos",
                    "Grafo de acoplamento (hardware)": "Qubits físicos",
                },
                {
                    "Característica": "Arestas",
                    "Grafo de interações (circuito)": "Pares com porta de dois qubits",
                    "Grafo de acoplamento (hardware)": "Acoplamentos permitidos",
                },
                {
                    "Característica": "Peso",
                    "Grafo de interações (circuito)": "Nº de interações do par",
                    "Grafo de acoplamento (hardware)": "Taxa de erro do link",
                },
                {
                    "Característica": "Tipo",
                    "Grafo de interações (circuito)": "Não direcionado",
                    "Grafo de acoplamento (hardware)": "Direcionado",
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "A ordem das operações do circuito é guardada à parte para o "
        "roteamento. As taxas de erro têm mediana de 0,15% e ficam entre "
        "0,02% e 1%."
    )


# [IA] Claude Code (Claude Opus 5.5) – conteúdo das etapas do pipeline
PIPELINE_STEPS = (
    (
        "1. Pré-processamento",
        "Gera matrizes e métricas dos dois grafos.",
        "Dijkstra de todas as origens; profundidade do DAG",
    ),
    (
        "2. Placement inicial",
        "Escolhe a posição física de cada qubit lógico.",
        "Busca exata, multi-start ou fluxo de custo mínimo",
    ),
    (
        "3. Roteamento",
        "Executa o circuito em ordem, inserindo SWAPs.",
        "Roteador por caminhos pré-computados",
    ),
    (
        "4. Avaliação",
        "Conta SWAPs e estima o erro roteado.",
        "Modelo de falhas independentes",
    ),
)

# [IA] Claude Code (Claude Opus 5.5) – estilo CSS das caixas e setas do pipeline
_PIPELINE_STYLE = """
<style>
.pipeline-flow {
    display: flex;
    align-items: stretch;
    gap: .5rem;
    margin: .5rem 0 1.5rem 0;
}
.pipeline-step {
    flex: 1 1 0;
    border: 1px solid rgba(128, 128, 128, .35);
    border-radius: .5rem;
    padding: .9rem 1rem;
}
.pipeline-step .step-title {
    color: #2563EB;
    font-weight: 600;
    margin-bottom: .4rem;
}
.pipeline-step .step-text {
    margin-bottom: .6rem;
}
.pipeline-step .step-method {
    font-size: .85rem;
    opacity: .7;
}
.pipeline-arrow {
    display: flex;
    align-items: center;
    color: #2563EB;
    font-size: 1.5rem;
}
@media (max-width: 900px) {
    .pipeline-flow { flex-direction: column; }
    .pipeline-arrow { justify-content: center; transform: rotate(90deg); }
}
</style>
"""


# [IA] Claude Code (Claude Opus 5.5) – renderização do pipeline em caixas ligadas por setas
def _pipeline_flow() -> None:
    """Mostra as etapas do pipeline como caixas ligadas por setas."""
    steps = [
        '<div class="pipeline-step">'
        f'<div class="step-title">{title}</div>'
        f'<div class="step-text">{text}</div>'
        f'<div class="step-method">{method}</div>'
        "</div>"
        for title, text, method in PIPELINE_STEPS
    ]
    arrow = '<div class="pipeline-arrow">→</div>'
    st.html(_PIPELINE_STYLE + f'<div class="pipeline-flow">{arrow.join(steps)}</div>')


# [IA] Claude Code (Claude Opus 5.5) – seção do pipeline e objetivo comum de avaliação
def _show_pipeline() -> None:
    st.divider()
    st.subheader(":blue[Pipeline]")
    _pipeline_flow()
    st.markdown("#### Objetivo comum")
    st.markdown(
        r"""
        Todos os métodos do projeto são comparados pelo **mesmo objetivo
        lexicográfico**: primeiro o erro estimado após o roteamento, depois o
        número de SWAPs.
        """
    )
    st.latex(
        r"\operatorname{custo}(m) = \bigl(E_{\mathrm{route}}(m),\ "
        r"S_{\mathrm{route}}(m)\bigr), \qquad "
        r"E_{\mathrm{route}}(m) = 1 - \prod_{g \in \mathcal{R}(m)} (1 - p_g)"
    )
    st.caption(
        "m = mapeamento lógico → físico; 𝓡(m) = portas do circuito roteado; "
        "p_g = taxa de erro do link onde a porta g executa."
    )


# [IA] Claude Code (Claude Opus 5.5) – descrição do Dijkstra de todas as origens e das estruturas do circuito
def _show_preprocessing() -> None:
    st.markdown("#### Caminhos de menor erro no hardware")
    st.markdown(
        r"""
        O roteador precisa saber, para **todo par** de qubits físicos, por onde
        mover um estado. Em vez de usar o menor número de saltos, o projeto
        procura o caminho que **maximiza a probabilidade de sucesso**, ou seja,
        o produto de $(1-p_e)$ ao longo das arestas.

        **Transformação do peso.** Produto não é aditivo, mas o logaritmo é.
        Cada link recebe o custo
        """
    )
    st.latex(
        r"q(p_e) = -\ln(1 - p_e) \ \ge 0, \qquad "
        r"\min_\pi \sum_{e \in \pi} q(p_e) \iff "
        r"\max_\pi \prod_{e \in \pi} (1 - p_e)"
    )
    st.markdown(
        r"""
        Como todos os custos são não negativos, o **Dijkstra** é aplicável.
        A chave da fila de prioridade é a tupla
        $(\text{risco acumulado}, \text{saltos})$, então, entre caminhos de
        mesmo risco, vence o mais curto. Os vizinhos são visitados em ordem de
        índice para que os empates sejam determinísticos.

        **Erro de um link.** Se existem os dois sentidos $a\to b$ e $b\to a$,
        a taxa usada é a média deles; se só existe um, usa-se esse valor.
        """
    )
    st.code(
        """para cada origem s do hardware:
    dist[s] ← (0, 0);  fila ← {(0, 0, s)}
    enquanto fila não vazia:
        (risco, saltos, u) ← extrai_mínimo(fila)
        se (risco, saltos) ≠ dist[u]: continue        # entrada obsoleta
        path_matrix[s][u] ← reconstrói caminho via pai[]
        para v em vizinhos_ordenados(u):
            cand ← (risco − ln(1 − p_uv), saltos + 1)
            se cand < dist[v]:
                dist[v] ← cand;  pai[v] ← u
                error_matrix[s][v] ← 1 − exp(−cand.risco)
                insere(fila, cand, v)""",
        language="text",
    )
    st.markdown(
        r"""
        **Saídas reutilizadas por todos os algoritmos:**

        - `path_matrix[a][b]`: sequência de qubits físicos do caminho escolhido.
        - `error_matrix[a][b]`: erro acumulado $1 - \prod(1-p_e)$ desse caminho.
        - Métricas por qubit físico: grau, distância média (em saltos), erro
          médio dos links adjacentes e erro médio dos caminhos. Pares
          inalcançáveis recebem penalidade máxima.

        **Complexidade:** $O\bigl(V\,(V+E)\log V\bigr)$ de tempo; matrizes
        $V\times V$ e até $O(V^3)$ de memória para guardar todos os caminhos.

        **Por que não Floyd–Warshall?** Ele resolveria o mesmo problema com a
        recorrência $D_{ij} \leftarrow \min(D_{ij}, D_{ir}+D_{rj})$, mas custa
        $O(V^3)$ independentemente da esparsidade. As topologias reais de
        hardware são esparsas (linha, anel, grid, heavy-hex), então $V$
        execuções de Dijkstra são mais baratas.
        """
    )

    st.divider()
    st.markdown("#### Estruturas do circuito")
    st.markdown(
        r"""
        Em uma única passada pelas operações de dois qubits, em ordem:

        - **Matriz de interações** $C_{ij}$: quantas portas envolvem os
          qubits lógicos $i$ e $j$.
        - **Grau** $G_q$ (parceiros distintos) e **interações** $N_q$ (total
          de portas) de cada qubit lógico.
        - **Grafo de dependências (DAG):** cada operação depende da última
          operação anterior em cada um dos seus dois operandos. A
          **profundidade** $D$ é o caminho mais longo desse DAG, calculado
          incrementalmente: $\text{prof}(v) = 1 + \max_{u \to v}
          \text{prof}(u)$.
        - **Pressão de profundidade** $\rho = (D-1)/(M-1)$, com $M$ o número
          de interações: $\rho \approx 0$ indica operações paralelizáveis e
          $\rho = 1$ indica uma cadeia totalmente serial.
        """
    )


# [IA] Claude Code (Claude Opus 5.5) – descrição do roteamento ordenado com SWAPs
def _show_routing() -> None:
    st.markdown(
        r"""
        Dado um mapeamento inicial $m$, o roteador percorre as operações **na
        ordem do circuito**, porque cada SWAP altera onde os próximos operandos
        estão:

        1. Busca as posições físicas atuais $a = m(q_1)$ e $b = m(q_2)$.
        2. Lê o caminho pré-computado $[v_0 = a, v_1, \dots, v_d = b]$.
        3. Insere $d-1$ SWAPs ao longo do caminho, levando o primeiro operando
           até $v_{d-1}$, vizinho de $b$. Cada SWAP troca os ocupantes lógicos
           (ou um qubit livre) das duas posições.
        4. Executa a porta no link $v_{d-1}\!-\!v_d$ e atualiza o mapeamento
           antes da próxima operação.
        """
    )
    st.code(
        """para cada operação (q1, q2) em ordem:
    caminho ← path_matrix[m(q1)][m(q2)]
    para cada link (a, b) nos d−1 primeiros passos do caminho:
        troca ocupantes de a e b em m;  swaps += 1
        sucesso *= (1 − p_ab)^3                       # SWAP = 3 portas
    sucesso *= (1 − p_link_final)                     # a porta do circuito
retorna swaps, 1 − sucesso, m_final""",
        language="text",
    )
    st.markdown(
        r"""
        **Modelo de erro:** falhas independentes; cada SWAP vale três portas de
        dois qubits no mesmo link. O erro estimado é
        $E = 1 - \prod_g (1-p_g)$.

        **Complexidade:** $O(M \cdot L)$ por avaliação, com $M$ operações e
        $L$ o comprimento máximo de caminho. Esse é o custo que domina as
        buscas, que chamam o roteador para cada candidato.

        **Limitações:** a política de SWAPs é fixa (sempre ao longo do caminho
        de menor erro, movendo o primeiro operando). Não considera erros de um
        qubit, leitura, decoerência, crosstalk ou direção das portas.
        """
    )


# [IA] Claude Code (Claude Opus 5.5) – descrição da busca exata
def _show_exact_search() -> None:
    st.markdown(
        r"""
        Enumera, por **busca em profundidade com backtracking**, todas as
        atribuições injetivas de $k$ qubits lógicos em $n$ físicos. A cada
        folha (mapeamento completo), roteia o circuito inteiro e mantém o
        melhor resultado segundo
        """
    )
    st.latex(
        r"m^\star = \arg\min_{\mathrm{lex}}\ "
        r"\bigl(E_{\mathrm{route}}(m),\ S_{\mathrm{route}}(m),\ "
        r"m(0), \dots, m(k-1)\bigr)"
    )
    st.markdown(
        r"""
        A tupla de índices físicos é o último critério de desempate, o que
        torna o resultado determinístico.
        """
    )
    st.code(
        """dfs(prefixo):
    se |prefixo| = k:
        r ← route_circuit(prefixo)
        melhor ← min(melhor, (r.erro, r.swaps, prefixo))
        retorna
    para cada físico i não usado:
        marca i;  dfs(prefixo + [i]);  desmarca i

# paralelização: um processo por escolha do 1º qubit lógico
melhor ← min(dfs([p]) para p em 0..n−1)   via ProcessPoolExecutor""",
        language="text",
    )
    st.markdown(
        r"""
        **Tamanho do espaço:** $|\mathcal{M}| = P(n,k) = \dfrac{n!}{(n-k)!}$.
        Por exemplo, 3 lógicos em 4 físicos geram 24 mapeamentos, mas 8 em 12
        já geram cerca de 20 milhões.

        **Complexidade:** $O\bigl(P(n,k) \cdot M \cdot L\bigr)$.

        **Garantia:** ótimo para o objetivo do roteador **sobre os mapeamentos
        iniciais**, mas não sobre todas as sequências possíveis de SWAPs.
        Serve como **referência de qualidade** para as heurísticas. No CLI,
        só é usada quando $P(n,k) < 10^8$; no benchmark, só em casos de até 4
        qubits lógicos.
        """
    )


# [IA] Claude Code (Claude Opus 5.5) – descrição da heurística multi-start com hill climbing
def _show_multistart() -> None:
    st.markdown(
        r"""
        Em vez de varrer todo o espaço, gera vários pontos de partida e
        refina cada um por busca local. Os candidatos são divididos igualmente
        entre três estratégias (o resto vai para a aleatória):
        """
    )
    st.markdown("#### Estratégias de início")
    random_column, degree_column, pair_column = st.columns(3)
    with random_column, st.container(border=True):
        st.markdown(
            """
            **🎲 Aleatória**

            Sorteia $k$ qubits físicos distintos sem reposição e os atribui
            aos lógicos em ordem. Garante diversidade.
            """
        )
    with degree_column, st.container(border=True):
        st.markdown(
            """
            **🔗 Por grau**

            Ordena os lógicos por (grau ↓, interações ↓) e os físicos por
            (grau ↓, erro médio de caminho ↑, distância média ↑) e pareia as
            duas listas: o qubit mais conectado vai para a posição mais
            central.
            """
        )
    with pair_column, st.container(border=True):
        st.markdown(
            """
            **⭐ Par mais frequente**

            Coloca o par lógico que mais interage no **link físico de menor
            erro**. Os demais são pareados por (interações ↓, grau ↓) com os
            físicos ordenados por (grau ↓, erro de caminho ↑).
            """
        )
    st.markdown(
        r"""
        Os inícios adicionais das estratégias determinísticas são
        **perturbações com seed fixa**: algumas vezes, um qubit lógico é movido
        para um físico aleatório e, se este estiver ocupado, os dois trocam de
        lugar.
        """
    )
    st.markdown("#### Busca local (hill climbing)")
    st.markdown("A cada iteração, avalia **toda a vizinhança** do mapeamento atual:")
    st.latex(
        r"\mathcal{N}_{\mathrm{swap}}(m) = \{ m^{i \leftrightarrow j} \}"
        r"\ \ \left(\tbinom{k}{2}\text{ vizinhos}\right), \qquad "
        r"\mathcal{N}_{\mathrm{move}}(m) = \{ m^{i \to p} : p \text{ livre} \}"
        r"\ \ \bigl(k(n-k)\text{ vizinhos}\bigr)"
    )
    st.markdown(
        r"""
        - **Troca** (inspirada no 2-opt): dois qubits lógicos trocam de
          posição física.
        - **Movimento:** um qubit lógico vai para um físico desocupado. Isso é
          específico do problema retangular $k \le n$.

        Cada vizinho é avaliado com o **roteamento completo**, com cache por
        mapeamento. O melhor vizinho que melhora estritamente o custo é aceito;
        se nenhum melhora, a busca para em um mínimo local.
        """
    )
    st.code(
        """inícios ← aleatórios ∪ grau(+perturbações) ∪ par_frequente(+perturbações)
para cada início m (em paralelo):
    repita:
        m' ← argmin_lex custo(v) para v em N_swap(m) ∪ N_move(m)
        se custo(m') < custo(m): m ← m'
        senão: pare                                   # mínimo local
finalistas ← mínimos locais ∪ inícios originais
retorna argmin_lex (erro, swaps, índices) dos finalistas""",
        language="text",
    )
    st.markdown(
        r"""
        **Complexidade:** por iteração,
        $O\bigl((\binom{k}{2} + k(n-k)) \cdot M \cdot L\bigr)$, multiplicada
        pelo número de iterações e de inícios. Termina sempre, porque o espaço
        é finito e só melhorias estritas são aceitas.

        **Garantia:** nenhuma de otimalidade global, mas os inícios variados
        reduzem a chance de ficar preso em um mínimo local ruim. Com seed fixa,
        o resultado é reprodutível mesmo com paralelismo.
        """
    )


# [IA] Claude Code (Claude Opus 5.5) – descrição do fluxo de custo mínimo
def _show_min_cost_flow() -> None:
    st.markdown(
        r"""
        Modela o placement inicial como uma **atribuição injetiva de custo
        mínimo** em uma rede de fluxo. Todas as arestas têm capacidade 1:
        """
    )
    st.code(
        """s ──(cap 1, custo 0)──▶ l_q ──(cap 1, custo C(q,Q))──▶ t_Q ──(cap 1, custo 0)──▶ t
     para cada lógico q        (todos os pares q, Q)           para cada físico Q""",
        language="text",
    )
    st.markdown(
        r"""
        A capacidade em $s\to l_q$ faz cada lógico ser atribuído uma única vez,
        e a capacidade em $t_Q\to t$ faz cada físico receber no máximo um
        lógico. Assim, **um fluxo de valor $k$ é exatamente um mapeamento
        injetivo completo**, e o fluxo de custo mínimo resolve:
        """
    )
    st.latex(
        r"\min \sum_{q,Q} C(q,Q)\,x_{qQ}"
        r"\quad\text{s.a.}\quad \sum_Q x_{qQ} = 1,\ \ \sum_q x_{qQ} \le 1,"
        r"\ \ x_{qQ}\in\{0,1\}"
    )

    st.markdown("#### Custo de atribuição")
    st.markdown(
        r"""
        Com a normalização limitada $R(x,M)=\min(1, x/M)$, a **importância**
        de um qubit lógico combina grau e volume de interações:
        $I_q = \tfrac12 R(G_q, G_{\max}) + \tfrac12 R(N_q, N_{\max})$.
        Três penalidades medem o quanto o físico $Q$ é adequado para $q$:
        """
    )
    st.latex(
        r"""
        \begin{aligned}
        P_{\mathrm{grau}} &= R\bigl(\max(0,\ G_q - d_Q),\ G_{\max}\bigr)
            && \text{físico com vizinhos insuficientes}\\
        P_{\mathrm{dist}} &= I_q \cdot R(\bar d_Q,\ \bar d_{\max})
            && \text{físico longe do resto do chip}\\
        P_{\mathrm{erro}} &= I_q \cdot \bigl[0{,}7\,R(\bar p_Q,\ \bar p_{\mathrm{global}})
            + 0{,}3\,R(\bar e_Q,\ \bar e_{\max})\bigr]
            && \text{links adjacentes e caminhos ruidosos}
        \end{aligned}
        """
    )
    st.latex(
        r"C(q,Q) = w_{\mathrm{grau}}P_{\mathrm{grau}} + "
        r"w_{\mathrm{dist}}P_{\mathrm{dist}} + w_{\mathrm{erro}}P_{\mathrm{erro}}"
    )
    st.markdown(
        r"""
        **Pesos adaptativos.** Os pesos são interpolados pela pressão de
        profundidade $\rho$ do circuito:
        """
    )
    st.latex(
        r"\mathbf{w} = (1-\rho)\,(0{,}2;\ 0{,}2;\ 0{,}6) + "
        r"\rho\,(0{,}45;\ 0{,}35;\ 0{,}2)"
    )
    st.markdown(
        r"""
        Circuitos paralelos ($\rho\approx0$) priorizam **erro**; circuitos
        seriais ($\rho\approx1$) dão mais peso a **grau e distância**, porque
        cada SWAP atrasa toda a cadeia seguinte.
        """
    )
    st.markdown("#### Resolução por caminhos aumentantes")
    st.markdown(
        r"""
        O algoritmo mantém um **grafo residual** (aresta reversa com custo
        $-c$, que permite desfazer atribuições anteriores) e, a cada rodada,
        encontra o caminho $s \to t$ mais barato e empurra uma unidade de
        fluxo. Para usar Dijkstra mesmo com custos negativos nas arestas
        reversas, aplica **potenciais de vértice** (técnica de Johnson):
        """
    )
    st.latex(
        r"c^{\pi}(u,v) = c(u,v) + \pi(u) - \pi(v) \ \ge 0, \qquad "
        r"\pi(v) \leftarrow \pi(v) + \operatorname{dist}(v)"
    )
    st.code(
        """constrói residual: aresta (u→v) cap 1 custo c;  reversa (v→u) cap 0 custo −c
π ← 0
repita:
    dist ← Dijkstra(s) sobre custos reduzidos c + π(u) − π(v), arestas com cap > 0
    se t inalcançável: pare
    π(v) += dist(v) para todo v alcançado
    empurra 1 unidade no caminho s → t;  fluxo += 1;  custo += Σ c
mapeamento ← arestas l_q → t_Q saturadas
mapeamento ← hill_climb(mapeamento)                  # refino com custo roteado""",
        language="text",
    )
    st.markdown(
        r"""
        **Complexidade:** $k$ aumentos, cada um com Dijkstra em um grafo de
        $k+n+2$ vértices e $O(kn)$ arestas, ou seja, $O\bigl(k \cdot kn
        \log(k+n)\bigr)$. É **polinomial** e não depende de $P(n,k)$.

        **Garantia e limitações:** a atribuição é ótima **para o custo
        heurístico $C(q,Q)$**, que é construído a partir de resumos por qubit
        e não otimiza diretamente a adjacência entre pares que interagem nem
        os SWAPs. Por isso, o resultado é refinado pelo mesmo hill climbing da
        heurística multi-start, agora com o custo roteado real. O fluxo
        funciona como um **ponto de partida informado e barato** para a busca
        local.
        """
    )


# [IA] Claude Code (Claude Opus 5.5) – descrição do baseline Qiskit SABRE
def _show_sabre() -> None:
    st.markdown(
        """
        Não foi desenvolvido no projeto; serve como **referência externa** para
        comparar os métodos acima com um transpiler amplamente usado.

        - `SabreLayout` escolhe o layout inicial (seed fixa, uma tentativa).
        - `SabreSwap` com a heurística `decay` insere os SWAPs. Ele olha uma
          janela de portas futuras em vez de seguir um caminho fixo.
        - Recebe as mesmas interações de dois qubits, representadas como `cx`
          e na mesma ordem. O erro é avaliado com o mesmo modelo
          (SWAP = 3 portas).

        Diferença principal: o SABRE decide os SWAPs **dinamicamente**,
        enquanto os métodos do projeto otimizam o **placement inicial** e
        usam uma política de roteamento fixa.
        Documentação: [SabreLayout](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.transpiler.passes.SabreLayout).
        """
    )


# [IA] Claude Code (Claude Opus 5.5) – abas dos algoritmos e tabela de resumo comparativo
def _show_algorithms() -> None:
    st.divider()
    st.subheader(":blue[Algoritmos desenvolvidos]")
    st.caption(
        "Cada aba descreve o algoritmo como implementado no código, com "
        "pseudocódigo, complexidade e garantias."
    )
    tabs = st.tabs(
        [
            "1 · Pré-processamento",
            "2 · Roteamento",
            "3 · Busca exata",
            "4 · Multi-start",
            "5 · Fluxo de custo mínimo",
            "Baseline: SABRE",
        ]
    )
    sections = (
        _show_preprocessing,
        _show_routing,
        _show_exact_search,
        _show_multistart,
        _show_min_cost_flow,
        _show_sabre,
    )
    for tab, section in zip(tabs, sections):
        with tab:
            section()

    st.markdown("#### Resumo comparativo")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Método": "Busca exata",
                    "Ideia": "Enumera todos os placements (DFS)",
                    "Otimiza": "Erro roteado, depois SWAPs",
                    "Garantia": "Ótimo entre placements iniciais",
                    "Custo": "P(n,k) · roteamento",
                    "Uso": "Referência em casos pequenos",
                },
                {
                    "Método": "Multi-start + hill climbing",
                    "Ideia": "Inícios variados + busca local troca/movimento",
                    "Otimiza": "Erro roteado, depois SWAPs",
                    "Garantia": "Mínimo local",
                    "Custo": "inícios · iterações · (k²+kn) · roteamento",
                    "Uso": "Casos médios e grandes",
                },
                {
                    "Método": "Fluxo min-cost + hill climbing",
                    "Ideia": "Atribuição ótima por custo heurístico + refino",
                    "Otimiza": "C(q,Q), depois erro roteado",
                    "Garantia": "Ótimo para C(q,Q); mínimo local no final",
                    "Custo": "Polinomial + um hill climbing",
                    "Uso": "Início informado e barato",
                },
                {
                    "Método": "Qiskit SABRE",
                    "Ideia": "Layout e SWAPs com lookahead",
                    "Otimiza": "Heurística própria do Qiskit",
                    "Garantia": "Nenhuma (heurística)",
                    "Custo": "Quase linear nas portas",
                    "Uso": "Baseline de mercado",
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )


# [IA] Claude Code (Claude Opus 5.5) – montagem da página de apresentação
def show_presentation(
    circuits: pd.DataFrame,
    topologies: pd.DataFrame,
    benchmarks: pd.DataFrame,
) -> None:
    _show_problem()
    _show_pipeline()
    _show_algorithms()

    st.divider()
    st.subheader(":blue[Dados e navegação]")
    columns = st.columns(4)
    columns[0].metric("Circuitos", f"{len(circuits):,}")
    columns[1].metric("Topologias", f"{len(topologies):,}")
    columns[2].metric(
        "Famílias de circuitos",
        f"{circuits['categoria'].nunique():,}",
    )
    columns[3].metric(
        "Famílias de hardware",
        f"{topologies['categoria'].nunique():,}",
    )
    if not benchmarks.empty:
        st.caption(
            f"{len(benchmarks):,} execuções de benchmark pré-computadas "
            "disponíveis para comparação."
        )

    st.markdown(
        """
        - **Caso selecionado:** escolha um circuito e uma topologia para ver as
          métricas dos grafos, gerar suas visualizações e comparar os
          mapeamentos de cada algoritmo.
        - **Comparação de algoritmos:** compare SWAPs, erro estimado e tempo
          por topologia, tamanho do circuito e execução.
        """
    )
    st.info(
        "O erro estimado vem de um modelo com taxas sintéticas e falhas "
        "independentes; não inclui erros de um qubit, leitura, decoerência "
        "ou crosstalk, e não é uma medição em hardware real."
    )
