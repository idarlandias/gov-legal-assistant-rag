"""Converte as respostas dos formulários online (CSV baixado da planilha do Google) nos arquivos de avaliação.

Na planilha de respostas: Arquivo > Fazer download > Valores separados por vírgula (.csv).

Uso:
    python scripts/folha_gabarito/ler_respostas_forms.py pesquisa respostas_pesquisa.csv
        → data/validacao/gabarito_rcpn.csv + respostas_parte_b_<cartorio>.json (última resposta, ou --linha N)
    python scripts/folha_gabarito/ler_respostas_forms.py diario respostas_diario.csv
        → data/validacao/diario_balcao_<cartorio>.csv (um arquivo por cartório)

Os arquivos gerados ficam no .gitignore: contêm o nome do Oficial e dados reais do balcão.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import avaliar_gabarito as ag  # noqa: E402
import forms_config as fc  # noqa: E402
import resumir_diario as rd  # noqa: E402

DIR_VALIDACAO = RAIZ / "data" / "validacao"


class RespostaInvalida(ValueError):
    pass


def _codigo(pares, rotulo: str) -> str:
    """Texto exibido no formulário → código; vazio continua vazio."""
    rotulo = (rotulo or "").strip()
    if not rotulo:
        return ""
    for codigo, texto in pares:
        if texto == rotulo:
            return codigo
    raise RespostaInvalida(f"opção não reconhecida: {rotulo!r}")


def _slug(texto: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_") or "cartorio"


def _ler_csv(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def pesquisa(linhas: list[dict], destino: Path = DIR_VALIDACAO, indice: int = -1) -> dict:
    if not linhas:
        raise RespostaInvalida("o CSV da pesquisa não tem respostas")
    r = {k.strip(): (v or "").strip() for k, v in linhas[indice].items()}
    nome, funcao = r.get(fc.VALIDACAO["nome"], ""), r.get(fc.VALIDACAO["funcao"], "")
    data = r.get("Carimbo de data/hora") or r.get("Timestamp", "")
    validado_por = nome + (f" ({funcao})" if funcao else "")
    cartorio = _slug(r.get(fc.VALIDACAO["cartorio"], "") or r.get(fc.VALIDACAO["municipio"], ""))
    avisos, respondidos = [], 0

    caminho = destino / ag.GABARITO_RCPN.name
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ag.COLUNAS_GABARITO, lineterminator="\n")
        w.writeheader()
        for caso in ag.casos_rcpn():
            n = caso["id"]
            decisao = _codigo(fc.DECISOES, r.get(fc.t_decisao(n), ""))
            fundamentos = r.get(fc.t_fundamentos(n), "")
            respondidos += bool(decisao)
            if decisao and not fundamentos:
                avisos.append(f"caso {n}: decisão marcada sem fundamentos (a avaliação exige fundamentos)")
            w.writerow({"pergunta_id": n, "pergunta": caso["pergunta"], "atribuicao": "RCPN",
                        "decisao_esperada": decisao, "quem_decide": _codigo(fc.QUEM_DECIDE, r.get(fc.t_quem(n), "")),
                        "fundamentos": fundamentos, "resposta_esperada": r.get(fc.t_como(n), ""),
                        "erro_grave_se": r.get(fc.t_erro(n), ""),
                        "validado_por": validado_por if decisao and nome else "",
                        "data_validacao": data if decisao and nome else ""})
    if not nome:
        avisos.append("resposta sem nome: os casos não contam como validados")

    parte_b = destino / f"respostas_parte_b_{cartorio}.json"
    parte_b.write_text(json.dumps({
        "parte_b": {fc.t_b(i): r.get(fc.t_b(i), "") for i in range(1, len(fc.PERGUNTAS_B) + 1)},
        "autorizacao": _codigo(fc.AUTORIZACAO, r.get(fc.VALIDACAO["autorizacao"], "")),
        "cartorio": r.get(fc.VALIDACAO["cartorio"], ""), "municipio": r.get(fc.VALIDACAO["municipio"], ""),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"arquivos": [str(caminho), str(parte_b)], "avisos": avisos, "casos_respondidos": respondidos}


def diario(linhas: list[dict], destino: Path = DIR_VALIDACAO) -> dict:
    d = fc.DIARIO
    por_cartorio: dict[str, list[dict]] = defaultdict(list)
    for r in linhas:
        r = {k.strip(): (v or "").strip() for k, v in r.items()}
        cartorio = _slug(r.get(d["cartorio"], ""))
        por_cartorio[cartorio].append({
            "data": r.get(d["data"], ""), "cartorio": cartorio,
            "atribuicao": _codigo(fc.DIARIO_ATRIBUICAO, r.get(d["atribuicao"], "")),
            "tipo_pedido": r.get(d["tipo"], ""), "perfil_requerente": r.get(d["perfil"], ""),
            "canal_entrada": _codigo(fc.DIARIO_CANAL, r.get(d["canal"], "")),
            "gerou_duvida": _codigo(fc.DIARIO_DUVIDA, r.get(d["duvida"], "")),
            "quem_decidiu": _codigo(fc.DIARIO_QUEM, r.get(d["quem"], "")),
            "tempo_min": r.get(d["tempo"], ""), "consultou": "",
            "desfecho": _codigo(fc.DIARIO_DESFECHO, r.get(d["desfecho"], "")), "observacao": "",
        })
    arquivos = []
    for cartorio, regs in sorted(por_cartorio.items()):
        caminho = destino / f"diario_balcao_{cartorio}.csv"
        with caminho.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rd.COLUNAS, lineterminator="\n")
            w.writeheader()
            w.writerows(regs)
        rd.ler_diario(caminho)  # valida no formato do resumidor
        arquivos.append(str(caminho))
    return {"arquivos": arquivos, "avisos": [], "pedidos": sum(len(v) for v in por_cartorio.values())}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("formulario", choices=("pesquisa", "diario"))
    ap.add_argument("csv", type=Path)
    ap.add_argument("--linha", type=int, default=-1, help="Qual resposta da pesquisa usar (padrão: a última)")
    ap.add_argument("--destino", type=Path, default=DIR_VALIDACAO)
    args = ap.parse_args()
    try:
        linhas = _ler_csv(args.csv)
        res = pesquisa(linhas, args.destino, args.linha) if args.formulario == "pesquisa" else diario(linhas,
                                                                                                    args.destino)
    except (RespostaInvalida, rd.LinhaInvalida) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2
    for a in res["arquivos"]:
        print("gravado:", a)
    for a in res["avisos"]:
        print("aviso:", a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
