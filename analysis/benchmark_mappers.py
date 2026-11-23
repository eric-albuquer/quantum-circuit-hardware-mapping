from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import qiskit
from qiskit import QuantumCircuit
from qiskit.transpiler import CouplingMap, PassManager
from qiskit.transpiler.passes import (
    ApplyLayout,
    EnlargeWithAncilla,
    FullAncillaAllocation,
    SabreLayout,
    SabreSwap,
)

from src.circuit_graph.graph import CircuitGraph
from src.circuit_graph.loader import load_circuit_graph
from src.mapping import (
    count_possible_mappings,
    heuristic_map,
    optimal_map,
    route_circuit,
)
from src.mapping_common import hill_climb_placement
from src.mapping_flow import (
    build_min_cost_max_flow_graph,
    compute_max_flow_min_cost,
    extract_mapping_from_residual_graph,
)
from src.topology_graph.graph import TopologyGraph
from src.topology_graph.loader import load_topology_graph


ALGORITHMS = (
    "Busca exata",
    "Heurística multi-start",
    "Fluxo min-cost + hill climb",
    "Qiskit SABRE",
)
CIRCUIT_FAMILIES = ("ghz", "modular_adder", "qft", "qaoa")
TOPOLOGY_FAMILIES = (
    "line",
    "ring",
    "full",
    "grid",
    "heavy_hex",
    "heavy_square",
)
SAME_SIZE_TOPOLOGY_FAMILIES = ("line", "ring", "full")
DEFAULT_QUBIT_COUNTS = (4, 6, 8, 10, 12)
DEFAULT_EXACT_MAX_QUBITS = 4


def default_cases(
    repository_root: Path,
    qubit_counts: tuple[int, ...] = DEFAULT_QUBIT_COUNTS,
    topology_families: tuple[str, ...] = TOPOLOGY_FAMILIES,
) -> list[tuple[Path, Path]]:
    topology_paths = {
        family: sorted(
            (
                repository_root
                / "datasets"
                / "topologies"
                / family
            ).glob("*_weighted_edges.csv")
        )
        for family in topology_families
    }
    cases = []
    for qubit_count in qubit_counts:
        circuits = [
            repository_root
            / "datasets"
            / "interaction_order"
            / "algorithms"
            / family
            / f"{family}_{qubit_count}qubits_ordered_interactions.csv"
            for family in CIRCUIT_FAMILIES
        ]
        topologies = []
        for family in topology_families:
            compatible_topologies = [
                path
                for path in topology_paths[family]
                if _qubit_count(path) >= qubit_count
            ]
            if family in SAME_SIZE_TOPOLOGY_FAMILIES:
                compatible_topologies = [
                    path
                    for path in compatible_topologies
                    if _qubit_count(path) == qubit_count
                ]
            elif compatible_topologies:
                smallest_size = min(
                    _qubit_count(path) for path in compatible_topologies
                )
                compatible_topologies = [
                    path
                    for path in compatible_topologies
                    if _qubit_count(path) == smallest_size
                ]
            topologies.extend(compatible_topologies)
        cases.extend(
            (circuit, topology)
            for circuit in circuits
            for topology in topologies
            if circuit.is_file()
        )
    return cases


def _mapping_json(mapping: dict[int, int]) -> str:
    return json.dumps(
        {str(logical): physical for logical, physical in sorted(mapping.items())},
        separators=(",", ":"),
    )


def _should_run_exact(
    circuit: CircuitGraph,
    topology: TopologyGraph,
    max_exact_placements: int,
    exact_max_qubits: int,
) -> bool:
    return (
        circuit.qubit_count <= exact_max_qubits
        and count_possible_mappings(circuit, topology) <= max_exact_placements
    )


