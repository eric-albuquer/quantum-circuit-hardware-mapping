# Datasets de circuitos quânticos e topologias

**Documentation:** [English](README.md)

Este repositório prepara dados para um projeto de algoritmos em grafos com
dois objetivos relacionados: atender aos requisitos algorítmicos em um grafo
dirigido e ponderado de grande porte e estudar como as interações dos
circuitos quânticos se relacionam com a conectividade do hardware. A proposta
integra a geração de datasets quânticos e o resumo das interações entre
qubits lógicos com algoritmos de grafos, posicionamento físico, experimentos
de roteamento, relatórios e visualizações analíticas.

## Pergunta de pesquisa e problema

Um circuito descreve **qubits lógicos** e operações entre eles. Um dispositivo
quântico possui **qubits físicos** conectados de acordo com uma topologia de
acoplamento. Uma operação lógica entre dois qubits só pode ser executada
diretamente se os qubits físicos associados aos operandos tiverem uma conexão
compatível no hardware. Caso contrário, o roteamento precisa mover estados
lógicos pelo grafo de hardware, normalmente inserindo portas SWAP.

A pergunta de pesquisa é: **Como os padrões de interação dos circuitos e a
conectividade/custo do hardware afetam o posicionamento de qubits lógicos e o
custo de roteamento, e quais algoritmos de grafos podem sugerir
posicionamentos e rotas com menos SWAPs?**

A comparação futura deve medir quantidade de SWAPs inseridos, comprimento das
rotas, profundidade do circuito compilado e — somente com um modelo de custo
explicitado — exposição a erros do hardware. Um posicionamento é uma função
injetiva dos qubits lógicos nos físicos. Uma solução de roteamento também
precisa respeitar a ordem das operações e atualizar o posicionamento vigente
à medida que o circuito é executado. Caminhos mínimos estáticos podem sugerir
rotas, mas não resolvem sozinhos o problema dinâmico completo de roteamento
com múltiplos qubits.

## Modelos de grafo e classificação

| Modelo | Vértices | Arestas | Classificação e pesos |
| --- | --- | --- | --- |
| Grafo de interações do circuito (um grafo por circuito) | Qubits lógicos, identificados pelos índices do QASM | Um par é uma aresta quando tem ao menos uma instrução de dois qubits; o CSV também registra pares com zero interações | Simples, sem laços, não dirigido, ponderado e não necessariamente conexo. O peso inteiro é a quantidade de instruções de dois qubits do par; é não negativo. Direção, tipo e ordem temporal das portas são agregados. |
| Grafo de acoplamento do hardware (um grafo por topologia) | Qubits físicos de um `CouplingMap` do Qiskit | Arcos direcionados para os acoplamentos permitidos entre origem e destino | Simples, dirigido, ponderado, estático e atualmente conexo nas topologias geradas. JSON/CSV armazenam taxas sintéticas positivas de erro de porta e fidelidades derivadas; arcos recíprocos podem ter valores sintéticos diferentes. Não há pesos negativos. |

Os grafos de circuito e de hardware têm domínios de vértices diferentes:
qubits **lógicos** versus qubits **físicos**. Não devem ser tratados como um
único grafo nem comparados pela igualdade de índices sem definir um
posicionamento.

### Implementação futura dos algoritmos de grafos

Implementar os algoritmos do grupo em `src/graphs/algorithms.py` e reutilizar
essa implementação nas duas frentes de análise, em vez de usar o algoritmo de
uma biblioteca como implementação entregue:

1. **BFS e DFS:** implementar percursos sobre listas de adjacência dirigidas,
   explicitar a regra de alcançabilidade em grafos dirigidos e executar cada
   algoritmo a partir de pelo menos três vértices de origem documentados.
   Usá-los para alcançabilidade e exploração da topologia, não como
   algoritmos de caminho mínimo ponderado.
2. **Dijkstra:** implementar e validar caminhos mínimos para custos não
   negativos; relatar pelo menos cinco pares origem/destino. No hardware,
   custo unitário por aresta responde à pergunta de menor número de saltos;
   um custo não negativo de erro de porta documentado responde a outra
   pergunta de rota ponderada.
3. **Bellman–Ford:** implementar caminhos mínimos no dataset principal
   positivo e validar separadamente a detecção de ciclo negativo em um
   pequeno grafo sintético com uma construção de aresta/ciclo negativo
   documentada, se exigido. Não introduzir pesos negativos sem explicação no
   dataset real nem interpretar custos negativos sintéticos como taxas de
   erro físico.
