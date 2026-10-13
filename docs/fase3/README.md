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
| 7 | [06_entrega_radical_e_pensamento_divergente.md](06_entrega_radical_e_pensamento_divergente.md) | Ideação, mindset e formas alternativas de entrega de valor |
| 8 | [07_entregas_professora_zandona.md](07_entregas_professora_zandona.md) | As 3 entregas consolidadas para a Profª Daniele Zandoná |
| 9 | [08_revisao_2026-10-13.md](08_revisao_2026-10-13.md) | Revisão de 13/10: fundamento invertido do Art. 1.131 e defeitos encontrados |
| 10 | [09_relatorio_para_analise.md](09_relatorio_para_analise.md) | Relatório autossuficiente da auditoria para análise externa |
| 11 | [10_relatorio_pos_correcoes.md](10_relatorio_pos_correcoes.md) | Correções aplicadas, números medidos depois delas e itens abertos |
| 12 | [11_relatorio_correcoes_rodada2.md](11_relatorio_correcoes_rodada2.md) | 2ª rodada: canal AMARELO, consulta do Ato, guarda do 1.131, README e verificador v2 |
| 13 | [12_relatorio_rodada3_readme_ui.md](12_relatorio_rodada3_readme_ui.md) | 3ª rodada: README e UI alinhados ao código, tema claro, guarda de UI e manifesto de normas |
| 14 | [13_relatorio_rodada4_chat_ui_manifesto.md](13_relatorio_rodada4_chat_ui_manifesto.md) | 4ª rodada: regras únicas do chat e do Ato Pronto, aba do tarjador fora da UI, datas do corpus |
| 15 | [14_relatorio_rodada5_fechamento.md](14_relatorio_rodada5_fechamento.md) | 5ª rodada: manifesto e barra lateral, README e doc 06 retificados, fechamento e push |

## Checklist
- [ ] Revisar as 25 perguntas com um oficial ou DPO
- [ ] Rodar o benchmark: Jus IA, Jurídico AI, LLM genérico e RAG atual
- [ ] Entrevistar 2 a 3 cartórios de RI do Vale do Jaguaribe
- [ ] Gate 1: seguir, pivotar ou abandonar
- [x] Montar o corpus da Fase 3 (fontes oficiais indexadas com schema 2 e especialidade)
- [x] MVP estreito com saída estruturada (Gerador de Ato Pronto de Balcão e UI Alfândega)
- [ ] Resubmeter ao funil com dados novos

