"""Formulários online: o script gerado, a simulação dele em Node e o leitor do CSV de respostas."""

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "scripts" / "folha_gabarito"))

import avaliar_gabarito as ag  # noqa: E402
import forms_config as fc  # noqa: E402
import gerar_google_forms as gf  # noqa: E402
import ler_respostas_forms as lf  # noqa: E402
import resumir_diario as rd  # noqa: E402


def test_script_versionado_esta_atualizado(tmp_path):
    novo = gf.gerar(tmp_path / "x.gs")
    assert novo.read_text(encoding="utf-8") == gf.SAIDA.read_text(encoding="utf-8")


def test_vocabulario_igual_ao_dos_avaliadores():
    assert {c for c, _ in fc.DECISOES} == ag.DECISOES
    assert {c for c, _ in fc.DIARIO_DESFECHO} == rd.VALORES["desfecho"]
    assert {c for c, _ in fc.DIARIO_QUEM} == rd.VALORES["quem_decidiu"]
    assert {c for c, _ in fc.DIARIO_CANAL} == rd.VALORES["canal_entrada"]
    assert {c for c, _ in fc.DIARIO_ATRIBUICAO} <= rd.VALORES["atribuicao"]


def test_titulos_unicos_e_todos_os_casos():
    casos = ag.casos_rcpn()
    itens = [i for i in gf.itens_pesquisa(casos) if i["tipo"] not in ("secao", "texto_info")]
    titulos = [i["titulo"] for i in itens]
    assert len(titulos) == len(set(titulos)), "os títulos viram colunas do CSV: precisam ser únicos"
    for c in casos:
        assert fc.t_decisao(c["id"]) in titulos


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js ausente")
def test_script_roda_contra_uma_simulacao_do_apps_script(tmp_path):
    """Executa o .gs no Node com FormApp/SpreadsheetApp simulados e conta os itens criados."""
    simulacao = r"""
const fs = require('fs');
const criados = [];
function cadeia(registro) {
  return new Proxy({}, { get: (_, m) => (...a) => {
    registro.push([m, a]);
    return String(m).startsWith('get') ? 'https://exemplo/' + String(m) : cadeia(registro);
  } });
}
global.FormApp = {
  DestinationType: { SPREADSHEET: 'SPREADSHEET' },
  createTextValidation: () => cadeia([]),
  create: (titulo) => { const reg = []; criados.push({ titulo, reg }); return cadeia(reg); },
};
global.SpreadsheetApp = { create: () => cadeia([]) };
global.Logger = { log: () => {} };
eval(fs.readFileSync(process.argv[2], 'utf8') + '\ncriarFormularios();');
console.log(JSON.stringify(criados.map(f => ({ titulo: f.titulo,
  perguntas: f.reg.filter(([m]) => /^add(MultipleChoice|Checkbox|ParagraphText|Text|Date)Item$/.test(m)).length,
  secoes: f.reg.filter(([m]) => m === 'addPageBreakItem').length }))));
"""
    js = tmp_path / "sim.js"
    js.write_text(simulacao, encoding="utf-8")
    saida = subprocess.run(["node", str(js), str(gf.SAIDA)], capture_output=True, text=True, encoding="utf-8")
    assert saida.returncode == 0, saida.stderr
    pesquisa, diario = json.loads(saida.stdout)
    assert pesquisa["titulo"] == fc.TITULO_PESQUISA and diario["titulo"] == fc.TITULO_DIARIO
    n = len(ag.casos_rcpn())
    assert pesquisa["secoes"] == n + 2  # um por caso + perguntas rápidas + validação
    assert pesquisa["perguntas"] == 5 * n + len(fc.PERGUNTAS_B) + 6
    assert diario["perguntas"] == 10


def _csv(caminho: Path, linhas: list[dict]):
    campos = list(dict.fromkeys(k for r in linhas for k in r))
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)
    return caminho


def test_leitor_da_pesquisa_gera_gabarito_avaliavel(tmp_path):
    rotulo = dict(fc.DECISOES)
    resposta = {"Carimbo de data/hora": "20/10/2026 10:15:00",
                fc.t_decisao(105): rotulo["ENCAMINHAR_JUIZ"], fc.t_quem(105): "Oficial ou substituto",
                fc.t_fundamentos(105): "CNJ 149, art. 114, §1º",
                fc.t_decisao(101): rotulo["DEFERIR"], fc.t_fundamentos(101): "CNJ 149, art. 113",
                fc.t_decisao(102): rotulo["DEFERIR"],  # sem fundamentos: aviso
                fc.t_b(1): "cerca de 30", fc.VALIDACAO["nome"]: "Oficial Teste", fc.VALIDACAO["funcao"]: "Oficial",
                fc.VALIDACAO["cartorio"]: "Cartório do 1º Ofício de Russas", fc.VALIDACAO["municipio"]: "Russas",
                fc.VALIDACAO["autorizacao"]: dict(fc.AUTORIZACAO)["funcao_municipio"]}
    res = lf.pesquisa(lf._ler_csv(_csv(tmp_path / "p.csv", [resposta])), tmp_path)
    assert res["casos_respondidos"] == 3 and any("caso 102" in a for a in res["avisos"])
    linhas = list(csv.DictReader((tmp_path / "gabarito_rcpn.csv").open(encoding="utf-8")))
    assert {int(x["pergunta_id"]) for x in linhas if x["validado_por"]} == {101, 102, 105}
    sem_102 = tmp_path / "g.csv"
    with sem_102.open("w", encoding="utf-8", newline="") as f:  # o caso sem fundamentos é rejeitado pelo avaliador
        w = csv.DictWriter(f, fieldnames=ag.COLUNAS_GABARITO, lineterminator="\n")
        w.writeheader()
        w.writerows(x for x in linhas if x["pergunta_id"] != "102")
    gabarito = ag.ler_gabarito(sem_102)
    assert ag.concordancia_motor_rcpn(gabarito)["concordantes"] == 2
    b = json.loads((tmp_path / "respostas_parte_b_cartorio_do_1o_oficio_de_russas.json").read_text(encoding="utf-8"))
    assert b["autorizacao"] == "funcao_municipio" and b["parte_b"][fc.t_b(1)] == "cerca de 30"


def test_leitor_do_diario_gera_um_arquivo_por_cartorio(tmp_path):
    d = fc.DIARIO
    base = {d["data"]: "2026-10-20", d["atribuicao"]: "Registro Civil", d["canal"]: "Balcão",
            d["tipo"]: "inteiro teor de nascimento", d["perfil"]: "terceiro", d["duvida"]: "Sim",
            d["quem"]: "Oficial", d["tempo"]: "12", d["desfecho"]: "Encaminhado ao juiz"}
    linhas = [base | {d["cartorio"]: "russas_rcpn"}, base | {d["cartorio"]: "russas_rcpn", d["duvida"]: "Não"},
              base | {d["cartorio"]: "limoeiro_ri", d["atribuicao"]: "Registro de Imóveis"}]
    res = lf.diario(lf._ler_csv(_csv(tmp_path / "d.csv", linhas)), tmp_path)
    assert res["pedidos"] == 3 and len(res["arquivos"]) == 2
    resumo = rd.resumir(rd.ler_diario(tmp_path / "diario_balcao_russas_rcpn.csv"))
    assert resumo["cartorios"]["russas_rcpn"]["duvidas"] == 1


def test_opcao_desconhecida_e_rejeitada():
    with pytest.raises(lf.RespostaInvalida):
        lf._codigo(fc.DECISOES, "Talvez")
