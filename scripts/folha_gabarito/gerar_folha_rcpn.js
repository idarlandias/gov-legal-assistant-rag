// Uso: npm install docx@9.5.1 && node scripts/folha_gabarito/gerar_folha_rcpn.js data/validacao/casos_rcpn.json data/validacao/documento_cartorio_registro_civil.docx
// Documento único para o cartório: carta de apresentação, 13 casos de Registro Civil (gabarito, teste cego:
// nenhuma resposta do sistema), perguntas rápidas sobre o balcão, diário de balcão opcional e validação.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  HeadingLevel, BorderStyle, ShadingType, Footer, PageNumber, HeightRule,
} = require("docx");

const [, , casosPath, saida] = process.argv;
const casos = JSON.parse(fs.readFileSync(casosPath, "utf8")).casos;

const FONTE = "Arial";
const AZUL = "1F4E79";
const LARGURA = 9638; // A4 com margens de 2 cm (DXA)
const COL1 = 2600, COL2 = LARGURA - COL1;
const borda = { style: BorderStyle.SINGLE, size: 4, color: "8C8C8C" };
const bordas = { top: borda, bottom: borda, left: borda, right: borda };

const p = (texto, op = {}) => new Paragraph({
  spacing: { after: op.after ?? 120, before: op.before ?? 0 },
  alignment: op.align,
  pageBreakBefore: op.quebra,
  children: [new TextRun({ text: texto, bold: op.bold, italics: op.italics, size: op.size ?? 21, font: FONTE,
                           color: op.color })],
});

const titulo = (texto, quebra = true) => new Paragraph({
  heading: HeadingLevel.HEADING_1, pageBreakBefore: quebra, spacing: { after: 160 },
  children: [new TextRun({ text: texto, font: FONTE, bold: true, size: 30, color: AZUL })],
});

const subtitulo = (texto, quebra = false) => new Paragraph({
  heading: HeadingLevel.HEADING_2, pageBreakBefore: quebra, spacing: { before: quebra ? 0 : 200, after: 120 },
  children: [new TextRun({ text: texto, font: FONTE, bold: true, size: 26 })],
});

const celula = (filhos, largura, op = {}) => new TableCell({
  width: { size: largura, type: WidthType.DXA },
  borders: bordas,
  shading: op.fundo ? { fill: op.fundo, type: ShadingType.CLEAR, color: "auto" } : undefined,
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  children: filhos,
});

const vazio = () => [new Paragraph({ children: [new TextRun({ text: "", font: FONTE })] })];

const linha = (rotulo, conteudo, altura) => new TableRow({
  cantSplit: true,
  height: altura ? { value: altura, rule: HeightRule.ATLEAST } : undefined,
  children: [
    celula([p(rotulo, { bold: true, after: 0, size: 20 })], COL1, { fundo: "F2F2F2" }),
    celula(conteudo, COL2),
  ],
});

const tabela = (linhas) => new Table({ width: { size: LARGURA, type: WidthType.DXA }, columnWidths: [COL1, COL2],
                                        rows: linhas });

const opcoes = (itens) => itens.map((t) => p(`☐  ${t}`, { after: 40, size: 20 }));

// ---------------------------------------------------------------- carta de apresentação

