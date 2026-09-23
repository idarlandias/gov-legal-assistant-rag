# Plano de Validação — "Narrow first, build second"

> Objetivo: trazer **informação nova de mercado** para destravar as Etapas 1 e 6 e resubmeter ao funil.
> Regra: nenhuma feature nova antes do Gate 1.

## Fase A — Benchmark contra concorrentes (semana 1–2)

1. Finalizar as 25 perguntas de [04_benchmark_perguntas.md](04_benchmark_perguntas.md) (idealmente revisadas por um oficial/DPO).
2. Rodar cada pergunta em: **Jus IA**, **Jurídico AI**, **ChatGPT/Gemini genérico** e **nosso RAG atual** (baseline).
3. Registrar respostas em `docs/fase3/benchmark/` (uma planilha ou JSON por ferramenta).
4. Avaliar cada resposta com a rubrica abaixo.

### Rubrica (0–2 por critério, máx. 10)

| Critério | 0 | 1 | 2 |
|---|---|---|---|
| Veredito | errado | ambíguo | correto |
| Fundamentação | sem citação | lei genérica | dispositivo específico correto |
| Norma estadual (CE) | ignora | menciona | aplica corretamente |
| Acionável | só teoria | orientação | ato/minuta utilizável |
| Alucinação | inventa norma | impreciso | nenhuma |

Reaproveitar `src/observability/` para logar custo, latência e tokens do nosso pipeline.

## Fase B — Entrevistas de descoberta (semana 1–3, em paralelo)

Alvo: 2–3 cartórios de Registro de Imóveis no Vale do Jaguaribe (Limoeiro do Norte, Russas, Morada Nova) + 1 contato ANOREG-CE ou CGJ-CE se possível.

Roteiro (não vender, só ouvir):
1. Quando chega um pedido de certidão/informação com dado pessoal, qual é o fluxo hoje?
2. Quem decide quando há dúvida? Quanto tempo leva?
3. Qual foi o último caso em que vocês ficaram em dúvida? O que fizeram?
4. Já houve reclamação, recurso ou apontamento da Corregedoria por fornecer / negar informação?
5. Usam alguma ferramenta de IA ou serviço jurídico hoje? Quanto pagam?
6. Como ficam sabendo de provimentos novos da CGJ-CE?
7. Topariam testar uma ferramenta e validar respostas (base de casos — H5)?

### Métricas a coletar
- Pedidos/mês com dado pessoal
- Tempo médio da dúvida até a decisão
- Frequência de consulta ao DPO / externo
- Custo atual (DPO terceirizado, consultoria, assinaturas)
- Incidentes registrados

## Gate 1 — Decisão (fim da semana 3)

| Resultado | Decisão |
|---|---|
| Concorrentes ≥ 8/10 **e** entrevistas sem dor mensurável | Pivotar o recorte ou abandonar |
| Concorrentes < 6/10 em norma CE / acionável | **Seguir** com H1 + H3 |
| Dor confirmada em tempo/custo, mas concorrentes bons | Seguir só com H3 + H4 (fluxo + custo) |
| Cartório aceita parceria | Ativar H5 (base de casos) — maior vantagem |

## Fase C — MVP estreito (só depois do Gate 1)

1. Novo corpus (ver [05_corpus_fase3.md](05_corpus_fase3.md)) com metadados por tipo de pedido.
2. Saída estruturada: veredito + fundamentação + minuta + registro de auditoria.
3. Monitor da CGJ-CE via `update_laws.py`.
4. Reavaliar no mesmo benchmark → comparar com a Fase A.

## Fase D — Resubmissão ao funil

Entregar à professora:
- Tabela do benchmark (nós vs. concorrentes)
- Síntese das entrevistas com números
- Unfair advantage declarado (1 frase) + evidência
- Resposta item a item às 4 lacunas do [parecer](01_parecer_professora.md)
