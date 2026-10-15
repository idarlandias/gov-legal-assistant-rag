"""Lê o PDF preenchido pelo cartório e gera os arquivos de avaliação, sem transcrição manual.

Saídas em data/validacao/ (todas no .gitignore: contêm o nome do Oficial e dados reais do balcão):
    gabarito_rcpn.csv                  Parte A, no formato de scripts/avaliar_gabarito.py
    diario_balcao_<cartorio>.csv       Parte C, no formato de scripts/resumir_diario.py
    respostas_parte_b_<cartorio>.json  Parte B e a autorização de uso do nome

Uso:
    python scripts/folha_gabarito/ler_pdf_preenchido.py caminho/do/pdf_devolvido.pdf --cartorio russas_rcpn
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

from pypdf import PdfReader

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "scripts" / "folha_gabarito"))

import avaliar_gabarito as ag  # noqa: E402
import resumir_diario as rd  # noqa: E402
from gerar_pdf_preenchivel import COLS_DIARIO, LINHAS_DIARIO, PERGUNTAS_B, VAZIO  # noqa: E402

DIR_VALIDACAO = RAIZ / "data" / "validacao"


def _valor(campo: dict | None) -> str:
    if not campo:
        return ""
    v = campo.get("/V", "")
    v = str(v).strip()
    if v.startswith("/"):
        v = v[1:]  # radio: "/DEFERIR" → "DEFERIR"
    return "" if v in (VAZIO, "Off") else v


def _slug(texto: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_") or "cartorio"


def ler(pdf: Path) -> dict:
    campos = PdfReader(str(pdf)).get_fields() or {}

    def v(nome: str) -> str:
        return _valor(campos.get(nome))

    casos = []
    for caso in ag.casos_rcpn():
        n = caso["id"]
        casos.append({"id": n, "pergunta": caso["pergunta"], "decisao": v(f"caso_{n}_decisao"),
                      "quem_decide": v(f"caso_{n}_quem_decide"), "fundamentos": v(f"caso_{n}_fundamentos"),
                      "como_atender": v(f"caso_{n}_como_atender"), "erro_grave": v(f"caso_{n}_erro_grave")})
    diario = []
    for linha in range(1, LINHAS_DIARIO + 1):
        reg = {campo: v(f"diario_{linha:02d}_{campo}") for campo, *_ in COLS_DIARIO}
        if any(reg.values()):
            diario.append(reg | {"linha": linha})
    return {
        "casos": casos,
        "parte_b": {f"{i}. {p}": v(f"b_{i}") for i, p in enumerate(PERGUNTAS_B, start=1)},
        "diario": diario,
        "validacao": {k: v(f"val_{k}") for k in ("nome", "funcao", "serventia", "data", "assinatura", "autorizacao")},
        "carta": {k: v(f"carta_{k}") for k in ("serventia", "municipio", "local_data")},
    }


def gravar(dados: dict, cartorio: str, destino: Path = DIR_VALIDACAO) -> dict[str, list[str]]:
    avisos: list[str] = []
    val = dados["validacao"]
    validado_por = val["nome"] + (f" ({val['funcao']})" if val["funcao"] else "")
    respondidos = [c for c in dados["casos"] if c["decisao"]]
    arquivos = []

    if respondidos:
        caminho = destino / ag.GABARITO_RCPN.name
        with caminho.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=ag.COLUNAS_GABARITO, lineterminator="\n")
            w.writeheader()
            for c in dados["casos"]:
                w.writerow({"pergunta_id": c["id"], "pergunta": c["pergunta"], "atribuicao": "RCPN",
                            "decisao_esperada": c["decisao"], "quem_decide": c["quem_decide"],
                            "fundamentos": c["fundamentos"], "resposta_esperada": c["como_atender"],
                            "erro_grave_se": c["erro_grave"], "validado_por": validado_por if c["decisao"] else "",
                            "data_validacao": val["data"] if c["decisao"] else ""})
                if c["decisao"] and not c["fundamentos"]:
                    avisos.append(f"caso {c['id']}: decisão marcada sem fundamentos (a avaliação exige fundamentos)")
        if not val["nome"]:
            avisos.append("validação sem nome: os casos não contam como validados até o nome ser preenchido")
        arquivos.append(str(caminho))

    completos = []
    for reg in dados["diario"]:
        faltam = [c for c in ("data", "atribuicao", "gerou_duvida", "quem_decidiu", "desfecho") if not reg[c]]
        if faltam:
            avisos.append(f"diário, linha {reg['linha']}: faltam {', '.join(faltam)} (linha ignorada)")
        else:
            completos.append(reg)
    if completos:
        caminho = destino / f"diario_balcao_{cartorio}.csv"
        with caminho.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rd.COLUNAS, lineterminator="\n")
            w.writeheader()
            for reg in completos:
                w.writerow({"data": reg["data"], "cartorio": cartorio, "atribuicao": reg["atribuicao"],
                            "tipo_pedido": reg["tipo_pedido"], "perfil_requerente": reg["perfil_requerente"],
                            "canal_entrada": "balcao", "gerou_duvida": reg["gerou_duvida"],
                            "quem_decidiu": reg["quem_decidiu"], "tempo_min": reg["tempo_min"],
                            "consultou": "", "desfecho": reg["desfecho"], "observacao": ""})
        rd.ler_diario(caminho)  # valida no formato do resumidor
        arquivos.append(str(caminho))

    caminho = destino / f"respostas_parte_b_{cartorio}.json"
    caminho.write_text(json.dumps({"parte_b": dados["parte_b"], "autorizacao": val["autorizacao"],
                                   "serventia": val["serventia"] or dados["carta"]["serventia"]},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
    arquivos.append(str(caminho))
    return {"arquivos": arquivos, "avisos": avisos}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--cartorio", help="Apelido curto do cartório (padrão: derivado da serventia)")
    ap.add_argument("--destino", type=Path, default=DIR_VALIDACAO)
    args = ap.parse_args()

    dados = ler(args.pdf)
    cartorio = args.cartorio or _slug(dados["validacao"]["serventia"] or dados["carta"]["municipio"])
    res = gravar(dados, cartorio, args.destino)
    print(f"casos respondidos: {sum(1 for c in dados['casos'] if c['decisao'])} de {len(dados['casos'])} | "
          f"linhas do diário: {len(dados['diario'])} | autorização: {dados['validacao']['autorizacao'] or 'não marcada'}")
    for a in res["arquivos"]:
        print("gravado:", a)
    for a in res["avisos"]:
        print("aviso:", a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