def _record(
    algorithm: str,
    circuit_path: Path,
    topology_path: Path,
    run: int,
    seed: int,
    elapsed_seconds: float,
    swap_count: int,
    expected_error_rate: float,
    initial_mapping: dict[int, int],
    final_mapping: dict[int, int],
    possible_mappings: int,
    logical_qubits: int,
    physical_qubits: int,
    initial_candidates: int,
) -> dict[str, object]:
    return {
        "algorithm": algorithm,
        "circuit_category": circuit_path.parent.name,
        "circuit": circuit_path.stem.removesuffix("_ordered_interactions"),
        "topology_category": topology_path.parent.name,
        "topology": topology_path.stem.removesuffix("_weighted_edges"),
        "run": run,
        "seed": seed,
        "elapsed_seconds": elapsed_seconds,
        "swap_count": swap_count,
        "expected_error_rate": expected_error_rate,
        "initial_mapping": _mapping_json(initial_mapping),
        "final_mapping": _mapping_json(final_mapping),
        "possible_mappings": possible_mappings,
        "logical_qubits": logical_qubits,
        "physical_qubits": physical_qubits,
        "initial_candidates": initial_candidates,
        "implementation_version": (
            f"Qiskit {qiskit.__version__}"
            if algorithm == "Qiskit SABRE"
            else "local"
        ),
    }


def _run_sabre(
    circuit,
    quantum_circuit: QuantumCircuit,
    coupling_map: CouplingMap,
    topology,
    seed: int,
) -> tuple[int, float, dict[int, int], dict[int, int]]:
    pass_manager = PassManager(
        [
            SabreLayout(
                coupling_map,
                seed=seed,
                skip_routing=True,
                layout_trials=1,
            ),
            FullAncillaAllocation(coupling_map),
            EnlargeWithAncilla(),
            ApplyLayout(),
            SabreSwap(coupling_map, heuristic="decay", seed=seed),
        ]
    )
    routed_circuit = pass_manager.run(quantum_circuit)
    initial_layout = pass_manager.property_set["layout"]
    final_layout = pass_manager.property_set.get("final_layout")
    initial_mapping = {
        logical: int(initial_layout[quantum_circuit.qubits[logical]])
        for logical in range(circuit.qubit_count)
    }
    final_mapping = (
        initial_mapping.copy()
        if final_layout is None
        else {
            logical: int(
                final_layout[
                    routed_circuit.qubits[initial_mapping[logical]]
                ]
            )
            for logical in range(circuit.qubit_count)
        }
    )

    success_probability = 1.0
    swap_count = 0
    for instruction in routed_circuit.data:
        operation = instruction.operation
        if operation.num_qubits != 2:
            continue
        physical_1 = routed_circuit.find_bit(instruction.qubits[0]).index
        physical_2 = routed_circuit.find_bit(instruction.qubits[1]).index
        gate_error = topology.link_error_rate(physical_1, physical_2)
        if operation.name == "swap":
            success_probability *= (1.0 - gate_error) ** 3
            swap_count += 1
        else:
            success_probability *= 1.0 - gate_error
    return (
        swap_count,
        1.0 - success_probability,
        initial_mapping,
        final_mapping,
    )


