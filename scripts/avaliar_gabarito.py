"""Gabarito do registrador e avaliação das respostas de cada sistema contra ele.

1. `gabarito_modelo.csv` traz as 26 perguntas (25 do benchmark + a 26 externa) com os campos jurídicos
   EM BRANCO: quem preenche é o registrador, por escrito. Nenhuma resposta esperada é gerada aqui.
   O registrador salva a cópia preenchida como `data/validacao/gabarito.csv`.
2. Cada resposta de cada sistema é julgada por uma pessoa contra o gabarito, numa linha de
   `data/validacao/avaliacao_<sistema>.csv`: acerto (certo/parcial/errado/sem_resposta) e se ela
   contraria a norma (sim/nao).
3. Este script calcula, por sistema, só sobre as perguntas com gabarito VALIDADO (validado_por preenchido):
   percentual de acerto e número de respostas contrárias à norma (meta sugerida: zero).

Uso:
    python scripts/avaliar_gabarito.py --gerar-modelo
    python scripts/avaliar_gabarito.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.fase3.coleta import SISTEMAS, normalizar_sistema, perguntas_oficiais  # noqa: E402

DIR_VALIDACAO = RAIZ / "data" / "validacao"
GABARITO_MODELO = DIR_VALIDACAO / "gabarito_modelo.csv"
GABARITO = DIR_VALIDACAO / "gabarito.csv"
# Casos de Registro Civil (ids 101+): texto da situação + fatos estruturados para rodar o motor de regras
CASOS_RCPN = DIR_VALIDACAO / "casos_rcpn.json"
GABARITO_RCPN_MODELO = DIR_VALIDACAO / "gabarito_rcpn_modelo.csv"
GABARITO_RCPN = DIR_VALIDACAO / "gabarito_rcpn.csv"

COLUNAS_GABARITO = ("pergunta_id", "pergunta", "atribuicao", "decisao_esperada", "quem_decide", "fundamentos",
                    "resposta_esperada", "erro_grave_se", "validado_por", "data_validacao")
DECISOES = {"DEFERIR", "DEFERIR_COM_EXIGENCIA", "INDEFERIR_NOTA", "INFORMAR", "ENCAMINHAR_JUIZ", "NAO_SE_APLICA"}
COLUNAS_AVALIACAO = ("sistema", "pergunta_id", "acerto", "contraria_norma", "observacao", "avaliado_por")
ACERTOS = {"certo", "parcial", "errado", "sem_resposta"}


class ArquivoInvalido(ValueError):
    pass


def casos_rcpn(caminho: Path = CASOS_RCPN) -> list[dict]:
    return json.loads(caminho.read_text(encoding="utf-8"))["casos"]


def gerar_modelo(destino: Path = GABARITO_MODELO, perguntas: dict[int, str] | None = None) -> None:
    perguntas = perguntas if perguntas is not None else perguntas_oficiais()
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLUNAS_GABARITO)
        for pid, texto in sorted(perguntas.items()):
            w.writerow([pid, texto] + [""] * (len(COLUNAS_GABARITO) - 2))


def gerar_modelo_rcpn(destino: Path = GABARITO_RCPN_MODELO) -> None:
    gerar_modelo(destino, {c["id"]: c["pergunta"] for c in casos_rcpn()})


# ---------------------------------------------------------------- motor de regras × registrador

def decisao_do_motor(entrada: dict) -> str | None:
    """Canal do motor de regras do Registro Civil no vocabulário do gabarito (None = o motor não decide)."""
    from src.fase3 import regras_rcpn as rc
    from src.fase3.regras_ri import Cobertura

    r = rc.decidir(entrada["tipo"], entrada.get("solicitante", ""), entrada.get("dado_sensivel"),
                   entrada.get("informacao_vedada"), entrada.get("registrado_falecido"),
                   entrada.get("registro_bloqueado", False))
    if r.cobertura != Cobertura.REGRA:
        return None
    if r.canal == "VERMELHO" and r.exige_autorizacao_judicial:
        return "ENCAMINHAR_JUIZ"
    return {"VERDE": "DEFERIR", "AMARELO": "DEFERIR_COM_EXIGENCIA"}.get(r.canal)


def concordancia_motor_rcpn(gabarito: dict[int, dict], casos: list[dict] | None = None) -> dict:
    """Compara a decisão do motor com a do registrador nos casos de Registro Civil já validados."""
    casos = casos if casos is not None else casos_rcpn()
    comparados = []
    for c in casos:
        if c["id"] not in gabarito:
            continue
        motor = decisao_do_motor(c["entrada"])
        registrador = gabarito[c["id"]]["decisao_esperada"]
        comparados.append({"id": c["id"], "motor": motor, "registrador": registrador, "concorda": motor == registrador})
    n = len(comparados)
    concordantes = sum(x["concorda"] for x in comparados)
    return {"comparados": n, "concordantes": concordantes,
            "pct_concordancia": round(100 * concordantes / n, 1) if n else None,
            "divergencias": [x for x in comparados if not x["concorda"]]}


def _ler(caminho: Path, colunas: tuple[str, ...]) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        if tuple(leitor.fieldnames or ()) != colunas:
            raise ArquivoInvalido(f"{caminho.name}: colunas esperadas {colunas}")
        return [{k: (v or "").strip() for k, v in linha.items()} for linha in leitor if any((v or "").strip()
                                                                                          for v in linha.values())]


def ler_gabarito(caminho: Path = GABARITO) -> dict[int, dict]:
    """Só as perguntas validadas (validado_por preenchido) entram na avaliação."""
    validadas = {}
    for linha in _ler(caminho, COLUNAS_GABARITO):
        if not linha["validado_por"]:
            continue
        if linha["decisao_esperada"] not in DECISOES:
            raise ArquivoInvalido(f"pergunta {linha['pergunta_id']}: decisao_esperada fora de {sorted(DECISOES)}")
        if not linha["fundamentos"]:
            raise ArquivoInvalido(f"pergunta {linha['pergunta_id']}: gabarito validado sem fundamentos")
        validadas[int(linha["pergunta_id"])] = linha
    return validadas


def ler_avaliacoes(arquivos: list[Path]) -> list[dict]:
    linhas = []
    for arq in arquivos:
        for linha in _ler(arq, COLUNAS_AVALIACAO):
            linha["sistema"] = normalizar_sistema(linha["sistema"])
            if linha["sistema"] not in SISTEMAS:
                raise ArquivoInvalido(f"{arq.name}: sistema desconhecido {linha['sistema']!r}")
            if linha["acerto"] not in ACERTOS or linha["contraria_norma"] not in {"sim", "nao"}:
                raise ArquivoInvalido(f"{arq.name}: pergunta {linha['pergunta_id']} com acerto/contraria_norma "
                                      "inválidos")
            linha["pergunta_id"] = int(linha["pergunta_id"])
            linhas.append(linha)
    return linhas


def avaliar(gabarito: dict[int, dict], avaliacoes: list[dict]) -> dict[str, dict]:
    """Por sistema: só perguntas com gabarito validado; as demais são contadas como ignoradas."""
    out: dict[str, dict] = {}
    for s in SISTEMAS:
        das = [a for a in avaliacoes if a["sistema"] == s]
        if not das:
            continue
        validas = [a for a in das if a["pergunta_id"] in gabarito]
        n = len(validas)
        conta = {k: sum(a["acerto"] == k for a in validas) for k in sorted(ACERTOS)}
        out[s] = {
            "avaliadas": n,
            "ignoradas_sem_gabarito": len(das) - n,
            **conta,
            "pct_certo": round(100 * conta["certo"] / n, 1) if n else None,
            "contrarias_a_norma": sum(a["contraria_norma"] == "sim" for a in validas),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gerar-modelo", action="store_true", help="(Re)gera gabarito_modelo.csv com as 26 perguntas")
    ap.add_argument("--dir", type=Path, default=DIR_VALIDACAO)
    args = ap.parse_args()

    if args.gerar_modelo:
        gerar_modelo(args.dir / GABARITO_MODELO.name)
        gerar_modelo_rcpn(args.dir / GABARITO_RCPN_MODELO.name)
        print(f"modelos gerados: {GABARITO_MODELO.name}, {GABARITO_RCPN_MODELO.name}")
        return 0
    arquivos = [args.dir / GABARITO.name, args.dir / GABARITO_RCPN.name]
    if not any(a.exists() for a in arquivos):
        print("Sem gabarito validado: o registrador deve preencher os modelos e salvar como "
              f"{GABARITO.name} (benchmark) e/ou {GABARITO_RCPN.name} (Registro Civil).")
        return 1
    try:
        gabarito = {pid: linha for a in arquivos if a.exists() for pid, linha in ler_gabarito(a).items()}
        res = avaliar(gabarito, ler_avaliacoes(sorted(args.dir.glob("avaliacao_*.csv"))))
    except ArquivoInvalido as e:
        print(f"Arquivo inválido: {e}", file=sys.stderr)
        return 2
    conc = concordancia_motor_rcpn(gabarito)
    if conc["comparados"]:
        print(f"Motor de regras × registrador (Registro Civil): {conc['concordantes']} de {conc['comparados']} "
              f"({conc['pct_concordancia']:g}%)")
        for d in conc["divergencias"]:
            print(f"   caso {d['id']}: motor={d['motor']} registrador={d['registrador']}")
    print(f"Perguntas com gabarito validado: {len(gabarito)}")
    print("| Sistema | Avaliadas | Certo | Parcial | Errado | Sem resposta | % certo | Contrárias à norma |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for s, r in res.items():
        pct = "—" if r["pct_certo"] is None else f"{r['pct_certo']:g}%"
        print(f"| {s} | {r['avaliadas']} | {r['certo']} | {r['parcial']} | {r['errado']} | {r['sem_resposta']} "
              f"| {pct} | {r['contrarias_a_norma']} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