const carta = [
  p("______________________ (CE), ____ de ______________ de 2026.", { align: AlignmentType.RIGHT, after: 360 }),
  p("Ao(À) Oficial do Registro Civil das Pessoas Naturais", { bold: true, after: 120 }),
  p("Serventia:  ____________________________________________________________", { after: 120 }),
  p("Município:  ____________________________________________________________", { after: 360 }),
  p("Assunto: pedido de colaboração em pesquisa sobre o atendimento de pedidos de certidão", { bold: true,
                                                                                              after: 240 }),
  p("Prezado(a) Oficial,", { after: 200 }),
  p("Meu nome é Idarlan Magalhães e participo da Residência em Inteligência Artificial da SiDi/Softex. Estudo " +
    "como funciona, na prática, o atendimento de pedidos de certidão no Registro Civil quando o pedido envolve " +
    "dados pessoais: quem pode pedir, o que exigir do requerente e quando a expedição depende de autorização " +
    "judicial."),
  p("Estou desenvolvendo uma ferramenta de apoio ao balcão que mostra ao atendente o que a norma exige para cada " +
    "tipo de pedido. Ela não decide nada: a decisão e a responsabilidade continuam sendo do Oficial. Antes de " +
    "qualquer uso, preciso saber se ela acerta, e para isso preciso da resposta de quem conhece a rotina e a norma."),
  p("Por isso, peço sua colaboração para responder este documento. Ele tem três partes:"),
  p("•  Parte A — 13 situações de balcão: como o(a) senhor(a) atenderia cada uma (cerca de 30 a 40 minutos);",
    { after: 60 }),
  p("•  Parte B — 7 perguntas rápidas sobre o atendimento no seu cartório (cerca de 5 minutos);", { after: 60 }),
  p("•  Parte C — opcional: anotar, durante uma semana, os pedidos de certidão do balcão, sem nenhum dado pessoal."),
  p("Garantias:", { bold: true, before: 120, after: 60 }),
  p("•  Todos os casos são fictícios. Nenhum dado pessoal de ninguém é pedido ou registrado.", { after: 60 }),
  p("•  As respostas serão usadas apenas nesta pesquisa. O(A) senhor(a) escolhe, na última página, se seu nome " +
    "pode ser citado.", { after: 60 }),
  p("•  Não se trata de venda nem de avaliação do cartório. Não existe resposta \"errada\": vale a sua prática e " +
    "a sua leitura da norma.", { after: 60 }),
  p("•  Pode responder em partes, deixar itens em branco ou desistir a qualquer momento."),
  p("Agradeço desde já a atenção e fico à disposição para buscar o documento ou para fazer as perguntas " +
    "pessoalmente, se for mais prático.", { before: 120, after: 480 }),
  p("Atenciosamente,", { after: 600 }),
  p("_______________________________________", { after: 40 }),
  p("Idarlan Magalhães", { bold: true, after: 40 }),
  p("Residência em Inteligência Artificial — SiDi/Softex", { after: 40 }),
  p("E-mail: idarlandias@gmail.com      Telefone/WhatsApp: ______________________", { after: 40 }),
];

// ---------------------------------------------------------------- instruções

const instrucoes = [
  titulo("Como preencher"),
  p("Parte A — Situações de balcão", { bold: true, size: 23, after: 80 }),
  p("Cada página traz uma situação fictícia. Para cada uma:"),
  p("1. Marque a decisão que o(a) senhor(a) tomaria (uma opção).", { after: 60 }),
  p("2. Marque quem decide esse caso no dia a dia: o escrevente ou o Oficial.", { after: 60 }),
  p("3. Escreva a norma e o artigo que fundamentam a resposta. Se não lembrar o número, descreva a regra.",
    { after: 60 }),
  p("4. Escreva como atenderia: o que diria ao requerente e o que exigiria.", { after: 60 }),
  p("5. Escreva o que seria um erro grave nesse caso."),
  p("Se a situação estiver incompleta ou depender de um fato que não foi informado, diga isso no item 4. Essa " +
    "informação também é valiosa.", { italics: true, color: "595959" }),
  p("Parte B — Perguntas rápidas", { bold: true, size: 23, before: 200, after: 80 }),
  p("Estimativas bastam. Não é preciso consultar registros."),
  p("Parte C — Diário de balcão (opcional)", { bold: true, size: 23, before: 200, after: 80 }),
  p("Uma linha por pedido de certidão, durante uma semana, sem nome, CPF, número de matrícula ou de protocolo. " +
    "Serve para saber quantos pedidos geram dúvida de verdade."),
  p("Ao final", { bold: true, size: 23, before: 200, after: 80 }),
  p("Preencha a página de validação e escolha se seu nome pode ser citado. Obrigado!"),
];

// ---------------------------------------------------------------- parte A

const DECISOES = [
  "Deferir (atender sem exigência adicional)",
  "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
  "Indeferir em nota fundamentada",
  "Encaminhar ao juízo competente (autorização judicial)",
  "Apenas informar / orientar",
  "Não se aplica ao Registro Civil",
];

function blocoCaso(c, i) {
  return [
    ...(i === 0 ? [titulo("Parte A — Situações de balcão do Registro Civil")] : []),
    subtitulo(`Caso ${c.id}`, i > 0),
    new Paragraph({ spacing: { after: 160 }, shading: { fill: "F7F9FC", type: ShadingType.CLEAR, color: "auto" },
                    border: { left: { style: BorderStyle.SINGLE, size: 18, color: AZUL, space: 6 } },
                    children: [new TextRun({ text: c.pergunta, font: FONTE, size: 22 })] }),
    tabela([
      linha("1. Decisão (marque uma)", opcoes(DECISOES)),
      linha("2. Quem decide no balcão", opcoes(["Escrevente", "Oficial ou substituto"])),
      linha("3. Fundamentos (norma e artigo)", vazio(), 1500),
      linha("4. Como atender (o que dizer e o que exigir)", vazio(), i === 0 ? 2300 : 2700),
      linha("5. O que seria um erro grave neste caso", vazio(), 1700),
    ]),
  ];
}

