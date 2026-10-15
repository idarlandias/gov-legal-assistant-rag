// Uso: npm install docx@9.5.1 && node scripts/folha_gabarito/gerar_folha_rcpn.js data/validacao/casos_rcpn.json data/validacao/folha_gabarito_registro_civil.docx
// Folha de gabarito do Registro Civil para o registrador (teste cego: nenhuma resposta do sistema).
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  HeadingLevel, BorderStyle, ShadingType, Footer, PageNumber, PageBreak, HeightRule,
} = require("docx");

const [, , casosPath, saida] = process.argv;
const casos = JSON.parse(fs.readFileSync(casosPath, "utf8")).casos;

const FONTE = "Arial";
const LARGURA = 9638; // A4 com margens de 2 cm (DXA)
const COL1 = 2600, COL2 = LARGURA - COL1;
const borda = { style: BorderStyle.SINGLE, size: 4, color: "8C8C8C" };
const bordas = { top: borda, bottom: borda, left: borda, right: borda };

const p = (texto, op = {}) => new Paragraph({
  spacing: { after: op.after ?? 120, before: op.before ?? 0 },
  alignment: op.align,
  children: [new TextRun({ text: texto, bold: op.bold, italics: op.italics, size: op.size ?? 21, font: FONTE,
                           color: op.color })],
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

const opcoes = (itens) => itens.map((t) => p(`☐  ${t}`, { after: 40, size: 20 }));

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
    new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 0, after: 120 }, pageBreakBefore: i > 0,
                    children: [new TextRun({ text: `Caso ${c.id}`, font: FONTE, bold: true, size: 26 })] }),
    new Paragraph({ spacing: { after: 160 }, shading: { fill: "F7F9FC", type: ShadingType.CLEAR, color: "auto" },
                    border: { left: { style: BorderStyle.SINGLE, size: 18, color: "1F4E79", space: 6 } },
                    children: [new TextRun({ text: c.pergunta, font: FONTE, size: 22 })] }),
    new Table({
      width: { size: LARGURA, type: WidthType.DXA },
      columnWidths: [COL1, COL2],
      rows: [
        linha("1. Decisão (marque uma)", opcoes(DECISOES)),
        linha("2. Quem decide no balcão", opcoes(["Escrevente", "Oficial ou substituto"])),
        linha("3. Fundamentos (norma e artigo)", vazio(), 1700),
        linha("4. Como atender (o que dizer e o que exigir)", vazio(), 2900),
        linha("5. O que seria um erro grave neste caso", vazio(), 1900),
      ],
    }),
  ];
}

const capa = [
  new Paragraph({ heading: HeadingLevel.TITLE, alignment: AlignmentType.LEFT, spacing: { after: 120 },
                  children: [new TextRun({ text: "Casos de balcão do Registro Civil das Pessoas Naturais",
                                           font: FONTE, bold: true, size: 34, color: "1F4E79" })] }),
  p("Folha de respostas esperadas para validação por registrador civil", { size: 24, after: 240, color: "404040" }),
  p("Para que serve", { bold: true, size: 24, after: 80 }),
  p("Esta folha reúne 13 situações comuns no balcão do Registro Civil. Sua resposta, como registrador, será " +
    "usada como gabarito para medir se uma ferramenta de apoio ao balcão aplica corretamente as normas de " +
    "publicidade e proteção de dados. A ferramenta não decide: a decisão é sempre do Oficial."),
  p("Como preencher", { bold: true, size: 24, before: 120, after: 80 }),
  p("1. Leia cada caso e responda como o atendimento deveria ser feito, segundo as normas vigentes no Ceará."),
  p("2. Marque uma decisão, indique quem decide e cite a norma e o artigo que fundamentam a resposta."),
  p("3. Se o caso estiver incompleto ou depender de um fato não informado, registre isso no item 4."),
  p("4. Não há resposta certa sugerida nesta folha. Responda com base na sua prática e na norma."),
  p("Os casos são fictícios e não contêm dados pessoais. Nenhuma resposta da ferramenta foi incluída, para não " +
    "influenciar o gabarito.", { italics: true, color: "595959", before: 120 }),
  new Paragraph({ children: [new PageBreak()] }),
];

const validacao = [
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { after: 160 },
                  children: [new TextRun({ text: "Validação", font: FONTE, bold: true, size: 26 })] }),
  p("Declaro que as respostas acima refletem meu entendimento das normas aplicáveis ao Registro Civil das " +
    "Pessoas Naturais no Ceará na data abaixo."),
  new Table({
    width: { size: LARGURA, type: WidthType.DXA },
    columnWidths: [COL1, COL2],
    rows: ["Nome", "Função (Oficial, substituto, escrevente)", "Serventia e município", "Data", "Assinatura"]
      .map((r) => linha(r, vazio(), 700)),
  }),
];

const doc = new Document({
  creator: "Idarlan Magalhães",
  title: "Casos de balcão do Registro Civil — gabarito",
  styles: { default: { document: { run: { font: FONTE, size: 21 } } } },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 },
                          margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ text: "Casos de Registro Civil · página ", font: FONTE, size: 16, color: "808080" }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONTE, size: 16, color: "808080" }),
    ] })] }) },
    children: [...capa, ...casos.flatMap((c, i) => blocoCaso(c, i)), ...validacao],
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(saida, buf); console.log("gerado:", saida); });
