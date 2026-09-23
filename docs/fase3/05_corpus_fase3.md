# Corpus da Fase 3

## Critério de inclusão
Somente **fontes oficiais e de uso livre** (legislação, atos normativos, orientações de órgãos públicos). Material de terceiros protegido por direito autoral **não entra**.

## Excluído

| Item | Motivo |
|---|---|
| `data/corpus/concursos/legislacao_transito/` (apostilas e aulas de cursinho) | Material protegido por direito autoral; não é dado proprietário; fora do recorte. Removido do versionamento (`.gitignore`), mantido apenas localmente. |
| CTB, concursos, Lei 14.133, Guia de Transparência Ativa | Fora do recorte vertical (continuam na Fase 2). |

## Incluir (a baixar e catalogar em `corpus_metadata.json`)

| Fonte | Órgão | Uso no recorte |
|---|---|---|
| Lei 6.015/1973 — Registros Públicos | Planalto | Publicidade registral, certidões |
| Lei 13.709/2018 — LGPD (já no corpus) | Planalto/ANPD | Bases legais, direitos do titular |
| Lei 12.527/2011 — LAI | Planalto | Acesso à informação × sigilo |
| Lei 8.935/1994 — Lei dos Cartórios | Planalto | Deveres do oficial |
| Provimento CNJ 149/2023 — Código Nacional de Normas (compilado) | CNJ | Capítulo de LGPD nas serventias |
| Código de Normas Notarial e Registral do CE (Prov. 04/2023/CGJCE + alterações até o Prov. 15/2026) | CGJ-CE | Norma estadual (H2) |
| Guias e orientações da ANPD (agentes de tratamento, incidentes) | ANPD | Tratamento, incidentes |
| Pareceres/manifestações públicas da AGU sobre LAI × LGPD | AGU | Conflito publicidade × privacidade |

## Metadados novos por chunk
- `tipo_pedido`: certidão | busca | informação_verbal | poder_público | titular | compartilhamento | incidente
- `esfera`: federal | CNJ | estadual_CE
- `vigencia_inicio` / `revogado_por`: para o monitor de atualização (`update_laws.py`)
- `dispositivo`: artigo/§/inciso, para citação exata

## Fontes
- [Provimento CNJ 149/2023](https://atos.cnj.jus.br/atos/detalhar/5243)
- [Código de Normas Extrajudicial — TJCE](https://www.tjce.jus.br/corregedoria/codigo-de-normas-extrajudicial/)
