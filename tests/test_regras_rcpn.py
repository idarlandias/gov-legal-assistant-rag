"""Motor de regras do Registro Civil: canal pela norma, autorização judicial só quando a norma exige."""

import itertools
import json
import re
import unicodedata
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.fase3 import regras_rcpn as rc
from src.fase3.ato_pronto import (
    ESPECIALIDADES_RCPN, VEREDITOS_RCPN, CanalRisco, PedidoBalcao, build_ato_pronto_prompt, processar_ato_pronto,
)
from src.fase3.regras_ri import Cobertura
from src.fase3.sources import FONTES_POR_ID

CORPUS = Path(__file__).resolve().parents[1] / "data" / "corpus_fase3" / "dispositivos.jsonl"


def _artigos(r):
    return {f"{f.norma}|{f.artigo}" for f in r.fundamentos}


# ---------------------------------------------------------------- tabela

@pytest.mark.parametrize("tipo", [rc.BREVE_RELATO, rc.OBITO, rc.BUSCA_INDICES])
def test_livres_sem_requerimento(tipo):
    r = rc.decidir(tipo, rc.TERCEIRO)
    assert (r.cobertura, r.canal, r.exige_identificacao, r.exige_autorizacao_judicial) == (
        Cobertura.REGRA, "VERDE", False, False)


def test_inteiro_teor_pelo_proprio_exige_requerimento_sem_juiz():
    r = rc.decidir(rc.INTEIRO_TEOR, rc.PROPRIO)
    assert (r.canal, r.exige_finalidade, r.exige_autorizacao_judicial, r.documento) == (
        "AMARELO", True, False, "requerimento_inteiro_teor")
    assert {"Provimento CNJ 149/2023|Art. 114, caput", "Provimento CNJ 149/2023|Art. 117, §3º"} <= _artigos(r)


def test_terceiro_com_dado_sensivel_de_pessoa_viva_so_com_juiz():
    r = rc.decidir(rc.INTEIRO_TEOR, rc.TERCEIRO, dado_sensivel=True, informacao_vedada=False,
                   registrado_falecido=False)
    assert (r.canal, r.exige_autorizacao_judicial) == ("VERMELHO", True)
    assert {"Provimento CNJ 149/2023|Art. 114, §1º", "Código de Normas CGJ-CE|Art. 255, §1º"} <= _artigos(r)


def test_dado_sensivel_de_falecido_dispensa_juiz():
    r = rc.decidir(rc.INTEIRO_TEOR, rc.PARENTE, dado_sensivel=True, informacao_vedada=False, registrado_falecido=True)
    assert (r.canal, r.exige_autorizacao_judicial) == ("AMARELO", False)
    assert "Provimento CNJ 149/2023|Art. 119" in _artigos(r)
    assert any("linha reta" in a for a in r.alertas)


def test_informacao_vedada_exige_juiz_mesmo_apos_o_obito():
    r = rc.decidir(rc.INTEIRO_TEOR, rc.TERCEIRO, dado_sensivel=False, informacao_vedada=True, registrado_falecido=True)
    assert (r.canal, r.exige_autorizacao_judicial) == ("VERMELHO", True)
    assert {"Código de Normas CGJ-CE|Art. 471, §2º", "Código de Normas CGJ-CE|Art. 471, §3º"} <= _artigos(r)


def test_terceiro_sem_dado_sensivel_nem_vedado_exige_so_requerimento():
    r = rc.decidir(rc.INTEIRO_TEOR, rc.TERCEIRO, dado_sensivel=False, informacao_vedada=False)
    assert (r.canal, r.exige_autorizacao_judicial) == ("AMARELO", False)


def test_sem_as_respostas_o_caso_fica_condicional_e_so_pergunta_o_necessario():
    r = rc.decidir(rc.INTEIRO_TEOR, rc.TERCEIRO)
    assert r.cobertura == Cobertura.CONDICIONAL and r.canal is None
    assert rc.PERGUNTA_SENSIVEL in r.pergunta and rc.PERGUNTA_VEDADA in r.pergunta
    assert rc.PERGUNTA_FALECIDO not in r.pergunta  # o óbito só importa se houver dado sensível
    r = rc.decidir(rc.INTEIRO_TEOR, rc.TERCEIRO, dado_sensivel=True, informacao_vedada=False)
    assert r.cobertura == Cobertura.CONDICIONAL and r.pergunta == rc.PERGUNTA_FALECIDO


def test_quesitos_com_dado_restrito_tem_o_tratamento_do_inteiro_teor():
    assert rc.decidir(rc.QUESITOS, rc.TERCEIRO, dado_sensivel=False).canal == "VERDE"
    r = rc.decidir(rc.QUESITOS, rc.TERCEIRO, dado_sensivel=True, informacao_vedada=False, registrado_falecido=False)
    assert r.canal == "VERMELHO"
    assert "Provimento CNJ 149/2023|Art. 116, caput" in _artigos(r)


@pytest.mark.parametrize("solicitante,falecido,canal", [
    (rc.PROPRIO, None, "VERDE"), (rc.TERCEIRO, False, "VERMELHO"), (rc.TERCEIRO, True, "AMARELO")])
def test_procedimento_preparatorio(solicitante, falecido, canal):
    assert rc.decidir(rc.PROCEDIMENTO, solicitante, registrado_falecido=falecido).canal == canal


