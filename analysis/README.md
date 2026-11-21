# Algorithm interaction dataset

For the complete project overview, see the
[project README](../README.md).

Generate a pairwise interaction dataset from the QASM circuits in
`datasets/algorithms/`:

```powershell
python -m analysis.generate_algorithm_interactions
```

The output is grouped by algorithm and qubit count under
`datasets/interaction_analysis/algorithms/<algorithm>/`. For example,
`ghz/pair_interactions_5qubits.csv` contains the pairwise interactions for
five-qubit GHZ circuits. Each row represents one unordered qubit pair in one
circuit. Pairs with no two-qubit gates are included with an
`interaction_count` of `0`.

The columns are `algorithm`, `circuit`, `num_qubits`, `qubit_1`, `qubit_2`, and
`interaction_count`. The count is the number of two-qubit instructions between
the pair; it does not distinguish gate types.

## Ordered interaction edge lists

Generate one ordered edge-list CSV per circuit with:

```powershell
python -m analysis.generate_ordered_interactions
```

The output is grouped by algorithm under
`datasets/interaction_order/algorithms/<algorithm>/`. Each row is one
two-qubit instruction, in its original circuit order; repeated edges are
preserved. Multi-qubit custom gates are expanded into their defined
instructions, and each resulting interaction retains the index of the
original circuit instruction. The columns are `algorithm`, `circuit`, `num_qubits`,
`interaction_index` (zero-based among two-qubit instructions),
`instruction_index` (zero-based in the complete circuit), `gate`,
`qubit_1`, and `qubit_2`. The qubit columns preserve operand order, which is
significant for directed gates such as `cx`. One-qubit, measurement, and
barrier instructions are not written as edges.

## AVD visualizations

Generate exploratory and explanatory figures from the precomputed ordered
interaction and hardware topology CSVs:

```powershell
python -m pip install -r requirements-analysis.txt
python -m analysis.visualize_avd
```

The default output is `out/parte2/`: six PNGs, `metricas_grafos.csv` (including
interaction count, dependency depth and pressure, per-qubit maxima, directed
in/out degrees, global link error, and path-distance/error maxima), and
`notas_analiticas.md` with an interpretation for each figure. The sample graph views use the six-qubit
`modular_adder` circuit and `line` topology. Override them with `--circuit`
and `--topology`; both arguments are CSV basenames without their suffixes.
The interaction graph lists the most frequent pair names only when there are
at most six tied pairs; larger groups are summarized by their count.

The figures characterize the precomputed datasets; they do not benchmark
mapping algorithms. The benchmark below measures multi-start heuristic,
min-cost-flow-seeded mapping, and Qiskit's SABRE for the same
circuit/topology pairs, with five runs per case and method. Exact search is
limited to selected small cases.

Run a repeatable comparison of the implemented methods and Qiskit SABRE, then
launch the Streamlit dashboard:

```powershell
python -m analysis.benchmark_mappers
python -m streamlit run analysis/streamlit_app.py
```

The default benchmark covers 120 cases: GHZ, modular-adder, QFT, and QAOA
circuits at four, six, eight, ten, and twelve qubits, paired with `line`,
`ring`, `full`, `grid`, `heavy_hex`, and `heavy_square` topologies. Line, ring,
and full topologies use the same physical size as the circuit; the other
families use the smallest available topology that fits. Each case runs five
seeds for multi-start heuristic, min-cost flow plus hill climbing, and Qiskit SABRE.
Exact search is included only for cases with at most four logical qubits and no
more than 100,000 possible placements; it is a reference for these small
cases, not a baseline for the full matrix. Set `--exact-max-qubits 0` to
disable exact search or use `--max-exact-placements` to lower its placement
limit. Use repeated `--qubit-count` options to precompute other available
logical sizes, repeated `--topology-family` options to choose architectures,
and repeated `--circuit` and `--topology` options to select specific inputs.
The CSV records initial/final logical-to-physical mappings, SWAP count,
estimated error, and elapsed time.

The dashboard separates dataset-wide graphs from the selected circuit and
topology, groups selection controls by circuit family and hardware architecture,
and shows per-run mappings and error estimates. The selected-case view exposes
the graph classes' precomputed circuit and topology metrics, per-qubit profiles,
the logical interaction matrix, physical path-distance matrix, and cumulative
path-error matrix. Algorithm checkboxes default to multi-start, min-cost flow,
and SABRE; exact search is optional. The dashboard generates bar charts for
median SWAPs, estimated error, and runtime by topology, line charts by logical
qubit count, and a separate time/error scatter plot per selected algorithm.
aggregate charts compare the three methods available across the full matrix;
exact search remains visible for the small reference cases. The comparison
filters include individual topology datasets as well as topology family and
logical-qubit count, and charts are separated into topology, scaling,
per-execution, detail, and interpretation tabs.
If `metricas_grafos.csv` has an outdated schema, the dashboard regenerates it;
circuit and topology choices are limited to source files currently present.
SABRE is measured with Qiskit; VF2Layout remains a qualitative
market reference because it finds a perfect layout only when the circuit graph
embeds in the device topology. Estimated errors use synthetic link error rates,
not real hardware measurements. Run the app with
`python -m streamlit run analysis/streamlit_app.py`.
