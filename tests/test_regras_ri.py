"""Motor de regras do Registro de Imóveis: canal pela norma, fundamentos literais, IA só redige."""

import json
import re
import unicodedata
from unittest.mock import MagicMock

import pytest

from src.fase3 import regras_ri as rr
from src.fase3.ato_pronto import (
    EXPANSAO_TIPO_PEDIDO, CanalRisco, PedidoBalcao, build_ato_pronto_prompt, processar_ato_pronto,
)
from src.fase3.sources import FONTES_POR_ID

TERCEIRO = "Terceiro sem comprovação de vínculo ou interesse jurídico"
TITULAR = "Próprio Titular / Proprietário do Imóvel"
CORPUS = rr.__file__.replace("src\\fase3\\regras_ri.py", "data\\corpus_fase3\\dispositivos.jsonl").replace(
    "src/fase3/regras_ri.py", "data/corpus_fase3/dispositivos.jsonl")


# ---------------------------------------------------------------- tabela

def test_caso_mais_comum_terceiro_pede_matricula_sem_motivo_e_verde():
    """O ponto central da validação: certidão de matrícula exige só identificação, nunca finalidade."""
    r = rr.decidir("Certidão de Inteiro Teor de Matrícula", TERCEIRO, ["CPF completo", "Estado Civil / Regime de Bens"])
    assert (r.cobertura, r.canal, r.exige_identificacao, r.exige_finalidade) == (rr.Cobertura.REGRA, "VERDE", True,
                                                                                  False)
    # o §10 entra como base para reproduzir TODO o conteúdo, nunca para omitir  guarda-1131: ok
    assert {f.artigo for f in r.fundamentos} >= {"Art. 1.128, caput", "Art. 123, caput", "Art. 1.131, §10"}  # guarda-1131: ok
    assert not r.gera_ficha
    assert any("reproduz todo o conteúdo" in a for a in r.alertas)


@pytest.mark.parametrize("tipo,canal,artigos", [
    ("Certidão de Situação Jurídica Atual (Vigente)", "VERDE", {"Art. 1.129", "Art. 125, caput"}),
    ("Busca por Indicador Pessoal (Pesquisa de Bens por CPF/Nome)", "AMARELO", {"Art. 1.128, §2º, IV", "Art. 126"}),
    ("Informação Verbal no Balcão ou por Telefone", "AMARELO", {"Art. 1.128, §2º, V", "Art. 127"}),
    ("Acesso em Lote / Convênio com Empresa Imobiliária ou Fintech", "AMARELO",
     {"Art. 1.128, §2º, II", "Art. 123, §3º", "Art. 124"}),
])
def test_regras_diretas(tipo, canal, artigos):
    r = rr.decidir(tipo, TERCEIRO)
    assert r.canal == canal
    assert artigos <= {f.artigo for f in r.fundamentos}
    assert r.gera_ficha == (canal == "AMARELO")
    if canal == "AMARELO":
        assert {"Art. 1.128, §3º", "Art. 128"} <= {f.artigo for f in r.fundamentos}


def test_informacao_verbal_ao_titular_dispensa_finalidade():
    r = rr.decidir("Informação Verbal no Balcão ou por Telefone", TITULAR)
    assert (r.canal, r.exige_finalidade) == ("VERDE", False)


@pytest.mark.parametrize("tipo,sim,nao", [
    ("Cópia de Título / Documento Arquivado no Cartório", "VERDE", "AMARELO"),
    ("Histórico de Ônus / Cadeia Filiatória / Ônus Cancelados", "AMARELO", "VERDE"),
])
def test_condicionais_so_decidem_com_a_resposta(tipo, sim, nao):
    sem = rr.decidir(tipo, TERCEIRO)
    assert sem.cobertura == rr.Cobertura.CONDICIONAL and sem.canal is None and sem.pergunta
    assert rr.decidir(tipo, TERCEIRO, condicao=True).canal == sim
    assert rr.decidir(tipo, TERCEIRO, condicao=False).canal == nao


@pytest.mark.parametrize("tipo", ["Pedido de Exclusão de Dados da Matrícula com base na LGPD",
                                  "Pedido de Retificação de Dado Pessoal na Matrícula",
                                  "Requisição por Órgão Público / Polícia / Prefeitura sem Ordem Judicial",
                                  "tipo que não existe"])
def test_sem_regra_nao_inventa_canal(tipo):
    r = rr.decidir(tipo, TERCEIRO)
    assert r.cobertura == rr.Cobertura.SEM_REGRA and r.canal is None


def test_tabela_cobre_todas_as_opcoes_da_ui_e_nunca_devolve_vermelho():
    assert set(rr.TABELA) == set(EXPANSAO_TIPO_PEDIDO)
    resultados = [rr.INFORMACAO_TITULAR]
    for r in rr.TABELA.values():
        resultados += [r, r.se_sim, r.se_nao]
    assert all(r is None or r.canal in (None, "VERDE", "AMARELO") for r in resultados)


