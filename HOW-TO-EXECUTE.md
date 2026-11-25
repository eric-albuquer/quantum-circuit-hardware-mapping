* [ ] 

# Mapeamento de Circuitos Quânticos em Hardware (Grafos) + Análise e Visualização de Dados

Projeto final de Teoria dos Grafos + Análise e Visualização de Dados (AVD) — 2026.2.

Estuda como os padrões de interação de um circuito quântico e a conectividade do
hardware afetam a **alocação** dos qubits lógicos nos qubits físicos e o custo de
**roteamento** (SWAPs inseridos). O problema é modelado com dois grafos (o de
interações do circuito e o de acoplamento do hardware), e algoritmos de grafos
buscam alocações e rotas com menos SWAPs e menor erro estimado.

> **Os requisitos do projeto estão concentrados na aplicação Streamlit.**
> Apresentação do problema, EDA, execução dos algoritmos, comparação e análise
> AVD ficam todos em `analysis/streamlit_app.py`. Para avaliar o projeto, basta
> instalar as dependências e abrir o app (veja [Como executar](#como-executar)).

## Requisitos

- Python 3.12 (ou compatível)
- Dependências em `requirements-analysis.txt`: matplotlib, networkx, numpy,
  pandas, qiskit e streamlit

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements-analysis.txt
```

Só é necessário para **regerar** os datasets (os dados já estão no repositório):

```bash
pip install qiskit_qasm3_import mqt.bench
```

Para rodar os testes: `pip install pytest`.

> O networkx é usado apenas como apoio na análise e nos testes. Os algoritmos de
> alocação e roteamento do projeto estão em `src/`.

## Como executar

Execute sempre a partir da raiz do projeto.

### 1. Aplicação Streamlit (principal)

```bash
python -m streamlit run analysis/streamlit_app.py
```

O app abre no navegador (por padrão em `http://localhost:8501`). Ele lê os dados
pré-computados em `datasets/` e `out/parte2/`, então não exige nenhuma etapa
anterior. Para recarregar após editar o código, use "Rerun" ou "Always rerun" no
menu do app.

### 2. Demais comandos (opcionais, para regerar dados e saídas)

```bash
python -m src.mapping_flow                 # mapeia um circuito em uma topologia (fluxo de custo mínimo)
python -m src.mapping                      # busca exata/heurística de alocação (CLI)
python -m analysis.benchmark_mappers       # gera out/parte2/mapping_benchmarks.csv
python -m analysis.visualize_avd           # gera as figuras e métricas em out/parte2/
python -m analysis.generate_algorithm_interactions   # interações por par de qubits
python -m analysis.generate_ordered_interactions     # interações em ordem de execução
python -m dataset_generation               # gera circuitos, topologias e interações base
```

Exemplos com parâmetros:

```bash
python -m src.mapping_flow \
  --circuit datasets/interaction_order/algorithms/ghz/ghz_3qubits_ordered_interactions.csv \
  --topology datasets/topologies/full/full_4qubits_weighted_edges.csv

python -m analysis.benchmark_mappers --runs 3 --circuit-family qaoa --topology-family grid
python -m analysis.visualize_avd --circuit modular_adder_6qubits --topology line_6qubits
```

## Aplicação Streamlit

O app tem cinco abas:

| Aba                                  | O que mostra                                                                                                                                                                                                                  |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Apresentação**             | O problema, os dois grafos (interações e acoplamento), o pipeline do projeto e os algoritmos desenvolvidos.                                                                                                                 |
| **EDA**                        | Exploração dos datasets: famílias de circuitos e de hardware, escala, métricas e distribuições.                                                                                                                         |
| **Caso selecionado**           | Escolha de um circuito e de uma topologia, métricas e matrizes dos grafos, perfil por qubit e resultados dos algoritmos. A aba **Executar agora** roda os quatro métodos na hora, em vez de ler o CSV pré-computado. |
| **Comparação de algoritmos** | Resultados agregados do benchmark, com filtros por etapa (família de circuito, topologia, número de qubits) e gráficos de SWAPs medianos, erro estimado e tempo.                                                           |
| **Análise AVD**               | Visualizações exploratórias e explanatórias, com as análises correspondentes.                                                                                                                                            |

Detalhes de uso:

- Os filtros das abas **Caso selecionado** e **Comparação de algoritmos** são
  escolhidos em etapas (família do circuito → circuito → arquitetura → topologia).
- Em **Executar agora** o usuário define número de execuções, candidatos do
  multi-start, semente inicial e o limite de alocações da busca exata. A execução
  roda em um processo separado (`python -m analysis.live_run`), porque o Qiskit
  derrubava o interpretador quando chamado na thread do Streamlit. Casos com mais
  de 500 (qubits lógicos × físicos) pedem confirmação explícita.
- Resultados ao vivo ficam só na sessão e **não** sobrescrevem
  `out/parte2/mapping_benchmarks.csv`.
- O tema azul do app está em `.streamlit/config.toml`.

## Algoritmos comparados

| Método                                | Ideia                                                                                                                    |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Busca exata                            | Testa todas as alocações; só roda para casos pequenos (limite configurável).                                         |
| Multi-start                            | Heurística com várias alocações iniciais, melhoradas por busca local e ranqueadas pelo roteador.                     |
| Fluxo de custo mínimo + hill climbing | Alocação inicial por fluxo máximo de custo mínimo, refinada por hill climbing e aceita só se melhorar o roteamento. |
| Qiskit SABRE                           | Referência de mercado para comparação.                                                                                |

As métricas são SWAPs inseridos, erro estimado e tempo de execução. O erro usa
taxas **sintéticas** por conexão de hardware, não medições de dispositivos reais.

## Estrutura

```
.
├── analysis/
│   ├── streamlit_app.py                    # aplicação Streamlit (ponto de entrada)
│   ├── presentation.py                     # aba "Apresentação"
│   ├── avd_tab.py                          # aba "Análise AVD"
│   ├── live_run.py                         # execução ao vivo de um caso (subprocesso)
│   ├── labels.py                           # nomes legíveis dos datasets
│   ├── benchmark_mappers.py                # benchmark dos métodos de alocação
│   ├── visualize_avd.py                    # figuras, métricas e notas de AVD
│   ├── interactions.py                     # interações de um circuito QASM
│   ├── generate_algorithm_interactions.py  # interações por par (CSV)
│   └── generate_ordered_interactions.py    # interações em ordem (CSV)
├── src/
│   ├── circuit_graph/                      # grafo de interações do circuito (graph, loader)
│   ├── topology_graph/                     # grafo de acoplamento do hardware (graph, loader)
│   ├── mapping.py                          # busca exata e heurística de alocação
│   ├── mapping_common.py                   # validação, roteamento e hill climbing
│   └── mapping_flow.py                     # alocação por fluxo de custo mínimo
├── dataset_generation/                     # geração de circuitos, topologias e aleatórios
├── datasets/
│   ├── algorithms/                         # circuitos QASM (MQT Bench e aleatórios)
│   ├── topologies/                         # topologias ponderadas (JSON e CSV)
│   ├── interaction_analysis/               # interações por par de qubits
│   └── interaction_order/                  # interações em ordem de execução
├── out/parte2/                             # saídas geradas (figuras, métricas, benchmark, notas)
├── tests/                                  # testes (pytest)
├── docs/                                   # enunciado, critérios e material de apoio
├── .streamlit/config.toml                  # tema do app
├── README.md                               # documentação técnica detalhada
└── requirements-analysis.txt
```

O `README.md` descreve em detalhe os modelos de grafos, a formulação matemática da
alocação, o modelo de erro e o inventário dos datasets. O `analysis/README.md`
documenta as análises e o benchmark.

## Datasets

| Dataset                 | Origem                                                       | Conteúdo                                               |
| ----------------------- | ------------------------------------------------------------ | ------------------------------------------------------- |
| Circuitos de algoritmos | **Reais** (MQT Bench, nível algorítmico, OpenQASM 2) | 516 circuitos em 28 famílias                           |
| Circuitos aleatórios   | Gerados (Qiskit)                                             | 15 circuitos (4 a 12 qubits, profundidades 10, 20 e 30) |
| Topologias de hardware  | Estrutura real, **erros sintéticos**                  | 63 mapas de acoplamento (JSON e CSV)                    |
| Interações por par    | Derivado dos circuitos                                       | 29 CSVs                                                 |
| Interações em ordem   | Derivado dos circuitos                                       | 531 CSVs                                                |

A estrutura dos circuitos é real. As taxas de erro das conexões de hardware são
sintéticas (mediana de 0,15%, limitadas entre 0,02% e 1%). Conclusões sobre erro
valem para o modelo adotado, não para dispositivos reais.

## Testes

```bash
python -m pytest                                      # todos os testes
python -m pytest tests/test_mapping.py                # alocação e roteamento
python -m pytest tests/test_mapping_max_flow_min_cost.py  # fluxo de custo mínimo
python -m pytest tests/test_benchmark_mappers.py      # benchmark
python -m pytest tests/test_live_run.py               # execução ao vivo
python -m pytest tests/test_interactions.py           # interações dos circuitos
python -m pytest tests/test_visualize_avd_metrics.py  # métricas de AVD
python -m pytest tests/test_weighted_topologies.py    # topologias ponderadas
python -m pytest tests/test_labels.py                 # nomes dos datasets
```

## Declaração de uso de IA

[Documento de declaração de uso de IA](https://docs.google.com/document/d/1a_AzeSNbBuQOpufTuFRQ0rQSwkhV5YSE/edit?usp=sharing&ouid=115450337528857953689&rtpof=true&sd=true)

Os trechos de código com apoio de IA estão marcados no código com
`# [IA] <ferramenta> – <finalidade>`.

* [ ] Integrantes

Amanda Luz
Caio Almeida
Eric Albuquerque
Gabriel Aniceto
Mircio Ferreira
