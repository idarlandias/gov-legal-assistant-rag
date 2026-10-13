"""Coleta comparativa: registrador, exportador, pontuador e separação das camadas."""

import io
import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import exportar_rag_coleta as exp  # noqa: E402
import pontuar_coleta as pc  # noqa: E402
import registrar_resposta as reg  # noqa: E402
from src.fase3.coleta import (  # noqa: E402
    ORDEM_COLETA_JSON, PERGUNTA_26, PERGUNTAS_COLETA_MD, PERGUNTAS_JSON, SISTEMA_PROPRIO, SISTEMAS,
    RespostaColetada, gravar, ler_todas, ordem_por_sistema, perguntas_coleta_md, perguntas_oficiais,
)

EXECUCAO = RAIZ / "docs" / "fase3" / "benchmark" / "results" / "rag-fase3-20261013-113528-reverificado.json"
CE = "Código de Normas CGJ-CE"
INDICE = {(1128, ""): {CE}, (123, ""): {"Provimento CNJ 149/2023"}, (17, ""): {"Lei 6.015/1973"}}

# Qualquer termo de ancoragem numa saída comparativa invalida a comparação
TERMOS_ANCORAGEM = re.compile(r"verificad|nao_recuperad|não recuperad|norma_divergente|ancor|recuperad|"
                              r"taxa_verificavel|cobertura", re.IGNORECASE)


def _resposta(**kw) -> RespostaColetada:
    base = dict(pergunta_id=3, pergunta_texto=perguntas_oficiais()[3], sistema="jus_ia", modelo_ou_plano="plano X",
                coletado_em="2026-10-14T09:00:00-03:00", resposta_integral="Ver Art. 1.128 do Código de Normas.")
    return RespostaColetada(**{**base, **kw})


# ---------------------------------------------------------------- schema

def test_nome_antigo_aceito_na_leitura_e_gravado_com_o_novo(tmp_path):
    r = _resposta(sistema="cartorioseguro", trechos_recuperados=[])
    assert r.sistema == SISTEMA_PROPRIO
    pasta = tmp_path / "cartorioseguro"
    pasta.mkdir()
    (pasta / "3.json").write_text(json.dumps({**r.model_dump(), "sistema": "cartorioseguro"}), encoding="utf-8")
    assert ler_todas(tmp_path)[SISTEMA_PROPRIO][3].sistema == SISTEMA_PROPRIO


@pytest.mark.parametrize("campo,valor", [
    ("coletado_em", "2026-10-14T09:00:00"),          # sem fuso
    ("coletado_em", "2026-10-14T09:00:00+00:00"),    # fuso errado
    ("pergunta_texto", "texto parafraseado"),        # texto diferente do oficial
    ("sistema", "chatgpt"),                          # sistema desconhecido
    ("resposta_integral", "   "),                    # vazia sem recusa
])
def test_schema_rejeita(campo, valor):
    with pytest.raises(ValueError):
        _resposta(**{campo: valor})


def test_trechos_recuperados_so_no_rag_proprio():
    with pytest.raises(ValueError, match="RAG próprio"):
        _resposta(trechos_recuperados=["Lei 6.015/1973 — Art. 17"])


# ---------------------------------------------------------------- registrador

def _args(tmp_path, *extra):
    return ["--sistema", "juridico_ai", "--pergunta", "26", "--modelo", "plano Y",
            "--coletado-em", "2026-10-14T10:00:00-03:00", "--base", str(tmp_path), *extra]


def test_registrador_grava_texto_integral_sem_truncar(tmp_path):
    texto = ("Linha com acentuação, § e “aspas”.\n\n" * 3000) + "fim sem quebra"
    arq = tmp_path / "resp.txt"
    arq.write_bytes(texto.encode("utf-8"))
    assert reg.main(_args(tmp_path, "--arquivo", str(arq), "--citacao", "Art. 1.103")) == 0
    salvo = json.loads((tmp_path / "juridico_ai" / "26.json").read_text(encoding="utf-8"))
    assert salvo["resposta_integral"] == texto
    assert salvo["pergunta_texto"] == PERGUNTA_26
    assert salvo["citacoes_declaradas"] == ["Art. 1.103"]


