"""Testes de isolamento de domínio e comportamento do Tutor de Concursos.

Uso: `uv run pytest tests/test_domains.py -v`
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest

@pytest.fixture(scope="module")
def pipeline():
    pytest.importorskip("dotenv")
    from dotenv import load_dotenv
    load_dotenv()

    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        pytest.skip("API key nao configurada em .env")

    from src.pipeline.rag import build_rag_pipeline
    return build_rag_pipeline(corpus_dir="data/corpus")

def test_isolamento_dominio_lgpd(pipeline):
    """Garante que buscas com domínio 'lgpd' filtram apenas documentos da LGPD."""
    hits = pipeline.retrieve("tratamento de dados", k=5, domain="lgpd")
    for h in hits:
        # Verifica se o arquivo retornado tem relação com LGPD (ex: LGPD ou 13709)
        assert any(x in h["source"].upper() for x in ["LGPD", "13709"]), f"Documento incorreto retornado para o domínio LGPD: {h['source']}"

def test_isolamento_dominio_licitacoes(pipeline):
    """Garante que buscas com domínio 'licitacoes' filtram apenas documentos de licitações."""
    hits = pipeline.retrieve("dispensa de licitação", k=5, domain="licitacoes")
    for h in hits:
        assert any(x in h["source"].lower() for x in ["licitacao", "14133", "contratos"]), f"Documento incorreto para licitações: {h['source']}"

def test_concursos_resposta_negativa_fora_de_escopo(pipeline):
    """Verifica se perguntas de concurso fora do escopo ou com base de concursos vazia retornam a resposta estrita de erro."""
    # Como o diretório concursos foi criado recentemente e pode estar sem PDFs de concurso ainda,
    # a busca vetorial no domínio 'concursos' deve retornar vazio, ativando a resposta antialucinação.
    result = pipeline.answer("Qual o regime de tributação simplificado para microempresas conforme esta apostila?", domain="concursos")
    assert "Não encontrado no corpus de estudos" in result["answer"], f"O RAG de concursos falhou na ancoragem. Resposta gerada: {result['answer']}"

def test_concursos_comportamento_didatico_se_tiver_dados(pipeline):
    """Se houver dados de concurso, valida se o RAG executa. Se não, valida o retorno antialucinação padrão."""
    result = pipeline.answer("Explique a diferença entre ativo e passivo segundo a aula.", domain="concursos")
    # Caso não haja arquivos indexados no domínio concursos:
    if not pipeline.retrieve("ativo passivo", domain="concursos"):
        assert "Não encontrado no corpus de estudos" in result["answer"]
    else:
        # Se houver, a resposta não deve ser vazia
        assert len(result["answer"]) > 0
        assert "Não encontrado no corpus de estudos" not in result["answer"]