def _benchmark_case(
    circuit_path: Path,
    topology_path: Path,
    runs: int,
    initial_candidates: int,
    seed: int,
    max_exact_placements: int,
    exact_max_qubits: int,
) -> list[dict[str, object]]:
    circuit = load_circuit_graph(str(circuit_path))
    topology = load_topology_graph(str(topology_path))
    possible_mappings = count_possible_mappings(circuit, topology)
    run_exact = _should_run_exact(
        circuit,
        topology,
        max_exact_placements,
        exact_max_qubits,
    )

    quantum_circuit = QuantumCircuit(circuit.qubit_count)
    for interaction in circuit.fpga:
        quantum_circuit.cx(interaction.qubit_1, interaction.qubit_2)
    coupling_map = CouplingMap(
        couplinglist=[
            [source, target]
            for source, neighbors in topology.graph.items()
            for target in neighbors
            if source != target
        ]
    )

    records: list[dict[str, object]] = []
    for run in range(1, runs + 1):
        run_seed = seed + run - 1
        print(
            f"{circuit_path.parent.name}/{circuit_path.stem} × "
            f"{topology_path.parent.name}/{topology_path.stem}: "
            f"execução {run}/{runs}",
            flush=True,
        )

        if run_exact:
            start = time.perf_counter()
            mapping = optimal_map(circuit, topology, max_workers=1)
            routing = route_circuit(circuit, topology, mapping)
            records.append(
                _record(
                    ALGORITHMS[0], circuit_path, topology_path, run, run_seed,
                    time.perf_counter() - start, routing.swap_count,
                    routing.expected_error_rate, mapping, routing.final_mapping,
                    possible_mappings, circuit.qubit_count, topology.qubit_count,
                    initial_candidates,
                )
            )

        start = time.perf_counter()
        mapping = heuristic_map(
            circuit,
            topology,
            initial_candidates=initial_candidates,
            seed=run_seed,
            max_workers=1,
        )
        routing = route_circuit(circuit, topology, mapping)
        records.append(
            _record(
                ALGORITHMS[1], circuit_path, topology_path, run, run_seed,
                time.perf_counter() - start, routing.swap_count,
                routing.expected_error_rate, mapping, routing.final_mapping,
                possible_mappings, circuit.qubit_count, topology.qubit_count,
                initial_candidates,
            )
        )

        start = time.perf_counter()
        flow_graph = build_min_cost_max_flow_graph(circuit, topology)
        max_flow, _, residual_graph = compute_max_flow_min_cost(
            flow_graph,
            "s",
            "t",
        )
        if max_flow != circuit.qubit_count:
            raise ValueError("Min-cost flow could not assign every logical qubit")
        mapping = extract_mapping_from_residual_graph(
            circuit,
            topology,
            residual_graph,
        )
        mapping, _ = hill_climb_placement(circuit, topology, mapping)
        routing = route_circuit(circuit, topology, mapping)
        records.append(
            _record(
                ALGORITHMS[2], circuit_path, topology_path, run, run_seed,
                time.perf_counter() - start, routing.swap_count,
                routing.expected_error_rate, mapping, routing.final_mapping,
                possible_mappings, circuit.qubit_count, topology.qubit_count,
                initial_candidates,
            )
        )

        start = time.perf_counter()
        (
            swap_count,
            expected_error,
            initial_mapping,
            final_mapping,
        ) = _run_sabre(
            circuit,
            quantum_circuit,
            coupling_map,
            topology,
            run_seed,
        )
        records.append(
            _record(
                ALGORITHMS[3], circuit_path, topology_path, run, run_seed,
                time.perf_counter() - start, swap_count, expected_error,
                initial_mapping, final_mapping, possible_mappings,
                circuit.qubit_count, topology.qubit_count, initial_candidates,
            )
        )
    return records


# [IA] Claude Code (Claude Sonnet 5.5) – execução de um único caso a partir do app Streamlit
def run_case(
    circuit_path: Path,
    topology_path: Path,
    runs: int = 5,
    initial_candidates: int = 10,
    seed: int = 42,
    max_exact_placements: int = 100_000,
    exact_max_qubits: int = 64,
    on_run=None,
) -> list[dict[str, object]]:
    """Executa os quatro métodos em um caso e devolve um registro por execução.

    Cada execução usa a seed ``seed + run - 1``, como o benchmark em lote. A
    busca exata só roda se o número de placements couber em
    ``max_exact_placements``. ``on_run(feitas, total)`` é chamado ao fim de
    cada execução, para o chamador atualizar uma barra de progresso.
    """
    if runs < 1:
        raise ValueError("runs deve ser pelo menos 1")
    if initial_candidates < 1:
        raise ValueError("initial_candidates deve ser pelo menos 1")
    if max_exact_placements < 0:
        raise ValueError("max_exact_placements deve ser não negativo")

    records: list[dict[str, object]] = []
    for run in range(1, runs + 1):
        run_records = _benchmark_case(
            circuit_path,
            topology_path,
            1,
            initial_candidates,
            seed + run - 1,
            max_exact_placements,
            exact_max_qubits,
        )
        for record in run_records:
            record["run"] = run
        records.extend(run_records)
        if on_run is not None:
            on_run(run, runs)
    return records


