import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from qiskit import qasm2, qasm3
from qiskit.circuit import QuantumCircuit

from dataset_generation.paths import DATASETS_ROOT


def load_circuit(path: Path) -> QuantumCircuit:
    content = path.read_text(encoding="utf-8")
    if "OPENQASM 3" in content.upper():
        return qasm3.loads(content)
    return qasm2.loads(
        content,
        custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS,
        strict=False,
    )


def analyze_interactions(path: Path) -> tuple[int, np.ndarray]:
    circuit = load_circuit(path)
    qubit_count = circuit.num_qubits
    interaction_matrix = np.zeros((qubit_count, qubit_count), dtype=int)

    for instruction in circuit.data:
        if len(instruction.qubits) != 2:
            continue
        first = circuit.find_bit(instruction.qubits[0]).index
        second = circuit.find_bit(instruction.qubits[1]).index
        interaction_matrix[first, second] += 1
        interaction_matrix[second, first] += 1

    return qubit_count, interaction_matrix


def display_interactions(path: Path) -> None:
    qubit_count, matrix = analyze_interactions(path)
    labels = [f"Q{index}" for index in range(qubit_count)]
    dataframe = pd.DataFrame(matrix, columns=labels, index=labels)

    print(f"\nInteraction matrix for {path.name}:")
    print(dataframe.to_string())

    ranking = [
        (int(matrix[first, second]), f"Q{first} <-> Q{second}")
        for first in range(qubit_count)
        for second in range(first + 1, qubit_count)
        if matrix[first, second] > 0
    ]
    ranking.sort(reverse=True, key=lambda item: item[0])

    print("\nMost frequent logical interactions:")
    for weight, pair in ranking[:10]:
        print(f"  {pair}: {weight} interactions")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze two-qubit interactions in QASM circuits.")
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DATASETS_ROOT / "algorithms" / "random",
        help="QASM file or directory to analyze (default: datasets/algorithms/random).",
    )
    path = parser.parse_args().path

    if path.is_file():
        qasm_files = [path] if path.suffix.lower() == ".qasm" else []
    elif path.is_dir():
        qasm_files = sorted(path.rglob("*.qasm"))
    else:
        parser.error(f"Input path does not exist: {path}")

    if not qasm_files:
        parser.error(f"No QASM files found at: {path}")

    for qasm_file in qasm_files:
        display_interactions(qasm_file)


if __name__ == "__main__":
    main()
