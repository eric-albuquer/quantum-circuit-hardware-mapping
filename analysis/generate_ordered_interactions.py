import csv
import logging
from pathlib import Path

from analysis.interactions import analyze_ordered_interactions
from dataset_generation.paths import DATASETS_ROOT


LOGGER = logging.getLogger(__name__)
INPUT_ROOT = DATASETS_ROOT / "algorithms"
OUTPUT_ROOT = DATASETS_ROOT / "interaction_order" / "algorithms"
COLUMNS = (
    "algorithm",
    "circuit",
    "num_qubits",
    "interaction_index",
    "instruction_index",
    "gate",
    "qubit_1",
    "qubit_2",
)


def generate_ordered_interaction_dataset(
    input_root: Path = INPUT_ROOT,
    output_root: Path = OUTPUT_ROOT,
) -> tuple[int, int]:
    """Write an ordered two-qubit edge list for each algorithm circuit."""
    if not input_root.is_dir():
        raise FileNotFoundError(f"Algorithm dataset directory does not exist: {input_root}")

    circuit_paths = sorted(input_root.rglob("*.qasm"))
    if not circuit_paths:
        raise FileNotFoundError(f"No QASM circuits found in: {input_root}")

    failed_circuits = 0

    for circuit_path in circuit_paths:
        relative_path = circuit_path.relative_to(input_root)
        algorithm = relative_path.parts[0]
        try:
            qubit_count, interactions = analyze_ordered_interactions(circuit_path)
        except Exception:
            failed_circuits += 1
            LOGGER.exception("Failed to analyze circuit: %s", circuit_path)
            continue

        output_path = output_root / algorithm / f"{circuit_path.stem}_ordered_interactions.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.writer(output_file)
            writer.writerow(COLUMNS)
            writer.writerows(
                (
                    algorithm,
                    circuit_path.stem,
                    qubit_count,
                    interaction_index,
                    instruction_index,
                    gate,
                    qubit_1,
                    qubit_2,
                )
                for interaction_index, instruction_index, gate, qubit_1, qubit_2 in interactions
            )

    LOGGER.info(
        "Ordered interaction dataset complete: %d circuits analyzed, %d failed.",
        len(circuit_paths) - failed_circuits,
        failed_circuits,
    )
    return len(circuit_paths), failed_circuits


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    _, failed_circuits = generate_ordered_interaction_dataset()
    if failed_circuits:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
