import logging
from collections import defaultdict
from pathlib import Path

import pandas as pd

from analysis.interactions import analyze_interactions
from dataset_generation.paths import DATASETS_ROOT


LOGGER = logging.getLogger(__name__)
INPUT_ROOT = DATASETS_ROOT / "algorithms"
OUTPUT_ROOT = DATASETS_ROOT / "interaction_analysis" / "algorithms"
COLUMNS = (
    "algorithm",
    "circuit",
    "num_qubits",
    "qubit_1",
    "qubit_2",
    "interaction_count",
)


def generate_algorithm_interaction_dataset(
    input_root: Path = INPUT_ROOT,
    output_root: Path = OUTPUT_ROOT,
) -> tuple[int, int]:
    """Write a pairwise interaction CSV for each algorithm."""
    if not input_root.is_dir():
        raise FileNotFoundError(f"Algorithm dataset directory does not exist: {input_root}")

    circuit_paths = sorted(input_root.rglob("*.qasm"))
    if not circuit_paths:
        raise FileNotFoundError(f"No QASM circuits found in: {input_root}")

    rows_by_algorithm: dict[str, list[dict[str, str | int]]] = defaultdict(list)
    failed_circuits = 0

    for circuit_path in circuit_paths:
        algorithm = circuit_path.relative_to(input_root).parts[0]
        try:
            qubit_count, matrix = analyze_interactions(circuit_path)
        except Exception:
            failed_circuits += 1
            LOGGER.exception("Failed to analyze circuit: %s", circuit_path)
            continue

        for first in range(qubit_count):
            for second in range(first + 1, qubit_count):
                rows_by_algorithm[algorithm].append(
                    {
                        "algorithm": algorithm,
                        "circuit": circuit_path.stem,
                        "num_qubits": qubit_count,
                        "qubit_1": first,
                        "qubit_2": second,
                        "interaction_count": int(matrix[first, second]),
                    }
                )

    for algorithm, rows in rows_by_algorithm.items():
        algorithm_dir = output_root / algorithm
        algorithm_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows, columns=COLUMNS).to_csv(
            algorithm_dir / "pair_interactions.csv",
            index=False,
        )

    LOGGER.info(
        "Interaction dataset complete: %d circuits analyzed, %d failed, %d algorithm files written.",
        len(circuit_paths) - failed_circuits,
        failed_circuits,
        len(rows_by_algorithm),
    )
    return len(circuit_paths), failed_circuits


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    _, failed_circuits = generate_algorithm_interaction_dataset()
    if failed_circuits:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
