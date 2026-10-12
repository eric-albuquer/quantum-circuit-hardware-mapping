import logging
from pathlib import Path

from mqt.bench import BenchmarkLevel, get_benchmark
from qiskit import qasm2

from dataset_generation.paths import DATASETS_ROOT


LOGGER = logging.getLogger(__name__)
BENCHMARKS = (
    "bmw_quark_cardinality",
    "bmw_quark_copula",
    "bv",
    "cdkm_ripple_carry_adder",
    "dj",
    "draper_qft_adder",
    "full_adder",
    "ghz",
    "graphstate",
    "grover",
    "half_adder",
    "hhl",
    "hrs_cumulative_multiplier",
    "modular_adder",
    "multiplier",
    "qaoa",
    "qft",
    "qftentangled",
    "qnn",
    "qpeexact",
    "qpeinexact",
    "qwalk",
    "rg_qft_multiplier",
    "seven_qubit_steane_code",
    "shor",
    "shors_nine_qubit_code",
    "vbe_ripple_carry_adder",
    "vqe_real_amp",
    "vqe_su2",
    "vqe_two_local",
    "wstate",
)


def _is_supported_size(benchmark: str, qubit_count: int) -> bool:
    if benchmark == "grover" and qubit_count > 10:
        return False
    if benchmark in {"shor", "hhl"} and qubit_count > 15:
        return False
    if "multiplier" in benchmark and qubit_count > 16:
        return False
    if "adder" in benchmark and qubit_count > 20:
        return False
    return True


def generate_benchmarks(
    output_root: Path = DATASETS_ROOT / "algorithms",
    qubit_counts: range = range(3, 31),
) -> None:
    """Generate MQT benchmark circuits, grouped by benchmark name."""
    output_root.mkdir(parents=True, exist_ok=True)
    generated = 0
    skipped = 0

    for benchmark in BENCHMARKS:
        benchmark_dir = output_root / benchmark
        for qubit_count in qubit_counts:
            if not _is_supported_size(benchmark, qubit_count):
                continue

            try:
                circuit = get_benchmark(
                    benchmark=benchmark,
                    level=BenchmarkLevel.ALG,
                    circuit_size=qubit_count,
                )
                benchmark_dir.mkdir(parents=True, exist_ok=True)
                output_path = benchmark_dir / f"{benchmark}_{qubit_count}qubits.qasm"
                qasm2.dump(circuit, str(output_path))
                generated += 1
            except Exception as error:
                skipped += 1
                LOGGER.warning(
                    "Skipped benchmark %s at %d qubits: %s",
                    benchmark,
                    qubit_count,
                    error,
                )

    LOGGER.info(
        "Benchmark generation complete: %d circuits generated, %d unsupported or failed requests.",
        generated,
        skipped,
    )
