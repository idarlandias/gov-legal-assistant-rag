"""Chat e Ato Pronto usam a MESMA constante de regras de decisão, sem tarja em nenhum dos dois."""

import re

import src.fase3.ato_pronto as ato_pronto
import src.fase3.pipeline as pipeline
from src.fase3 import regras_prompt
from src.fase3.ato_pronto import PedidoBalcao, build_ato_pronto_prompt
from src.fase3.pipeline import build_cartorio_prompt
from src.fase3.regras_prompt import DECISOES, REGRA_INTEIRO_TEOR, REGRAS_DECISAO

PEDIDO = PedidoBalcao(tipo_pedido="Certidão de Inteiro Teor de Matrícula", solicitante="Terceiro identificado")


def test_os_dois_modulos_importam_o_mesmo_objeto():
    assert pipeline.REGRAS_DECISAO is regras_prompt.REGRAS_DECISAO
    assert ato_pronto.REGRAS_DECISAO is regras_prompt.REGRAS_DECISAO


def test_os_dois_prompts_contem_as_regras():
    assert REGRAS_DECISAO in build_cartorio_prompt("ctx", "pergunta")
    assert REGRAS_DECISAO in build_ato_pronto_prompt("ctx", PEDIDO)


def test_triade_e_regra_do_inteiro_teor():
    assert DECISOES == (
        "DEFERIR",
        "DEFERIR MEDIANTE EXIGÊNCIA PRÉVIA (identificação e finalidade, com ficha do Art. 1.128, §3º, "
        "do Código de Normas da CGJ-CE)",
        "INDEFERIR (nota devolutiva fundamentada)",
    )
    assert REGRA_INTEIRO_TEOR in REGRAS_DECISAO


def test_chat_so_menciona_supressao_na_regra_que_a_proibe():
    prompt = build_cartorio_prompt("ctx", "pergunta").replace(REGRA_INTEIRO_TEOR, "")
    assert not re.search(r"tarj|suprim|integralmente|condicionado", prompt, re.IGNORECASE)
