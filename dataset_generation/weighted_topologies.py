import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from qiskit.transpiler import CouplingMap

from dataset_generation.paths import DATASETS_ROOT


LOGGER = logging.getLogger(__name__)
TOPOLOGY_CONFIG = {
    "line": tuple(range(3, 20)),
    "ring": tuple(range(3, 20)),
    "full": tuple(range(3, 20)),
    "grid": ((3, 3), (4, 4), (5, 5), (8, 8), (10, 10)),
    "heavy_hex": (3, 5, 7, 9),
    "heavy_square": (3, 5, 7),
}


def _generate_qubit_properties(qubit_count: int, rng: np.random.Generator) -> dict[str, dict[str, float]]:
    readout_errors = np.clip(
        rng.lognormal(mean=np.log(0.02), sigma=0.4, size=qubit_count),
        0.001,
        0.15,
    )
    t1_times = np.clip(rng.normal(loc=150.0, scale=30.0, size=qubit_count), 30.0, 300.0)

    return {
        str(index): {
            "readout_error": float(readout_errors[index]),
            "readout_fidelity": float(1.0 - readout_errors[index]),
            "t1_coherence_us": float(t1_times[index]),
        }
        for index in range(qubit_count)
    }


def _generate_weighted_edges(
    edges: list[tuple[int, int]],
    rng: np.random.Generator,
) -> list[dict[str, float | int]]:
    gate_errors = np.clip(
        rng.lognormal(mean=np.log(0.015), sigma=0.5, size=len(edges)),
        0.002,
        0.10,
    )
    return [
        {
            "source_qubit": int(source),
            "target_qubit": int(target),
            "gate_error_rate": float(gate_errors[index]),
            "gate_fidelity": float(1.0 - gate_errors[index]),
        }
        for index, (source, target) in enumerate(edges)
    ]


def _save_weighted_topology(
    topology: str,
    qubit_count: int,
    edges: list[tuple[int, int]],
    output_root: Path,
    identifier: str | None = None,
) -> None:
    topology_dir = output_root / topology
    topology_dir.mkdir(parents=True, exist_ok=True)
    dataset_id = identifier or str(qubit_count)
    filename_base = topology_dir / f"{topology}_{dataset_id}qubits_weighted"

    seed = sum((index + 1) * ord(character) for index, character in enumerate(f"{topology}_{dataset_id}"))
    rng = np.random.default_rng(seed)
    qubit_properties = _generate_qubit_properties(qubit_count, rng)
    weighted_edges = _generate_weighted_edges(edges, rng)

    data = {
        "architecture_type": topology,
        "num_qubits": int(qubit_count),
        "qubit_properties": qubit_properties,
        "coupling_map_weighted": weighted_edges,
    }
    with filename_base.with_suffix(".json").open("w", encoding="utf-8") as output_file:
        json.dump(data, output_file, indent=2)
    pd.DataFrame(weighted_edges).to_csv(
        filename_base.parent / f"{filename_base.name}_edges.csv",
        index=False,
    )


def generate_weighted_topologies(
    output_root: Path = DATASETS_ROOT / "topologies",
) -> None:
    """Generate weighted coupling maps grouped by topology."""
    generated = 0
    for qubit_count in TOPOLOGY_CONFIG["line"]:
        _save_weighted_topology(
            "line",
            qubit_count,
            CouplingMap.from_line(num_qubits=qubit_count).get_edges(),
            output_root,
        )
        generated += 1

    for qubit_count in TOPOLOGY_CONFIG["ring"]:
        _save_weighted_topology(
            "ring",
            qubit_count,
            CouplingMap.from_ring(num_qubits=qubit_count).get_edges(),
            output_root,
        )
        generated += 1

    for qubit_count in TOPOLOGY_CONFIG["full"]:
        _save_weighted_topology(
            "full",
            qubit_count,
            CouplingMap.from_full(num_qubits=qubit_count).get_edges(),
            output_root,
        )
        generated += 1

    for rows, columns in TOPOLOGY_CONFIG["grid"]:
        qubit_count = rows * columns
        identifier = f"{rows}x{columns}_{qubit_count}"
        _save_weighted_topology(
            "grid",
            qubit_count,
            CouplingMap.from_grid(num_rows=rows, num_columns=columns).get_edges(),
            output_root,
            identifier,
        )
        generated += 1

    for topology in ("heavy_hex", "heavy_square"):
        for distance in TOPOLOGY_CONFIG[topology]:
            try:
                coupling_map = getattr(CouplingMap, f"from_{topology}")(distance=distance)
                _save_weighted_topology(
                    topology,
                    coupling_map.size(),
                    coupling_map.get_edges(),
                    output_root,
                )
                generated += 1
            except Exception as error:
                LOGGER.warning(
                    "Skipped %s topology at distance %d: %s",
                    topology,
                    distance,
                    error,
                )

    LOGGER.info("Weighted topology generation complete: %d topologies generated.", generated)
