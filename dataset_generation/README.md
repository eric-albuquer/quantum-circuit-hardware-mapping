# Dataset generation

For the project overview in both languages, see the
[English README](../README.md) and [Portuguese README](../README.pt-BR.md).

The generators are separated by dataset type. Generated benchmark circuits
are stored under `datasets/algorithms/<benchmark>/`, random circuits under
`datasets/algorithms/random/`, and hardware maps under
`datasets/topologies/<topology>/`.

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
algorithm under `datasets/interaction_analysis/algorithms/`.
