# Relatório: fase 4, posicionamento como assistente de conformidade

> **Data:** 15/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Continuação de:** [20_relatorio_fase3_registro_civil.md](20_relatorio_fase3_registro_civil.md). Commit `9a47a38` (local). Último push: `a25fe0a`.

## 1. O que a fase corrige

A validação de 15/10 apontou contradições entre o que a proposta dizia e o que a norma e o mercado mostram. Esta fase alinha o discurso público (README, tela e entregas antigas) ao produto que existe depois das fases 2 e 3.

| Antes | Agora | Por quê |
|---|---|---|
| "Decisão operacional", "veredito direto" | **Assistente de conformidade**: mostra o que a norma exige, prepara o documento e redige a minuta; **a decisão é do Oficial** | o sistema produz sugestão; regras estaduais restringem decisão jurídica por IA |
| "Multas severas da ANPD" como dor | risco **disciplinar**, perante a Corregedoria; "multa da ANPD" foi para as hipóteses não validadas | não há caso registrado de sanção da ANPD a cartório |
| "Conflito LAI × LGPD" | publicidade pela **Lei 6.015/1973 (art. 17)** e pelo **Prov. CNJ 149/2023 (arts. 113 a 128)** | a LAI não rege as certidões de cartório |
| Concorrentes: Jus IA e ChatGPT | concorrentes diretos: **IAs feitas para cartório** (AryaBolt, Sele IA, Notário IA), além das IAs jurídicas gerais e do fluxo atual | são essas que disputam o mesmo cliente |
| Só Registro de Imóveis, "Analogia da Alfândega" | **Registro de Imóveis e Registro Civil**, com canais definidos por atribuição | resultado das fases 2 e 3 |
| Matriz "Zero-UI de chat", "ROPA instantâneo" | matriz com o que é verificável: regra com trecho literal, documento exigido montado sem IA, latência medida; o resto como "não medido" | nada de afirmação sem prova |

## 2. Mudanças

- **README:**
  - topo novo, com o posicionamento e a decisão do Oficial;
  - seção "O problema" corrigida;
  - fluxo regra → documento → minuta e tabela de canais do RI e do RCPN;
  - nova seção "O que ainda falta provar" (diário de balcão, gabarito, concorrentes reais);
  - comparação contra as IAs para cartório;
  - limitações atualizadas;
  - diagrama com o motor de regras;
  - **215 testes**.
- **Tela:**
  - subtítulo e descrição da aba no mesmo posicionamento;
  - métrica "Documento exigido pela norma: montado sem IA";
  - matriz comparativa contra as IAs para cartório;
  - legenda "Registro de Imóveis e Registro Civil (CE)".
- **Docs 06 e 07** (entregas de ideação de setembro): **nota de retificação no topo**, listando o que foi superado. São seis pontos: tarja, justificativa para matrícula, veredito/vinculante, multa da ANPD, LAI e concorrentes. O texto original foi preservado como registro.

## 3. Verificações

- Suíte offline: **215 testes passando**.
- `AppTest` da tela sem exceção, com o painel "Canal definido por regra…".
- Guarda do 1.131 sem ocorrência nova fora dos relatórios de auditoria. A nota dos docs 06/07 e a tabela do doc 19 citam o §10 como base para **reproduzir** todo o conteúdo e estão marcadas com a liberação documentada.

## 4. O que fica para o campo

O posicionamento está coerente com a norma, mas a nota da validação só muda com evidência:
1. diário de balcão em 3 cartórios;
2. gabarito assinado por registrador, incluindo casos de **Registro Civil**, que ainda faltam no benchmark;
3. respostas das IAs para cartório na coleta.

Os instrumentos estão em `data/validacao/` e `data/benchmark/`.
