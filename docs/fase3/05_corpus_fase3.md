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

## Primeira medição (benchmark, 25 perguntas)

| | RAG atual (coleção `docs`) | RAG Fase 3 (coleção `fase3`) |
|---|---:|---:|
| "Não encontrado no corpus" | 20 | **14** |
| Fontes citadas | LGPD/LAI genéricas, apostilas | CNJ 149, Código CE, Lei 6.015, ANPD |

**Gargalo identificado: a recuperação, não o corpus.** O embedding padrão do Chroma (`all-MiniLM-L6-v2`) é treinado em inglês. Na pergunta 1, o Art. 17 da Lei 6.015 responde a pergunta quase palavra por palavra e ficou fora dos 300 primeiros resultados. Na pergunta 23, que cita o Provimento 15/2026 pelo nome, ele só aparece na 27ª posição. Próximo passo: embedding multilíngue e busca híbrida (BM25 + vetorial).

## Fontes
- [Provimento CNJ 149/2023](https://atos.cnj.jus.br/atos/detalhar/5243)
- [Código de Normas Extrajudicial — TJCE](https://www.tjce.jus.br/corregedoria/codigo-de-normas-extrajudicial/)
- [Resolução CD/ANPD 15/2024 — DOU](https://www.in.gov.br/en/web/dou/-/resolucao-cd/anpd-n-15-de-24-de-abril-de-2024-556243024)
- [Guias da ANPD](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes)
