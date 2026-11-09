# Algorithm interaction dataset

For the complete project overview in both languages, see the
[English README](../README.md) and [Portuguese README](../README.pt-BR.md).

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
preserved. The columns are `algorithm`, `circuit`, `num_qubits`,
`interaction_index` (zero-based among two-qubit instructions),
`instruction_index` (zero-based in the complete circuit), `gate`,
`qubit_1`, and `qubit_2`. The qubit columns preserve operand order, which is
significant for directed gates such as `cx`. One-qubit, measurement, and
barrier instructions are not written as edges.
