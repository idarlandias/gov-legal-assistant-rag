"""Resposta vazia do LLM (ex.: gpt-oss-20b esgotando tokens raciocinando) nunca passa calada."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.fase3.pipeline import Fase3Pipeline
from src.pipeline.rag import (
    MAX_TOKENS_NOVA_TENTATIVA,
    RESPOSTA_VAZIA,
    RAGPipeline,
    RespostaVaziaError,
    resposta_vazia,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "benchmark"))


def _resp(conteudo, finish_reason="stop", tool_calls=None) -> MagicMock:
    msg = MagicMock(content=conteudo, tool_calls=tool_calls)
    r = MagicMock()
    r.choices = [MagicMock(message=msg, finish_reason=finish_reason)]
    return r


def _pipeline(*respostas) -> RAGPipeline:
    pipe = object.__new__(RAGPipeline)  # sem cliente real, Chroma ou embeddings
    pipe.llm_model = "openai/gpt-oss-20b"
    pipe.client = MagicMock()
    pipe.client.chat.completions.create.side_effect = list(respostas)
    return pipe


@pytest.fixture(autouse=True)
def _groq(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("PREMIUM_MODEL", raising=False)


def _chamadas(pipe):
    return pipe.client.chat.completions.create.call_args_list


# ---------------------------------------------------------------- camada de chamada ao Groq

def test_finish_reason_length_tenta_de_novo_com_120b_e_mais_tokens():
    pipe = _pipeline(_resp("", finish_reason="length"), _resp("Resposta completa."))
    resp = pipe._call_chat_completions(model="openai/gpt-oss-20b", messages=[])
    assert resp.choices[0].message.content == "Resposta completa."
    assert len(_chamadas(pipe)) == 2
    segunda = _chamadas(pipe)[1].kwargs
    assert segunda["model"] == "openai/gpt-oss-120b"
    assert segunda["max_tokens"] == MAX_TOKENS_NOVA_TENTATIVA


def test_length_com_texto_parcial_tambem_conta_como_vazia():
    assert resposta_vazia(_resp("Raciocínio cortado no meio", finish_reason="length"))


def test_conteudo_so_espacos_com_stop_tenta_de_novo():
    pipe = _pipeline(_resp("   \n ", finish_reason="stop"), _resp("Ok na segunda."))
    assert pipe._call_chat_completions(model="openai/gpt-oss-20b", messages=[]).choices[0].message.content == "Ok na segunda."
    assert len(_chamadas(pipe)) == 2


def test_duas_falhas_levantam_resposta_vazia_explicita():
    pipe = _pipeline(_resp(None, finish_reason="length"), _resp("", finish_reason="length"))
    with pytest.raises(RespostaVaziaError) as exc:
        pipe._call_chat_completions(model="openai/gpt-oss-20b", messages=[])
    assert RESPOSTA_VAZIA in str(exc.value)
    assert exc.value.finish_reason == "length" and exc.value.modelo == "openai/gpt-oss-120b"
    assert len(_chamadas(pipe)) == 2  # UMA nova tentativa, não mais


def test_resposta_normal_nao_repete():
    pipe = _pipeline(_resp("Resposta."))
    pipe._call_chat_completions(model="openai/gpt-oss-20b", messages=[])
    assert len(_chamadas(pipe)) == 1


def test_tool_calls_com_conteudo_vazio_nao_e_resposta_vazia():
    pipe = _pipeline(_resp(None, finish_reason="tool_calls", tool_calls=[MagicMock()]))
    pipe._call_chat_completions(model="openai/gpt-oss-20b", messages=[])
    assert len(_chamadas(pipe)) == 1


def test_premium_model_do_env_tem_prioridade(monkeypatch):
    monkeypatch.setenv("PREMIUM_MODEL", "qwen/qwen3.8-27b")
    pipe = _pipeline(_resp(""), _resp("ok"))
    pipe._call_chat_completions(model="openai/gpt-oss-20b", messages=[])
    assert _chamadas(pipe)[1].kwargs["model"] == "qwen/qwen3.8-27b"


# ---------------------------------------------------------------- answer() da Fase 3

def test_answer_marca_resposta_vazia_em_vez_de_string_vazia():
    pipe = object.__new__(Fase3Pipeline)
    pipe.retrieve = MagicMock(return_value=[{"text": "t", "source": "s", "page": 0, "norma": "Lei 6.015/1973",
                                             "dispositivo": "Art. 17"}])
    pipe.llm_model = "openai/gpt-oss-20b"
    pipe._call_chat_completions = MagicMock(side_effect=RespostaVaziaError("openai/gpt-oss-120b", "length"))
    out = pipe.answer("pergunta")
    assert out["status"] == RESPOSTA_VAZIA
    assert out["answer"].startswith(RESPOSTA_VAZIA) and out["answer"].strip()
    assert out["sources"] == [("Lei 6.015/1973 — Art. 17", 0)]


# ---------------------------------------------------------------- benchmark

def test_benchmark_separa_resposta_vazia_de_respondida_e_nao_encontrado():
    import run_rag_benchmark as rb

    casos = [
        {"resposta": "Emitir a certidão. Art. 17 da Lei 6.015/1973.", "erro": None},
        {"resposta": "Não encontrado no corpus.", "erro": None},
        {"resposta": "", "erro": None},  # o caso da #19 em JSONs antigos
        {"resposta": "RESPOSTA_VAZIA: o modelo não produziu...", "status": RESPOSTA_VAZIA, "erro": None},
        {"resposta": "", "erro": "TimeoutError: x"},
    ]
    assert [rb.classificar_resposta(c) for c in casos] == [
        rb.RESPONDIDA, rb.NAO_ENCONTRADO, rb.RESPOSTA_VAZIA, rb.RESPOSTA_VAZIA, rb.ERRO]
    assert rb.agregar_status(casos) == {"RESPONDIDA": 1, "NAO_ENCONTRADO": 1, "RESPOSTA_VAZIA": 2, "ERRO": 1}


def test_planilha_tem_status_e_contagem_no_resumo(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    import build_planilha
    import run_rag_benchmark as rb

    out = tmp_path / "p.xlsx"
    sys.argv = ["build_planilha.py", "--out", str(out)]
    assert build_planilha.main() == 0
    meta = {"data": "2026-10-13T10:00:00", "provider": "groq", "llm_model": "m", "k": 5, "git_commit": "x",
            "ferramenta": "RAG Fase 3"}
    rec = {"id": 19, "resposta": "", "fontes": "", "latencia_s": 1.0, "tokens_entrada": 1, "tokens_saida": 2048,
           "erro": None}
    rb.fill_xlsx(out, meta, [rec], overwrite=False)
    wb = openpyxl.load_workbook(out)
    ws = wb["Respostas"]
    r = next(i for i in range(2, ws.max_row + 1) if ws[f"A{i}"].value == 19 and ws[f"B{i}"].value == "RAG Fase 3")
    assert ws[f"X{r}"].value == rb.RESPOSTA_VAZIA
    resumo = wb["Resumo"]
    assert resumo["O3"].value == "Resposta vazia"
    assert '"RESPOSTA_VAZIA"' in resumo["O8"].value  # linha da 5ª ferramenta (RAG Fase 3)
