"""Consulta de recuperação do Ato Pronto: vocabulário das normas, não rótulos crus da UI."""

import ast
from pathlib import Path

import pytest

from src.fase3.ato_pronto import EXPANSAO_TIPO_PEDIDO, K_ATO_PRONTO, PedidoBalcao, gerar_query_recuperacao

UI = Path(__file__).resolve().parents[1] / "src" / "ui" / "streamlit_app.py"


def _opcoes_de_pedido_da_ui() -> list[str]:
    arvore = ast.parse(UI.read_text(encoding="utf-8"))
    for no in ast.walk(arvore):
        if isinstance(no, ast.Assign) and any(getattr(t, "id", "") == "opcoes_pedidos" for t in no.targets):
            return [ast.literal_eval(e) for e in no.value.elts]
    raise AssertionError("opcoes_pedidos não encontrado na UI")


def test_toda_opcao_da_ui_tem_expansao_normativa():
    faltando = [o for o in _opcoes_de_pedido_da_ui() if o.lower() not in EXPANSAO_TIPO_PEDIDO]
    assert not faltando, f"Opções da UI sem expansão: {faltando}"


def test_consulta_usa_expansao_e_termos_livres_no_final():
    p = PedidoBalcao(tipo_pedido="Certidão de Inteiro Teor de Matrícula", solicitante="Terceiro",
                     dados_sensiveis=["CPF"], detalhes_caso="pediu no balcão às 10h")
    q = gerar_query_recuperacao(p)
    assert q.startswith(EXPANSAO_TIPO_PEDIDO["certidão de inteiro teor de matrícula"])
    assert q.endswith("pediu no balcão às 10h")


def test_tipo_sem_expansao_usa_o_rotulo():
    p = PedidoBalcao(tipo_pedido="Pedido Desconhecido", solicitante="Terceiro")
    assert gerar_query_recuperacao(p).startswith("Pedido Desconhecido")


def test_top_k_do_ato_pronto_e_8():
    assert K_ATO_PRONTO == 8


# ---------------------------------------------------------------- regressão no índice real

@pytest.fixture(scope="module")
def retriever():
    try:
        from src.fase3.index import open_collection
        from src.fase3.retrieval import HybridRetriever

        col, emb = open_collection()
    except Exception as e:  # sem índice fase3 ou sem o modelo E5 baixado (ex.: CI)
        pytest.skip(f"índice fase3 indisponível: {type(e).__name__}: {e}")
    return HybridRetriever(col, emb)


def test_regressao_certidao_inteiro_teor_terceiro_traz_cnj_123_e_ce_1128(retriever):
    from src.fase3.pipeline import ESPECIALIDADES_RI
    from src.fase3.retrieval import rotulo_fonte

    pedido = PedidoBalcao(tipo_pedido="Certidão de Inteiro Teor de Matrícula",
                          solicitante="Terceiro sem comprovação de vínculo ou interesse jurídico")
    # mesmo caminho do Fase3Pipeline.retrieve
    hits = retriever.search(gerar_query_recuperacao(pedido), k=K_ATO_PRONTO, especialidades=set(ESPECIALIDADES_RI))
    rotulos = [rotulo_fonte(h) for h in hits]
    assert "Provimento CNJ 149/2023 — Art. 123" in rotulos, rotulos
    assert "Código de Normas CGJ-CE — Art. 1128" in rotulos, rotulos