4. **Árvore geradora mínima (MST):** usar somente em um grafo explicitamente
   não dirigido, conexo e ponderado. O grafo de interações do circuito é uma
   entrada exploratória natural. Para usar uma topologia dirigida de hardware,
   primeiro é necessária uma projeção não dirigida com regra declarada para
   agregar os custos dos arcos recíprocos. A MST é uma espinha dorsal conexa
   de custo mínimo, não uma solução de roteamento: as arestas de hardware
   omitidas continuam existindo, e as rotas não devem ser restringidas à
   árvore a menos que isso seja um experimento separado.
5. **Posicionamento e roteamento:** desenvolver posicionamentos-base (por
   exemplo, associação gulosa baseada em frequência/grau) e compará-los com
   alternativas. Roteirizar as interações do circuito por caminhos no
   hardware, acompanhando a evolução do mapeamento lógico-físico. Otimizar
   primeiro um objetivo declarado, como o número de SWAPs; analisar
   profundidade e erro sintético separadamente, em vez de misturar unidades
   incompatíveis em um peso sem justificativa.

Usar e testar essas implementações no grafo grande escolhido quando o tipo
de grafo permitir e nos grafos de circuito/hardware quando a pergunta fizer
sentido. Registrar combinações incompatíveis em vez de mudar silenciosamente
a direção do grafo ou o significado dos pesos.

### Checkpoint e entregáveis de análise

Antes de usar o dataset grande da atividade, documentar e obter aprovação
para sua fonte, `|V|`, `|E|`, tipo do grafo, significado/origem dos pesos,
presença de pesos negativos e pergunta de pesquisa. O grafo não aéreo
escolhido, dirigido e ponderado deve conter pelo menos 20 mil arestas, ou o
projeto deve fornecer um script de download reproduzível. Se o caso com ciclo
negativo do Bellman–Ford for necessário, manter seu pequeno grafo de teste
sintético separado desse dataset.

A etapa de análise futura deve produzir:

- Casos exigidos de BFS/DFS, pelo menos cinco pares para Dijkstra e casos de
  Bellman–Ford com e sem ciclo negativo.
- `out/parte2/parte2_report.json`, com casos, metadados dos grafos e tempos
  médios de pelo menos cinco execuções; incluir escalabilidade em três
  tamanhos de grafo e documentar o método de cronometragem.
- Gráficos comparativos de tempo, comportamento dos algoritmos e caminhos.
- Pelo menos quatro visualizações AVD (análise visual de dados): duas
  exploratórias e duas explanatórias, cada uma acompanhada de notas
  analíticas.
- Discussão crítica em PDF sobre adequação dos algoritmos, pressupostos,
  complexidade, direção e pesos dos grafos e limitações ao transferir os
  resultados para posicionamento/roteamento quântico.

## Estrutura do repositório

```text
analysis/
  generate_algorithm_interactions.py
  interactions.py
dataset_generation/
  benchmarks.py
  random_circuits.py
  weighted_topologies.py
  paths.py
datasets/
  algorithms/
    <benchmark>/*.qasm
    random/*.qasm
  topologies/<topology>/*_weighted.json
  topologies/<topology>/*_weighted_edges.csv
  interaction_analysis/algorithms/<categoria>/pair_interactions.csv
docs/
  assets/ghz_5qubits_qiskit.txt
```

Os dados gerados são separados por categoria e, quando útil, por benchmark ou
topologia. A análise de interações fica separada dos circuitos QASM originais
e dos geradores.

## Inventário dos datasets

O snapshot atual contém:

| Dataset | Conteúdo | Quantidade atual |
| --- | --- | ---: |
| Circuitos de algoritmos | Circuitos do MQT Bench em OpenQASM 2, agrupados por benchmark | 516 circuitos em 28 pastas de benchmark |
| Circuitos aleatórios | Circuitos gerados em OpenQASM 3 | 15 circuitos: 4, 6, 8, 10 e 12 qubits nas profundidades 10, 20 e 30 |
| Topologias ponderadas | Metadados JSON e listas de arestas CSV | 63 mapas de acoplamento, cada um representado nos dois formatos (126 arquivos) |
| Interações por pares | Um CSV por categoria/algoritmo, derivado dos circuitos QASM | 29 CSVs e 75.767 linhas circuito/par |

Essas quantidades descrevem o snapshot atual. A disponibilidade de benchmarks
pode variar conforme as versões do MQT Bench e os tamanhos de circuito
suportados.

### Circuitos de algoritmos

