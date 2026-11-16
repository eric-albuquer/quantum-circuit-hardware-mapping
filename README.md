# Quantum circuit and topology datasets

This repository prepares data for a graph-algorithms project with two related
goals: meet the algorithmic requirements on a large directed, weighted graph,
and study how quantum-circuit interactions relate to hardware connectivity.
The project brings together quantum datasets, logical-qubit interaction
analysis, graph algorithms, physical placement, routing experiments, reports,
and visual analytics.

## Research question and problem

A circuit describes **logical qubits** and operations between them. A quantum
device provides **physical qubits** connected according to a coupling
topology. A logical two-qubit operation can execute directly only if the
physical qubits assigned to its operands have a compatible hardware
connection. Otherwise, routing must move logical states through the hardware
graph, typically by inserting SWAP gates.

The research question is: **How do circuit interaction patterns and hardware
connectivity/costs affect logical-qubit placement and routing overhead, and
which graph algorithms can suggest lower-SWAP routes and placements?**

The eventual comparison should measure inserted SWAP count, route length,
compiled circuit depth, and—only with a clearly stated cost model—exposure to
hardware error. A placement is an injective mapping from logical qubits to
physical qubits. A routing solution must also respect operation order and
update the current placement as the circuit executes. Static shortest paths
can provide route suggestions, but do not alone solve the full dynamic
multi-qubit routing problem.

## Graph models and classification

| Model | Vertices | Edges | Classification and weights |
| --- | --- | --- | --- |
| Circuit interaction graph (one graph per circuit) | Logical qubits, identified by their QASM indices | A pair is an edge when the pair has at least one two-qubit instruction; the CSV also records pairs with zero interactions | Simple, loop-free, undirected, weighted, and not necessarily connected. The integer weight is the number of two-qubit instructions for the pair; it is nonnegative. Gate direction, type, and temporal order are aggregated away. |
| Hardware coupling graph (one graph per topology) | Physical qubits in a Qiskit `CouplingMap` | Directed arcs for allowed source-to-target couplings | Simple directed, weighted, static, and currently connected for the generated topologies. The JSON/CSV stores synthetic positive gate-error rates (0.15% median, clipped to 0.02%–1%) and derived fidelities; reciprocal arcs may have different synthetic values. No negative weights are present. |

The circuit and hardware graph have different vertex domains: **logical**
qubits versus **physical** qubits. They must not be treated as one graph or
compared by matching vertex indices without defining a placement.

### Planned graph-algorithm implementation

Implement the group's algorithms in `src/graphs/algorithms.py` and reuse that
implementation across both analysis parts rather than relying on a library
algorithm as the submitted implementation:

1. **BFS and DFS:** implement traversals over directed adjacency lists, make
   the directed reachability rule explicit, and run each from at least three
   documented source vertices. Use them for reachability and topology
   exploration, not as weighted shortest-path algorithms.
2. **Dijkstra:** implement and validate shortest paths for nonnegative edge
   costs; report at least five source/target pairs. On hardware graphs, a
   unit edge cost answers a minimum-hop question, while a documented
   nonnegative gate-error cost answers a different weighted-route question.
3. **Bellman–Ford:** implement shortest paths on the positive main dataset,
   and separately validate the negative-cycle detection behavior on a small
   synthetic graph with a documented negative-edge/cycle construction, if
   required. Do not introduce unexplained negative weights into the real
   dataset or interpret synthetic negative costs as physical error rates.
4. **Minimum spanning tree (MST):** use only on an explicitly undirected,
   connected, weighted graph. The circuit interaction graph is a natural
   exploratory input. A directed hardware map first needs a declared
   undirected projection (for example, a documented aggregation of reciprocal
   arc costs). An MST is a minimum-cost connected backbone, not a routing
   solution: omitted hardware edges still exist, and routing must not be
   restricted to the tree unless that is a separate experiment.
