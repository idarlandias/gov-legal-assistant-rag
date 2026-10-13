"""Grava uma resposta coletada manualmente (colada de outro sistema), validando o schema.

O texto vem de --arquivo ou do stdin e é gravado EXATAMENTE como recebido (nunca truncado).
O texto da pergunta é preenchido pelo id, a partir do texto oficial. Não sobrescreve sem --force.

Uso:
    python scripts/registrar_resposta.py --sistema jus_ia --pergunta 3 --modelo "Jus IA (plano Pro)" \
        --arquivo resposta.txt
    Get-Content resposta.txt -Raw | python scripts/registrar_resposta.py --sistema llm_generico --pergunta 26 \
        --modelo "ChatGPT (GPT-5, plano Plus)" --citacao "Art. 1.103 do Código de Normas"
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from pydantic import ValidationError  # noqa: E402

from src.fase3.coleta import (  # noqa: E402
    DIR_COLETA, FUSO_COLETA, SISTEMA_PROPRIO, RespostaColetada, gravar, perguntas_oficiais,
)


def ler_texto(arquivo: Path | None) -> str:
    """Texto integral; só o BOM (marca do PowerShell/Notepad, não conteúdo) é descartado."""
    dados = arquivo.read_bytes() if arquivo else sys.stdin.buffer.read()
    return dados.decode("utf-8-sig")


def montar(args, texto: str) -> RespostaColetada:
    return RespostaColetada(
        pergunta_id=args.pergunta,
        pergunta_texto=perguntas_oficiais().get(args.pergunta, ""),
        sistema=args.sistema,
        modelo_ou_plano=args.modelo,
        coletado_em=args.coletado_em or datetime.now(FUSO_COLETA).isoformat(timespec="seconds"),
        resposta_integral=texto,
        citacoes_declaradas=args.citacao or [],
        recusou_responder=args.recusou,
        observacao=args.observacao or "",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sistema", required=True)
    ap.add_argument("--pergunta", type=int, required=True)
    ap.add_argument("--modelo", required=True, help="Modelo ou plano usado na coleta")
    ap.add_argument("--arquivo", type=Path, help="Arquivo com a resposta (sem ele, lê do stdin)")
    ap.add_argument("--citacao", action="append", help="Citação declarada à parte (repetível)")
    ap.add_argument("--recusou", action="store_true", help="O sistema se recusou a responder")
    ap.add_argument("--observacao")
    ap.add_argument("--coletado-em", help="ISO 8601 -03:00 (padrão: agora)")
    ap.add_argument("--base", type=Path, default=DIR_COLETA)
    ap.add_argument("--force", action="store_true", help="Sobrescreve resposta já registrada")
    args = ap.parse_args(argv)

    try:
        resp = montar(args, ler_texto(args.arquivo))
        if resp.sistema == SISTEMA_PROPRIO:
            ap.error("o RAG próprio entra pela exportação do benchmark (scripts/exportar_rag_coleta.py)")
        destino = gravar(resp, args.base, force=args.force)
    except ValidationError as e:
        print(f"Resposta inválida:\n{e}", file=sys.stderr)
        return 2
    except FileExistsError as e:
        print(str(e), file=sys.stderr)
        return 3
    print(f"gravado: {destino} ({len(resp.resposta_integral)} caracteres)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
