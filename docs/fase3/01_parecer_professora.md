# Parecer da Professora — Funil Discovery + Auditoria Cética

> Registrado em 2026-09-23. Texto original preservado; destaques ao final.

## Resultado do funil

Rodei o funil completo (Discovery) e a auditoria (Cético) sobre a ideia de RAG jurídico para cartórios.

Resumo do resultado: a dor é real e bem documentada — inclusive a AGU e o governo de MG já brigaram com a mesma ambiguidade LAI x LGPD que o exemplo do CPF ilustra. Mas a proposta trava nas duas etapas decisivas:

- **Etapa 1** (nenhum unfair advantage declarado) e
- **Etapa 6** (fricção baixa, porque já existem caminhos prontos — DPO obrigatório por Provimento CNJ, ANOREG+, e assistentes jurídicos genéricos maduros como Jus IA e Jurídico AI, já comprados por tribunais via licitação).

A auditoria cética rebaixou o veredito por causa disso: pela regra do elo mais fraco, Etapa 6 vermelha já impede nota verde.

Dor real não basta sem diferenciação clara num mercado horizontal já ocupado.

## Recado direto

> Idarlan, tem que pensar em um diferencial competitivo que as demais plataformas não tenham, senão você vai perder tempo desenvolvendo e já têm concorrência. Acho que vale a pena dar uma olhada em como criar essa Unfair Advantage, ou melhorar o que já existe por aí, ficando mais barato ou mais eficiente.

## Principais riscos

- Concorrência direta madura e não mapeada, com tração comprovada no setor público (Jus IA, Jurídico AI e outros).
- Nenhum unfair advantage declarado — arquitetura de RAG jurídico é replicável por qualquer concorrente com acesso ao mesmo corpus legal público.
- ANOREG/BR já é o canal institucional natural do setor de cartórios para temas de compliance — pode virar gatekeeper ou parceiro necessário, não neutro.
- Baixa fricção de resolver a dor por outros meios já disponíveis (DPO obrigatório, assistentes jurídicos genéricos, ANOREG+).

## Lacunas — o que o owner deve trazer para revalidação

1. Qual é o unfair advantage concreto: dado proprietário, integração exclusiva com sistema de cartório, parceria institucional (ANOREG/IRIB/CNJ) ou curadoria especializada que um assistente genérico não tem?
2. Por que um cartório escolheria construir/adotar uma ferramenta nova em vez de assinar o Jus IA ou similar, que já resolve o mesmo tipo de pergunta e já tem tração no setor público?
3. Evidência de que o caminho atual (perguntar ao DPO, usar assistente genérico) é de fato mais custoso/arriscado do que parece — por exemplo, tempo médio de resposta do DPO, taxa de erro observada, ou reclamações internas registradas.
4. Um recorte vertical específico (ex.: só cartórios de registro de imóveis, ou só a interseção LAI x LGPD x publicidade registral) com uma base de conhecimento curada que nenhum concorrente genérico tem hoje.

## Próximos passos sugeridos

- Testar o Jus IA e o Jurídico AI com as mesmas perguntas reais do público-alvo (ex.: o exemplo do CPF no Portal da Transparência) para medir se eles já entregam uma resposta satisfatória — se sim, o gap de mercado pode ser menor do que a proposta assume.
- Conversar com um DPO de cartório real (ou com a Corregedoria/ANOREG) para entender o fluxo de dúvida-resposta hoje e onde ele realmente falha.
- Se avançar, buscar ativamente um recorte com unfair advantage real antes de comprometer tempo de engenharia — **narrow first, build second**.
- Se as lacunas acima forem preenchidas com nova informação de mercado — não apenas com documentação mais bem organizada —, este parecer deve ser revisado, e a proposta deve ser resubmetida ao funil.

---

## Leitura do direcionamento (síntese)

| Ponto | Implicação para a Fase 3 |
|---|---|
| Etapa 1 vermelha | Declarar **um** unfair advantage concreto e verificável — não "RAG bem feito". |
| Etapa 6 vermelha | Provar que o caminho atual (DPO / Jus IA) falha ou custa caro, **com números**. |
| Regra do elo mais fraco | Não adianta polir o resto; as etapas 1 e 6 decidem a nota. |
| "Mais barato ou mais eficiente" | Custo por consulta e tempo de resposta viram métricas de primeira classe. |
| "Narrow first, build second" | Validação de mercado **antes** de código novo. |
| Resubmissão | Só com **informação nova de mercado**, não com documentação reorganizada. |
