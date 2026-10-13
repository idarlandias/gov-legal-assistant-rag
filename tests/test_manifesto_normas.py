"""Manifesto da barra lateral: 11 fontes, quatro campos preenchidos, nada vindo do Last-Modified."""

import json

import pytest

from src.fase3.manifesto import CAMPOS, MANIFESTO, carregar_normas


def _gravar(tmp_path, fontes):
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"fontes": fontes}, ensure_ascii=False), encoding="utf-8")
    return p


def test_manifesto_real_tem_11_fontes_completas():
    fontes = carregar_normas()
    assert len(fontes) == 11
    assert all(f["baixado_em"] == "2026-09-23" for f in fontes)


def test_manifesto_nao_usa_last_modified():
    texto = MANIFESTO.read_text(encoding="utf-8").lower()
    assert "last-modified" not in texto and "last_modified" not in texto


def test_falha_com_menos_de_11_fontes(tmp_path):
    fontes = carregar_normas()[:10]
    with pytest.raises(ValueError, match="10 fontes"):
        carregar_normas(_gravar(tmp_path, fontes))


@pytest.mark.parametrize("campo", CAMPOS)
def test_falha_com_campo_vazio_ou_ausente(tmp_path, campo):
    fontes = carregar_normas()
    fontes[3] = {**fontes[3], campo: "  "}
    with pytest.raises(ValueError, match=campo):
        carregar_normas(_gravar(tmp_path, fontes))
    del fontes[3][campo]
    with pytest.raises(ValueError, match=campo):
        carregar_normas(_gravar(tmp_path, fontes))


def test_barra_lateral_le_o_manifesto_sem_imagem_remota():
    from pathlib import Path
    ui = (Path(__file__).resolve().parents[1] / "src" / "ui" / "streamlit_app.py").read_text(encoding="utf-8")
    assert "carregar_normas()" in ui
    assert "st.image(" not in ui and "icons8" not in ui
    assert 'st.expander("Diagnóstico técnico", expanded=False)' in ui
