# [IA] Claude Code (Claude Sonnet 5.5) – execução de um caso em processo separado para o app Streamlit
"""Executa os quatro métodos em um caso e imprime o resultado como JSON.

O app Streamlit chama este módulo em um subprocesso, em vez de rodar o Qiskit
dentro da thread do script (onde ele derrubou o interpretador). Protocolo na
saída padrão, uma linha JSON por mensagem:

    {"progress": <execuções feitas>, "total": <execuções>}
    {"records": [<um registro por algoritmo e execução>]}

Todo o resto que os algoritmos imprimem vai para a saída de erro.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path

from analysis.benchmark_mappers import run_case


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--circuit", type=Path, required=True)
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--initial-candidates", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-exact-placements", type=int, default=100_000)
    args = parser.parse_args(argv)

    protocol = sys.stdout

    def emit(message: dict[str, object]) -> None:
        protocol.write(json.dumps(message) + "\n")
        protocol.flush()

    with contextlib.redirect_stdout(sys.stderr):
        records = run_case(
            args.circuit,
            args.topology,
            runs=args.runs,
            initial_candidates=args.initial_candidates,
            seed=args.seed,
            max_exact_placements=args.max_exact_placements,
            on_run=lambda done, total: emit({"progress": done, "total": total}),
        )
    emit({"records": records})


if __name__ == "__main__":
    main()
