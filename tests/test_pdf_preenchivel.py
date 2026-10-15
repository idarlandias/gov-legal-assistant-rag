"""PDF preenchível do cartório: gera, preenche como o Oficial faria, lê de volta e avalia."""

import json
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "scripts" / "folha_gabarito"))

import avaliar_gabarito as ag  # noqa: E402
import gerar_pdf_preenchivel as gp  # noqa: E402
import ler_pdf_preenchido as lp  # noqa: E402
import resumir_diario as rd  # noqa: E402


def _preencher(origem: Path, destino: Path, valores: dict) -> None:
    writer = PdfWriter(clone_from=str(origem))
    for pagina in writer.pages:
        writer.update_page_form_field_values(pagina, valores, auto_regenerate=False)
    with destino.open("wb") as f:
        writer.write(f)


def test_pdf_tem_campos_de_todos_os_casos_e_valores_do_gabarito(tmp_path):
    pdf = gp.gerar(tmp_path / "doc.pdf")
    campos = PdfReader(str(pdf)).get_fields()
    for caso in ag.casos_rcpn():
        for sufixo in ("decisao", "quem_decide", "fundamentos", "como_atender", "erro_grave"):
            assert f"caso_{caso['id']}_{sufixo}" in campos
    estados = {s.lstrip("/") for s in campos["caso_101_decisao"]["/_States_"]} - {"Off"}
    assert estados == ag.DECISOES, "as opções do PDF precisam ser exatamente o vocabulário do gabarito"
    opcoes = {o for o in campos["diario_01_desfecho"]["/Opt"]} - {gp.VAZIO}
    assert opcoes == rd.VALORES["desfecho"]


def test_pdf_nao_traz_resposta_do_sistema(tmp_path):
    pdf = gp.gerar(tmp_path / "doc.pdf")
    campos = PdfReader(str(pdf)).get_fields()
    preenchidos = {k: v.get("/V") for k, v in campos.items() if v.get("/V") not in (None, "", "/Off", gp.VAZIO)}
    assert preenchidos == {}, "teste cego: nenhum campo pode vir preenchido"


def test_ida_e_volta_gera_gabarito_e_diario_avaliaveis(tmp_path):
    pdf = gp.gerar(tmp_path / "doc.pdf")
    preenchido = tmp_path / "devolvido.pdf"
    _preencher(pdf, preenchido, {
        "caso_105_decisao": "/ENCAMINHAR_JUIZ", "caso_105_quem_decide": "/oficial",
        "caso_105_fundamentos": "Prov. CNJ 149/2023, art. 114, §1º", "caso_105_como_atender": "Encaminhar ao juízo.",
        "caso_101_decisao": "/DEFERIR", "caso_101_fundamentos": "CNJ 149, art. 113",
        "b_1": "cerca de 30", "diario_01_data": "20/10", "diario_01_atribuicao": "RCPN",
        "diario_01_gerou_duvida": "sim", "diario_01_quem_decidiu": "oficial", "diario_01_desfecho": "encaminhado_juiz",
        "diario_01_tempo_min": "15", "diario_02_data": "20/10",  # linha 2 incompleta: deve ser ignorada com aviso
        "val_nome": "Oficial Teste", "val_funcao": "Oficial", "val_data": "20/10/2026",
        "val_autorizacao": "/funcao_municipio",
    })
    dados = lp.ler(preenchido)
    assert dados["validacao"]["autorizacao"] == "funcao_municipio"
    res = lp.gravar(dados, "teste_rcpn", tmp_path)
    assert any("linha 2" in a for a in res["avisos"])

    gabarito = ag.ler_gabarito(tmp_path / "gabarito_rcpn.csv")
    assert set(gabarito) == {101, 105}
    assert gabarito[105]["decisao_esperada"] == "ENCAMINHAR_JUIZ"
    assert gabarito[105]["validado_por"] == "Oficial Teste (Oficial)"
    conc = ag.concordancia_motor_rcpn(gabarito)
    assert conc["comparados"] == 2 and conc["concordantes"] == 2

    diario = rd.ler_diario(tmp_path / "diario_balcao_teste_rcpn.csv")
    assert len(diario) == 1 and diario[0]["gerou_duvida"] == "sim"
    b = json.loads((tmp_path / "respostas_parte_b_teste_rcpn.json").read_text(encoding="utf-8"))
    assert b["parte_b"][f"1. {gp.PERGUNTAS_B[0]}"] == "cerca de 30"


def test_respostas_devolvidas_ficam_fora_do_git():
    import subprocess
    for caminho in ("data/validacao/gabarito_rcpn.csv", "data/validacao/respostas_parte_b_x.json",
                    "data/validacao/diario_balcao_x.csv"):
        r = subprocess.run(["git", "check-ignore", caminho], cwd=RAIZ, capture_output=True)
        assert r.returncode == 0, f"{caminho} precisa estar no .gitignore (nome do Oficial / dados reais)"
