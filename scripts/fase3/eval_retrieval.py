"""Avalia só a recuperação (sem LLM): em que posição o dispositivo certo aparece?

Os ALVOS são PROVISÓRIOS: foram escolhidos lendo a lei, não pelo gabarito do oficial/DPO.
Quando o gabarito da planilha estiver preenchido, atualize-os a partir dele.

Uso:
    python scripts/fase3/eval_retrieval.py
    python scripts/fase3/eval_retrieval.py --modos denso bm25 hibrido
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# id da pergunta -> dispositivos aceitos (fonte_id, dispositivo ou None = qualquer um da fonte)
ALVOS: dict[int, list[tuple[str, str | None]]] = {
    1: [("lei_6015_1973", "Art. 17")],
    2: [("lei_6015_1973", "Art. 19")],
    11: [("lei_12527_2011", "Art. 31")],
    18: [("lei_13709_2018", "Art. 18")],
    20: [("lei_6015_1973", "Art. 212"), ("lei_6015_1973", "Art. 213")],
    23: [("prov_cgjce_15_2026", None)],
    25: [("res_anpd_15_2024", None), ("lei_13709_2018", "Art. 48")],
}
PROFUNDIDADE = 50


def posicao(hits: list[dict], aceitos: list[tuple[str, str | None]]) -> int | None:
    for pos, h in enumerate(hits, start=1):
        disp = (h.get("dispositivo") or "").replace(" (ato de aprovação)", "")
        if any(h.get("fonte_id") == f and (d is None or disp == d) for f, d in aceitos):
            return pos
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modos", nargs="+", default=["denso", "bm25", "hibrido"])
    args = ap.parse_args()

    from src.fase3.index import open_collection
    from src.fase3.retrieval import HybridRetriever

    perguntas = {p["id"]: p["pergunta"] for p in json.loads(
        (ROOT / "docs/fase3/benchmark/perguntas.json").read_text(encoding="utf-8"))["perguntas"]}
    col, emb = open_collection()
    ret = HybridRetriever(col, emb)

    print(f"{'#':>3} " + " ".join(f"{m:>8}" for m in args.modos))
    posicoes: dict[str, list[int | None]] = {m: [] for m in args.modos}
    for qid, aceitos in ALVOS.items():
        linha = []
        for modo in args.modos:
            p = posicao(ret.search(perguntas[qid], k=PROFUNDIDADE, modo=modo), aceitos)
            posicoes[modo].append(p)
            linha.append(f"{p if p else '>' + str(PROFUNDIDADE):>8}")
        print(f"{qid:>3} " + " ".join(linha))

    print()
    n = len(ALVOS)
    for modo, ps in posicoes.items():
        r5 = sum(1 for p in ps if p and p <= 5) / n
        r10 = sum(1 for p in ps if p and p <= 10) / n
        mrr = sum(1 / p for p in ps if p) / n
        print(f"{modo:>8}: recall@5={r5:.0%}  recall@10={r10:.0%}  MRR={mrr:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
