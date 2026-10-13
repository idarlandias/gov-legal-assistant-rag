"""Matriz do que já foi coletado e do que falta, por sistema e pergunta (1–25 do benchmark + 26 externa).

Uso:
    python scripts/status_coleta.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.fase3.coleta import DIR_COLETA, SISTEMAS, ler_todas, perguntas_oficiais  # noqa: E402


def matriz(base: Path = DIR_COLETA) -> tuple[str, dict[str, list[int]]]:
    todas = ler_todas(base)
    ids = sorted(perguntas_oficiais())
    faltam = {s: [i for i in ids if i not in todas.get(s, {})] for s in SISTEMAS}
    largura = max(len(s) for s in SISTEMAS)
    linhas = [" " * largura + "  " + "".join(f"{i:>3}" for i in ids) + "   coletadas"]
    for s in SISTEMAS:
        marcas = "".join("  X" if i in todas.get(s, {}) else "  ." for i in ids)
        linhas.append(f"{s:<{largura}}  {marcas}   {len(ids) - len(faltam[s])}/{len(ids)}")
    return "\n".join(linhas), faltam


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, default=DIR_COLETA)
    args = ap.parse_args()
    texto, faltam = matriz(args.base)
    print(texto)
    print("\nX = coletada  . = falta")
    for s, ids in faltam.items():
        if ids:
            print(f"faltam em {s}: {', '.join(map(str, ids))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
