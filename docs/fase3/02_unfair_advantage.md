# Unfair Advantage — Hipóteses para a Fase 3

> Status: **hipóteses**. Nenhuma vale até passar pelo [plano de validação](03_plano_validacao.md).

## Diagnóstico do projeto atual (Fase 2)

O `gov-legal-assistant-rag` é **horizontal**: LGPD + Lei 14.133 + Transparência + Procedimentos + CTB num único chat, com corpus 100% público. É exatamente o perfil que o parecer considera replicável.

**Reaproveitável (infra):** `src/pipeline/rag.py`, `cache.py`, `routing.py`, `tools.py`, `security_skill.py`, `update_laws.py`, `src/observability/`.
**Muda (produto):** corpus, formato de saída, público-alvo, métricas de avaliação.

## Recorte proposto

> **Cartórios de Registro de Imóveis do Ceará — decisões de publicidade registral na interseção LAI × LGPD.**

Pergunta-tipo: *"Requerente X pede certidão / informação Y sobre a matrícula Z. Posso fornecer? Integral, com tarja, ou devo negar? Com base em quê?"*

## As 5 hipóteses de vantagem

### H1 — Corpus vertical curado (não disponível pronto em assistente genérico)
Base restrita e estruturada por **tipo de pedido**, não por lei:
- Lei 6.015/73 (Registros Públicos), LGPD (13.709/18), LAI (12.527/11)
- Provimento CNJ 149/2023 — Código Nacional de Normas do Foro Extrajudicial (consolidou e revogou o Prov. 134/2022, que tratava de LGPD nas serventias)
- Código de Normas do Serviço Notarial e Registral do Ceará (Prov. 04/2023/CGJCE e alterações)
- Orientações da ANPD, pareceres (ex.: AGU sobre LAI × LGPD), decisões da CGJ-CE

**Como medir:** taxa de citação correta do dispositivo específico vs. Jus IA / Jurídico AI no benchmark.

### H2 — Atualização normativa regional contínua
O Código de Normas do CE muda com frequência (ex.: Provimento nº 15/2026/CGJCE, publicado em 08/09/2026, alterou requisitos de qualificação das partes). Ferramenta nacional genérica tende a ficar desatualizada na norma estadual.
- Reaproveita `update_laws.py`: monitorar a página de provimentos da CGJ-CE, reindexar e **alertar** o cartório sobre o que mudou.

**Como medir:** defasagem (dias) entre publicação do provimento e resposta correta no sistema vs. concorrentes.

### H3 — Saída = ato pronto, não conversa (ataca a Etapa 6 / fricção)
Entrada estruturada (tipo de requerente, dado pedido, finalidade) → saída:
1. **Veredito:** fornecer / fornecer com tarja / negar / exigir justificativa
2. **Fundamentação** com dispositivo citado
3. **Minuta** da resposta ao requerente ou nota devolutiva
4. **Registro** para trilha de auditoria LGPD (registro de operações de tratamento)

O assistente genérico responde a pergunta; este **encaixa no fluxo do balcão** e gera evidência de compliance.

**Como medir:** tempo balcão → decisão (min) com e sem a ferramenta.

### H4 — Custo e privacidade (o "mais barato" do parecer)
- Roteamento (`routing.py`) + cache semântico (`cache.py`) → custo por consulta muito abaixo de assinatura por usuário.
- Opção **on-premise / modelo local** para pedidos com dado pessoal: o dado do requerente não sai da serventia.
- Público: cartórios pequenos do interior, para quem assinatura de ferramenta jurídica premium não fecha a conta.

**Como medir:** custo/consulta (R$) e custo mensal por serventia vs. preço público dos concorrentes.

### H5 — Base de casos validados (o único dado proprietário real)
Com 1 cartório parceiro: cada dúvida real respondida e **validada pelo DPO / oficial** entra na base como caso-precedente. Com o tempo, é um ativo que nenhum concorrente acessa.

**Como medir:** nº de casos validados; ganho de acurácia no benchmark com vs. sem base de casos.

## Combinação recomendada

**H1 + H3 + H5** como núcleo (recorte estreito + ato pronto + dado proprietário), com **H2 e H4** como reforço. Resposta às lacunas do parecer:

| Lacuna do parecer | Resposta |
|---|---|
| 1. Qual unfair advantage? | Curadoria vertical (H1) + base de casos validados (H5) |
| 2. Por que não Jus IA? | Gera o ato e a trilha LGPD (H3), norma CE atualizada (H2), custo menor (H4) — **a provar no benchmark** |
| 3. Evidência de custo do caminho atual | Entrevistas + medição de tempo/erro (plano de validação) |
| 4. Recorte vertical | Registro de Imóveis CE × publicidade registral × LAI/LGPD |

## Riscos que continuam abertos

- **ANOREG/BR e IRIB** podem ser gatekeepers → tratar como parceiros potenciais, não concorrentes.
- Se Jus IA / Jurídico AI acertarem ≥ 80% do benchmark, H1 cai e o foco vira H3 + H4 (fluxo + custo).
- Sem cartório parceiro, H5 não existe — é a hipótese mais forte e a mais dependente de relacionamento.

## Fontes
- [Provimento CNJ 149/2023 — Código Nacional de Normas](https://atos.cnj.jus.br/atos/detalhar/5243)
- [Provimento CNJ 134/2022 (revogado pelo 149/2023)](https://atos.cnj.jus.br/atos/detalhar/4707)
- [Código de Normas Extrajudicial — TJCE](https://www.tjce.jus.br/corregedoria/codigo-de-normas-extrajudicial/)
- [Provimento nº 04/2023/CGJCE](https://www.tjce.jus.br/corregedoria/post/provimento-no-04-2023-cgjce/)
- [CGJ-CE atualiza normas extrajudiciais (Prov. 15/2026)](https://www.tjce.jus.br/noticias/corregedoria-geral-da-justica-atualiza-normas-dos-servicos-extrajudiciais-e-reforca-a-seguranca-juridica-dos-registros-imobiliarios/)
