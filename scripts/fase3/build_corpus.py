"""Monta o corpus da Fase 3: baixa as fontes oficiais e indexa na coleção Chroma "fase3".

Uso:
    python scripts/fase3/build_corpus.py              # download + index
    python scripts/fase3/build_corpus.py download     # só baixa / verifica mudanças
    python scripts/fase3/build_corpus.py index        # só reindexa a partir de raw/
    python scripts/fase3/build_corpus.py stats        # resumo do manifest
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", nargs="?", default="all", choices=["all", "download", "index", "stats"])
    ap.add_argument("--only", help="IDs de fonte separados por vírgula (padrão: todas)")
    args = ap.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from src.fase3.corpus import download, load_manifest
    from src.fase3.sources import FONTES, FONTES_POR_ID

    fontes = FONTES
    if args.only:
        ids = args.only.split(",")
        faltando = [i for i in ids if i not in FONTES_POR_ID]
        if faltando:
            print(f"ERRO: fontes desconhecidas: {faltando}", file=sys.stderr)
            return 1
        fontes = [FONTES_POR_ID[i] for i in ids]

    if args.acao in ("all", "download"):
        print("Baixando fontes oficiais...")
        status = download(fontes)
        for fid, st in status.items():
            print(f"  {fid:22} {st}")
        erros = [f for f, s in status.items() if s.startswith("ERRO")]
        if erros:
            print(f"FALHA no download de {erros}; índice não foi alterado.", file=sys.stderr)
            return 1

    if args.acao in ("all", "index"):
        if args.only:
            print("ERRO: index sempre reconstrói todas as fontes (sem --only).", file=sys.stderr)
            return 1
        from src.fase3.index import COLLECTION, rebuild

        print(f"Indexando na coleção '{COLLECTION}'...")
        stats = rebuild(FONTES)
        for fid, st in stats.items():
            print(f"  {fid:22} {st['dispositivos']:5} dispositivos  {st['chunks']:5} chunks")
        print(f"Total: {sum(s['chunks'] for s in stats.values())} chunks")

    if args.acao == "stats":
        for fid, m in load_manifest().items():
            idx = m.get("indice", {})
            print(f"{fid:22} {m.get('bytes', 0) // 1024:6} KB  baixado {m.get('baixado_em')}  "
                  f"{idx.get('dispositivos', '-')} disp / {idx.get('chunks', '-')} chunks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
