"""Exporta as respostas de uma execução do benchmark do RAG para o formato da coleta.

Assim o RAG próprio é pontuado pelo mesmo caminho dos concorrentes (scripts/pontuar_coleta.py).
Os rótulos de fontes recuperadas viram `trechos_recuperados` (base da camada 2).

Uso:
    python scripts/exportar_rag_coleta.py docs/fase3/benchmark/results/rag-fase3-20261013-113528-reverificado.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.fase3.coleta import DIR_COLETA, SISTEMA_PROPRIO, RespostaColetada, gravar  # noqa: E402

RECUSA = {"NAO_ENCONTRADO", "RESPOSTA_VAZIA", "ERRO"}


def _trechos(fontes: str) -> list[str]:
    return [f.strip() for f in (fontes or "").split(";") if f.strip()]


def converter(execucao: dict, origem: str) -> list[RespostaColetada]:
    meta = execucao["meta"]
    coletado_em = meta["data"] if meta["data"][-6] in "+-" else meta["data"] + "-03:00"
    saida = []
    for r in execucao["resultados"]:
        status = r.get("status_resposta") or ""
        saida.append(RespostaColetada(
            pergunta_id=r["id"],
            pergunta_texto=r["pergunta"],
            sistema=SISTEMA_PROPRIO,
            modelo_ou_plano=r.get("modelo") or meta.get("llm_model") or "",
            coletado_em=coletado_em,
            resposta_integral=r.get("resposta") or "",
            citacoes_declaradas=[],
            recusou_responder=status in RECUSA,
            observacao=f"Exportado de {origem} (status_resposta={status}, k={meta.get('k')}, "
                       f"filtro={meta.get('filtro_especialidade')}, commit {meta.get('git_commit')}).",
            trechos_recuperados=_trechos(r.get("fontes", "")),
        ))
    return saida


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("execucao", type=Path)
    ap.add_argument("--base", type=Path, default=DIR_COLETA)
    ap.add_argument("--force", action="store_true", help="Sobrescreve respostas já exportadas")
    args = ap.parse_args()

    execucao = json.loads(args.execucao.read_text(encoding="utf-8"))
    origem = args.execucao.name
    respostas = converter(execucao, origem)
    for r in respostas:
        gravar(r, args.base, force=args.force)
    print(f"{len(respostas)} respostas exportadas para {args.base / SISTEMA_PROPRIO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