def test_busca_em_outras_fontes_exige_requerimento_fundamentado():
    r = rc.decidir(rc.BUSCA_OUTRAS, rc.TERCEIRO)
    assert (r.canal, r.documento) == ("AMARELO", "requerimento_busca")


def test_registro_bloqueado_bloqueia_tudo():
    for tipo in rc.TIPOS_RCPN:
        r = rc.decidir(tipo, rc.PROPRIO, registro_bloqueado=True)
        assert (r.canal, r.exige_autorizacao_judicial) == ("VERMELHO", True)


def test_vermelho_so_existe_quando_a_norma_exige_juiz():
    """Nunca há recusa do sistema: todo VERMELHO no Registro Civil é encaminhamento ao juízo."""
    respostas = (None, True, False)
    for tipo, solicitante, s, v, f in itertools.product(rc.TIPOS_RCPN, rc.SOLICITANTES_RCPN, respostas, respostas,
                                                        respostas):
        r = rc.decidir(tipo, solicitante, s, v, f)
        assert r.canal != "VERMELHO" or r.exige_autorizacao_judicial


def _so_letras(t: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", t.lower())


def test_todo_fundamento_e_transcricao_literal_do_corpus():
    if not CORPUS.exists():
        pytest.skip(f"PULADO: {CORPUS} ausente (gitignored; gere com scripts/fase3/build_corpus.py)")
    sigla_para_id = {f.sigla: fid for fid, f in FONTES_POR_ID.items()}
    textos = {}
    for linha in CORPUS.open(encoding="utf-8"):
        d = json.loads(linha)
        textos[(d["fonte_id"], d["dispositivo"].replace(".", ""))] = _so_letras(d["texto"])
    for f in rc.TODOS_FUNDAMENTOS:
        texto = textos.get((sigla_para_id[f.norma], f.chave.replace(".", "")), "")
        assert _so_letras(f.trecho) in texto, f"{f.norma} {f.artigo}: trecho não encontrado no corpus"


# ---------------------------------------------------------------- integração com o Ato Pronto

def _pipe(canal_llm: str):
    pipe = MagicMock()
    pipe.llm_model = "mock"
    pipe.retrieve.return_value = [{"text": "Art. 114...", "source": "s", "page": 1,
                                   "norma": "Provimento CNJ 149/2023", "dispositivo": "Art. 114"}]
    r = MagicMock()
    r.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "canal": canal_llm, "veredito": "SUGESTÃO: SOMENTE COM AUTORIZAÇÃO JUDICIAL",
        "instrucao_balcao": "Encaminhar ao juízo.", "fundamentacao": [], "minuta_ato": "Termo de encaminhamento.",
        "auditoria_lgpd": {"finalidade": "x", "base_legal_lgpd": "x", "categoria_titular": "x",
                           "dados_tratados": ["x"], "salvaguardas_adotadas": "x"}})))]
    pipe._call_chat_completions.return_value = r
    return pipe


def _pedido(**kw):
    base = dict(tipo_pedido=rc.INTEIRO_TEOR, solicitante=rc.TERCEIRO, protocolo="PROT-RC", atribuicao="RCPN",
                dado_sensivel=True, informacao_vedada=False, registrado_falecido=False)
    return PedidoBalcao(**(base | kw))


def test_ato_pronto_rcpn_encaminha_ao_juizo_com_requerimento():
    pipe = _pipe("VERMELHO")
    saida = processar_ato_pronto(pipe, _pedido())
    assert saida.canal == CanalRisco.VERMELHO
    assert saida.regra.exige_autorizacao_judicial
    assert saida.ficha.titulo == "REQUERIMENTO DE CERTIDÃO EM INTEIRO TEOR" and saida.ficha.encaminhar_ao_juizo
    texto = saida.ficha.texto()
    assert "Motivo do pedido" in texto and "ENCAMINHAMENTO" in texto and "Grau de parentesco" in texto
    assert pipe.retrieve.call_args.kwargs["especialidades"] == ESPECIALIDADES_RCPN


def test_ato_pronto_rcpn_ia_divergente_vira_indefinido():
    saida = processar_ato_pronto(_pipe("AMARELO"), _pedido())
    assert saida.canal == CanalRisco.INDEFINIDO
    assert "a norma indica VERMELHO" in saida.regra.divergencia_llm


def test_ato_pronto_rcpn_condicional_nao_chama_ia():
    pipe = _pipe("VERDE")
    saida = processar_ato_pronto(pipe, _pedido(dado_sensivel=None, informacao_vedada=None, registrado_falecido=None))
    assert saida.canal == CanalRisco.INDEFINIDO
    pipe._call_chat_completions.assert_not_called()


def test_prompt_rcpn_usa_especialidade_vereditos_e_canais_proprios():
    pedido = _pedido()
    prompt = build_ato_pronto_prompt("ctx", pedido, regra=rc.decidir(rc.INTEIRO_TEOR, rc.TERCEIRO, True, False, False))
    assert "Especialista em Registro Civil das Pessoas Naturais do Ceará" in prompt
    assert all(v in prompt for v in VEREDITOS_RCPN)
    assert "SOMENTE COM AUTORIZAÇÃO JUDICIAL" in prompt and "Art. 1.128" not in prompt
