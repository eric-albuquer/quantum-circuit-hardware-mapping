# [IA] Claude Code (Claude Sonnet 5.5) – nomes legíveis para circuitos, topologias e famílias
"""Rótulos de exibição para os nomes dos datasets.

Os nomes internos (``modular_adder_14qubits``, ``heavy_hex_19qubits``) são
nomes de arquivo e continuam sendo usados para localizar dados. Estas funções
só produzem o texto mostrado ao usuário.
"""

from __future__ import annotations

import re

ACRONYMS = {
    "bmw", "bv", "cdkm", "dj", "ghz", "hhl", "hrs", "qaoa", "qft", "qnn",
    "qpe", "rg", "su2", "vbe", "vqe",
}
# Nomes de benchmark escritos sem separador, que o título automático não quebra.
JOINED_WORDS = {
    "graphstate": "Graph State",
    "qftentangled": "QFT Entangled",
    "qpeexact": "QPE Exact",
    "qpeinexact": "QPE Inexact",
    "qwalk": "Quantum Walk",
    "wstate": "W State",
}
_QUBITS_SUFFIX = re.compile(r"_(\d+)qubits$")
_DEPTH_PART = re.compile(r"_depth(\d+)_id\d+$")


def _words(text: str) -> str:
    """Troca ``_`` por espaço e põe cada palavra em maiúscula (siglas em caixa alta)."""
    words = []
    for word in text.split("_"):
        if word in JOINED_WORDS:
            words.append(JOINED_WORDS[word])
        elif word in ACRONYMS:
            words.append(word.upper())
        else:
            words.append(word.capitalize())
    return " ".join(words)


def dataset_label(name: object) -> str:
    """Rótulo legível para uma família, um circuito ou uma topologia.

    ``modular_adder`` -> ``Modular Adder``;
    ``modular_adder_14qubits`` -> ``Modular Adder · 14 qubits``;
    ``grid_3x3_9qubits`` -> ``Grid 3x3 · 9 qubits``;
    ``random_4qubits_depth10_id0`` -> ``Random · 4 qubits · profundidade 10``.
    Valores que não são texto (ou que já são rótulos, como ``Todas``) passam
    sem alteração.
    """
    if not isinstance(name, str):
        return str(name)
    text = name
    suffix = []
    depth = _DEPTH_PART.search(text)
    if depth:
        text = text[: depth.start()]
        suffix.append(f"profundidade {depth.group(1)}")
    qubits = _QUBITS_SUFFIX.search(text)
    if qubits:
        text = text[: qubits.start()]
        suffix.insert(0, f"{qubits.group(1)} qubits")
    elif re.search(r"_(\d+)qubits_depth", name):
        # random_<n>qubits_depth<d>_id<i>: o número de qubits fica antes da profundidade.
        match = re.match(r"^(.*?)_(\d+)qubits$", text)
        if match:
            text = match.group(1)
            suffix.insert(0, f"{match.group(2)} qubits")
    return " · ".join([_words(text), *suffix])
