# Quantum circuit and topology datasets

**Documentation:** [Português (Brasil)](README.pt-BR.md)

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
| Hardware coupling graph (one graph per topology) | Physical qubits in a Qiskit `CouplingMap` | Directed arcs for allowed source-to-target couplings | Simple directed, weighted, static, and currently connected for the generated topologies. The JSON/CSV stores synthetic positive gate-error rates and derived fidelities; reciprocal arcs may have different synthetic values. No negative weights are present. |

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
5. **Placement and routing:** develop baseline placements (for example,
   frequency/degree-based greedy matching) and compare them with alternatives.
   Route each circuit interaction along hardware paths while tracking the
   evolving logical-to-physical mapping. Optimize a stated objective such as
   SWAP count first; analyze depth and synthetic error separately rather than
   mixing incompatible units into one undocumented weight.

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
  interaction_analysis/algorithms/<category>/pair_interactions.csv
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
count of zero. One CSV is written per benchmark or circuit category:

```text
datasets/interaction_analysis/algorithms/ghz/pair_interactions.csv
datasets/interaction_analysis/algorithms/random/pair_interactions.csv
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
python -m pip install qiskit mqt.bench numpy pandas
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
