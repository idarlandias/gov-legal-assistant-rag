"""Testes do benchmark da Fase 3 (sem chamar LLM)."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "benchmark"))

openpyxl = pytest.importorskip("openpyxl")

import build_planilha  # noqa: E402
import run_rag_benchmark as rb  # noqa: E402


def test_perguntas_json_valido():
    data = json.loads(rb.PERGUNTAS_JSON.read_text(encoding="utf-8"))
    ids = [p["id"] for p in data["perguntas"]]
    assert len(ids) == 25
    assert len(set(ids)) == len(ids)
    assert rb.RAG_TOOL in data["ferramentas"]
    assert all(p["pergunta"].strip() and p["categoria"].strip() for p in data["perguntas"])


def test_load_perguntas_filtra_e_rejeita_id_inexistente():
    assert [p["id"] for p in rb.load_perguntas({2, 11})] == [2, 11]
    with pytest.raises(SystemExit):
        rb.load_perguntas({999})


def test_fmt_sources_deduplica_mantendo_ordem():
    assert rb.fmt_sources([("a.pdf", 1), ("b.pdf", 3), ("a.pdf", 1)]) == "a.pdf:p1; b.pdf:p3"


def _planilha(tmp_path):
    out = tmp_path / "p.xlsx"
    sys.argv = ["build_planilha.py", "--out", str(out)]
    assert build_planilha.main() == 0
    return out


def test_build_planilha_recusa_sobrescrever(tmp_path):
    out = _planilha(tmp_path)
    sys.argv = ["build_planilha.py", "--out", str(out)]
    assert build_planilha.main() == 1


def test_fill_xlsx_preenche_so_rag_e_respeita_overwrite(tmp_path):
    out = _planilha(tmp_path)
    meta = {"data": "2026-09-23T10:00:00", "provider": "gemini", "llm_model": "m", "k": 5,
            "git_commit": "abc123"}
    rec = {"id": 1, "resposta": "R1", "fontes": "x.pdf:p1", "latencia_s": 1.5,
           "tokens_entrada": 100, "tokens_saida": 20, "erro": None}
    falha = {**rec, "id": 2, "erro": "Boom"}

    assert rb.fill_xlsx(out, meta, [rec, falha], overwrite=False) == (1, 0)

    ws = openpyxl.load_workbook(out)["Respostas"]
    rag = {ws[f"A{r}"].value: r for r in range(2, ws.max_row + 1) if ws[f"B{r}"].value == rb.RAG_TOOL}
    r1 = rag[1]
    assert ws[f"G{r1}"].value == "R1"
    assert ws[f"J{r1}"].value == 100
    assert ws[f"R{r1}"].value.startswith("=IF(")  # fórmula preservada
    assert ws[f"G{rag[2]}"].value is None  # erro não é gravado
    # Linha de outra ferramenta com o mesmo ID fica intacta
    assert all(ws[f"G{r}"].value is None for r in range(2, ws.max_row + 1) if r != r1)

    rec2 = {**rec, "resposta": "R1-novo"}
    assert rb.fill_xlsx(out, meta, [rec2], overwrite=False) == (0, 1)
    assert rb.fill_xlsx(out, meta, [rec2], overwrite=True) == (1, 0)
    assert openpyxl.load_workbook(out)["Respostas"][f"G{r1}"].value == "R1-novo"
