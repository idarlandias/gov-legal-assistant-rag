"""Gera o PDF PREENCHÍVEL do documento para o cartório (Registro Civil).

O Oficial abre no Adobe Reader, Chrome ou Edge, marca as opções, digita as respostas e salva.
Os valores dos campos já usam o vocabulário do gabarito e do diário de balcão, para que
scripts/folha_gabarito/ler_pdf_preenchido.py extraia tudo sem transcrição manual.

Uso:
    python scripts/folha_gabarito/gerar_pdf_preenchivel.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

RAIZ = Path(__file__).resolve().parents[2]
CASOS = RAIZ / "data" / "validacao" / "casos_rcpn.json"
SAIDA = RAIZ / "data" / "validacao" / "documento_cartorio_registro_civil_preenchivel.pdf"

AUTOR = "Idarlan Magalhães"
QUALIFICACOES = ("Residente em Inteligência Artificial Aplicada a Ambientes Corporativos · SiDi/Softex",
                 "Desenvolvedor de sistemas e aplicações web")
CONTATOS = ("idarlandias@gmail.com", "github.com/idarlandias", "linkedin.com/in/idarlandias")

AZUL = HexColor("#1F4E79")
CINZA = HexColor("#595959")
CAMPO = HexColor("#F3F6FA")
BORDA = HexColor("#8C8C8C")
MARGEM = 56

# Valores = vocabulário de scripts/avaliar_gabarito.py (DECISOES) e de scripts/resumir_diario.py (VALORES)
DECISOES = [
    ("DEFERIR", "Deferir (atender sem exigência adicional)"),
    ("DEFERIR_COM_EXIGENCIA", "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)"),
    ("INDEFERIR_NOTA", "Indeferir em nota fundamentada"),
    ("ENCAMINHAR_JUIZ", "Encaminhar ao juízo competente (autorização judicial)"),
    ("INFORMAR", "Apenas informar / orientar"),
    ("NAO_SE_APLICA", "Não se aplica ao Registro Civil"),
]
QUEM_DECIDE = [("escrevente", "Escrevente"), ("oficial", "Oficial ou substituto")]
PERGUNTAS_B = [
    "Quantos pedidos de certidão o cartório atende por dia, em média?",
    "Desses, quantos fazem o atendente parar para consultar alguém ou a norma?",
    "Em que tipos de pedido a dúvida é mais comum?",
    "Quando há dúvida, quem decide: o escrevente, o substituto ou o Oficial?",
    "O cartório registra quem pediu a certidão e para quê? Onde (livro, sistema, planilha)?",
    "Que sistema o cartório usa? Ele tem algum recurso de inteligência artificial?",
    "A última correição apontou algo sobre dados pessoais ou certidões?",
]
# Diário: (campo, título, largura, opções da lista ou None para texto livre)
COLS_DIARIO = [
    ("data", "Data (dd/mm)", 52, None),
    ("atribuicao", "Atribuição", 62, ["", "RCPN", "RI", "OUTRA"]),
    ("tipo_pedido", "Tipo de pedido", 150, None),
    ("perfil_requerente", "Quem pediu", 108, None),
    ("gerou_duvida", "Gerou dúvida?", 56, ["", "sim", "nao"]),
    ("quem_decidiu", "Quem decidiu", 94, ["", "escrevente", "substituto", "oficial", "consulta_externa",
                                           "nao_se_aplica"]),
    ("tempo_min", "Tempo (min)", 46, None),
    ("desfecho", "Resultado", 122, ["", "emitida", "emitida_com_exigencia", "exigencia_pendente", "recusada_nota",
                                    "orientado", "encaminhado_juiz", "desistiu"]),
]  # soma das larguras + espaçamento (7 × 4) = 718 pt, dentro dos 730 úteis do A4 em paisagem
LINHAS_DIARIO = 18
VAZIO = "-"
AUTORIZACAO = [
    ("nome", "Podem citar meu nome, função e serventia."),
    ("funcao_municipio", "Prefiro não ser identificado(a): citar apenas a função e o município."),
    ("agregado", "Não autorizo citar nenhuma informação; as respostas podem ser usadas apenas de forma agregada."),
]

S_TEXTO = ParagraphStyle("t", fontName="Helvetica", fontSize=10.5, leading=14.5, spaceAfter=6)
S_PEQ = ParagraphStyle("p", parent=S_TEXTO, fontSize=9, leading=12, textColor=CINZA)
S_TIT = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=AZUL, spaceAfter=10)
S_SUB = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, leading=17, spaceAfter=6)
S_ROT = ParagraphStyle("r", fontName="Helvetica-Bold", fontSize=10, leading=13)
S_DIR = ParagraphStyle("d", parent=S_TEXTO, alignment=TA_RIGHT)


class Doc:
    def __init__(self, caminho: Path):
        self.c = Canvas(str(caminho), pagesize=A4)
        self.c.setTitle("Pesquisa sobre atendimento de pedidos de certidão — Registro Civil")
        self.c.setAuthor("Idarlan Magalhães")
        self.pagina = 1
        self.largura, self.altura = A4
        self.y = self.altura - MARGEM

    @property
    def util(self) -> float:
        return self.largura - 2 * MARGEM

    def nova_pagina(self, paisagem: bool = False):
        self._rodape()
        self.c.showPage()
        self.pagina += 1
        tamanho = landscape(A4) if paisagem else A4
        self.c.setPageSize(tamanho)
        self.largura, self.altura = tamanho
        self.y = self.altura - MARGEM

    def _rodape(self):
        self.c.setFont("Helvetica", 7.5)
        self.c.setFillColor(HexColor("#808080"))
        self.c.drawString(MARGEM, 30, f"{AUTOR} · {CONTATOS[0]}")
        self.c.drawRightString(self.largura - MARGEM, 30, "Pesquisa — atendimento de pedidos de certidão do "
                                                           f"Registro Civil · página {self.pagina}")
        self.c.setFillColor(HexColor("#000000"))

    def par(self, texto: str, estilo=S_TEXTO, recuo: float = 0, depois: float | None = None):
        p = Paragraph(texto, estilo)
        _, h = p.wrap(self.util - recuo, self.altura)
        p.drawOn(self.c, MARGEM + recuo, self.y - h)
        self.y -= h + (estilo.spaceAfter if depois is None else depois)

    def caixa_caso(self, texto: str):
        p = Paragraph(texto, ParagraphStyle("c", parent=S_TEXTO, fontSize=11, leading=15))
        _, h = p.wrap(self.util - 20, self.altura)
        self.c.setFillColor(HexColor("#F7F9FC"))
        self.c.rect(MARGEM, self.y - h - 12, self.util, h + 12, stroke=0, fill=1)
        self.c.setFillColor(AZUL)
        self.c.rect(MARGEM, self.y - h - 12, 3, h + 12, stroke=0, fill=1)
        self.c.setFillColor(HexColor("#000000"))
        p.drawOn(self.c, MARGEM + 12, self.y - h - 6)
        self.y -= h + 24

    def texto_campo(self, nome: str, altura: float, largura: float | None = None, x: float | None = None,
                    multilinha: bool = True, tooltip: str = "", tamanho: float = 10):
        largura = largura or self.util
        x = MARGEM if x is None else x
        self.c.acroForm.textfield(
            name=nome, tooltip=tooltip or nome, x=x, y=self.y - altura, width=largura, height=altura,
            fontName="Helvetica", fontSize=tamanho, borderColor=BORDA, fillColor=CAMPO, textColor=HexColor("#000000"),
            borderWidth=0.6, fieldFlags="multiline" if multilinha else "", forceBorder=True)

    def radios(self, nome: str, opcoes: list[tuple[str, str]], em_linha: bool = False):
        x = MARGEM + 6
        for valor, rotulo in opcoes:
            self.c.acroForm.radio(name=nome, value=valor, selected=False, x=x, y=self.y - 11, size=11,
                                  buttonStyle="circle", borderColor=BORDA, fillColor=white, forceBorder=True,
                                  tooltip=rotulo)
            self.c.setFont("Helvetica", 10)
            self.c.drawString(x + 17, self.y - 9, rotulo)
            if em_linha:
                x += 200
            else:
                self.y -= 17
        if em_linha:
            self.y -= 17
        self.y -= 4

    def salvar(self):
        self._rodape()
        self.c.save()


def cabecalho(d: Doc):
    """Papel timbrado: faixa azul, monograma, nome, qualificações e contatos."""
    c = d.c
    c.setFillColor(AZUL)
    c.rect(0, d.altura - 10, d.largura, 10, stroke=0, fill=1)
    topo = d.altura - 46
    cx, cy, r = MARGEM + 23, topo - 20, 23
    c.circle(cx, cy, r, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(cx, cy - 6, "IM")
    x = MARGEM + 58
    c.setFillColor(HexColor("#1F2328"))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, topo - 10, AUTOR)
    c.setFillColor(AZUL)
    c.setFont("Helvetica", 9.5)
    for i, q in enumerate(QUALIFICACOES):
        c.drawString(x, topo - 25 - 12 * i, q)
    c.setStrokeColor(AZUL)
    c.setLineWidth(1.2)
    c.line(MARGEM, topo - 52, d.largura - MARGEM, topo - 52)
    c.setFillColor(CINZA)
    c.setFont("Helvetica", 8.5)
    c.drawString(MARGEM, topo - 64, "   ·   ".join(CONTATOS))
    c.setFillColor(HexColor("#000000"))
    d.y = topo - 80


def carta(d: Doc):
    cabecalho(d)
    d.c.setFont("Helvetica", 10.5)
    d.c.drawRightString(d.largura - MARGEM - 255, d.y - 13, "Local e data:")
    d.texto_campo("carta_local_data", 18, largura=250, x=d.largura - MARGEM - 250, multilinha=False,
                  tooltip="Município e data, ex.: Russas, 20 de outubro de 2026")
    d.y -= 32
    d.par("<b>Ao(À) Oficial do Registro Civil das Pessoas Naturais</b>", depois=8)
    rotulo_x = 158
    for rotulo, nome, dica in (
            ("Cartório (nome da serventia):", "carta_serventia",
             "Nome oficial do cartório, como na placa ou no carimbo. Ex.: Cartório do 1º Ofício de Registro Civil"),
            ("Município:", "carta_municipio", "Cidade do cartório. Ex.: Russas")):
        d.c.setFont("Helvetica", 10.5)
        d.c.drawString(MARGEM, d.y - 13, rotulo)
        d.texto_campo(nome, 18, largura=d.util - rotulo_x, x=MARGEM + rotulo_x, multilinha=False, tooltip=dica)
        d.y -= 24
    d.y -= 4
    d.par("<b>Assunto: pedido de colaboração em pesquisa sobre o atendimento de pedidos de certidão</b>", depois=10)
    for t in [
        "Prezado(a) Oficial,",
        "Meu nome é Idarlan Magalhães. Sou residente em Inteligência Artificial Aplicada a Ambientes Corporativos pela "
        "SiDi/Softex e desenvolvedor de sistemas e aplicações web. Estudo como funciona, na prática, o atendimento de pedidos de certidão no Registro Civil quando o pedido envolve dados "
        "pessoais: quem pode pedir, o que exigir do requerente e quando a expedição depende de autorização judicial.",
        "Estou desenvolvendo uma ferramenta de apoio ao balcão que mostra ao atendente o que a norma exige para cada "
        "tipo de pedido. Ela não decide nada: a decisão e a responsabilidade continuam sendo do Oficial. Antes de "
        "qualquer uso, preciso saber se ela acerta, e para isso preciso da resposta de quem conhece a rotina e a norma.",
        "Por isso, peço sua colaboração para responder este documento, que pode ser preenchido no próprio computador. "
        "Ele tem três partes:",
    ]:
        d.par(t)
    for t in ["<b>Parte A</b> — 13 situações de balcão: como o(a) senhor(a) atenderia cada uma (cerca de 30 a 40 min);",
              "<b>Parte B</b> — 7 perguntas rápidas sobre o atendimento no seu cartório (cerca de 5 minutos);",
              "<b>Parte C</b> — opcional: anotar, durante uma semana, os pedidos de certidão do balcão, sem dado pessoal."]:
        d.par(f"• {t}", recuo=10, depois=3)
    d.y -= 6
    d.par("<b>Garantias</b>", depois=3)
    for t in ["Todos os casos são fictícios. Nenhum dado pessoal de ninguém é pedido ou registrado.",
              "As respostas serão usadas apenas nesta pesquisa. O(A) senhor(a) escolhe, na última página, se seu nome "
              "pode ser citado.",
              "Não se trata de venda nem de avaliação do cartório. Não existe resposta \"errada\": vale a sua prática "
              "e a sua leitura da norma.",
              "Pode responder em partes, deixar itens em branco ou desistir a qualquer momento."]:
        d.par(f"• {t}", recuo=10, depois=3)
    d.y -= 6
    d.par("Agradeço desde já a atenção. Depois de preencher, basta <b>salvar o arquivo</b> e me devolver por e-mail ou "
          "WhatsApp. Se preferir, posso buscar uma via impressa ou fazer as perguntas pessoalmente.", depois=18)
    d.par("Atenciosamente,", depois=12)
    # assinatura no mesmo padrão do cabeçalho
    d.c.setStrokeColor(AZUL)
    d.c.setLineWidth(2)
    d.c.line(MARGEM, d.y, MARGEM, d.y - 58)
    d.c.setFillColor(HexColor("#1F2328"))
    d.c.setFont("Helvetica-Bold", 11.5)
    d.c.drawString(MARGEM + 10, d.y - 11, AUTOR)
    d.c.setFillColor(AZUL)
    d.c.setFont("Helvetica", 9)
    for i, q in enumerate(QUALIFICACOES):
        d.c.drawString(MARGEM + 10, d.y - 24 - 11 * i, q)
    d.c.setFillColor(CINZA)
    d.c.setFont("Helvetica", 8.5)
    d.c.drawString(MARGEM + 10, d.y - 49, "   ·   ".join(CONTATOS))
    # WhatsApp na mesma linha dos contatos, à direita
    d.c.drawRightString(d.largura - MARGEM - 112, d.y - 49, "WhatsApp:")
    topo_assinatura = d.y
    d.y = topo_assinatura - 38
    d.texto_campo("carta_telefone", 16, largura=108, x=d.largura - MARGEM - 108, multilinha=False,
                  tooltip="Seu telefone/WhatsApp com DDD", tamanho=9)
    d.c.setFillColor(HexColor("#000000"))
    d.y = topo_assinatura - 64


def instrucoes(d: Doc):
    d.nova_pagina()
    d.par("Como preencher", S_TIT)
    d.par("<b>No computador:</b> abra este arquivo no Adobe Reader (gratuito), no Chrome ou no Edge. Clique nas "
          "bolinhas para marcar e nas caixas cinza para digitar. Ao terminar, <b>salve o arquivo</b> (Ctrl+S) e "
          "devolva por e-mail ou WhatsApp.")
    d.par("<b>Parte A — Situações de balcão.</b> Para cada caso: (1) marque a decisão que o(a) senhor(a) tomaria; "
          "(2) marque quem decide esse caso no dia a dia; (3) escreva a norma e o artigo que fundamentam a resposta "
          "(se não lembrar o número, descreva a regra); (4) escreva como atenderia: o que diria ao requerente e o que "
          "exigiria; (5) escreva o que seria um erro grave nesse caso.")
    d.par("Se a situação estiver incompleta ou depender de um fato não informado, diga isso no item 4. Essa "
          "informação também é valiosa.", S_PEQ)
    d.par("<b>Parte B — Perguntas rápidas.</b> Estimativas bastam; não é preciso consultar registros.")
    d.par("<b>Parte C — Diário de balcão (opcional).</b> Uma linha por pedido de certidão, durante uma semana, sem "
          "nome, CPF, número de matrícula ou de protocolo. Serve para saber quantos pedidos geram dúvida de verdade.")
    d.par("<b>Ao final</b>, preencha a página de validação e escolha se seu nome pode ser citado. A assinatura pode "
          "ser digitada ou feita pelo assinador gratuito do gov.br. Obrigado!")


def parte_a(d: Doc, casos: list[dict]):
    for i, caso in enumerate(casos):
        d.nova_pagina()
        if i == 0:
            d.par("Parte A — Situações de balcão do Registro Civil", S_TIT)
        n = caso["id"]
        d.par(f"Caso {n}", S_SUB)
        d.caixa_caso(caso["pergunta"])
        d.par("1. Decisão (marque uma)", S_ROT, depois=4)
        d.radios(f"caso_{n}_decisao", DECISOES)
        d.par("2. Quem decide no balcão", S_ROT, depois=4)
        d.radios(f"caso_{n}_quem_decide", QUEM_DECIDE, em_linha=True)
        for rotulo, campo, altura in (("3. Fundamentos (norma e artigo)", "fundamentos", 76),
                                      ("4. Como atender (o que dizer e o que exigir)", "como_atender",
                                       130 if i == 0 else 160),
                                      ("5. O que seria um erro grave neste caso", "erro_grave", 92)):
            d.par(rotulo, S_ROT, depois=4)
            d.texto_campo(f"caso_{n}_{campo}", altura, tooltip=rotulo)
            d.y -= altura + 10


def parte_b(d: Doc):
    d.nova_pagina()
    d.par("Parte B — Perguntas rápidas sobre o atendimento", S_TIT)
    for i, pergunta in enumerate(PERGUNTAS_B, start=1):
        d.par(f"{i}. {pergunta}", S_ROT, depois=4)
        altura = 54 if i in (3, 5, 6, 7) else 30
        d.texto_campo(f"b_{i}", altura, tooltip=pergunta)
        d.y -= altura + 10


def parte_c(d: Doc):
    d.nova_pagina(paisagem=True)
    d.par("Parte C — Diário de balcão (opcional, uma semana)", S_TIT, depois=4)
    d.par("Uma linha por pedido de certidão. <b>Não anote nome, CPF, matrícula nem protocolo.</b> Atribuição: RCPN = "
          "Registro Civil, RI = Registro de Imóveis. Gerou dúvida: o atendente precisou parar para consultar alguém "
          "ou a norma? Escolha as opções nas listas.", S_PEQ, depois=8)
    x0 = MARGEM
    d.c.setFont("Helvetica-Bold", 8.5)
    x = x0
    for _, titulo, largura, _ in COLS_DIARIO:
        d.c.drawString(x + 2, d.y - 10, titulo)
        x += largura + 4
    d.y -= 16
    for linha in range(1, LINHAS_DIARIO + 1):
        x = x0
        for campo, titulo, largura, opcoes in COLS_DIARIO:
            nome = f"diario_{linha:02d}_{campo}"
            if opcoes:
                # "-" = não preenchido (o reportlab não aceita valor inicial vazio numa lista)
                d.c.acroForm.choice(name=nome, tooltip=f"{titulo} (linha {linha})", value=VAZIO,
                                    options=[VAZIO] + [o for o in opcoes if o],
                                    x=x, y=d.y - 17, width=largura, height=17, fontName="Helvetica", fontSize=8,
                                    borderColor=BORDA, fillColor=CAMPO, borderWidth=0.5, forceBorder=True,
                                    fieldFlags="combo")
            else:
                d.c.acroForm.textfield(name=nome, tooltip=f"{titulo} (linha {linha})", x=x, y=d.y - 17,
                                       width=largura, height=17, fontName="Helvetica", fontSize=8, borderColor=BORDA,
                                       fillColor=CAMPO, borderWidth=0.5, forceBorder=True)
            x += largura + 4
        d.y -= 21


def validacao(d: Doc):
    d.nova_pagina()
    d.par("Validação e autorização", S_TIT)
    d.par("Declaro que as respostas deste documento refletem meu entendimento das normas aplicáveis e da rotina do "
          "atendimento na data abaixo.", depois=12)
    for rotulo, nome in (("Nome", "val_nome"), ("Função (Oficial, substituto, escrevente)", "val_funcao"),
                         ("Serventia e município", "val_serventia"), ("Data", "val_data"),
                         ("Assinatura (digitada ou gov.br)", "val_assinatura")):
        d.par(rotulo, S_ROT, depois=4)
        d.texto_campo(nome, 20, multilinha=False, tooltip=rotulo)
        d.y -= 30
    d.y -= 6
    d.par("Uso do meu nome na pesquisa (marque uma):", S_ROT, depois=6)
    d.radios("val_autorizacao", AUTORIZACAO)
    d.y -= 10
    d.par("<font color='#1F4E79'><i>Muito obrigado pela colaboração.</i></font>")


def gerar(saida: Path = SAIDA, casos_path: Path = CASOS) -> Path:
    casos = json.loads(casos_path.read_text(encoding="utf-8"))["casos"]
    d = Doc(saida)
    carta(d)
    instrucoes(d)
    parte_a(d, casos)
    parte_b(d)
    parte_c(d)
    validacao(d)
    d.salvar()
    return saida


if __name__ == "__main__":
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else SAIDA
    print("gerado:", gerar(destino))