def test_registrador_le_stdin(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO("﻿resposta via stdin\n".encode("utf-8"))))
    assert reg.main(_args(tmp_path)) == 0
    salvo = json.loads((tmp_path / "juridico_ai" / "26.json").read_text(encoding="utf-8"))
    assert salvo["resposta_integral"] == "resposta via stdin\n"


def test_registrador_nao_sobrescreve_sem_force(tmp_path, monkeypatch):
    arq = tmp_path / "r.txt"
    arq.write_text("primeira", encoding="utf-8")
    assert reg.main(_args(tmp_path, "--arquivo", str(arq))) == 0
    arq.write_text("segunda", encoding="utf-8")
    assert reg.main(_args(tmp_path, "--arquivo", str(arq))) == 3
    destino = tmp_path / "juridico_ai" / "26.json"
    assert json.loads(destino.read_text(encoding="utf-8"))["resposta_integral"] == "primeira"
    assert reg.main(_args(tmp_path, "--arquivo", str(arq), "--force")) == 0
    assert json.loads(destino.read_text(encoding="utf-8"))["resposta_integral"] == "segunda"


def test_registrador_rejeita_schema_invalido(tmp_path):
    arq = tmp_path / "r.txt"
    arq.write_text("x", encoding="utf-8")
    assert reg.main(["--sistema", "juridico_ai", "--pergunta", "26", "--modelo", "p", "--coletado-em",
                     "2026-10-14T10:00:00", "--base", str(tmp_path), "--arquivo", str(arq)]) == 2
    assert not (tmp_path / "juridico_ai").exists()


# ---------------------------------------------------------------- exportador

def test_exportador_preserva_as_25_respostas_do_rag(tmp_path):
    execucao = json.loads(EXECUCAO.read_text(encoding="utf-8"))
    respostas = exp.converter(execucao, EXECUCAO.name)
    assert [r.pergunta_id for r in respostas] == list(range(1, 26))
    for r, orig in zip(respostas, execucao["resultados"]):
        assert r.sistema == SISTEMA_PROPRIO
        assert r.resposta_integral == orig["resposta"]
        assert r.coletado_em.endswith("-03:00")
        assert r.recusou_responder == (orig["status_resposta"] != "RESPONDIDA")
        assert r.trechos_recuperados == [f.strip() for f in orig["fontes"].split(";") if f.strip()]
    for r in respostas:
        gravar(r, tmp_path)
    assert len(ler_todas(tmp_path)[SISTEMA_PROPRIO]) == 25


def test_exportacao_versionada_bate_com_a_execucao():
    """O que está em data/benchmark/respostas_externas é a conversão fiel da execução de 13/10 11h35."""
    execucao = json.loads(EXECUCAO.read_text(encoding="utf-8"))
    gravadas = ler_todas()[SISTEMA_PROPRIO]
    for r in exp.converter(execucao, EXECUCAO.name):
        assert gravadas[r.pergunta_id] == r


# ---------------------------------------------------------------- pontuador: camada 1

@pytest.mark.parametrize("texto,classe,declarada", [
    ("Conforme o Art. 1.128 do Código de Normas.", "EXISTE", True),
    ("Conforme o Art. 9999 da Lei 6.015/73.", "ARTIGO_INEXISTENTE_NA_NORMA", True),
    ("Conforme o Art. 1.128 da Lei 6.015/73.", "ARTIGO_INEXISTENTE_NA_NORMA", True),
    ("Conforme o Art. 543 do Código Civil.", "NORMA_FORA_DO_CORPUS", True),
    ("Conforme o Art. 123.", "EXISTE", False),
    ("Conforme o Art. 4444.", "ARTIGO_INEXISTENTE_NA_NORMA", False),
])
def test_classificacao_de_existencia(texto, classe, declarada):
    [c] = pc.classificar_existencia(texto, INDICE)
    assert (c["classe"], c["norma_declarada"]) == (classe, declarada)


def test_resumo_camada1_conta_ce_prov15_recusa_e_mediana():
    respostas = {
        1: _resposta(pergunta_id=1, pergunta_texto=perguntas_oficiais()[1],
                     resposta_integral="O Prov. 15/2026/CGJCE mudou o Art. 1.103 do Código de Normas."),
        2: _resposta(pergunta_id=2, pergunta_texto=perguntas_oficiais()[2], resposta_integral="Não sei.",
                     recusou_responder=True),
        3: _resposta(resposta_integral="Art. 17 da Lei 6.015 garante a publicidade."),
    }
    r = pc.resumo_camada1(respostas, INDICE)["resumo"]
    assert r["respostas"] == 3
    assert r["respostas_com_norma_ce"] == 1
    assert r["respostas_prov15_ou_art1103"] == 1
    assert r["respostas_sem_dispositivo"] == 1
    assert r["mediana_palavras"] == 8