Os circuitos são obtidos do
[MQT Bench](https://www.cda.cit.tum.de/mqtbench/) no nível algorítmico (`ALG`)
e gravados como arquivos QASM 2. O intervalo solicitado é de 3 a 30 qubits,
sujeito aos tamanhos suportados por cada benchmark e aos limites de geração.
Exemplos incluem `ghz`, `qft`, `qaoa`, `grover`, somadores e algoritmos
variacionais.

Exemplo de diretório e arquivo:

```text
datasets/algorithms/ghz/ghz_5qubits.qasm
```

### Circuitos aleatórios

Os circuitos aleatórios são gerados com `random_circuit` do Qiskit, limitados
a operandos de até dois qubits e serializados em QASM 3. A configuração atual
usa 5 quantidades de qubits (4 a 12, de 2 em 2) e 3 profundidades (10, 20 e
30). O `id` no nome de arquivo identifica a posição da profundidade na
configuração; não representa amostras repetidas com a mesma profundidade.

Não há uma semente aleatória definida para os circuitos; portanto, a geração
novamente pode produzir circuitos diferentes.

### Datasets de topologias de hardware

Cada topologia é gerada com `CouplingMap` do Qiskit. O conjunto atual contém
63 mapas:

| Topologia | Configurações | Representação |
| --- | --- | --- |
| `line` | 3 a 19 qubits | Cada qubit interno se conecta aos vizinhos imediatos; cada extremidade tem um vizinho. |
| `ring` | 3 a 19 qubits | Uma linha com uma conexão adicional entre as extremidades. |
| `full` | 3 a 19 qubits | Todos os pares de qubits físicos são conectados; serve como referência de conectividade densa. |
| `grid` | 3×3, 4×4, 5×5, 8×8 e 10×10 | Grade bidimensional com conexões entre vizinhos imediatos. |
| `heavy_hex` | Distâncias 3, 5, 7 e 9 | Topologia esparsa heavy-hex. |
| `heavy_square` | Distâncias 3, 5 e 7 | Topologia esparsa heavy-square. |

Os mapas heavy-hex no snapshot atual têm 19, 57, 115 e 193 qubits; os mapas
heavy-square têm 21, 65 e 133 qubits. Os tamanhos são definidos pelos
construtores de topologia do Qiskit.

Exemplo de diretório:

```text
datasets/topologies/grid/
  grid_3x3_9qubits_weighted.json
  grid_3x3_9qubits_weighted_edges.csv
```

O JSON contém:

- `architecture_type`: nome da topologia.
- `num_qubits`: quantidade de qubits físicos.
- `qubit_properties`: `readout_error`, `readout_fidelity` e
  `t1_coherence_us` de cada qubit.
- `coupling_map_weighted`: entradas direcionadas de origem/destino com
  `gate_error_rate` e `gate_fidelity`.

O CSV contém a lista de arestas ponderadas do mapa de acoplamento. Os mapas
retornados pelo Qiskit são direcionados; por isso, uma conexão física
bidirecional normalmente aparece como duas entradas direcionadas.

**Importante:** os valores de erro e coerência do hardware são amostras
sintéticas, não medições de um processador quântico real. Erros de leitura e
de portas de dois qubits são amostrados de distribuições log-normais
limitadas; os tempos T1 são amostrados de uma distribuição normal limitada.
Os dados não incluem T2, duração das portas, data de calibração ou origem em
um dispositivo real. As sementes são derivadas do identificador da topologia,
tornando reprodutíveis as propriedades sintéticas de uma mesma topologia.

### Dataset de interações por pares

Gere os dados de interação com:

```powershell
python -m analysis.generate_algorithm_interactions
```

Para cada circuito QASM, a análise conta as instruções de dois qubits de cada
par não ordenado de qubits lógicos. Pares que nunca interagem são incluídos
com contagem zero. É gravado um CSV por benchmark ou categoria de circuito:

```text
datasets/interaction_analysis/algorithms/ghz/pair_interactions.csv
datasets/interaction_analysis/algorithms/random/pair_interactions.csv
```

| Coluna | Significado |
| --- | --- |
| `algorithm` | Pasta do benchmark / identificador do algoritmo. |
| `circuit` | Nome do arquivo do circuito sem a extensão `.qasm`. |
| `num_qubits` | Quantidade de qubits lógicos do circuito. |
| `qubit_1`, `qubit_2` | Par não ordenado de qubits lógicos, com `qubit_1 < qubit_2`. |
| `interaction_count` | Quantidade de instruções de dois qubits que envolvem o par. |

Este é um resumo lógico das interações, não um resultado de mapeamento físico.
Todos os tipos de instrução de dois qubits são contados juntos, sem distinguir
a direção da porta ou a ordem das operações; portas com mais de dois qubits
não são convertidas em interações por pares. Pares de um qubit consigo mesmo
não são incluídos.

## Início rápido

Use Python 3.12 ou uma versão compatível. Na raiz do projeto, no PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
python -m dataset_generation --help
```

Para criar um ambiente novo, instale os pacotes utilizados pelos geradores:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install qiskit mqt.bench numpy pandas
```

Gere os três datasets de origem:

```powershell
python -m dataset_generation
```

Gere apenas uma categoria:

```powershell
python -m dataset_generation algorithms
python -m dataset_generation random
python -m dataset_generation topologies
```

Gere ou atualize os CSVs de interações por pares depois que os arquivos QASM
dos algoritmos estiverem disponíveis:

```powershell
python -m analysis.generate_algorithm_interactions
```

Consulte as interações de um arquivo QASM ou de todos os arquivos QASM dentro
de um diretório:

```powershell
python -m analysis.interactions datasets/algorithms/ghz/ghz_5qubits.qasm
python -m analysis.interactions datasets/algorithms/ghz
python -m analysis.interactions datasets/algorithms/random
```

Os exemplos de caminho usam barras normais, aceitas pelo Python no Windows;
no PowerShell também é possível usar barras invertidas.

## Ilustração de circuito gerada pelo Qiskit

O diagrama abaixo é o circuito GHZ de cinco qubits gerado diretamente a
partir de [`ghz_5qubits.qasm`](datasets/algorithms/ghz/ghz_5qubits.qasm)
com o desenhador textual do Qiskit. O texto UTF-8 gerado também está em
[`docs/assets/ghz_5qubits_qiskit.txt`](docs/assets/ghz_5qubits_qiskit.txt).

```text
                            ┌───┐ ░ ┌─┐            
   q_0: ────────────────────┤ X ├─░─┤M├────────────
                       ┌───┐└─┬─┘ ░ └╥┘┌─┐         
   q_1: ───────────────┤ X ├──■───░──╫─┤M├─────────
                  ┌───┐└─┬─┘      ░  ║ └╥┘┌─┐      
   q_2: ──────────┤ X ├──■────────░──╫──╫─┤M├──────
             ┌───┐└─┬─┘           ░  ║  ║ └╥┘┌─┐   
   q_3: ─────┤ X ├──■─────────────░──╫──╫──╫─┤M├───
        ┌───┐└─┬─┘                ░  ║  ║  ║ └╥┘┌─┐
   q_4: ┤ H ├──■──────────────────░──╫──╫──╫──╫─┤M├
        └───┘                     ░  ║  ║  ║  ║ └╥┘
meas: 5/═════════════════════════════╩══╩══╩══╩══╩═
                                     0  1  2  3  4 
```

## Ferramentas

| Ferramenta | Uso no projeto |
| --- | --- |
| Python | Execução dos geradores e da análise. |
| Qiskit | Circuitos quânticos, serialização/leitura OpenQASM, circuitos aleatórios, mapas de acoplamento e visualização de circuitos. |
| MQT Bench | Fonte dos circuitos de benchmark estruturados. |
| NumPy | Geração de propriedades sintéticas das topologias e matrizes de interação. |
| pandas | Listas de arestas em CSV, datasets de interação e saída tabular. |
| Qiskit Aer | Disponível no ambiente de desenvolvimento para futuras simulações; os scripts atuais de geração e análise não o utilizam. |

O ambiente de desenvolvimento atual foi validado com Python 3.12.1, Qiskit
2.5.2, MQT Bench 2.3.0, NumPy 2.5.4 e pandas 3.0.6.

## Próximas análises sugeridas

- Comparar tamanho, densidade, distribuições de grau, centralidade e pesos de
  interação dos grafos de circuitos e de hardware.
- Testar posicionamentos iniciais de qubits lógicos e heurísticas de
  roteamento em cada topologia.
- Registrar SWAPs inseridos, quantidade de portas de dois qubits após
  compilação, profundidade, tempo de compilação e proxies de erro/fidelidade
  definidos explicitamente.
- Comparar roteamento que considera apenas a topologia com roteamento que
  considera propriedades sintéticas das conexões, mantendo separadas as
  conclusões sintéticas e as de dispositivos reais.
- Separar os experimentos por circuito, e não por linha de par, para evitar
  que linhas do mesmo circuito apareçam simultaneamente nos conjuntos de
  treino e teste.

Esses itens são possibilidades de pesquisa, não resultados já produzidos por
este repositório.
