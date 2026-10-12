# Algorithm interaction dataset

For the complete project overview in both languages, see the
[English README](../README.md) and [Portuguese README](../README.pt-BR.md).

Generate a pairwise interaction dataset from the QASM circuits in
`datasets/algorithms/`:

```powershell
python -m analysis.generate_algorithm_interactions
```

The output is grouped by algorithm under
`datasets/interaction_analysis/algorithms/<algorithm>/pair_interactions.csv`.
Each row represents one unordered qubit pair in one circuit. Pairs with no
two-qubit gates are included with an `interaction_count` of `0`.

The columns are `algorithm`, `circuit`, `num_qubits`, `qubit_1`, `qubit_2`, and
`interaction_count`. The count is the number of two-qubit instructions between
the pair; it does not distinguish gate types.