# ---------------------------------------------------------------- separação das camadas

def test_campos_comparativos_sao_so_de_camada1():
    for chave, rotulo in pc.CAMPOS_COMPARATIVOS:
        assert not TERMOS_ANCORAGEM.search(chave) and not TERMOS_ANCORAGEM.search(rotulo), chave


def test_tabela_comparativa_nunca_inclui_ancoragem():
    c1 = pc.resumo_camada1({3: _resposta()}, INDICE)["resumo"]
    contaminado = {**c1, "verificadas": 47, "nao_recuperada": 6, "taxa_verificavel": 0.85,
                   "cobertura_fundamentada": 0.72}
    tabela = pc.tabela_comparativa({SISTEMA_PROPRIO: contaminado, "jus_ia": c1})
    assert not TERMOS_ANCORAGEM.search(tabela), tabela
    assert "47" not in tabela and "0.85" not in tabela


def test_tabela_comparativa_marca_sem_acesso_em_vez_de_omitir():
    tabela = pc.tabela_comparativa({SISTEMA_PROPRIO: pc.resumo_camada1({3: _resposta()}, INDICE)["resumo"]})
    cabecalho = tabela.splitlines()[0]
    assert all(s in cabecalho for s in SISTEMAS)
    assert tabela.count("sem acesso") == (len(SISTEMAS) - 1) * len(pc.CAMPOS_COMPARATIVOS)


def test_camada2_so_existe_para_quem_expoe_contexto():
    assert pc.resumo_camada2({3: _resposta()}) is None


def test_camada2_do_rag_reproduz_o_verificador_v2_da_execucao():
    meta = json.loads(EXECUCAO.read_text(encoding="utf-8"))["meta"]["citacoes"]
    c2 = pc.resumo_camada2(ler_todas()[SISTEMA_PROPRIO])
    assert (c2["total"], c2["verificadas"], c2["nao_recuperada"], c2["fora_do_corpus"]) == (
        meta["total"], meta["verificadas"], meta["nao_recuperada"], meta["fora_do_corpus"])
    assert c2["perguntas_com_citacao_verificada"] == meta["perguntas_fundamentadas"]


def test_camada1_contra_o_corpus_real():
    if not pc.CORPUS.exists():
        pytest.skip(f"PULADO: {pc.CORPUS} ausente (gitignored; gere com scripts/fase3/build_corpus.py)")
    indice = pc.carregar_indice_corpus()
    [c] = pc.classificar_existencia("Art. 1.128 do Código de Normas", indice)
    assert c["classe"] == "EXISTE"


# ---------------------------------------------------------------- folha e ordem de coleta

def test_folha_de_coleta_tem_texto_identico_e_26_externa():
    assert PERGUNTAS_COLETA_MD.read_text(encoding="utf-8") == perguntas_coleta_md()
    blocos = re.findall(r"```text\n(.*?)\n```", PERGUNTAS_COLETA_MD.read_text(encoding="utf-8"), re.DOTALL)
    oficiais = json.loads(PERGUNTAS_JSON.read_text(encoding="utf-8"))["perguntas"]
    assert blocos[:25] == [p["pergunta"] for p in oficiais]
    assert blocos[25] == PERGUNTA_26 and len(blocos) == 26
    assert "## Pergunta 26 (externa ao benchmark)" in PERGUNTAS_COLETA_MD.read_text(encoding="utf-8")
    assert len(oficiais) == 25  # a 26 não entra em perguntas.json


def test_ordem_de_coleta_reproduzivel_e_diferente_por_sistema():
    salvo = json.loads(ORDEM_COLETA_JSON.read_text(encoding="utf-8"))
    assert salvo["ordens"] == ordem_por_sistema(salvo["seed"])
    ordens = list(salvo["ordens"].values())
    assert all(sorted(o) == list(range(1, 27)) for o in ordens)
    assert len({tuple(o) for o in ordens}) == len(SISTEMAS)