def benchmark(
    cases: list[tuple[Path, Path]],
    output_path: Path,
    runs: int = 5,
    initial_candidates: int = 10,
    seed: int = 42,
    max_exact_placements: int = 100_000,
    exact_max_qubits: int = DEFAULT_EXACT_MAX_QUBITS,
) -> None:
    if runs < 5:
        raise ValueError("Use pelo menos cinco execuções para cada algoritmo")
    if initial_candidates < 1:
        raise ValueError("initial_candidates deve ser pelo menos 1")
    if max_exact_placements < 0:
        raise ValueError("max_exact_placements deve ser não negativo")
    if exact_max_qubits < 0:
        raise ValueError("exact_max_qubits deve ser não negativo")
    if not cases:
        raise ValueError("Nenhum par circuito/topologia compatível foi selecionado")

    records = []
    for circuit_path, topology_path in cases:
        records.extend(
            _benchmark_case(
                circuit_path,
                topology_path,
                runs,
                initial_candidates,
                seed,
                max_exact_placements,
                exact_max_qubits,
            )
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "algorithm",
        "circuit_category",
        "circuit",
        "topology_category",
        "topology",
        "run",
        "seed",
        "elapsed_seconds",
        "swap_count",
        "expected_error_rate",
        "initial_mapping",
        "final_mapping",
        "possible_mappings",
        "logical_qubits",
        "physical_qubits",
        "initial_candidates",
        "implementation_version",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(
        f"Saved {len(records)} runs across {len(cases)} cases to {output_path}"
    )


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Benchmark mapping algorithms over circuit/topology cases."
    )
    parser.add_argument(
        "--circuit",
        type=Path,
        action="append",
        help="Interaction CSV. Repeat the option to add cases.",
    )
    parser.add_argument(
        "--topology",
        type=Path,
        action="append",
        help="Weighted topology CSV. Repeat the option to add cases.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repository_root / "out" / "parte2" / "mapping_benchmarks.csv",
    )
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--initial-candidates", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--qubit-count",
        type=int,
        action="append",
        help=(
            "Logical qubit count to benchmark. Repeat to add scenarios; "
            f"default: {', '.join(map(str, DEFAULT_QUBIT_COUNTS))}."
        ),
    )
    parser.add_argument(
        "--topology-family",
        choices=TOPOLOGY_FAMILIES,
        action="append",
        help=(
            "Topology family to benchmark. Repeat to add families; "
            f"default: {', '.join(TOPOLOGY_FAMILIES)}."
        ),
    )
    parser.add_argument("--max-exact-placements", type=int, default=100_000)
    parser.add_argument(
        "--exact-max-qubits",
        type=int,
        default=DEFAULT_EXACT_MAX_QUBITS,
        help=(
            "Run exhaustive search only up to this many logical qubits; "
            "set to 0 to disable it."
        ),
    )
    args = parser.parse_args()

    qubit_counts = tuple(args.qubit_count or DEFAULT_QUBIT_COUNTS)
    topology_families = tuple(args.topology_family or TOPOLOGY_FAMILIES)
    available_cases = default_cases(
        repository_root,
        qubit_counts,
        topology_families,
    )
    circuits = args.circuit
    topologies = args.topology
    if circuits is None and topologies is None:
        cases = available_cases
    else:
        circuits = circuits or [
            circuit for circuit, _ in available_cases
        ]
        topologies = topologies or sorted(
            {topology for _, topology in available_cases}
        )
        cases = [
            (circuit, topology)
            for circuit in circuits
            for topology in topologies
            if circuit.is_file()
            and topology.is_file()
            and _qubit_count(circuit) <= _qubit_count(topology)
        ]
    if args.topology_family:
        cases = [
            (circuit, topology)
            for circuit, topology in cases
            if topology.parent.name in topology_families
        ]
    for circuit_path, topology_path in cases:
        if not circuit_path.is_file():
            parser.error(f"Circuit file does not exist: {circuit_path}")
        if not topology_path.is_file():
            parser.error(f"Topology file does not exist: {topology_path}")

    try:
        benchmark(
            cases,
            args.output,
            runs=args.runs,
            initial_candidates=args.initial_candidates,
            seed=args.seed,
            max_exact_placements=args.max_exact_placements,
            exact_max_qubits=args.exact_max_qubits,
        )
    except ValueError as error:
        parser.error(str(error))


def _qubit_count(path: Path) -> int:
    import re

    match = re.search(r"_(\d+)qubits", path.name)
    if not match:
        raise ValueError(f"Could not determine qubit count from filename: {path}")
    return int(match.group(1))


if __name__ == "__main__":
    main()
