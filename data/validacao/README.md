# Validação de campo: diário de balcão, conversas e gabarito

Esta pasta guarda os instrumentos que produzem a evidência pedida na validação de 15/10/2026. São três peças, e é com elas que a proposta volta ao funil:

| Instrumento | Arquivo | Quem preenche | Resultado |
|---|---|---|---|
| Diário de balcão (1 semana, 3 cartórios) | `diario_balcao_modelo.csv` → `diario_balcao_<cartorio>.csv` | escrevente, ao fim de cada atendimento | `python scripts/resumir_diario.py` |
| Conversas de qualificação (5 × 30 min) | `roteiro_conversas.md` | proponente | anotações + palavras usadas pelos cartorários |
| Gabarito dos 25 casos (+ a 26) | `gabarito_modelo.csv` | registrador da região, por escrito | `python scripts/avaliar_gabarito.py` |

## Regras de privacidade

- **Nenhum dado pessoal** no diário: nada de nome, CPF, matrícula ou número de protocolo. Registre só o tipo do pedido, o perfil de quem pede e o desfecho.
- Os diários preenchidos (`diario_balcao_<cartorio>.csv`) estão no `.gitignore` e **não vão para o GitHub**. Só o modelo é versionado.
- Use apenas casos fictícios ou anonimizados em qualquer teste do sistema.

## Diário de balcão: uma linha por pedido

| Coluna | Valores |
|---|---|
| `data` | AAAA-MM-DD |
| `cartorio` | apelido curto, ex.: `limoeiro_ri`, `russas_rcpn` (sem nome do oficial) |
| `atribuicao` | `RI` · `RCPN` · `NOTAS` · `PROTESTO` · `RTD_PJ` · `OUTRA` |
| `tipo_pedido` | texto curto, ex.: "certidão de matrícula", "inteiro teor de nascimento", "busca por nome" |
| `perfil_requerente` | texto curto, ex.: "próprio titular", "terceiro sem vínculo", "advogado", "órgão público" |
| `canal_entrada` | `balcao` · `telefone` · `email` · `whatsapp` · `online` |
| `gerou_duvida` | `sim` · `nao`: o atendente precisou parar, consultar alguém ou a norma? |
| `quem_decidiu` | `escrevente` · `oficial` · `substituto` · `consulta_externa` · `nao_se_aplica` |
| `tempo_min` | minutos do atendimento (aproximado) |
| `consultou` | o que consultou, ex.: "código de normas", "oficial", "colega", "nada" |
| `desfecho` | `emitida` · `emitida_com_exigencia` · `exigencia_pendente` · `recusada_nota` · `orientado` · `encaminhado_juiz` · `desistiu` |
| `observacao` | livre, **sem dado pessoal** |

## Gabarito do registrador

`gabarito_modelo.csv` traz as 26 perguntas com os campos jurídicos **em branco**. O sistema não sugere nenhuma resposta esperada: quem escreve é o registrador. A cópia preenchida é salva como `gabarito.csv`.

| Coluna | Conteúdo |
|---|---|
| `atribuicao` | `RI` ou `RCPN` (ou outra) |
| `decisao_esperada` | `DEFERIR` · `DEFERIR_COM_EXIGENCIA` · `INDEFERIR_NOTA` · `INFORMAR` · `ENCAMINHAR_JUIZ` · `NAO_SE_APLICA` |
| `quem_decide` | escrevente ou oficial |
| `fundamentos` | norma e artigo (obrigatório para a linha valer) |
| `resposta_esperada` | o que um bom atendimento diria |
| `erro_grave_se` | o que tornaria a resposta contrária à norma |
| `validado_por`, `data_validacao` | quem assinou e quando; **linha sem `validado_por` não entra na avaliação** |

## Casos de Registro Civil (13 casos, ids 101 a 113)

As 25 perguntas do benchmark são de Registro de Imóveis. Para o Registro Civil, `casos_rcpn.json` traz 13 situações de balcão. Elas cobrem breve relato, óbito, inteiro teor pedido pelo próprio registrado ou por terceiro, dado sensível de pessoa viva ou falecida, informação de menção vedada, quesitos, procedimento preparatório, buscas e registro bloqueado.
- **Nenhum caso traz resposta.** O campo `entrada` só repete, de forma estruturada, os fatos já descritos no texto.
- **Para o cartório:** entregue o documento único `documento_cartorio_registro_civil.pdf` (para imprimir) ou `.docx` (para preencher no Word). São 18 páginas:
  - carta de apresentação;
  - instruções;
  - Parte A: os 13 casos, um por página;
  - Parte B: 7 perguntas rápidas sobre o balcão;
  - Parte C: diário de balcão de uma semana (opcional);
  - página de validação, com a autorização de uso do nome.

  Depois, transcreva a Parte A para `gabarito_rcpn_modelo.csv` (salve como `gabarito_rcpn.csv`) e a Parte C para `diario_balcao_<cartorio>.csv`. O documento é regenerado a partir de `casos_rcpn.json` com `scripts/folha_gabarito/gerar_folha_rcpn.js`.
- **Teste cego:** não mostre ao registrador o que o sistema responde. A comparação só acontece na avaliação.
- **Concordância:** `python scripts/avaliar_gabarito.py` compara automaticamente a decisão do **motor de regras** com a do registrador em cada caso validado. A saída é o percentual de concordância e a lista das divergências.

## Avaliação de cada sistema

Uma pessoa julga cada resposta coletada contra o gabarito e registra em `avaliacao_<sistema>.csv`:

`sistema,pergunta_id,acerto,contraria_norma,observacao,avaliado_por`, com `acerto` = `certo` · `parcial` · `errado` · `sem_resposta` e `contraria_norma` = `sim` · `nao`.

O comando `python scripts/avaliar_gabarito.py` calcula o percentual de acerto e o **número de respostas contrárias à norma (meta: zero)** por sistema, só nas perguntas com gabarito validado.

**Critério de continuidade sugerido na validação:** com menos de **1 dúvida real por dia por cartório**, o formato de balcão não segue. O resumo separa Registro de Imóveis (RI) e Registro Civil (RCPN), e os números decidem a atribuição-alvo.
