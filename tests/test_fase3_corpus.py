"""Testes do corpus da Fase 3: extração, segmentação por artigo e chunks (sem rede)."""

from src.fase3 import corpus
from src.fase3.corpus import ATO_APROVACAO, _SUMARIO, html_to_text, segment_articles
from src.fase3.index import build_chunks
from src.fase3.sources import FONTES, FONTES_POR_ID


def _rotulos(texto: str, paginas: list[str] | None = None) -> list[str]:
    pages = [(i + 1, t) for i, t in enumerate(paginas or [texto])]
    return [d.dispositivo for d in segment_articles("x", pages)]


def test_fontes_ids_unicos_e_urls_https():
    assert len(FONTES_POR_ID) == len(FONTES)
    assert all(f.url.startswith("https://") for f in FONTES)
    assert {f.formato for f in FONTES} <= {"html", "pdf", "dou"}


def test_html_descarta_redacao_revogada_e_scripts():
    html = (b"<html><head><style>x{}</style></head><body>"
            b"<p>Art. 1\xba Texto vigente.</p><p><strike>Art. 2\xba Texto revogado.</strike></p>"
            b"<script>alert(1)</script><p>Art. 3\xba Outro.</p></body></html>")
    txt = html_to_text(html)  # latin-1, como o Planalto
    assert "Texto vigente" in txt and "Outro" in txt
    assert "revogado" not in txt and "alert" not in txt


def test_html_dou_captura_so_o_bloco_do_ato():
    html = (b'<html><body><nav>Menu do portal</nav><div class="texto-dou">'
            b"<p>Art. 1 Aprova o regulamento.</p></div><footer>Rodape</footer></body></html>")
    txt = html_to_text(html, only_class="texto-dou")
    assert txt == "Art. 1 Aprova o regulamento."


def test_segmenta_artigos_e_ignora_citacao_no_inicio_de_linha():
    texto = ("Art. 1º Primeiro.\nArt. 2º Segundo, conforme o\n"
             "Art. 150 da Lei tal.\nArt. 3º Terceiro.")
    assert _rotulos(texto) == ["Art. 1", "Art. 2", "Art. 3"]


def test_sufixo_letra_e_ordem_z_antes_de_aa(monkeypatch):
    monkeypatch.setattr(corpus, "MAX_SALTO", 10_000)  # trecho que não começa no Art. 1
    texto = "Art. 440-Y. a\nArt. 440 -Z. b\nArt. 440-AA. c\nArt. 441. d"
    assert _rotulos("Art. 439. x\n" + texto) == [
        "Art. 439", "Art. 440-Y", "Art. 440-Z", "Art. 440-AA", "Art. 441"]


def test_numero_com_ponto_de_milhar(monkeypatch):
    monkeypatch.setattr(corpus, "MAX_SALTO", 10_000)
    texto = "Art. 999. a\nArt. 1.000. b\nArt. 1.001. c"
    assert _rotulos("Art. 998. z\n" + texto)[-2:] == ["Art. 1000", "Art. 1001"]


def test_primeiro_artigo_longe_de_1_e_tratado_como_citacao():
    assert _rotulos("Nos termos do\nArt. 150 da Lei X, aprova-se:\nArt. 1º Primeiro.") == [
        "Preâmbulo", "Art. 1"]


def test_reinicio_no_codigo_anexo_marca_ato_de_aprovacao():
    paginas = [
        "Art. 1º Aprova o Código.\nArt. 2º Entra em vigor.",
        "CÓDIGO NACIONAL DE NORMAS\nArt. 1º Primeiro do código.\nArt. 2º Segundo do código.",
    ]
    assert _rotulos("", paginas) == [
        "Art. 1" + ATO_APROVACAO, "Art. 2" + ATO_APROVACAO, "Art. 1", "Art. 2"]


def test_titulo_entre_artigos_vai_para_o_artigo_seguinte():
    ds = segment_articles("x", [(1, "Art. 1º Um.\nCAPÍTULO II\nDOS REGISTROS\nArt. 2º Dois.")])
    assert "CAPÍTULO II" not in ds[0].texto
    assert ds[1].texto.startswith("CAPÍTULO II") and ds[1].secao == "CAPÍTULO II"


def test_remove_linhas_de_sumario():
    txt = "CAPÍTULO II.............................. 23\nDAS DISPOSIÇÕES........23\nArt. 1º Texto."
    assert _SUMARIO.sub("", txt) == "Art. 1º Texto."


def test_chunks_tem_cabecalho_de_citacao_e_metadados():
    fonte = FONTES_POR_ID["lei_6015_1973"]
    ds = segment_articles(fonte.id, [(0, "Art. 17. Qualquer pessoa pode requerer certidão. " * 60)])
    chunks = build_chunks(fonte, ds)
    assert len(chunks) > 1
    assert len({c.id for c in chunks}) == len(chunks)
    assert chunks[0].text.startswith("Lei 6.015/1973, Art. 17 [parte 1/")
    md = chunks[0].metadata
    assert md["source"] == "Lei 6.015/1973, Art. 17"
    assert md["dominio"] == "fase3" and md["esfera"] == "federal" and md["dispositivo"] == "Art. 17"
    assert all(isinstance(v, (str, int)) for v in md.values())  # tipos aceitos pelo Chroma
