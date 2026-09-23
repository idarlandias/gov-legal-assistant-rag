# Corpus da Fase 3

> Montado em 2026-09-23. Fonte da verdade: [`src/fase3/sources.py`](../../src/fase3/sources.py). Hashes e estatísticas: [`data/corpus_fase3/manifest.json`](../../data/corpus_fase3/manifest.json).

## Critério de inclusão
Somente **fontes oficiais e de uso livre**: legislação, atos normativos e orientações de órgãos públicos. Material de terceiros protegido por direito autoral **não entra**.

## Fontes indexadas (coleção Chroma `fase3`)

| Fonte | Órgão | Formato | Dispositivos | Chunks |
|---|---|---|---:|---:|
| Lei 6.015/1973 (Registros Públicos) | Planalto (compilada) | HTML | 318 | 410 |
| LGPD (Lei 13.709/2018) | Planalto (compilada) | HTML | 80 | 119 |
| LAI (Lei 12.527/2011) | Planalto | HTML | 50 | 65 |
| Decreto 7.724/2012 (regulamento da LAI) | Planalto | HTML | 79 | 105 |
| Lei 8.935/1994 (Notários e Registradores) | Planalto | HTML | 59 | 63 |
| Provimento CNJ 149/2023 (Código Nacional de Normas, compilado de 20/08/2026) | CNJ | PDF | 923 | 1.295 |
| Código de Normas Notarial e Registral do CE (versão atualizada, set/2026) | CGJ-CE | PDF | 1.828 | 2.104 |
| Provimento 15/2026/CGJCE | CGJ-CE | PDF | 5 | 13 |
| Resolução CD/ANPD 15/2024 (incidentes de segurança) | DOU | HTML | 25 | 36 |
| Guia ANPD — Agentes de Tratamento (2ª versão) | ANPD | PDF | 26 págs. | 86 |
| Guia ANPD — Segurança da Informação para pequeno porte | ANPD | PDF | 21 págs. | 63 |
| **Total** | | | **3.414** | **4.359** |

## Como o texto é tratado
- **Redação revogada fora:** o Planalto marca o texto revogado com `<strike>`, e esse texto é descartado. O corpus só tem a redação vigente.
- **Um chunk por artigo**, subdividido quando passa de 1.200 caracteres. Cada chunk começa com a citação (`Lei 6.015/1973, Art. 17`), que também vai no metadado `source`, para o LLM citar o dispositivo exato.
- **Metadados:** `fonte_id`, `dispositivo`, `secao` (último título, capítulo ou seção), `esfera` (federal, cnj, estadual_ce, anpd), `tipo_documento`, `fonte` (URL) e `page`.
- **Segmentação robusta:**
  - números de artigo só são aceitos em ordem crescente, para que uma citação como "Art. 150 da Lei..." no início de linha não quebre o artigo;
  - aceita os sufixos `-A` a `-AZ` e o ponto de milhar (`Art. 1.000`);
  - o ato de aprovação é separado do Código anexo e marcado com "(ato de aprovação)";
  - o sumário (linhas pontilhadas) é removido.
- **Guias sem articulado** (ANPD) são fatiados por página.

## Excluído

| Item | Motivo |
|---|---|
| `data/corpus/concursos/legislacao_transito/` (apostilas e aulas de cursinho) | Protegido por direito autoral; fora do recorte. Fora do repositório via `.gitignore`. |
| CTB, concursos, Lei 14.133, Guia de Transparência Ativa | Fora do recorte vertical; continuam na coleção `docs` da Fase 2. |

## Pendente
- Pareceres da AGU/CGU sobre o conflito LAI × LGPD: não há URL oficial estável em PDF; buscar e avaliar.
- Orientações do ONR/SREI sobre centrais eletrônicas (pergunta 22 do benchmark).

## Como reconstruir
```bash
python scripts/fase3/build_corpus.py            # baixa (só o que mudou) e reindexa
python scripts/fase3/build_corpus.py download   # só verifica e baixa mudanças
python scripts/fase3/build_corpus.py stats
```
Os originais ficam em `data/corpus_fase3/raw/` e o texto segmentado em `data/corpus_fase3/dispositivos.jsonl`. Os dois estão no `.gitignore` e são reproduzíveis pelo script; só o `manifest.json` é versionado.

## Recuperação híbrida
[`src/fase3/retrieval.py`](../../src/fase3/retrieval.py):
- **Denso:** `intfloat/multilingual-e5-small` (MIT, 384 dimensões) rodando em ONNX pelo onnxruntime, sem torch. Usa os prefixos `query:` e `passage:` que o E5 exige.
- **Esparso:** BM25 com tokenização em português: sem acento, sem stopwords, "6.015" vira "6015" e cada palavra é cortada nas 6 primeiras letras, como um stemmer barato.
- **Fusão:** RRF (k=60) sobre os 50 melhores de cada lista.
- **Trava de segurança:** o nome do modelo fica nos metadados da coleção, e abrir com outro modelo dá erro. Os dois modelos geram vetores de 384 dimensões, então a troca não daria erro sozinha; só devolveria lixo.
- Reindexar leva cerca de 11 minutos na CPU.

## Evolução no benchmark (25 perguntas, gpt-oss via Groq)

| Execução | "Não encontrado" | Respostas citando artigo | Tokens de entrada | Latência média |
|---|---:|---:|---:|---:|
| RAG atual (coleção `docs`, MiniLM) | 20 | 4 | 45 mil | 6,8 s |
| Fase 3, MiniLM | 14 | 9 | 48 mil | 8,1 s |
| Fase 3, E5 denso | 10 | 13 | 52 mil | 8,2 s |
| **Fase 3, E5 + BM25 (híbrido)** | **8** | **16** | 53 mil | 9,2 s |

A planilha usa a execução híbrida nas linhas "RAG Fase 3".

### Risco novo: mistura de especialidades
Com mais respostas, aparece um erro mais perigoso que o "não encontrado". Na pergunta 1 (certidão de matrícula pedida por terceiro), o sistema respondeu **"Não"** com base em regras de **Registro Civil** (Provimento CNJ 149, Art. 114 e Art. 117; Código CE, Art. 258). Para **Registro de Imóveis**, a Lei 6.015, Art. 17, diz que qualquer pessoa pode pedir certidão sem informar o motivo. O Código CE e o CNJ 149 misturam todas as especialidades (imóveis, civil, notas, protesto, títulos e documentos), e a busca não distingue uma da outra.

**Próximo passo sugerido:** metadado `especialidade`, extraído dos títulos e capítulos dos Códigos, com filtro ou reforço para Registro de Imóveis. É a curadoria vertical (H1) virando código.

### Avaliação só da recuperação
`scripts/fase3/eval_retrieval.py` mede em que posição o dispositivo esperado aparece. Os alvos atuais são **provisórios e estreitos**, escolhidos lendo a lei e não pelo gabarito. Eles marcam como erro trechos relevantes de outras normas, como o Código CE, Art. 1131 §10, sobre a certidão de inteiro teor da matrícula. Refazer os alvos a partir do gabarito do oficial/DPO.

## Fontes
- [Provimento CNJ 149/2023](https://atos.cnj.jus.br/atos/detalhar/5243)
- [Código de Normas Extrajudicial — TJCE](https://www.tjce.jus.br/corregedoria/codigo-de-normas-extrajudicial/)
- [Resolução CD/ANPD 15/2024 — DOU](https://www.in.gov.br/en/web/dou/-/resolucao-cd/anpd-n-15-de-24-de-abril-de-2024-556243024)
- [Guias da ANPD](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes)