5. **Placement and routing:** the detailed model, equations, precomputed
   structures, search strategies, physical assumptions, limitations, and
   command-line usage are documented in the
   [placement and routing guide](#placement-and-routing-model).

### Placement and routing model

The implementation is in `src/mapping.py`; the graph preprocessing is in
`src/circuit_graph/graph.py` and `src/topology_graph/graph.py`. This section
describes the behavior of the current code, including its approximations.

#### Flux-graph placement cost (`src/mapping2.py`)

`map2` builds a logical-to-physical flow graph. Its degree, mean-distance,
adjacent-error, and mean-path-error inputs are normalized to `[0, 1]` before
they are combined. `TopologyGraph` precomputes hardware-only metrics, while
`CircuitGraph` precomputes the dependency-graph depth and interaction counts.
Unreachable physical pairs receive a finite worst-case distance and path-error
penalty; the adjacent-error ratio is capped at `1` so the final cost remains
normalized.

The logical-qubit importance is
`I_q = 0.5 * G_q / G_max + 0.5 * N_q / N_max`. The final edge cost is
`C(q,Q) = w1 * P_degree + w2 * P_distance + w3 * P_error`, with the initial
noise weights `(0.2, 0.2, 0.6)` for shallow circuits and topology weights
`(0.45, 0.35, 0.2)` for deep circuits. The weights interpolate linearly using
the dependency-depth pressure
`(depth - 1) / (two_qubit_interactions - 1)`, defined as zero for circuits with
at most one two-qubit interaction. Thus fully parallel interactions favor the
shallow profile, while a fully serial dependency chain favors the deep profile.
The error penalty combines adjacent error relative to the chip-wide mean link
error and mean cumulative path error relative to the worst physical node, with
`alpha = 0.7` and `beta = 0.3`.

#### Inputs and precomputed data

The mapper consumes an ordered CSV of two-qubit circuit operations and a
weighted hardware-edge CSV:

- **Circuit input:** one row per two-qubit operation, including repeated
  operand pairs. Operand order, gate name, and operation index are retained.
  Custom multi-qubit instructions are expanded into their defined two-qubit
  operations while generating the ordered CSV. Single-qubit instructions,
  measurements, and barriers are not part of this routing input.
- **Hardware input:** directed coupling arcs with a synthetic
  `gate_error_rate` on each arc. The topology used by this experiment is
  connected, and qubit indices are expected to be contiguous from zero because
  the graph implementation uses those indices directly in square matrices.

`CircuitGraph` builds several structures when the CSV is loaded:

1. `fpga` stores the complete ordered operation list used by the router.
2. `iteraction_matrix` (spelling retained in the code) is a symmetric
   `k × k` matrix. Its entry `C[i][j]` is the number of two-qubit operations
   between logical qubits `i` and `j`; for valid operations on distinct
   operands, the diagonal is zero.
3. `dependency_graph` records, for each operation, its immediately preceding
   operation on either operand. It captures per-qubit ordering constraints,
   but the current router consumes `fpga` directly rather than scheduling from
   this dependency graph.

`TopologyGraph` first stores the input arcs in an adjacency dictionary. For
each ordered pair of physical qubits it then precomputes:

- `path_matrix[a][b]`: a path selected to minimize cumulative link-error risk,
  with hop count as a tie-breaker. It is not necessarily a minimum-hop path.
- `error_matrix[a][b]`: the cumulative error estimate along that selected
  path, not merely the error of the direct edge. Unreachable pairs retain an
  empty path and infinite error.

For a physical pair `{a,b}`, the undirected link error used by this experiment
is the arithmetic mean of the available directed arc error rates:

$$
p_{ab} =
\frac{1}{|\mathcal{A}_{ab}|}
\sum_{(u,v)\in\mathcal{A}_{ab}} p_{u\to v},
\qquad
\mathcal{A}_{ab} = \{(a,b),(b,a)\}\cap E.
$$

Here, \(E\) is the set of stored directed hardware arcs and
\(\mathcal{A}_{ab}\) contains whichever of the two directions are present.
Thus, if both directions exist, their error rates are averaged; if only one
exists, that rate is used.

If neither direction exists, there is no usable link. The all-pairs search
follows the stored directed adjacency arcs, while the error rate of each
traversed pair is averaged across the available reciprocal calibrations.
SWAPs and circuit-gate feasibility are otherwise treated as direction-agnostic.
Generated topologies generally contain both arcs for each physical connection;
with one-way input data, path reachability can remain asymmetric.

The all-pairs path preprocessing uses Dijkstra's algorithm. For a link error
\(p_e<1\), the edge weight is transformed to additive negative log-success:

$$
q(p_e)=-\ln(1-p_e), \qquad
Q(\pi)=\sum_{e\in\pi}q(p_e),
$$
$$
P_{\mathrm{success}}(\pi)
=\prod_{e\in\pi}(1-p_e)
=\exp\!\left(-Q(\pi)\right), \qquad
E(\pi)=1-P_{\mathrm{success}}(\pi).
$$

Minimizing \(Q(\pi)\) is equivalent to maximizing the product of link success
probabilities, or minimizing the modeled path error \(E(\pi)\). The number of
edges is the secondary ordering criterion; neighbors are visited in sorted
index order for deterministic tie handling. A link with \(p_e=1\) has infinite
negative-log cost. The precomputation runs once when a `TopologyGraph` is
constructed, before the mapping search, and is reused for every placement and
route. Its all-source Dijkstra work is approximately
\(O(V(V+E)\log V)\) with a binary heap; the two \(V\times V\) matrices use
\(O(V^2)\) entries, while storing every full path can require up to \(O(V^3)\)
vertex entries in the worst case.

#### Floyd–Warshall and the all-pairs path matrices

Floyd–Warshall is a dynamic-programming algorithm for all-pairs shortest paths.
It maintains a distance matrix and progressively allows each vertex as an
intermediate point. If `D^(r)[i][j]` is the minimum cost from `i` to `j` using
only the first `r` vertices as intermediates, its recurrence is:

$$
D^{(r)}_{ij} =
\min\!\left(
    D^{(r-1)}_{ij},
    D^{(r-1)}_{ir}+D^{(r-1)}_{rj}
\right).
$$

For this hardware cost model, the matrix can be initialized with the
negative-log link costs \(q(p)=-\ln(1-p)\) rather than raw error probabilities.
The recurrence then minimizes cumulative risk because path costs add in
negative-log space. A companion next-hop (or predecessor) matrix is needed to
reconstruct the actual physical-qubit sequence; a distance matrix alone gives
only the optimal cost. A tuple `(risk_cost, hop_count)` can be compared
lexicographically to preserve the current tie-break rule for equal-risk paths.
The standard algorithm takes \(O(V^3)\) time and \(O(V^2)\) space.

The current implementation does **not** run Floyd–Warshall. It obtains the
same all-pairs kind of result by running Dijkstra once per source, since all
transformed edge costs are nonnegative. `path_matrix[a][b]` stores the
reconstructed vertex sequence and `error_matrix[a][b]` stores the cumulative
error for that path; these are not a Floyd–Warshall distance/next-hop matrix.
This distinction matters when describing the implementation and its runtime:
the current preprocessing is approximately
\(O(V(V+E)\log V)\), whereas Floyd–Warshall would take \(O(V^3)\) regardless
of sparsity. Both approaches can be used to compute all-pairs paths, but
switching algorithms would be a separate implementation change.

The circuit matrix and operation dependency data are also computed once when
the circuit CSV is loaded. They are reused by the placement strategies; no
per-candidate reconstruction of these graph structures is required.

#### Number of possible placements

Let `k` be the number of logical circuit qubits and `n` the number of physical
hardware qubits. A placement must assign every logical qubit to a distinct
physical qubit, but does not need to use every physical qubit. Therefore the
number of injective mappings is the falling factorial:

$$
|\mathcal{M}|=P(n,k)
=n(n-1)\cdots(n-k+1)
=\frac{n!}{(n-k)!}.
$$

For example, mapping three logical qubits onto four physical qubits has
\(4\cdot3\cdot2=24\) possible initial placements. The CLI prints this integer in
scientific notation (for example, `2.400e+01`). If `n < k`, no placement
exists and the mapping flow raises an error.

#### Mathematical placement objective

Let \(\mathcal{M}\) be the set of all injective placements, \(m(i)\) the
physical qubit assigned to logical qubit \(i\), and \(\mathcal{R}(m)\) the
routed gate sequence produced by the current ordered shortest-risk-path
policy for initial placement \(m\). If \(p_g\) is the modeled error rate of
routed two-qubit gate \(g\), define:

$$
E_{\mathrm{route}}(m)
=1-\prod_{g\in\mathcal{R}(m)}(1-p_g), \qquad
S_{\mathrm{route}}(m)
=\text{number of inserted SWAP gates in }\mathcal{R}(m).
$$

The exact placement search solves this lexicographic minimization:

$$
m^\star =
\underset{m\in\mathcal{M}}{\operatorname{arg\,min}_{\mathrm{lex}}}
\left(
E_{\mathrm{route}}(m),
S_{\mathrm{route}}(m),
m(0),m(1),\ldots,m(k-1)
\right).
$$

The physical-index tuple is a deterministic final tie-breaker. This objective
minimizes the modeled routed error first and minimizes SWAP count only among
placements with the same routed error. It does not minimize SWAP count as the
primary objective.

The heuristic does not search the full set `M`. It locally minimizes a
placement proxy computed from the symmetric circuit interaction counts
\(C_{ij}\) and the precomputed risk-optimal path between the currently assigned
physical qubits. Let \(e_{ab}\) be the cumulative path error and \(d_{ab}\)
its hop count. The proxy objective is:

$$
E_{\mathrm{proxy}}(m)
=1-\prod_{0\le i<j<k}
\left(1-e_{m(i),m(j)}\right)^{C_{ij}}, \qquad
H_{\mathrm{proxy}}(m)
=\sum_{0\le i<j<k} C_{ij}\,d_{m(i),m(j)}.
$$

The minimization is lexicographic: reduce proxy error first, then weighted
path length. Equivalently, when all `e[a][b] < 1`, minimizing proxy error is
the same as minimizing the additive negative-log objective:

$$
L_{\mathrm{proxy}}(m)
=-\sum_{0\le i<j<k}C_{ij}
\ln\!\left(1-e_{m(i),m(j)}\right), \qquad
E_{\mathrm{proxy}}(m)
=1-\exp\!\left(-L_{\mathrm{proxy}}(m)\right).
$$

The implementation uses this log form for numerical stability and handles
certain-error (\(e_{ab}=1\)) pairs separately. For any one start, it repeatedly
applies the single best improving logical swap or move to an unused physical
qubit until no such move decreases
\((E_{\mathrm{proxy}},H_{\mathrm{proxy}})\). This is a local
minimum, not a proof of global optimality. The heuristic routes the distinct
finalists and selects among them using `(E_route, S_route, E_proxy, H_proxy,
physical-index tuple)`.

#### Ordered routing and the physical error model

`route_circuit(circuit, topology, mapping)` processes each operation in
`fpga` order, because a SWAP changes where later logical operands reside. For
an operation whose current physical operands are the endpoints of the
precomputed path
`[v0, v1, ..., v(d)]`, the router inserts `d - 1` SWAPs along the first
operand's path prefix (`v0-v1` through `v(d-2)-v(d-1)`). The operands are then
adjacent on the final link `v(d-1)-v(d)`, where the circuit operation is
applied. If the operands were already adjacent, no SWAP is needed. A SWAP
exchanges the logical occupants of its two physical endpoints; the
logical-to-physical mapping is updated before processing the next operation.
An unused physical qubit can receive a logical state during this process.

The error calculation assumes independent two-qubit gate failures and uses
the same link rate \(p\) for every two-qubit gate executed on that link. Each
inserted SWAP is modeled as three two-qubit gates, so its success probability
is \((1-p)^3\); each routed circuit interaction is modeled as one two-qubit
gate with success probability \((1-p)\). If the routed sequence contains
gates with rates \(p_1,\ldots,p_r\), the reported value is:

$$
P_{\mathrm{success}}=\prod_{g=1}^{r}(1-p_g),
\qquad
E_{\mathrm{route}}=1-P_{\mathrm{success}}.
$$

The product is accumulated as execution proceeds. Here, “expected error rate”
is a probability-style proxy under the stated independent-gate model, not an
empirically calibrated prediction of a processor's output quality. The
synthetic dataset's two-qubit gate rates are sampled from a clipped log-normal
distribution (0.15% median, 0.5 log-space sigma, clipped to 0.02%–1%).
`gate_fidelity` is stored as `1 - gate_error_rate`.

The model does **not** include single-qubit gate error, readout error,
decoherence/T1 or T2, gate durations, crosstalk, correlated errors, calibration
drift, direction-specific gate feasibility, or the physical decomposition
overhead for correcting gate direction. In particular, treating every SWAP
as exactly three equally noisy two-qubit gates is a simplifying assumption;
real hardware may require direction-correction gates or have different error
rates for each native operation. Operand order and gate names are preserved in
the input, but the current router does not use them to select direction-aware
implementations or gate-specific error rates.

#### Exact placement search

`optimal_map` enumerates all `P(n,k)` injective placements using depth-first
search. Each complete placement is passed through the ordered router and
scored lexicographically by:

1. routed `expected_error_rate`,
2. routed SWAP count,
3. the tuple of physical indices assigned to logical qubits in index order.

The last criterion makes ties deterministic. The search can partition work by
the first logical qubit's physical assignment and run these independent
prefixes in a `ProcessPoolExecutor`; `max_workers=1` runs sequentially. This
is exhaustive over **initial placements**, not over every possible sequence
of routing decisions: each placement is routed by the single path/SWAP policy
described above. Its work grows at least proportionally to `P(n,k)` times the
cost of routing one circuit, so exhaustive search quickly becomes impractical
as the number of available physical qubits grows.

#### Heuristic placement search

`heuristic_map` uses three starting strategies:

1. **Random start.** A placement is sampled uniformly from the injective
   mappings by drawing `k` distinct physical qubits without replacement and
   assigning them to logical qubits in index order. This independently
   randomized placement is distinct from perturbing a deterministic start.
2. **Degree-based start.** Logical qubits are ordered by the number of
   distinct interaction partners, then total interaction count, then logical
   index. Physical qubits are ordered by adjacency count (degree), lower
   accumulated path error to all physical qubits, lower average path length,
   then physical index. The ordered lists are paired.
3. **Most-frequent-pair start.** The most frequently interacting logical pair
   is selected, with total endpoint interaction counts and indices breaking
   ties. It is placed on the physical link with the lowest undirected link
   error, with endpoint degree and indices breaking ties. Remaining logical
   qubits are paired in descending interaction-degree/weight order with
   physical qubits ordered by degree, aggregate path error, and index.

The requested `initial_candidates` are divided as evenly as possible between
the three strategies; the random strategy receives any remainder. The first
random placement and the unperturbed start for each deterministic strategy
assigned at least one candidate are retained as final candidates. Additional
degree- and interaction-pair-based starts are created by seeded random
perturbations: a logical qubit is selected and assigned to a random physical
qubit; if that physical qubit is occupied, the two logical assignments are
exchanged. Repeating this a random number of times produces each perturbed
start. A fixed `seed` makes both the independent random placements and
perturbations reproducible. Therefore, even when `initial_candidates` is
smaller than three, at least one random initial placement is generated.

Every start is locally improved by greedy hill climbing. At each iteration,
the algorithm considers:

- swapping the physical assignments of any two logical qubits; and
- moving one logical qubit to any currently unused physical qubit.

This neighborhood is **inspired by the 2-opt idea of making a two-element
exchange to improve a solution**, but it is not the classical 2-opt algorithm
for a traveling-salesperson tour, which removes two tour edges and reconnects
or reverses a tour segment. Here, a placement is an assignment, so the
two-element exchange swaps the physical destinations of two logical qubits.
The additional move to an unused physical qubit is specific to the
rectangular \(k\)-logical-to-\(n\)-physical placement problem.

Formally, for a current injective placement \(m\), the swap neighborhood is

$$
\mathcal{N}_{\mathrm{swap}}(m)
=\{m^{i\leftrightarrow j}:0\le i<j<k\},\qquad
m^{i\leftrightarrow j}(i)=m(j),\quad
m^{i\leftrightarrow j}(j)=m(i),
$$

so \(\lvert\mathcal{N}_{\mathrm{swap}}(m)\rvert=\binom{k}{2}\). The
unused-site move neighborhood is

$$
\mathcal{N}_{\mathrm{move}}(m)
=\{m^{i\to p}:0\le i<k,\ p\in\mathcal{P}\setminus m(\mathcal{L})\},
\qquad
m^{i\to p}(i)=p.
$$

There are \(k(n-k)\) such moves, since \(n-k\) physical qubits are unoccupied.
Thus, each hill-climbing iteration examines
\(\binom{k}{2}+k(n-k)\) neighboring placements.
Here, \(\mathcal{L}\) and \(\mathcal{P}\) are the logical- and physical-qubit
sets. All assignments not shown in these definitions remain unchanged. The
algorithm evaluates the full neighborhood, chooses its best strictly
improving member, and repeats:

$$
m_{t+1}
=\underset{
 m'\in\{m_t\}\cup\mathcal{N}_{\mathrm{swap}}(m_t)\cup
 \mathcal{N}_{\mathrm{move}}(m_t)
}{\operatorname{arg\,min}_{\mathrm{lex}}}
\left(E_{\mathrm{proxy}}(m'),H_{\mathrm{proxy}}(m')\right).
$$

If the minimizer is \(m_t\), the search stops; ties with the current placement
are resolved in favor of stopping, matching the implementation's
strict-improvement check. Otherwise, that best strictly-improving candidate
becomes the next placement. This is **best-improvement hill climbing** over a
2-opt-like swap neighborhood, not an exhaustive search over
all placements and not a guarantee of a global optimum. Its result depends
on the starting candidate, which is why the implementation uses random,
degree-based, and most-frequent-pair starts.

Although the number of candidate moves is quadratic in the logical-qubit
count plus the logical-to-unused-physical move count, the implementation
updates the proxy using only interaction pairs incident to the moved logical
qubits. This avoids recomputing the full interaction objective for every
neighbor. The placement space is finite and only strictly improving moves
are accepted, so each hill-climbing run terminates at a neighborhood-local
minimum.

For a logical pair \((i,j)\) with \(C_{ij}\) interactions mapped to physical
pair \((a,b)\), let \(e_{ab}\) be `error_matrix[a][b]` and
\(d_{ab}=\operatorname{len}(\texttt{path\_matrix}[a][b])-1\). The proxy is:

$$
E_{\mathrm{proxy}}(m)
=1-\prod_{0\le i<j<k}
\left(1-e_{m(i),m(j)}\right)^{C_{ij}},
\qquad
H_{\mathrm{proxy}}(m)
=\sum_{0\le i<j<k}C_{ij}\,d_{m(i),m(j)}.
$$

If any interacting pair has path error \(1\), its proxy error is \(1\). The
implementation uses sums of logarithms for numerical stability and tracks
certain-error pairs separately. For each trial move it recomputes only
interactions incident to the moved logical qubits, rather than rescoring the
whole interaction matrix. The local search terminates at a local minimum with
respect to the two neighborhoods above; other placements may still have lower
cost.

The proxy treats every interaction between a given logical pair as if it used
the same precomputed path/error and does not model the dynamic SWAPs that may
be inserted when that pair is actually routed. To choose the final heuristic
answer, the implementation deduplicates locally improved placements while
retaining the strategy starts, routes each distinct finalist in circuit
order, and ranks them by actual routed error, SWAP count, proxy error, proxy
path length, and physical-index tuple. Thus the proxy guides placement search;
the finalist ranking uses the current ordered routing model.

Hill-climb starts are processed in parallel by default, using up to the
available CPU count; `max_workers=1` disables multiprocessing. This parallelism
changes runtime, not the set of starts or the deterministic result for a
fixed seed.

#### Main mapping flow and CLI

`map_and_route(circuit, topology, exact_search_limit=100_000_000, ...)` counts
possible placements and chooses:

$$
P(n,k)<\texttt{exact\_search\_limit}
\ \Longrightarrow\ \texttt{optimal\_map},
\qquad
P(n,k)\ge\texttt{exact\_search\_limit}
\ \Longrightarrow\ \texttt{heuristic\_map}.
$$

The comparison is strictly less-than, so a count equal to the threshold uses
the heuristic. The function then routes the selected initial mapping and
returns the count, algorithm label, initial mapping, `RoutingResult`, and
elapsed search-plus-routing time. The exact branch has already routed all
placements to compare them; the selected mapping is routed once more to
produce the common result object.

Run the default example datasets from the repository root:

```powershell
python -m src.mapping
```

Select other ordered-interaction and topology CSVs, or tune the search:

```powershell
python -m src.mapping `
  --circuit "datasets\interaction_order\algorithms\ghz\ghz_3qubits_ordered_interactions.csv" `
  --topology "datasets\topologies\full\full_4qubits_weighted_edges.csv" `
  --exact-search-limit 100000000 `
  --initial-candidates 100 `
  --seed 42 `
  --max-workers 1
```

The CLI reports possible placements in scientific notation, whether exact or
heuristic placement was selected, the mapping, the route/SWAP result, the
modeled routed error, and elapsed time. On Windows, scripts that use the
default process-based parallelism must protect their entry point with
`if __name__ == "__main__":`.

Use and test these implementations on the selected large assignment graph
where the graph type permits, and on the circuit/hardware graphs where the
question is meaningful. Record unsupported combinations instead of silently
changing graph direction or weight semantics.

### Checkpoint and analysis deliverables

Before using the large assignment dataset, document and obtain approval for
its source, `|V|`, `|E|`, graph type, weight meaning/origin, negative-weight
status, and research question. The selected non-air, directed, weighted graph
must contain at least 20,000 edges, or the project must provide a reproducible
download script. If Bellman–Ford's negative-cycle case is needed, keep its
small synthetic test graph separate from that dataset.

The later analysis stage should provide:

- Required BFS/DFS source cases, at least five Dijkstra pairs, and
  Bellman–Ford cases with and without a negative cycle.
- `out/parte2/parte2_report.json`, with cases, graph metadata, and mean
  runtimes from at least five executions; include scalability measurements at
  three graph sizes and document the timing method.
- Comparison plots for runtime, traversal/algorithm behavior, and paths.
- At least four AVD (visual analytics) views: two exploratory and two
  explanatory, each accompanied by analytical notes.
- A critical PDF discussion of algorithm suitability, assumptions, runtime,
  graph direction and weights, and limitations of transferring results to
  quantum placement/routing.

## Repository layout

```text
analysis/
  generate_algorithm_interactions.py
  generate_ordered_interactions.py
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
  interaction_analysis/algorithms/<category>/pair_interactions_<count>qubits.csv
  interaction_order/algorithms/<category>/*_ordered_interactions.csv
  interaction_order/algorithms/<category>/*_ordered_interactions.csv
docs/
  assets/ghz_5qubits_qiskit.txt
```

Generated data is grouped by category and, where useful, by benchmark or
topology. The interaction analysis is kept separate from the original QASM
circuits and from the generators.

## Dataset inventory

The checked-in/generated snapshot currently contains:

| Dataset | Contents | Snapshot |
| --- | --- | ---: |
| Algorithm circuits | MQT Bench circuits in OpenQASM 2, grouped into benchmark folders | 516 circuits across 28 benchmark folders |
| Random circuits | Generated OpenQASM 3 circuits | 15 circuits: 4, 6, 8, 10, and 12 qubits at depths 10, 20, and 30 |
| Weighted topologies | JSON metadata and CSV edge lists | 63 coupling maps, each represented in both formats (126 files) |
| Pairwise interactions | One CSV per circuit category/algorithm, derived from its QASM circuits | 29 CSV files and 75,767 pair/circuit rows |
| Ordered interactions | One ordered two-qubit edge-list CSV per algorithm circuit | 531 CSV files and 37,804 interaction rows |

These counts describe the current snapshot. Benchmark availability can vary
with MQT Bench versions and supported circuit sizes.

### Algorithm circuits

Circuits are generated from [MQT Bench](https://www.cda.cit.tum.de/mqtbench/)
at the algorithmic (`ALG`) level and written as QASM 2 files. The requested
range is 3–30 qubits, subject to each benchmark's supported sizes and
generation limits. Examples include `ghz`, `qft`, `qaoa`, `grover`, adders,
and variational algorithms.

Directory and file example:

```text
datasets/algorithms/ghz/ghz_5qubits.qasm
```

### Random circuits

Random circuits are generated with Qiskit's `random_circuit`, limited to
two-qubit operands, and serialized as QASM 3. The current configuration uses
5 qubit counts (4–12, in steps of 2) and 3 depths (10, 20, and 30). The `id`
in each filename identifies the depth's position in that configuration; it
does not represent repeated samples at a fixed depth.

No random seed is currently set for circuit generation, so regenerating this
dataset can produce different circuits.

### Hardware topology datasets

Each topology is generated with Qiskit's `CouplingMap`. The current set has 63
maps:

| Topology | Configurations | What it represents |
| --- | --- | --- |
| `line` | 3–19 qubits | Each interior qubit connects to its immediate neighbors; the endpoints have one neighbor each. |
| `ring` | 3–19 qubits | A line with an additional link joining its endpoints. |
| `full` | 3–19 qubits | Every pair of physical qubits is connected; this is a dense connectivity reference. |
| `grid` | 3×3, 4×4, 5×5, 8×8, and 10×10 | A two-dimensional nearest-neighbor layout. |
| `heavy_hex` | Distances 3, 5, 7, and 9 | A sparse heavy-hex coupling layout. |
| `heavy_square` | Distances 3, 5, and 7 | A sparse heavy-square coupling layout. |

The heavy-hex maps in the current snapshot contain 19, 57, 115, and 193
qubits; the heavy-square maps contain 21, 65, and 133 qubits. Their sizes are
determined by Qiskit's topology constructors.

Example directory:

```text
datasets/topologies/grid/
  grid_3x3_9qubits_weighted.json
  grid_3x3_9qubits_weighted_edges.csv
```

The JSON file contains:

- `architecture_type`: topology name.
- `num_qubits`: number of physical qubits.
- `qubit_properties`: per-qubit `readout_error`, `readout_fidelity`, and
  `t1_coherence_us`.
- `coupling_map_weighted`: directed source/target link entries with
  `gate_error_rate` and `gate_fidelity`.

The CSV file contains the weighted coupling-map edge list. The coupling maps
are directed as returned by Qiskit, so a bidirectional physical connection
typically appears as two directed entries.

**Important:** the hardware error and coherence values are synthetic samples,
not measurements from a real quantum processor. Readout errors and two-qubit
gate errors are sampled from clipped log-normal distributions; T1 times are
sampled from a clipped normal distribution. The generated data has no T2,
gate-duration, calibration timestamp, or real-device provenance. Seeds are
derived from the topology identifier so that a given topology's synthetic
properties are reproducible.

### Pairwise interaction dataset

Generate the pairwise interaction data with:

```powershell
python -m analysis.generate_algorithm_interactions
```

For each QASM circuit, the analysis counts two-qubit instructions for every
unordered logical-qubit pair. Pairs that never interact are included with a
count of zero. One CSV is written per qubit-count variation within each
benchmark or circuit category:

```text
datasets/interaction_analysis/algorithms/ghz/pair_interactions_5qubits.csv
datasets/interaction_analysis/algorithms/random/pair_interactions_4qubits.csv
```

| Column | Meaning |
| --- | --- |
| `algorithm` | Benchmark folder / algorithm identifier. |
| `circuit` | Circuit filename without the `.qasm` extension. |
| `num_qubits` | Number of logical qubits in the circuit. |
| `qubit_1`, `qubit_2` | Unordered logical-qubit pair, with `qubit_1 < qubit_2`. |
| `interaction_count` | Number of two-qubit instructions involving that pair. |

This is a logical interaction summary, not a physical mapping result. It
counts all two-qubit instruction types together, ignores gate direction and
operation order, and does not model multi-qubit gates as pairwise interactions.
The diagonal/self-pairs are not included.

### Ordered interaction edge lists

Generate a per-circuit edge list that retains the order of two-qubit
operations:

```powershell
python -m analysis.generate_ordered_interactions
```

Each two-qubit instruction is a separate row in
`datasets/interaction_order/algorithms/<algorithm>/<circuit>_ordered_interactions.csv`.
Repeated edges are preserved. Multi-qubit custom gates are expanded into
their defined instructions; each resulting interaction keeps the index of
the original circuit instruction. `interaction_index` gives the zero-based
order among two-qubit operations; `instruction_index` gives the zero-based
position in the complete Qiskit circuit. `gate` records the instruction name, and
`qubit_1` / `qubit_2` retain operand order (important for directed gates such
as `cx`). Single-qubit instructions, measurements, and barriers are omitted.
This sequence is suitable as the ordered edge input for constructing a
dependency graph; it is distinct from the aggregated, undirected pairwise
interaction summary above.

## Quick start

Use Python 3.12 or a compatible version. From the project root in PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
python -m dataset_generation --help
```

If creating a new environment, install the packages used by the generators:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install qiskit qiskit_qasm3_import mqt.bench numpy pandas
```

Generate all three source datasets:

```powershell
python -m dataset_generation
```

Generate one category only:

```powershell
python -m dataset_generation algorithms
python -m dataset_generation random
python -m dataset_generation topologies
```

Generate (or refresh) the pairwise interaction CSVs after the algorithm QASM
files are available:

```powershell
python -m analysis.generate_algorithm_interactions
```

Generate (or refresh) per-circuit ordered interaction edge lists:

```powershell
python -m analysis.generate_ordered_interactions
```

Inspect interactions for a QASM file or all QASM files under a directory:

```powershell
python -m analysis.interactions datasets/algorithms/ghz/ghz_5qubits.qasm
python -m analysis.interactions datasets/algorithms/ghz
python -m analysis.interactions datasets/algorithms/random
```

Paths in these examples use forward slashes as accepted by Python on Windows;
PowerShell users can also use backslashes.

## Qiskit circuit illustration

The following five-qubit GHZ circuit diagram was generated directly from
[`ghz_5qubits.qasm`](datasets/algorithms/ghz/ghz_5qubits.qasm) with Qiskit's
text drawer. The generated UTF-8 text is also available at
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

## Tools

| Tool | Use in this project |
| --- | --- |
| Python | Generator and analysis runtime. |
| Qiskit | Quantum circuits, OpenQASM serialization/parsing, random circuits, coupling maps, and circuit visualization. |
| MQT Bench | Source of structured benchmark circuits. |
| NumPy | Synthetic topology-property generation and interaction matrices. |
| pandas | CSV edge lists, interaction datasets, and tabular output. |
| Qiskit Aer | Available in the development environment for future simulation work; the current dataset generation and interaction scripts do not invoke it. |

The current development environment was validated with Python 3.12.1, Qiskit
2.5.2, MQT Bench 2.3.0, NumPy 2.5.4, and pandas 3.0.6.

## Suggested next analyses

- Compare circuit and hardware graph sizes, density, degree distributions,
  centrality, and interaction-weight distributions.
- Test initial placements of logical qubits and routing heuristics on each
  topology.
- Record inserted SWAP counts, compiled two-qubit gate counts, circuit depth,
  compilation runtime, and explicitly defined error/fidelity proxies.
- Compare topology-only routing with routing informed by synthetic link
  properties, while keeping synthetic and real-device conclusions separate.
- Split experiments by circuit (rather than by individual pair rows) to avoid
  putting rows from the same circuit in both training and test sets.

These are research directions, not results already produced by this
repository.