def _so_letras(t: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", t.lower())


def test_todo_fundamento_e_transcricao_literal_do_corpus():
    from pathlib import Path
    corpus = Path(CORPUS)
    if not corpus.exists():
        pytest.skip(f"PULADO: {corpus} ausente (gitignored; gere com scripts/fase3/build_corpus.py)")
    sigla_para_id = {f.sigla: fid for fid, f in FONTES_POR_ID.items()}
    textos: dict[tuple[str, str], str] = {}
    for linha in corpus.open(encoding="utf-8"):
        d = json.loads(linha)
        textos[(d["fonte_id"], d["dispositivo"].replace(".", ""))] = _so_letras(d["texto"])
    for f in rr.TODOS_FUNDAMENTOS:
        texto = textos.get((sigla_para_id[f.norma], f.chave.replace(".", "")), "")
        assert _so_letras(f.trecho) in texto, f"{f.norma} {f.artigo}: trecho não encontrado no corpus"


# ---------------------------------------------------------------- integração com o Ato Pronto

def _pipe(canal_llm: str | None):
    pipe = MagicMock()
    pipe.llm_model = "mock"
    pipe.retrieve.return_value = [{"text": "Art. 1.128. Qualquer pessoa...", "source": "s", "page": 1,
                                   "norma": "Código de Normas CGJ-CE", "dispositivo": "Art. 1128"}]
    if canal_llm:
        r = MagicMock()
        r.choices = [MagicMock(message=MagicMock(content=json.dumps({
            "canal": canal_llm, "veredito": "SUGESTÃO: DEFERIR", "instrucao_balcao": "Identificar o requerente.",
            "fundamentacao": [{"norma": "Código de Normas CGJ-CE", "artigo": "Art. 1.128, caput", "aplicacao": "x"}],
            "minuta_ato": "Despacho.", "auditoria_lgpd": {"finalidade": "x", "base_legal_lgpd": "x",
                                                          "categoria_titular": "x", "dados_tratados": ["x"],
                                                          "salvaguardas_adotadas": "x"}})))]
        pipe._call_chat_completions.return_value = r
    return pipe


def _pedido(tipo, solicitante=TERCEIRO, condicao=None):
    return PedidoBalcao(tipo_pedido=tipo, solicitante=solicitante, protocolo="PROT-T", condicao_confirmada=condicao)


def test_ia_que_concorda_com_a_regra_recebe_os_fundamentos_literais_primeiro():
    saida = processar_ato_pronto(_pipe("VERDE"), _pedido("Certidão de Inteiro Teor de Matrícula"))
    assert saida.canal == CanalRisco.VERDE
    assert saida.regra.cobertura == "REGRA" and not saida.regra.divergencia_llm
    assert saida.fundamentacao[0].artigo == "Art. 1.128, caput"
    assert [d.artigo for d in saida.fundamentacao].count("Art. 1.128, caput") == 1
    assert saida.ficha is None


def test_ia_que_diverge_da_regra_vira_indefinido():
    saida = processar_ato_pronto(_pipe("AMARELO"), _pedido("Certidão de Inteiro Teor de Matrícula"))
    assert saida.canal == CanalRisco.INDEFINIDO
    assert "a norma indica VERDE" in saida.regra.divergencia_llm
    assert saida.minuta_ato == ""


def test_condicional_sem_resposta_nao_chama_busca_nem_ia():
    pipe = _pipe("VERDE")
    saida = processar_ato_pronto(pipe, _pedido("Cópia de Título / Documento Arquivado no Cartório"))
    assert saida.canal == CanalRisco.INDEFINIDO
    assert "previsão legal" in saida.auditoria_lgpd.falha
    pipe.retrieve.assert_not_called()
    pipe._call_chat_completions.assert_not_called()


def test_busca_por_cpf_gera_ficha_do_paragrafo_3():
    saida = processar_ato_pronto(_pipe("AMARELO"), _pedido("Busca por Indicador Pessoal (Pesquisa de Bens por CPF/Nome)"))
    assert saida.canal == CanalRisco.AMARELO and saida.ficha is not None
    texto = saida.ficha.texto()
    for campo in ("Nome do requerente", "Finalidade declarada", "Art. 1.128, §3º", "Art. 128",
                  "Direito do titular"):
        assert campo in texto
    assert saida.ficha.emitida_em.endswith("-03:00")


def test_sem_regra_mantem_a_sugestao_da_ia_marcada():
    saida = processar_ato_pronto(_pipe("VERMELHO"), _pedido("Pedido de Exclusão de Dados da Matrícula com base na LGPD"))
    assert saida.canal == CanalRisco.VERMELHO
    assert saida.regra.cobertura == "SEM_REGRA"


def test_prompt_recebe_o_canal_decidido_e_os_trechos():
    regra = rr.decidir("Busca por Indicador Pessoal (Pesquisa de Bens por CPF/Nome)")
    prompt = build_ato_pronto_prompt("ctx", _pedido("Busca por Indicador Pessoal (Pesquisa de Bens por CPF/Nome)"),
                                     regra=regra)
    assert "CANAL DEFINIDO PELA NORMA (motor de regras; não altere): AMARELO" in prompt
    assert rr.CNJ_126.trecho in prompt
