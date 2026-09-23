"""Testes da recuperação híbrida da Fase 3 (sem baixar o modelo E5)."""

from src.fase3.retrieval import BM25, rrf, tokenize


def test_tokenize_remove_acento_stopword_e_junta_milhar():
    toks = tokenize("A certidão da Lei 6.015/1973 e o Provimento nº 15/2026")
    assert "certid" in toks
    assert "6015" in toks and "1973" in toks and "15" in toks and "2026" in toks
    assert "da" not in toks and "a" not in toks


def test_tokenize_plural_e_singular_tem_mesmo_radical():
    assert tokenize("certidões")[0] == tokenize("certidão")[0]


def test_bm25_acha_documento_pelo_numero_do_ato():
    docs = [
        "Provimento 12/2026 trata de emolumentos",
        "Provimento 15/2026 altera a qualificação das partes",
        "Lei geral de proteção de dados",
    ]
    assert BM25(docs).top("o que mudou com o Provimento nº 15/2026?", 1) == [1]


def test_bm25_consulta_sem_termo_conhecido_devolve_vazio():
    assert BM25(["texto qualquer"]).top("xyzabc", 5) == []


def test_rrf_premia_quem_aparece_bem_nas_duas_listas():
    fused = [doc for doc, _ in rrf([["a", "b", "c"], ["d", "b", "e"]])]
    assert fused[0] == "b"  # 2º nas duas listas vence 1º em uma só
    assert set(fused) == {"a", "b", "c", "d", "e"}
