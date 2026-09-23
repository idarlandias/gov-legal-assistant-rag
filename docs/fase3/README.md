# Fase 3 — Residência SiDi: do RAG horizontal ao recorte vertical

> Início: 2026-09-23 · Owner: Idarlan Magalhães

## Onde estamos
O parecer do funil (Discovery + Cético) confirmou a **dor real** (ambiguidade LAI × LGPD em cartórios), mas travou a proposta em:
- **Etapa 1:** nenhum unfair advantage declarado
- **Etapa 6:** baixa fricção, porque já existem DPO obrigatório, ANOREG+, Jus IA e Jurídico AI

## Direção da Fase 3
**Narrow first, build second.** Primeiro validar o mercado com números, depois construir.

Recorte candidato: **Registro de Imóveis no Ceará × publicidade registral × LAI/LGPD**, com saída em forma de **ato pronto** (veredito + fundamentação + minuta + registro de auditoria).

## Documentos
| # | Arquivo | Conteúdo |
|---|---|---|
| 1 | [01_parecer_professora.md](01_parecer_professora.md) | Parecer original e leitura do direcionamento |
| 2 | [02_unfair_advantage.md](02_unfair_advantage.md) | Hipóteses H1 a H5 e combinação recomendada |
| 3 | [03_plano_validacao.md](03_plano_validacao.md) | Benchmark, entrevistas, Gate 1 e MVP |
| 4 | [04_benchmark_perguntas.md](04_benchmark_perguntas.md) | 25 perguntas de balcão (gabarito a validar) |
| 5 | [05_corpus_fase3.md](05_corpus_fase3.md) | Fontes oficiais incluídas e excluídas |
| 6 | [benchmark/](benchmark/README.md) | Planilha de coleta e script que roda o RAG nas perguntas |

## Checklist
- [ ] Revisar as 25 perguntas com um oficial ou DPO
- [ ] Rodar o benchmark: Jus IA, Jurídico AI, LLM genérico e RAG atual
- [ ] Entrevistar 2 a 3 cartórios de RI do Vale do Jaguaribe
- [ ] Gate 1: seguir, pivotar ou abandonar
- [ ] Montar o corpus da Fase 3 (fontes oficiais)
- [ ] MVP estreito com saída estruturada
- [ ] Resubmeter ao funil com dados novos
