"""Resume diários de balcão e aplica o critério de continuidade da validação.

Cada cartório preenche uma cópia de data/validacao/diario_balcao_modelo.csv (uma linha por pedido,
SEM nome, CPF ou qualquer dado pessoal) e salva como data/validacao/diario_balcao_<cartorio>.csv
(gitignored). Este script lê todas as cópias e responde:
  - quantas dúvidas reais por dia cada cartório tem, separando Registro de Imóveis e Registro Civil;
  - quem decide quando há dúvida (escrevente ou oficial) e quanto tempo leva;
  - se o critério sugerido na validação (>= 1 dúvida real por dia por cartório) foi atingido.

Uso:
    python scripts/resumir_diario.py
    python scripts/resumir_diario.py --criterio 1.0 --saida docs/fase3/diario_balcao_resumo.md
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DIR_VALIDACAO = RAIZ / "data" / "validacao"
MODELO = DIR_VALIDACAO / "diario_balcao_modelo.csv"

COLUNAS = ("data", "cartorio", "atribuicao", "tipo_pedido", "perfil_requerente", "canal_entrada",
           "gerou_duvida", "quem_decidiu", "tempo_min", "consultou", "desfecho", "observacao")
VALORES = {
    "atribuicao": {"RI", "RCPN", "NOTAS", "PROTESTO", "RTD_PJ", "OUTRA"},
    "canal_entrada": {"balcao", "telefone", "email", "whatsapp", "online"},
    "gerou_duvida": {"sim", "nao"},
    "quem_decidiu": {"escrevente", "oficial", "substituto", "consulta_externa", "nao_se_aplica"},
    "desfecho": {"emitida", "emitida_com_exigencia", "exigencia_pendente", "recusada_nota", "orientado",
                 "encaminhado_juiz", "desistiu"},
}
CRITERIO_PADRAO = 1.0  # dúvidas reais por dia por cartório (sugestão da validação de 15/10/2026)


class LinhaInvalida(ValueError):
    pass


def ler_diario(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        if tuple(leitor.fieldnames or ()) != COLUNAS:
            raise LinhaInvalida(f"{caminho.name}: colunas diferentes do modelo {COLUNAS}")
        linhas = []
        for n, linha in enumerate(leitor, start=2):
            linha = {k: (v or "").strip() for k, v in linha.items()}
            if not any(linha.values()):
                continue
            for campo, validos in VALORES.items():
                if linha[campo] not in validos:
                    raise LinhaInvalida(f"{caminho.name}:{n}: {campo}={linha[campo]!r} fora de {sorted(validos)}")
            if not linha["data"] or not linha["cartorio"]:
                raise LinhaInvalida(f"{caminho.name}:{n}: data e cartorio são obrigatórios")
            try:
                linha["tempo_min"] = float(linha["tempo_min"].replace(",", ".")) if linha["tempo_min"] else None
            except ValueError as e:
                raise LinhaInvalida(f"{caminho.name}:{n}: tempo_min não numérico") from e
            linhas.append(linha)
    return linhas


def resumir(linhas: list[dict], criterio: float = CRITERIO_PADRAO) -> dict:
    por_cartorio: dict[str, list[dict]] = defaultdict(list)
    for linha in linhas:
        por_cartorio[linha["cartorio"]].append(linha)

    cartorios = {}
    for cartorio, ls in sorted(por_cartorio.items()):
        dias = len({ls_["data"] for ls_ in ls})
        duvidas = [x for x in ls if x["gerou_duvida"] == "sim"]
        por_atrib = {}
        for atrib in sorted({x["atribuicao"] for x in ls}):
            da = [x for x in ls if x["atribuicao"] == atrib]
            dv = [x for x in da if x["gerou_duvida"] == "sim"]
            por_atrib[atrib] = {"pedidos": len(da), "duvidas": len(dv), "duvidas_por_dia": round(len(dv) / dias, 2)}
        tempos = [x["tempo_min"] for x in duvidas if x["tempo_min"] is not None]
        decisores = defaultdict(int)
        for x in duvidas:
            decisores[x["quem_decidiu"]] += 1
        cartorios[cartorio] = {
            "dias": dias,
            "pedidos": len(ls),
            "duvidas": len(duvidas),
            "duvidas_por_dia": round(len(duvidas) / dias, 2),
            "tempo_mediano_duvida_min": statistics.median(tempos) if tempos else None,
            "quem_decidiu_nas_duvidas": dict(decisores),
            "por_atribuicao": por_atrib,
            "atinge_criterio": len(duvidas) / dias >= criterio,
        }
    return {
        "criterio_duvidas_por_dia": criterio,
        "cartorios": cartorios,
        "cartorios_que_atingem": sum(c["atinge_criterio"] for c in cartorios.values()),
        "total_cartorios": len(cartorios),
    }


def markdown(res: dict) -> str:
    linhas = [
        "# Resumo do diário de balcão",
        "",
        f"Critério: pelo menos **{res['criterio_duvidas_por_dia']:g} dúvida real por dia** por cartório. "
        f"Atingem: **{res['cartorios_que_atingem']} de {res['total_cartorios']}**.",
        "",
        "| Cartório | Dias | Pedidos | Dúvidas | Dúvidas/dia | RI dúvidas/dia | RCPN dúvidas/dia | Tempo mediano (min) "
        "| Decisão nas dúvidas | Critério |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for nome, c in res["cartorios"].items():
        ri = c["por_atribuicao"].get("RI", {}).get("duvidas_por_dia", 0)
        rc = c["por_atribuicao"].get("RCPN", {}).get("duvidas_por_dia", 0)
        dec = ", ".join(f"{k} {v}" for k, v in sorted(c["quem_decidiu_nas_duvidas"].items())) or "—"
        tempo = "—" if c["tempo_mediano_duvida_min"] is None else f"{c['tempo_mediano_duvida_min']:g}"
        linhas.append(f"| {nome} | {c['dias']} | {c['pedidos']} | {c['duvidas']} | {c['duvidas_por_dia']:g} | {ri:g} "
                      f"| {rc:g} | {tempo} | {dec} | {'atinge' if c['atinge_criterio'] else 'não atinge'} |")
    linhas += ["", "Dados sem nenhuma informação pessoal: uma linha por pedido, só tipo, perfil e desfecho.", ""]
    return "\n".join(linhas)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=DIR_VALIDACAO)
    ap.add_argument("--criterio", type=float, default=CRITERIO_PADRAO)
    ap.add_argument("--saida", type=Path, help="Grava o resumo em Markdown")
    args = ap.parse_args()

    arquivos = sorted(p for p in args.dir.glob("diario_balcao_*.csv") if p.name != MODELO.name)
    if not arquivos:
        print(f"Nenhum diário preenchido em {args.dir} (copie {MODELO.name} para diario_balcao_<cartorio>.csv).")
        return 1
    try:
        linhas = [linha for arq in arquivos for linha in ler_diario(arq)]
    except LinhaInvalida as e:
        print(f"Diário inválido: {e}", file=sys.stderr)
        return 2
    texto = markdown(resumir(linhas, args.criterio))
    print(texto)
    if args.saida:
        args.saida.write_text(texto, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