// ---------------------------------------------------------------- parte B

const PERGUNTAS_B = [
  ["Quantos pedidos de certidão o cartório atende por dia, em média?", 700],
  ["Desses, quantos fazem o atendente parar para consultar alguém ou a norma?", 700],
  ["Em que tipos de pedido a dúvida é mais comum?", 1100],
  ["Quando há dúvida, quem decide: o escrevente, o substituto ou o Oficial?", 800],
  ["O cartório registra quem pediu a certidão e para quê? Onde (livro, sistema, planilha)?", 900],
  ["Que sistema o cartório usa? Ele tem algum recurso de inteligência artificial?", 900],
  ["A última correição apontou algo sobre dados pessoais ou certidões?", 900],
];

const parteB = [
  titulo("Parte B — Perguntas rápidas sobre o atendimento"),
  tabela(PERGUNTAS_B.map(([q, h], i) => linha(`${i + 1}. ${q}`, vazio(), h))),
];

// ---------------------------------------------------------------- parte C

const COLS_C = [
  ["Data", 900], ["Atribuição (RC / RI)", 1000], ["Tipo de pedido", 2000], ["Quem pediu", 1500],
  ["Gerou dúvida? (S/N)", 900], ["Quem decidiu", 1300], ["Tempo (min)", 800], ["Resultado", 1238],
];
const cabC = new TableRow({ tableHeader: true, children: COLS_C.map(([t, w]) =>
  celula([p(t, { bold: true, size: 16, after: 0 })], w, { fundo: "F2F2F2" })) });
const linhasC = Array.from({ length: 20 }, () => new TableRow({
  height: { value: 420, rule: HeightRule.ATLEAST },
  children: COLS_C.map(([, w]) => celula(vazio(), w)) }));

const parteC = [
  titulo("Parte C — Diário de balcão (opcional, uma semana)"),
  p("Uma linha por pedido de certidão. Não anote nome, CPF, matrícula nem protocolo."),
  p("Atribuição: RC = Registro Civil, RI = Registro de Imóveis. Gerou dúvida: o atendente precisou parar para " +
    "consultar alguém ou a norma? Quem decidiu: escrevente, substituto ou Oficial. Resultado: emitida, emitida com " +
    "exigência, exigência pendente, recusada em nota, orientado, encaminhado ao juiz ou desistiu.",
    { size: 18, color: "404040" }),
  new Table({ width: { size: LARGURA, type: WidthType.DXA }, columnWidths: COLS_C.map(([, w]) => w),
              rows: [cabC, ...linhasC] }),
  p("Se precisar de mais linhas, continue no verso ou em outra folha.", { italics: true, size: 18, before: 120,
                                                                          color: "595959" }),
];

// ---------------------------------------------------------------- validação

const validacao = [
  titulo("Validação e autorização"),
  p("Declaro que as respostas deste documento refletem meu entendimento das normas aplicáveis e da rotina do " +
    "atendimento na data abaixo."),
  tabela(["Nome", "Função (Oficial, substituto, escrevente)", "Serventia e município", "Data", "Assinatura"]
    .map((r) => linha(r, vazio(), 650))),
  p("Uso do meu nome na pesquisa (marque uma):", { bold: true, before: 240, after: 80 }),
  ...opcoes(["Podem citar meu nome, função e serventia.",
             "Prefiro não ser identificado(a): citar apenas a função e o município.",
             "Não autorizo citar nenhuma informação; as respostas podem ser usadas apenas de forma agregada."]),
  p("Muito obrigado pela colaboração.", { before: 240, italics: true, color: AZUL }),
];

const doc = new Document({
  creator: "Idarlan Magalhães",
  title: "Pesquisa sobre atendimento de pedidos de certidão — Registro Civil",
  styles: { default: { document: { run: { font: FONTE, size: 21 } } } },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 },
                          margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ text: "Pesquisa — atendimento de pedidos de certidão do Registro Civil · página ", font: FONTE,
                    size: 16, color: "808080" }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONTE, size: 16, color: "808080" }),
    ] })] }) },
    children: [...carta, ...instrucoes, ...casos.flatMap((c, i) => blocoCaso(c, i)), ...parteB, ...parteC,
               ...validacao],
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(saida, buf); console.log("gerado:", saida); });
