# Dataset generation

For the project overview in both languages, see the
[English README](../README.md) and [Portuguese README](../README.pt-BR.md).

The generators are separated by dataset type. Generated benchmark circuits
are stored under `datasets/algorithms/<benchmark>/`, random circuits under
`datasets/algorithms/random/`, and hardware maps under
`datasets/topologies/<topology>/`.

Synthetic two-qubit gate error rates are generated from a log-normal
distribution with a 0.15% median and are clipped to 0.02%–1%. These per-gate
rates are combined across circuit operations, so the estimated execution error
still increases with circuit size.

Run all generators from the project root:

```powershell
python -m dataset_generation
```

Generate only one dataset category:

```powershell
python -m dataset_generation algorithms
python -m dataset_generation random
python -m dataset_generation topologies
```

The interaction analysis utility is kept separate from generation and can be
run with `python -m analysis.interactions [path]`. To create a pairwise
interaction dataset for all algorithm circuits, run
`python -m analysis.generate_algorithm_interactions`. Its output is grouped by
algorithm and qubit count under `datasets/interaction_analysis/algorithms/`,
with one `pair_interactions_<count>qubits.csv` file per variation.
