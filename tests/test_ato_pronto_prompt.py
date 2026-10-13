"""Prompt do Ato Pronto: canais sem supressão de dados, proibição explícita e snapshot.

Para atualizar o snapshot depois de uma mudança INTENCIONAL no prompt:
    ATUALIZAR_SNAPSHOT=1 python -m pytest tests/test_ato_pronto_prompt.py
"""

import difflib
import os
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.fase3.ato_pronto import (
    AVISO_RESPONSABILIDADE,
    CANAIS_PROMPT,
    REGRA_INTEIRO_TEOR,
    VEREDITOS,
    AtoProntoOutput,
    CanalRisco,
    PedidoBalcao,
    build_ato_pronto_prompt,
    processar_ato_pronto,
)

PROIBIDAS = ("tarja", "tarjar", "tarjamento", "suprimir")
SNAPSHOT = Path(__file__).parent / "snapshots" / "ato_pronto_prompt.txt"
UI = Path(__file__).resolve().parents[1] / "src" / "ui" / "streamlit_app.py"

PEDIDO = PedidoBalcao(tipo_pedido="Certidão de Inteiro Teor de Matrícula", solicitante="Terceiro identificado",
                      dados_sensiveis=["CPF"], detalhes_caso="Pedido no balcão", protocolo="PROT-SNAP")
CONTEXTO = "[Código de Normas CGJ-CE — Art. 1128]\nArt. 1.128. Qualquer pessoa pode requerer certidão..."


def _canal(nome: str) -> str:
    return next(linha for linha in CANAIS_PROMPT.splitlines() if linha.startswith(f"- Canal {nome}"))


# ---------------------------------------------------------------- canais

@pytest.mark.parametrize("palavra", PROIBIDAS)
def test_canais_nao_mencionam_supressao(palavra):
    assert palavra not in CANAIS_PROMPT.lower()


@pytest.mark.parametrize("palavra", PROIBIDAS)
def test_prompt_so_menciona_supressao_na_regra_que_a_proibe(palavra):
    prompt = build_ato_pronto_prompt(CONTEXTO, PEDIDO)
    assert REGRA_INTEIRO_TEOR in prompt
    assert palavra not in prompt.replace(REGRA_INTEIRO_TEOR, "").lower()


def test_amarelo_e_exigencia_previa_do_1128():
    amarelo = _canal("AMARELO")
    for trecho in ("EXIGÊNCIA PRÉVIA", "identificação do requerente", "indicação da finalidade",
                   "Art. 1.128, §2º, I a V", "§3º"):
        assert trecho in amarelo


def test_vermelho_nao_inclui_informacao_por_telefone():
    assert "telefone" not in _canal("VERMELHO").lower()
    assert "telefone" not in build_ato_pronto_prompt(CONTEXTO, PEDIDO).replace(PEDIDO.detalhes_caso, "").lower()


def test_regra_de_proibicao_literal_e_alternativa_do_125():
    assert REGRA_INTEIRO_TEOR == (
        "Nunca instrua a suprimir, tarjar ou omitir dados de uma certidão de inteiro teor. Se o caso parecer "
        "exigir conteúdo reduzido, indique a certidão de situação jurídica atual (Prov. CNJ 149/2023, Art. 125) "
        "como alternativa.")


def test_formato_json_lista_so_sugestoes():
    prompt = build_ato_pronto_prompt(CONTEXTO, PEDIDO)
    linha = next(x for x in prompt.splitlines() if x.strip().startswith('"veredito"'))
    assert all(v in linha for v in VEREDITOS)
    assert not re.search(r'"(IN)?DEFERIDO', linha)


# ---------------------------------------------------------------- snapshot

def test_snapshot_do_prompt():
    atual = build_ato_pronto_prompt(CONTEXTO, PEDIDO)
    if os.environ.get("ATUALIZAR_SNAPSHOT") or not SNAPSHOT.exists():
        SNAPSHOT.parent.mkdir(exist_ok=True)
        SNAPSHOT.write_text(atual, encoding="utf-8", newline="\n")
    esperado = SNAPSHOT.read_text(encoding="utf-8")
    diff = "".join(difflib.unified_diff(esperado.splitlines(True), atual.splitlines(True),
                                        "snapshot", "prompt atual"))
    assert atual == esperado, f"Prompt mudou. Se foi intencional, ATUALIZAR_SNAPSHOT=1.\n{diff}"


# ---------------------------------------------------------------- veredito como sugestão

def _saida(veredito: str, canal: str = "VERDE") -> AtoProntoOutput:
    return AtoProntoOutput.model_validate({
        "canal": canal, "veredito": veredito, "instrucao_balcao": "x", "minuta_ato": "x",
        "auditoria_lgpd": {"finalidade": "x", "base_legal_lgpd": "x", "categoria_titular": "x",
                           "dados_tratados": ["x"], "salvaguardas_adotadas": "x"}})


@pytest.mark.parametrize("entrada,esperado", [
    ("SUGESTÃO: DEFERIR", "SUGESTÃO: DEFERIR"),
    ("DEFERIDO INTEGRAL", "SUGESTÃO: DEFERIR INTEGRAL"),
    ("INDEFERIDO (NOTA DEVOLUTIVA)", "SUGESTÃO: INDEFERIR (NOTA DEVOLUTIVA)"),
    ("Exigir finalidade", "SUGESTÃO: Exigir finalidade"),
])
def test_veredito_sempre_vira_sugestao(entrada, esperado):
    assert _saida(entrada).veredito == esperado


def test_veredito_com_tarja_vira_indefinido():
    pipe = MagicMock()
    pipe.llm_model = "mock"
    pipe.retrieve.return_value = [{"text": "t", "source": "s", "page": 0, "norma": "Código de Normas CGJ-CE",
                                   "dispositivo": "Art. 1128"}]
    r = MagicMock()
    r.choices = [MagicMock(message=MagicMock(content=(
        '{"canal": "AMARELO", "veredito": "DEFERIDO COM TARJAMENTO", "instrucao_balcao": "x", "minuta_ato": "x",'
        ' "auditoria_lgpd": {"finalidade": "x", "base_legal_lgpd": "x", "categoria_titular": "x",'
        ' "dados_tratados": ["x"], "salvaguardas_adotadas": "x"}}')))]
    pipe._call_chat_completions.return_value = r
    assert processar_ato_pronto(pipe, PEDIDO).canal == CanalRisco.INDEFINIDO


# ---------------------------------------------------------------- UI

def test_ui_sem_tarja_no_amarelo_e_com_aviso_de_responsabilidade():
    ui = UI.read_text(encoding="utf-8")
    assert "Liberação com Tarjamento" not in ui
    assert "tarjamento protetivo" not in ui
    assert "🔴 Info Verbal por Telefone" not in ui
    assert "AVISO_RESPONSABILIDADE" in ui
    assert AVISO_RESPONSABILIDADE == "Sugestão de ato. A decisão e a responsabilidade são do Oficial Registrador."
