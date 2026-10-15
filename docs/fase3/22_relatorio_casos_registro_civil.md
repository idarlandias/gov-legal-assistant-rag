# Relatório: casos de Registro Civil para o gabarito

> **Data:** 15/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Continuação de:** [21_relatorio_fase4_posicionamento.md](21_relatorio_fase4_posicionamento.md). Commit `ed3ec19` (local). Último push: `36e25f7`.

## 1. O que foi entregue

| Arquivo | Para quem | Conteúdo |
|---|---|---|
| `data/validacao/gabarito_rcpn_modelo.csv` | **registrador civil** | 13 casos (ids 101 a 113) com os campos jurídicos em branco: decisão esperada, quem decide, fundamentos, resposta esperada, erro grave, validado por e data |
| `data/validacao/casos_rcpn.json` | sistema | o mesmo texto dos casos + os fatos em forma estruturada, para rodar o motor de regras |
| `scripts/avaliar_gabarito.py` | proponente | lê o gabarito do benchmark (RI) e o de Registro Civil e mede a **concordância do motor de regras com o registrador** |

## 2. Os 13 casos

Os casos cobrem todos os ramos do motor do Registro Civil:
- breve relato;
- óbito;
- inteiro teor pedido pelo próprio registrado e por terceiro;
- dado sensível de pessoa viva e de pessoa falecida (pedido por filho);
- informação de menção vedada (reconhecimento de filho averbado);
- quesitos sem dado restrito;
- procedimento preparatório com titular vivo e com titular falecido;
- busca nos índices e em outras fontes;
- registro bloqueado por determinação judicial.

Cada caso **descreve a situação e pergunta como atender**, sem resposta.

## 3. Como a avaliação funciona

1. O registrador preenche `gabarito_rcpn_modelo.csv` sem ver o que o sistema responde (**teste cego**) e o salva como `gabarito_rcpn.csv`.
2. O comando `python scripts/avaliar_gabarito.py` roda o motor de regras com os fatos de cada caso e compara a decisão com a do registrador:
   - VERDE equivale a DEFERIR;
   - AMARELO equivale a DEFERIR_COM_EXIGENCIA;
   - VERMELHO com autorização judicial equivale a ENCAMINHAR_JUIZ.
3. A saída é o **percentual de concordância** e a **lista das divergências**. Cada divergência ou é erro do motor, a corrigir, ou é interpretação a discutir com o registrador.

A comparação é automática: não depende de alguém julgar texto de resposta, porque o motor devolve uma decisão estruturada.

## 4. Verificações

- O modelo entregue ao registrador tem os campos jurídicos vazios (teste).
- Todos os 13 casos são entradas válidas do motor, que decide cada um, e juntos cobrem os três desfechos (teste).
- O cálculo da concordância foi testado com um gabarito fictício de concordância e divergência.
- Os ids 101 a 113 não colidem com as 26 perguntas da coleta (teste).
- Suíte offline: **218 testes passando**.

## 5. Próximo passo (campo)

Levar ao registrador civil o `gabarito_rcpn_modelo.csv`. Se possível, levar ao registrador de imóveis o `gabarito_modelo.csv`, com as 25 perguntas e a 26. Com as duas cópias assinadas, o projeto passa a ter, pela primeira vez, uma **medida de acerto jurídico**: a concordância do motor com o registrador, que é a prova que a validação de 15/10 pediu.
