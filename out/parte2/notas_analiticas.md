# Notas analíticas das visualizações

Os gráficos usam os CSVs pré-computados em `datasets/`; não executam algoritmos de mapeamento nem estimam tempos de execução. Os pesos das interações são contagens de gates de dois qubits. Os pesos do hardware são taxas de erro sintéticas.

## 1. `01_escala_circuitos.png`

Mostra o número de instruções de dois qubits por circuito em função do número de qubits. Cada ponto é um CSV pré-computado; a linha laranja resume a mediana em cada tamanho. A dispersão entre pontos de mesmo tamanho mostra que o número de qubits, sozinho, não explica o custo de roteamento. O diagrama de dispersão é adequado para observar escala e variabilidade sem ocultar circuitos individuais.

## 2. `02_relacao_interacoes_profundidade.png`

Relaciona quantidade de interações com a profundidade de dependência derivada da ordem dos gates de dois qubits; a cor representa a densidade do grafo lógico. Os cinco circuitos com mais interações são identificados para facilitar a investigação de casos extremos. Profundidade aqui não inclui gates de um qubit, medições ou barreiras porque esses atributos não estão nos CSVs de interações. O espalhamento multivariado permite ver relações e exceções sem presumir linearidade.

## 3. `03_estrutura_topologias.png`

Cada ponto representa uma topologia pré-computada; a densidade trata como link físico um par conectado por pelo menos um arco direcionado. A comparação entre famílias existentes (full, grid, heavy-hex, heavy-square, line e ring) evidencia o compromisso entre quantidade de qubits e conectividade. Topologias com tamanhos diferentes não são comparações controladas de desempenho; o gráfico descreve estrutura, não qualidade do mapeamento.

## 4. `04_erros_e_outliers.png`

Compara taxas de erro por família de topologia; pontos vermelhos indicam 219 observações fora dos limites de 1,5 × IQR calculados sobre todos os arcos. São sinalizações para inspeção, não erros a excluir: um link com erro alto pode ser um atributo físico real e relevante para o mapeamento. As taxas são sintéticas no dataset, portanto não devem ser interpretadas como calibrações de um dispositivo real. Boxplots resumem mediana, dispersão e caudas sem usar gráficos de pizza.

## 5. `05_grafo_interacoes.png`

Mostra o grafo lógico não direcionado de modular_adder_14qubits: nós são qubits lógicos, tamanho do nó indica grau, o laranja destaca os qubits de maior grau e os pares mais recorrentes, e largura/rótulo da aresta indicam a frequência de interações. O par mais frequente é q0–q6, q1–q6, q2–q6, q3–q6, q4–q6, q5–q6 (10 gates); o maior grau é dos qubits [6] (grau 13). A agregação perde ordem temporal e direção do gate, então o grafo explica afinidade estrutural, não uma rota nem um mapeamento.

## 6. `06_grafo_topologia.png`

Mostra a topologia física heavy_square_21qubits: tamanho do nó representa grau e cor/rótulo da aresta representa a taxa de erro média entre os arcos do par, em porcentagem (em topologias densas, os rótulos são omitidos para preservar legibilidade). O maior grau total é do qubit físico [17, 18] (entrada/saída por qubit: 17=4/4, 18=4/4). O link com maior erro é (6, 19) (0.294%) e o menor é (2, 11) (0.072%). A visualização agrega arcos recíprocos para legibilidade; o CSV original e as métricas preservam graus e contagens direcionadas. Este contraste ajuda a formular hipóteses de posicionamento, mas não prova desempenho.

## Comparação com soluções existentes

O repositório oferece `optimal_map` (busca exata), `heuristic_map` (busca multi-start) e uma inicialização por fluxo de custo mínimo seguida de hill climbing. `analysis/benchmark_mappers.py` mede multi-start, fluxo min-cost e Qiskit SABRE em 36 casos padrão (quatro famílias de circuito, três tamanhos e três topologias), com cinco execuções por método e caso. A busca exata é limitada aos 12 casos de quatro qubits. Consulte `out/parte2/mapping_benchmarks.csv` para tempos, SWAPs, mapeamentos iniciais/finais e erro estimado. SABRE é uma referência de mercado medida, enquanto VF2Layout é apenas uma referência qualitativa de layout: encontra embedding sem SWAP somente quando há subgrafo compatível. O erro do benchmark usa taxas sintéticas dos links e não representa hardware real. As figuras deste relatório continuam descritivas dos datasets e não alegam superioridade de algoritmo.
