"""Instrumentos de validação de campo: diário de balcão e gabarito do registrador."""

import csv
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import avaliar_gabarito as ag  # noqa: E402
import resumir_diario as rd  # noqa: E402


def _diario(tmp_path, nome, linhas):
    p = tmp_path / f"diario_balcao_{nome}.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rd.COLUNAS)
        w.writeheader()
        for linha in linhas:
            w.writerow({c: "" for c in rd.COLUNAS} | linha)
    return p


def _pedido(data, cartorio="limoeiro_ri", atrib="RI", duvida="nao", decisor="escrevente", tempo="3"):
    return {"data": data, "cartorio": cartorio, "atribuicao": atrib, "tipo_pedido": "certidão de matrícula",
            "perfil_requerente": "terceiro", "canal_entrada": "balcao", "gerou_duvida": duvida,
            "quem_decidiu": decisor, "tempo_min": tempo, "consultou": "nada", "desfecho": "emitida"}


# ---------------------------------------------------------------- diário

def test_modelo_do_diario_tem_so_o_cabecalho():
    linhas = rd.MODELO.read_text(encoding="utf-8").splitlines()
    assert linhas == [",".join(rd.COLUNAS)]


def test_resumo_aplica_o_criterio_e_separa_atribuicoes(tmp_path):
    a = _diario(tmp_path, "a", [
        _pedido("2026-10-20", duvida="sim", decisor="oficial", tempo="12"),
        _pedido("2026-10-20", atrib="RCPN", duvida="sim", decisor="oficial", tempo="20"),
        _pedido("2026-10-21", duvida="nao"),
        _pedido("2026-10-21", atrib="RCPN", duvida="sim", decisor="escrevente", tempo="8"),
    ])
    b = _diario(tmp_path, "b", [_pedido("2026-10-20", cartorio="russas_ri"),
                                _pedido("2026-10-21", cartorio="russas_ri")])
    res = rd.resumir(rd.ler_diario(a) + rd.ler_diario(b))
    lim = res["cartorios"]["limoeiro_ri"]
    assert (lim["dias"], lim["duvidas"], lim["duvidas_por_dia"]) == (2, 3, 1.5)
    assert lim["por_atribuicao"]["RCPN"]["duvidas_por_dia"] == 1.0
    assert lim["por_atribuicao"]["RI"]["duvidas_por_dia"] == 0.5
    assert lim["quem_decidiu_nas_duvidas"] == {"oficial": 2, "escrevente": 1}
    assert lim["tempo_mediano_duvida_min"] == 12
    assert lim["atinge_criterio"] and not res["cartorios"]["russas_ri"]["atinge_criterio"]
    assert res["cartorios_que_atingem"] == 1
    assert "1 de 2" in rd.markdown(res)


@pytest.mark.parametrize("campo,valor", [("gerou_duvida", "talvez"), ("atribuicao", "imoveis"),
                                         ("tempo_min", "dez")])
def test_diario_rejeita_valor_fora_do_dominio(tmp_path, campo, valor):
    p = _diario(tmp_path, "x", [_pedido("2026-10-20") | {campo: valor}])
    with pytest.raises(rd.LinhaInvalida):
        rd.ler_diario(p)


def test_diario_preenchido_fica_fora_do_git():
    import subprocess
    r = subprocess.run(["git", "check-ignore", "data/validacao/diario_balcao_limoeiro.csv"], cwd=RAIZ,
                       capture_output=True, text=True)
    assert r.returncode == 0, "diário preenchido precisa estar no .gitignore"
    r = subprocess.run(["git", "check-ignore", "data/validacao/diario_balcao_modelo.csv"], cwd=RAIZ,
                       capture_output=True, text=True)
    assert r.returncode == 1, "o modelo do diário precisa ser versionado"


# ---------------------------------------------------------------- gabarito

def test_modelo_do_gabarito_tem_26_perguntas_e_campos_juridicos_vazios(tmp_path):
    destino = tmp_path / "m.csv"
    ag.gerar_modelo(destino)
    assert destino.read_text(encoding="utf-8") == ag.GABARITO_MODELO.read_text(encoding="utf-8")
    linhas = list(csv.DictReader(destino.open(encoding="utf-8")))
    assert [int(x["pergunta_id"]) for x in linhas] == list(range(1, 27))
    for x in linhas:
        assert all(x[c] == "" for c in ag.COLUNAS_GABARITO[2:]), "o sistema não pode sugerir resposta esperada"


def _gabarito(tmp_path, linhas):
    p = tmp_path / "gabarito.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ag.COLUNAS_GABARITO)
        w.writeheader()
        for linha in linhas:
            w.writerow({c: "" for c in ag.COLUNAS_GABARITO} | linha)
    return p


def _avaliacao(tmp_path, sistema, linhas):
    p = tmp_path / f"avaliacao_{sistema}.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ag.COLUNAS_AVALIACAO)
        w.writeheader()
        for pid, acerto, contraria in linhas:
            w.writerow({"sistema": sistema, "pergunta_id": pid, "acerto": acerto, "contraria_norma": contraria,
                        "observacao": "", "avaliado_por": "x"})
    return p


def test_avaliacao_so_conta_perguntas_validadas(tmp_path):
    gab = _gabarito(tmp_path, [
        {"pergunta_id": "1", "pergunta": "p1", "decisao_esperada": "DEFERIR", "fundamentos": "norma X",
         "validado_por": "Oficial A"},
        {"pergunta_id": "2", "pergunta": "p2", "decisao_esperada": "DEFERIR", "fundamentos": "norma Y"},  # sem validação
    ])
    aval = [_avaliacao(tmp_path, "aryabolt", [(1, "errado", "sim"), (2, "certo", "nao")]),
            _avaliacao(tmp_path, "cartorioseguro", [(1, "certo", "nao")])]
    res = ag.avaliar(ag.ler_gabarito(gab), ag.ler_avaliacoes(aval))
    assert res["aryabolt"] == {"avaliadas": 1, "ignoradas_sem_gabarito": 1, "certo": 0, "errado": 1, "parcial": 0,
                               "sem_resposta": 0, "pct_certo": 0.0, "contrarias_a_norma": 1}
    assert res["assistente_registral_ce"]["pct_certo"] == 100.0


def test_gabarito_validado_sem_fundamento_e_rejeitado(tmp_path):
    gab = _gabarito(tmp_path, [{"pergunta_id": "1", "pergunta": "p1", "decisao_esperada": "DEFERIR",
                                "validado_por": "Oficial A"}])
    with pytest.raises(ag.ArquivoInvalido, match="fundamentos"):
        ag.ler_gabarito(gab)
