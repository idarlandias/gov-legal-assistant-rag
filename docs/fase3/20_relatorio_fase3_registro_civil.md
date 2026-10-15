# Relatório: fase 3, motor de regras do Registro Civil das Pessoas Naturais

> **Data:** 15/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Continuação de:** [19_relatorio_fase2_motor_regras.md](19_relatorio_fase2_motor_regras.md). Commit `3d69a1e` (local). Último push: `57b4e24`.

## 1. Por que o Registro Civil

No Registro de Imóveis, o caso comum (certidão de matrícula) tem regra simples: basta identificar o requerente. No Registro Civil, as regras de certidão dependem de fatos que o atendente precisa avaliar:
- quem pede: o próprio registrado ou um terceiro;
- a modalidade: breve relato, inteiro teor, quesitos ou procedimento preparatório;
- se o assento contém dado sensível ou informação de menção vedada;
- se o registrado é falecido.

E, ao contrário do RI, aqui **a própria norma exige autorização judicial** em alguns casos. A hipótese, ainda a confirmar no diário de balcão, é que o RCPN gere mais dúvida real no balcão.

## 2. Base normativa lida no corpus antes de escrever qualquer regra

O CNJ 149/2023, Arts. 113 a 121, e o Código de Normas CGJ-CE, Arts. 255 a 262, têm redação quase idêntica. O CE acrescenta três regras próprias:
- Art. 437: registro com bloqueio judicial;
- Art. 468: qualquer pessoa pode pedir certidão sem informar motivo;
- Art. 471: informações de menção vedada na certidão de nascimento e procedimento judicial quando o pedido é de terceiro.

Os **27 trechos** usados como fundamento foram conferidos literalmente contra o corpus.

## 3. A tabela

| Pedido | Quem pede / fatos | Canal | Base |
|---|---|---|---|
| Breve relato | qualquer pessoa | **VERDE**, sem requerimento nem identificação | CNJ 113; CE 468; CE 256 |
| Óbito (qualquer modalidade) | qualquer pessoa | **VERDE** | CNJ 118; CE 259 |
| Busca nos índices | qualquer pessoa | **VERDE**, sem justificação | CNJ 121; CE 262 |
| Inteiro teor | próprio registrado, representante ou mandatário | **AMARELO**: requerimento escrito, sem juiz | CNJ 114 caput, 117 e 117 §3º; CE 255 e 258 |
| Inteiro teor | terceiro, sem dado sensível nem informação vedada | **AMARELO**: requerimento | CNJ 117; CE 258 |
| Inteiro teor | terceiro, dado sensível, registrado **vivo** | **VERMELHO**: só com autorização judicial | CNJ 114 §1º; CE 255 §1º |
| Inteiro teor | terceiro, dado sensível, registrado **falecido** | **AMARELO**: requerimento, sem juiz | CNJ 119; CE 260; CNJ 114 §2º |
| Inteiro teor | terceiro, informação de menção vedada (mesmo após o óbito) | **VERMELHO**: submeter ao juízo | CE 471 §2º e §3º |
| Quesitos ou informação avulsa | dados restritos, sensíveis ou sigilosos | mesmo tratamento do inteiro teor | CNJ 116; CE 257 |
| Procedimento preparatório | próprio interessado | **VERDE** | CNJ 120; CE 261 |
| Procedimento preparatório | terceiro, titular vivo | **VERMELHO**: autorização judicial (salvo documento público de publicidade irrestrita) | CNJ 120; CE 261 |
| Procedimento preparatório | terceiro, titular falecido | **AMARELO**: apresentar a certidão de óbito | CNJ 120 parágrafo único |
| Busca em outras fontes | qualquer pessoa | **AMARELO**: requerimento fundamentado, com análise de finalidade pelo Oficial | CNJ 121 parágrafo único; CE 262 parágrafo único |
| Qualquer pedido | registro bloqueado | **VERMELHO**: só com autorização judicial | CE 437 parágrafo único |

**VERMELHO no Registro Civil significa sempre "somente com autorização judicial".** Um teste percorre todas as 567 combinações (7 pedidos × 3 perfis de requerente × 27 combinações de resposta) de pedido, requerente e respostas e confirma que nenhum VERMELHO sai sem essa exigência. O sistema nunca recusa por conta própria.

**Se falta uma resposta** (dado sensível, informação vedada, óbito), o caso fica CONDICIONAL: a IA não é chamada e a tela mostra a pergunta. O sistema só pergunta o que muda o canal; o óbito, por exemplo, só é perguntado quando há dado sensível.

## 4. Documentos montados sem IA

| Documento | Quando | Conteúdo |
|---|---|---|
| Requerimento de certidão em inteiro teor | inteiro teor (AMARELO ou VERMELHO) | identificação, **motivo**, grau de parentesco, se o registrado é falecido, modalidade de assinatura (CNJ 117 §3º; CE 258 §3º) e, quando for o caso, aviso de **encaminhamento ao juízo** |
| Requerimento de busca em outras fontes | busca fora dos índices | fontes, fundamentação e finalidade (CNJ 121 parágrafo único) |
| Ficha de identificação e finalidade (RI, fase 2) | AMARELO do Registro de Imóveis | CE 1.128 §3º; CNJ 128 |

## 5. Integração

- **Pedido:** `PedidoBalcao` passa a ter `atribuicao` (RI ou RCPN) e as respostas do atendente.
- **Busca:** no Registro Civil a busca no corpus usa o filtro `{registro_civil, geral}`. A consulta é expandida com o vocabulário das normas do RCPN.
- **Prompt do Registro Civil:** especialidade, canais e vereditos próprios ("SUGESTÃO: SOMENTE COM AUTORIZAÇÃO JUDICIAL"). **O prompt do Registro de Imóveis não mudou** (snapshot igual).
- **Tela:**
  - escolha "Registro de Imóveis / Registro Civil das Pessoas Naturais";
  - perguntas do RCPN e opção de bloqueio judicial;
  - título "CANAL VERMELHO — Somente com Autorização Judicial";
  - download do requerimento.
- **Conferência na tela:** `AppTest` de ponta a ponta para o RCPN (terceiro, dado sensível, registrado vivo → VERMELHO judicial com requerimento) e de novo para o RI, sem exceção.
- **Suíte offline:** **215 testes**, todos passando.

## 6. O que continua dependendo do campo

- A **interpretação** das regras (sobretudo o que conta como dado sensível ou informação vedada num assento real) precisa do gabarito de um registrador civil. As perguntas do benchmark são de RI; é preciso **um conjunto de casos de Registro Civil** para o gabarito.
- O **diário de balcão** já separa RI e RCPN e vai dizer qual atribuição tem mais dúvida real.
