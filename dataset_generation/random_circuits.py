import logging
from pathlib import Path

from qiskit import qasm3
from qiskit.circuit.random import random_circuit

from dataset_generation.paths import DATASETS_ROOT


LOGGER = logging.getLogger(__name__)
QUBIT_COUNTS = range(4, 13, 2)
DEPTHS = (10, 20, 30)


def generate_random_circuits(
    output_root: Path = DATASETS_ROOT / "algorithms" / "random",
    qubit_counts: range = QUBIT_COUNTS,
    depths: tuple[int, ...] = DEPTHS,
) -> None:
    """Generate random circuits in OpenQASM 3 format."""
    generated = 0
    output_root.mkdir(parents=True, exist_ok=True)

    for qubit_count in qubit_counts:
        for index, depth in enumerate(depths):
            try:
                circuit = random_circuit(qubit_count, depth=depth, max_operands=2)
                output_path = output_root / f"random_{qubit_count}qubits_depth{depth}_id{index}.qasm"
                with output_path.open("w", encoding="utf-8") as output_file:
                    qasm3.dump(circuit, output_file)
                generated += 1
            except Exception as error:
                LOGGER.error(
                    "Failed to generate a random circuit (%d qubits, depth %d): %s",
                    qubit_count,
                    depth,
                    error,
                )

    LOGGER.info("Random circuit generation complete: %d circuits generated.", generated)
