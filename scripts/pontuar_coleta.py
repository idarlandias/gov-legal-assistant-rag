"""Pontua as respostas coletadas, sem LLM, em duas camadas que NUNCA se misturam.

CAMADA 1 (existência) — vale para qualquer sistema e é a ÚNICA que entra em comparação:
    cada citação extraída pelo extrator do verificador v2 é conferida contra o corpus inteiro
    (data/corpus_fase3/dispositivos.jsonl): EXISTE / ARTIGO_INEXISTENTE_NA_NORMA / NORMA_FORA_DO_CORPUS.
    Citação sem norma declarada: EXISTE se o artigo existir em alguma norma do corpus, senão
    ARTIGO_INEXISTENTE_NA_NORMA; o total dessas citações é publicado à parte (sem_norma_declarada).

CAMADA 2 (ancoragem) — só o RAG próprio, que expõe os trechos recuperados:
    verificador v2 contra trechos_recuperados (VERIFICADA / NORMA_DIVERGENTE / NAO_RECUPERADA /
    FORA_DO_CORPUS). Sai em seção separada, jamais em tabela comparativa.

Uso:
    python scripts/pontuar_coleta.py                                  # imprime a camada 1 por sistema
    python scripts/pontuar_coleta.py --sistemas assistente_registral_ce \
        --relatorio docs/fase3/pontuacao_rag_2026-10-13.md
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from enum import Enum
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.fase3.coleta import (  # noqa: E402
    DIR_COLETA, PERGUNTA_26_ID, SISTEMA_PROPRIO, SISTEMAS, RespostaColetada, ler_todas,
)
from src.fase3.sources import FONTES_POR_ID  # noqa: E402
from src.fase3.verificador_citacoes import (  # noqa: E402
    VERIFICADOR_VERSAO, _chave_de_artigo, _extrair, _mencoes_de_norma, _normalizar, _rotulo, verificar,
)

CORPUS = RAIZ / "data" / "corpus_fase3" / "dispositivos.jsonl"
SIGLA_CE = FONTES_POR_ID["codigo_normas_ce"].sigla
SIGLA_PROV15 = FONTES_POR_ID["prov_cgjce_15_2026"].sigla
NORMAS_CE = {SIGLA_CE, SIGLA_PROV15}


class Existencia(str, Enum):
    EXISTE = "EXISTE"
    ARTIGO_INEXISTENTE_NA_NORMA = "ARTIGO_INEXISTENTE_NA_NORMA"
    NORMA_FORA_DO_CORPUS = "NORMA_FORA_DO_CORPUS"


# Únicos campos que uma saída comparativa pode conter (todos de camada 1)
CAMPOS_COMPARATIVOS = (
    ("respostas", "Respostas pontuadas"),
    ("citacoes", "Citações de artigo"),
    (Existencia.EXISTE.value, "Existem na norma citada"),
    (Existencia.ARTIGO_INEXISTENTE_NA_NORMA.value, "Artigo inexistente na norma"),
    (Existencia.NORMA_FORA_DO_CORPUS.value, "Norma fora do corpus"),
    ("sem_norma_declarada", "Citações sem norma declarada"),
    ("respostas_com_norma_ce", "Respostas que citam norma estadual do CE"),
    ("respostas_prov15_ou_art1103", "Respostas que citam o Prov. 15/2026 ou o Art. 1.103"),
    ("respostas_sem_dispositivo", "Recusas ou respostas sem dispositivo"),
    ("mediana_palavras", "Comprimento mediano (palavras)"),
)


# ---------------------------------------------------------------- camada 1

def carregar_indice_corpus(caminho: Path = CORPUS) -> dict[tuple[int, str], set[str]]:
    """{chave do artigo: siglas das normas do corpus em que ele existe} — o corpus inteiro, sem filtro."""
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho} não existe (é gerado por scripts/fase3/build_corpus.py)")
    indice: dict[tuple[int, str], set[str]] = {}
    with caminho.open(encoding="utf-8") as f:
        for linha in f:
            d = json.loads(linha)
            chave = _chave_de_artigo(d.get("dispositivo", ""))
            if chave:
                indice.setdefault(chave, set()).add(FONTES_POR_ID[d["fonte_id"]].sigla)
    return indice


def texto_pontuavel(resp: RespostaColetada) -> str:
    """Resposta integral + citações declaradas à parte (ex.: lista de referências do concorrente)."""
    return "\n\n".join([resp.resposta_integral, *resp.citacoes_declaradas])


def classificar_existencia(texto: str, indice: dict[tuple[int, str], set[str]]) -> list[dict]:
    vistas: set = set()
    out = []
    for trecho, chave, norma, _herdada in _extrair(texto or ""):
        if (chave, norma) in vistas:
            continue
        vistas.add((chave, norma))
        normas = indice.get(chave, set())
        if norma and norma.startswith("OUTRA:"):
            classe = Existencia.NORMA_FORA_DO_CORPUS
        elif norma:
            classe = Existencia.EXISTE if norma in normas else Existencia.ARTIGO_INEXISTENTE_NA_NORMA
        else:
            classe = Existencia.EXISTE if normas else Existencia.ARTIGO_INEXISTENTE_NA_NORMA
        out.append({"trecho": trecho, "artigo": _rotulo(chave), "norma_citada": norma,
                    "norma_declarada": norma is not None, "classe": classe.value})
    return out


def _cita_norma_ce(texto: str) -> bool:
    return any(m[2] in NORMAS_CE for m in _mencoes_de_norma(_normalizar(texto).lower()))


def _cita_prov15_ou_1103(texto: str, citacoes: list[dict]) -> bool:
    if any(m[2] == SIGLA_PROV15 for m in _mencoes_de_norma(_normalizar(texto).lower())):
        return True
    return any(c["artigo"] == "Art. 1103" and c["norma_citada"] in (SIGLA_CE, None) for c in citacoes)


def pontuar_resposta(resp: RespostaColetada, indice) -> dict:
    texto = texto_pontuavel(resp)
    citacoes = classificar_existencia(texto, indice)
    return {
        "pergunta_id": resp.pergunta_id,
        "citacoes": citacoes,
        "cita_norma_ce": _cita_norma_ce(texto),
        "cita_prov15_ou_1103": _cita_prov15_ou_1103(texto, citacoes),
        "sem_dispositivo": resp.recusou_responder or not citacoes,
        "palavras": len(resp.resposta_integral.split()),
    }


def resumo_camada1(respostas: dict[int, RespostaColetada], indice) -> dict:
    pontos = [pontuar_resposta(r, indice) for _, r in sorted(respostas.items())]
    cits = [c for p in pontos for c in p["citacoes"]]
    resumo = {
        "respostas": len(pontos),
        "citacoes": len(cits),
        **{e.value: sum(c["classe"] == e.value for c in cits) for e in Existencia},
        "sem_norma_declarada": sum(not c["norma_declarada"] for c in cits),
        "respostas_com_norma_ce": sum(p["cita_norma_ce"] for p in pontos),
        "respostas_prov15_ou_art1103": sum(p["cita_prov15_ou_1103"] for p in pontos),
        "respostas_sem_dispositivo": sum(p["sem_dispositivo"] for p in pontos),
        "mediana_palavras": statistics.median(p["palavras"] for p in pontos) if pontos else None,
    }
    return {"resumo": resumo, "por_pergunta": pontos}


# ---------------------------------------------------------------- camada 2 (só RAG próprio)

def resumo_camada2(respostas: dict[int, RespostaColetada]) -> dict | None:
    """Ancoragem contra os trechos recuperados; None se o sistema não expõe contexto."""
    com_contexto = {i: r for i, r in respostas.items() if r.trechos_recuperados is not None}
    if not com_contexto:
        return None
    totais = {"total": 0, "verificadas": 0, "norma_divergente": 0, "nao_recuperada": 0, "fora_do_corpus": 0}
    fundamentadas = 0
    for r in com_contexto.values():
        rel = verificar(texto_pontuavel(r), r.trechos_recuperados)
        for k in totais:
            totais[k] += getattr(rel, k)
        fundamentadas += rel.verificadas > 0
    return {**totais, "perguntas": len(com_contexto), "perguntas_com_citacao_verificada": fundamentadas,
            "versao_verificador": VERIFICADOR_VERSAO}


# ---------------------------------------------------------------- saídas

def _fmt(v) -> str:
    if v is None:
        return "—"
    return f"{v:g}" if isinstance(v, float) else str(v)


def tabela_comparativa(resumos_camada1: dict[str, dict | None]) -> str:
    """Tabela entre sistemas: SÓ campos de camada 1 (CAMPOS_COMPARATIVOS). Sistema sem dados = "sem acesso"."""
    cab = "| Métrica (camada 1: existência) | " + " | ".join(SISTEMAS) + " |"
    linhas = [cab, "|---|" + "---:|" * len(SISTEMAS)]
    for chave, rotulo in CAMPOS_COMPARATIVOS:
        cel = [_fmt(resumos_camada1[s].get(chave)) if resumos_camada1.get(s) else "sem acesso" for s in SISTEMAS]
        linhas.append(f"| {rotulo} | " + " | ".join(cel) + " |")
    return "\n".join(linhas)


def relatorio_sistema(sistema: str, c1: dict, c2: dict | None, origem: str) -> str:
    r = c1["resumo"]
    total = r["citacoes"] or 1
    partes = [
        f"# Pontuação da coleta: {sistema}",
        "",
        f"> Gerado por `scripts/pontuar_coleta.py`, sem LLM, verificador v{VERIFICADOR_VERSAO}. Origem: {origem}.",
        "> Este documento NÃO é um comparativo entre sistemas: as respostas dos concorrentes ainda não foram "
        "coletadas.",
        "",
        "## Camada 1: existência da citação no corpus oficial",
        "",
        "Cada artigo citado foi conferido contra o corpus inteiro (11 fontes, sem filtro de especialidade).",
        "",
        "| Classe | Citações | % |",
        "|---|---:|---:|",
        *[f"| {e.value} | {r[e.value]} | {100 * r[e.value] / total:.0f}% |" for e in Existencia],
        f"| **Total** | **{r['citacoes']}** | |",
        "",
        f"- Citações sem norma declarada (classificadas pela existência do artigo em alguma norma): "
        f"{r['sem_norma_declarada']}",
        f"- Respostas pontuadas: {r['respostas']}",
        f"- Respostas que citam norma estadual do CE (Código de Normas CGJ-CE ou Prov. 15/2026/CGJCE): "
        f"{r['respostas_com_norma_ce']}",
        f"- Respostas que citam o Prov. 15/2026/CGJCE ou o Art. 1.103 do Código de Normas: "
        f"{r['respostas_prov15_ou_art1103']}",
        f"- Recusas ou respostas sem nenhum dispositivo: {r['respostas_sem_dispositivo']}",
        f"- Comprimento mediano da resposta: {_fmt(r['mediana_palavras'])} palavras",
        "",
        "### Citações que não existem na norma citada ou estão fora do corpus",
        "",
    ]
    problemas = [(p["pergunta_id"], c) for p in c1["por_pergunta"] for c in p["citacoes"]
                 if c["classe"] != Existencia.EXISTE.value]
    partes += ([f"- #{i}: {c['artigo']} ({c['norma_citada'] or 'norma não declarada'}) → {c['classe']}"
                for i, c in problemas] or ["- nenhuma"])
    partes += ["", "## Camada 2: ancoragem nos trechos recuperados (só o RAG próprio)", ""]
    if c2 is None:
        partes.append("Não aplicável: o sistema não expõe os trechos usados na resposta.")
    else:
        partes += [
            "Mede se o artigo citado estava entre os trechos que o próprio RAG recuperou. Não é comparável com "
            "outros sistemas, que não expõem contexto, e por isso nunca entra em tabela comparativa.",
            "",
            "| Status (verificador v2) | Citações |",
            "|---|---:|",
            f"| VERIFICADA | {c2['verificadas']} |",
            f"| NORMA_DIVERGENTE | {c2['norma_divergente']} |",
            f"| NAO_RECUPERADA | {c2['nao_recuperada']} |",
            f"| FORA_DO_CORPUS | {c2['fora_do_corpus']} |",
            f"| **Total** | **{c2['total']}** |",
            "",
            f"Perguntas com ao menos uma citação ancorada: {c2['perguntas_com_citacao_verificada']} de "
            f"{c2['perguntas']}.",
        ]
    partes += [
        "",
        "## Limitações",
        "",
        "- A camada 1 mede a existência da citação, não a correção jurídica do conteúdo, que depende do gabarito "
        "do Oficial, ainda não coletado.",
        "- O corpus da Lei 6.015/1973 foi compilado sem trechos revogados: citar artigo revogado aparece como "
        "ARTIGO_INEXISTENTE_NA_NORMA.",
        "- A associação artigo → norma segue as regras do extrator do verificador v2 (norma mais próxima na "
        "frase; herança só de títulos).",
        "",
    ]
    return "\n".join(partes)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", type=Path, default=DIR_COLETA)
    ap.add_argument("--corpus", type=Path, default=CORPUS)
    ap.add_argument("--sistemas", default=",".join(SISTEMAS))
    ap.add_argument("--relatorio", type=Path, help="Markdown por sistema (exige um único sistema em --sistemas)")
    ap.add_argument("--json", type=Path, help="Grava os resumos (camada 1 e camada 2 em chaves separadas)")
    args = ap.parse_args()

    escolhidos = [s.strip() for s in args.sistemas.split(",") if s.strip()]
    todas = ler_todas(args.base)
    indice = carregar_indice_corpus(args.corpus)
    camada1 = {s: resumo_camada1(todas[s], indice) for s in escolhidos if todas.get(s)}
    camada2 = {SISTEMA_PROPRIO: resumo_camada2(todas[SISTEMA_PROPRIO])} if todas.get(SISTEMA_PROPRIO) else {}

    for s in escolhidos:
        if s not in camada1:
            print(f"{s}: sem respostas coletadas")
            continue
        r = camada1[s]["resumo"]
        print(f"{s}: " + ", ".join(f"{rot}={_fmt(r[k])}" for k, rot in CAMPOS_COMPARATIVOS))
        q26 = next((p for p in camada1[s]["por_pergunta"] if p["pergunta_id"] == PERGUNTA_26_ID), None)
        print(f"   pergunta 26: {'não coletada' if q26 is None else q26}")

    if args.relatorio:
        if len(escolhidos) != 1 or escolhidos[0] not in camada1:
            ap.error("--relatorio exige exatamente um sistema com respostas em --sistemas")
        s = escolhidos[0]
        base = args.base.resolve()
        origem = f"`{(base.relative_to(RAIZ) if base.is_relative_to(RAIZ) else base).as_posix()}/{s}/`"
        args.relatorio.write_text(relatorio_sistema(s, camada1[s], camada2.get(s), origem), encoding="utf-8")
        print(f"relatório: {args.relatorio}")
    if args.json:
        args.json.write_text(json.dumps({"camada1_existencia": {s: v["resumo"] for s, v in camada1.items()},
                                         "camada2_ancoragem_so_rag_proprio": camada2},
                                        ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
