"""Verificador determinístico de citações: mede alucinação de fundamento, sem LLM."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.fase3.ato_pronto import PedidoBalcao, processar_ato_pronto
from src.fase3.pipeline import Fase3Pipeline
from src.fase3.verificador_citacoes import VERIFICADOR_VERSAO, StatusCitacao, trechos_de_rotulos, verificar

CE = "Código de Normas CGJ-CE"
LEI = "Lei 6.015/1973"
CNJ = "Provimento CNJ 149/2023"
LGPD = "LGPD (Lei 13.709/2018)"

CHUNKS = [
    {"norma": CE, "dispositivo": "Art. 1128"},
    {"norma": LEI, "dispositivo": "Art. 17"},
    {"norma": LEI, "dispositivo": "Art. 213-A"},
    {"norma": CNJ, "dispositivo": "Art. 123"},
    {"norma": CE, "dispositivo": "Art. 123"},
    {"norma": LGPD, "dispositivo": "Art. 18"},
]


def _status(resposta: str, chunks=CHUNKS) -> list[tuple[str, StatusCitacao]]:
    return [(c.artigo, c.status) for c in verificar(resposta, chunks).citacoes]


# ---------------------------------------------------------------- o caso real

def test_caso_real_1128_atribuido_a_lei_6015_e_norma_divergente():
    # Sonda de 13/10: o LLM citou "Lei 6.015/73 Art. 1128"; o 1.128 recuperado é do Código CGJ-CE
    rel = verificar("Fundamentação: Lei 6.015/73, Art. 1128 — busca exige finalidade.", CHUNKS)
    assert rel.total == 1
    c = rel.citacoes[0]
    assert c.status == StatusCitacao.NORMA_DIVERGENTE
    assert c.norma_citada == LEI
    assert c.normas_no_contexto == [CE]
    assert rel.taxa_verificavel == 0.0


# ---------------------------------------------------------------- classificação

def test_verificada_com_ponto_de_milhar_e_traco_unicode():
    assert _status("Código de Normas da CGJ‑CE – Art. 1.128, § 2º, IV.") == [("Art. 1128", StatusCitacao.VERIFICADA)]


def test_1128_e_1_128_sao_o_mesmo_artigo():
    assert _status("Art. 1128 do Código de Normas.") == _status("Art. 1.128 do Código de Normas.")


def test_artigo_por_extenso_e_norma_depois():
    assert _status("Conforme o artigo 18 da LGPD, o titular pode pedir correção.") == [
        ("Art. 18", StatusCitacao.VERIFICADA)]


def test_nao_recuperada():
    assert _status("Nos termos do Art. 999 do Código de Normas.") == [("Art. 999", StatusCitacao.NAO_RECUPERADA)]


def test_numeracao_colidente_exige_a_norma_certa():
    so_ce = [{"norma": CE, "dispositivo": "Art. 123"}]
    assert _status("Art. 123 do Provimento CNJ 149/2023.", so_ce) == [("Art. 123", StatusCitacao.NORMA_DIVERGENTE)]
    assert _status("Art. 123 do Código de Normas CGJ-CE.", so_ce) == [("Art. 123", StatusCitacao.VERIFICADA)]


def test_lista_de_artigos_com_mesma_norma():
    assert _status("Nos termos dos arts. 123 e 124 do Provimento CNJ 149/2023.") == [
        ("Art. 123", StatusCitacao.VERIFICADA), ("Art. 124", StatusCitacao.NAO_RECUPERADA)]


def test_sufixo_de_letra():
    assert _status("Art. 213-A da Lei 6.015/1973.") == [("Art. 213-A", StatusCitacao.VERIFICADA)]


def test_varias_normas_na_mesma_frase():
    resposta = "Art. 17 da Lei nº 6.015/1973 c/c Art. 1128 do Código de Normas."
    assert _status(resposta) == [("Art. 17", StatusCitacao.VERIFICADA), ("Art. 1128", StatusCitacao.VERIFICADA)]


def test_norma_herdada_do_titulo_do_bloco():
    resposta = "1. **Código de Normas CGJ-CE**\n- Art. 1.128, caput\n- Art. 123"
    assert _status(resposta) == [("Art. 1128", StatusCitacao.VERIFICADA), ("Art. 123", StatusCitacao.VERIFICADA)]


def test_nao_herda_norma_de_frase_que_ja_tinha_artigo():
    # "Art. 213-A" não pode virar "da LGPD" só porque a frase anterior citou a LGPD
    rel = verificar("O Art. 18 assegura correção (LGPD). Ver também Art. 213-A.", CHUNKS)
    assert [(c.artigo, c.norma_citada, c.status) for c in rel.citacoes] == [
        ("Art. 18", LGPD, StatusCitacao.VERIFICADA), ("Art. 213-A", LEI, StatusCitacao.VERIFICADA)]
    assert rel.citacoes[1].norma_inferida


def test_nao_herda_norma_de_frase_comum_sem_artigo():
    # Benchmark de 13/10 (#9 e #18): a frase anterior só mencionava a LGPD, não era título
    resposta = ("Há tentativa de tratamento em desacordo com os princípios da LGPD. Portanto, o oficial deve "
                "recusar o pedido, emitindo uma Nota Devolutiva fundamentada no Art. 1128, § 4º.")
    assert _status(resposta) == [("Art. 1128", StatusCitacao.VERIFICADA)]


def test_cnj_sozinho_e_o_provimento_149():
    # Benchmark de 13/10 (#15): "Art. 123, § 1º (CNJ) / Art. 1.680, § 1º (CGJ-CE)"
    chunks = [{"norma": CNJ, "dispositivo": "Art. 123"}, {"norma": CE, "dispositivo": "Art. 1680"}]
    assert _status("| Art. 123, § 1º (CNJ) / Art. 1.680, § 1º (CGJ-CE) |", chunks) == [
        ("Art. 123", StatusCitacao.VERIFICADA), ("Art. 1680", StatusCitacao.VERIFICADA)]


def test_artigo_atribuido_a_lei_que_nao_o_tem_continua_divergente():
    # Benchmark de 13/10 (#25): "(Art. 178)" ao lado da LGPD; o 178 recuperado é do Código CE
    chunks = [{"norma": CE, "dispositivo": "Art. 178"}]
    assert _status("3. **Assegurar a conformidade com a LGPD** (Art. 178)", chunks) == [
        ("Art. 178", StatusCitacao.NORMA_DIVERGENTE)]


def test_sem_norma_e_artigo_ambiguo_nao_e_verificado():
    # Art. 123 existe no CNJ e no CE: sem dizer qual, não dá para confirmar
    assert _status("Aplica-se o Art. 123.") == [("Art. 123", StatusCitacao.NORMA_DIVERGENTE)]


def test_norma_fora_do_corpus_e_categoria_propria():
    # mesmo com "Art. 17" existindo nos trechos (da Lei 6.015), a norma citada não está no corpus
    rel = verificar("Art. 17 da Lei 14.382/2022.", CHUNKS)
    assert rel.citacoes[0].norma_citada.startswith("OUTRA")
    assert rel.citacoes[0].status == StatusCitacao.FORA_DO_CORPUS


def test_fora_do_corpus_nao_se_mistura_com_nao_recuperada():
    # Código Civil não existe no corpus (fonte inventada/externa); LGPD existe, mas o Art. 7 não veio
    rel = verificar("Doação conforme o Art. 543 do Código Civil. Base: art. 7º da LGPD.", CHUNKS)
    assert _status_de(rel) == [("Art. 543", StatusCitacao.FORA_DO_CORPUS), ("Art. 7", StatusCitacao.NAO_RECUPERADA)]
    assert (rel.fora_do_corpus, rel.nao_recuperada) == (1, 1)


def _status_de(rel):
    return [(c.artigo, c.status) for c in rel.citacoes]


# ---------------------------------------------------------------- agnóstico à origem

def test_aceita_trechos_de_qualquer_sistema():
    resposta = "Art. 17 da Lei 6.015/1973 e Art. 1.128 do Código de Normas CGJ-CE."
    como_tuplas = [("Lei nº 6.015/73", "art. 17"), ("Código de Normas da CGJ-CE", "Artigo 1.128")]
    como_rotulos = ["Lei 6.015/1973 — Art. 17", "Código de Normas CGJ-CE — Art. 1128:p229"]
    como_dicts = [{"norma": "Lei 6.015/1973", "artigo": "Art. 17"}, {"fonte_id": "codigo_normas_ce",
                                                                       "dispositivo": "Art. 1128"}]
    for trechos in (como_tuplas, como_rotulos, como_dicts):
        assert verificar(resposta, trechos).verificadas == 2, trechos


def test_trechos_de_rotulos_do_campo_fontes():
    fontes = ("Código de Normas CGJ-CE — Art. 1128:p229; Provimento CNJ 149/2023 — Art. 320-AE:p205; "
              "Guia ANPD — Agentes de Tratamento — p. 8:p8")
    assert trechos_de_rotulos(fontes)[:2] == [("Código de Normas CGJ-CE", "Art. 1128"),
                                              ("Provimento CNJ 149/2023", "Art. 320-AE")]


def test_relatorio_carrega_a_versao():
    assert verificar("Art. 17 da Lei 6.015/1973.", CHUNKS).versao == VERIFICADOR_VERSAO == 2


def test_chunk_de_indice_antigo_usa_fonte_id():
    chunks = [{"fonte_id": "codigo_normas_ce", "dispositivo": "Art. 1128"}]
    assert _status("Art. 1128 do Código de Normas CGJ-CE.", chunks) == [("Art. 1128", StatusCitacao.VERIFICADA)]


def test_citacao_repetida_conta_uma_vez():
    assert verificar("Art. 17 da Lei 6.015/1973. Reforço: Art. 17 da Lei 6.015/1973.", CHUNKS).total == 1


def test_ignora_hifen_seguido_de_texto():
    assert _status("Art. 17 - a certidão é livre.") == [("Art. 17", StatusCitacao.VERIFICADA)]


# ---------------------------------------------------------------- relatório

def test_relatorio_contagens_e_taxa():
    rel = verificar("Art. 17 da Lei 6.015/1973. Art. 1128 da Lei 6.015/1973. Art. 999 do Código de Normas.", CHUNKS)
    assert (rel.total, rel.verificadas, rel.norma_divergente, rel.nao_recuperada) == (3, 1, 1, 1)
    assert rel.taxa_verificavel == pytest.approx(1 / 3)
    assert len(rel.nao_verificadas()) == 2


def test_sem_citacoes_taxa_none():
    rel = verificar("Não encontrado no corpus.", CHUNKS)
    assert rel.total == 0 and rel.taxa_verificavel is None


# ---------------------------------------------------------------- integração

def _resposta(conteudo: str) -> MagicMock:
    r = MagicMock()
    r.choices = [MagicMock(message=MagicMock(content=conteudo))]
    return r


def test_answer_devolve_relatorio_de_citacoes():
    pipe = object.__new__(Fase3Pipeline)
    pipe.retrieve = MagicMock(return_value=[{**CHUNKS[0], "text": "Art. 1.128 ...", "page": 229}])
    pipe.llm_model = "mock"
    pipe._call_chat_completions = MagicMock(return_value=_resposta("Base: Lei 6.015/73, Art. 1128."))
    rel = pipe.answer("pergunta")["citacoes"]
    assert rel.norma_divergente == 1 and rel.taxa_verificavel == 0.0


ATO_JSON = """{"canal": "VERMELHO", "veredito": "INDEFERIDO (NOTA DEVOLUTIVA)", "instrucao_balcao": "x",
 "fundamentacao": [{"norma": "Lei 6.015/73", "artigo": "Art. 1128", "aplicacao": "x"}],
 "minuta_ato": "NOTA DEVOLUTIVA", "citacoes": {"total": 9, "verificadas": 9, "taxa_verificavel": 1.0},
 "auditoria_lgpd": {"finalidade": "x", "base_legal_lgpd": "x", "categoria_titular": "x",
                    "dados_tratados": ["x"], "salvaguardas_adotadas": "x"}}"""


def test_ato_pronto_verifica_fundamentacao_e_ignora_citacoes_do_llm():
    pipe = MagicMock()
    pipe.llm_model = "mock"
    pipe.retrieve.return_value = [{**CHUNKS[0], "text": "Art. 1.128 ...", "page": 229}]
    pipe._call_chat_completions.return_value = _resposta(ATO_JSON)
    saida = processar_ato_pronto(pipe, PedidoBalcao(tipo_pedido="Busca", solicitante="Terceiro"))
    # o LLM tentou declarar 9/9 verificadas; vale a conferência do sistema
    assert saida.citacoes.total == 1
    assert saida.citacoes.citacoes[0].status == StatusCitacao.NORMA_DIVERGENTE


# ---------------------------------------------------------------- benchmark

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "benchmark"))


def test_benchmark_agrega_e_grava_na_planilha(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    import build_planilha
    import run_rag_benchmark as rb

    por_pergunta = [rb.resumo_citacoes(verificar(t, CHUNKS)) for t in (
        "Art. 17 da Lei 6.015/1973. Art. 1128 da Lei 6.015/1973.", "Não encontrado no corpus.")]
    total = rb.agregar_citacoes([{"citacoes": c} for c in por_pergunta] + [{"citacoes": None}])
    assert (total["total"], total["verificadas"], total["perguntas_sem_citacao"]) == (2, 1, 1)
    assert total["taxa_verificavel"] == 0.5
    # cobertura: 1 pergunta fundamentada / 3 perguntas (a sem resultado também conta no denominador)
    assert (total["perguntas_fundamentadas"], total["total_perguntas"]) == (1, 3)
    assert total["cobertura_fundamentada"] == pytest.approx(1 / 3)
    assert total["versao_verificador"] == VERIFICADOR_VERSAO
    assert f"v{VERIFICADOR_VERSAO}" in rb.formatar_metricas_citacao(total)

    out = tmp_path / "p.xlsx"
    sys.argv = ["build_planilha.py", "--out", str(out)]
    assert build_planilha.main() == 0
    meta = {"data": "2026-10-13T10:00:00", "provider": "groq", "llm_model": "m", "k": 5,
            "git_commit": "x", "ferramenta": "RAG Fase 3"}
    rec = {"id": 1, "resposta": "r", "fontes": "f", "latencia_s": 1.0, "tokens_entrada": 1,
           "tokens_saida": 1, "erro": None, "citacoes": por_pergunta[0]}
    meta["citacoes"] = total
    assert rb.fill_xlsx(out, meta, [rec], overwrite=False) == (1, 0)
    wb = openpyxl.load_workbook(out)
    # versão gravada junto de toda taxa
    assert wb["Parametros"]["B6"].value == VERIFICADOR_VERSAO
    assert f"v{VERIFICADOR_VERSAO}" in wb["Resumo"]["L3"].value and f"v{VERIFICADOR_VERSAO}" in wb["Resumo"]["P3"].value
    assert "COUNTIFS" in wb["Resumo"]["P8"].value
    ws = wb["Respostas"]
    assert f"v{VERIFICADOR_VERSAO}" in ws["V1"].value
    r = next(i for i in range(2, ws.max_row + 1) if ws[f"A{i}"].value == 1 and ws[f"B{i}"].value == "RAG Fase 3")
    assert (ws[f"T{r}"].value, ws[f"U{r}"].value) == (2, 1)
    assert ws[f"V{r}"].value.startswith("=IF(")
    assert "NORMA_DIVERGENTE" in ws[f"W{r}"].value


def test_reverificar_resultado_salvo_sem_llm():
    import run_rag_benchmark as rb

    salvo = {"meta": {}, "resultados": [
        {"id": 1, "resposta": "Art. 1128 do Código de Normas CGJ-CE.", "fontes": "Código de Normas CGJ-CE — Art. 1128:p229",
         "erro": None},
        {"id": 2, "resposta": "Art. 543 do Código Civil.", "fontes": "Lei 6.015/1973 — Art. 17:p0", "erro": None},
        {"id": 3, "resposta": "", "fontes": "", "erro": None},  # vazia: conta no denominador da cobertura
    ]}
    cit = rb.reverificar(salvo)["meta"]["citacoes"]
    assert (cit["verificadas"], cit["fora_do_corpus"], cit["total"]) == (1, 1, 2)
    assert cit["cobertura_fundamentada"] == pytest.approx(1 / 3)
    assert cit["versao_verificador"] == VERIFICADOR_VERSAO
