# Plano de produto depois da validação de 15/10/2026

> **Data:** 15/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> O parecer da validação é confidencial e fica fora deste repositório público. Aqui está só o plano que decorre dele.

## 1. Onde estamos

A validação manteve a proposta em **vermelho**. Ela reconhece um avanço: trocar o chat livre por uma ferramenta de fluxo com trilha de auditoria. A nota só muda com **evidência de campo**:
- gabarito jurídico validado por um registrador;
- volume real de dúvidas no balcão;
- teste contra as IAs que já são vendidas para cartórios.

Melhorar documentação ou interface, sozinho, não muda a nota.

## 2. Mapa dos concorrentes (fontes públicas dos fornecedores, 15/10/2026)

| Concorrente | Foco declarado | Triagem de pedido de certidão com regra + registro de quem pediu e para quê |
|---|---|---|
| AryaBolt | assistente jurídica no WhatsApp; "escrevente virtual" do cartório; gestão de prazos; módulo de Protesto | não anunciado |
| Sele IA | Web: Notas, Registro Civil, Protesto · Desktop: Imóveis, RTD/PJ; redação de escrituras, qualificação de títulos, extração de dados de matrícula | não anunciado |
| Notário IA | Notas e Imóveis; redige atos e opera dentro do Sistema Notário, com aceite humano | não anunciado |
| LegJur AI, Jurídico AI, Jus IA | IA jurídica geral | pergunta livre |
| ONR (certidão automática, IARI) | pedidos online de certidão no RI, sem intervenção humana | substitui parte do balcão no RI |

Os concorrentes diretos competem em **produzir atos** e em **atender pelo WhatsApp**. O espaço ainda não ocupado, que é hipótese até ser testado, é **aplicar a regra de publicidade a cada pedido de certidão e gerar o registro exigido pela norma**.

## 3. Diferenciais a construir

| # | Diferencial | Por que importa |
|---|---|---|
| D1 | **Motor de regras determinístico**: o canal é decidido por uma tabela escrita a partir da norma (tipo de pedido × requerente × dado), e o LLM só redige a minuta. Divergência entre o LLM e a regra vira INDEFINIDO | elimina a resposta contrária à norma, o maior risco apontado; mantém a decisão com o oficial |
| D2 | **Registro exigido pela norma pronto**: no RI, a ficha de identificação e finalidade (CE 1.128 §3º / CNJ 128); no RCPN, o requerimento de inteiro teor com os campos obrigatórios | é o que a correição cobra; nenhum concorrente anuncia |
| D3 | **Citações conferidas** (já existe: verificador v2) e **versão da norma visível** (já existe: barra lateral) | o oficial vê o que foi citado e de que versão |
| D4 | **Gabarito validado por registradores do CE** | a única barreira difícil de copiar |
| D5 | **Entrega como módulo/API** para os sistemas já instalados | evita disputar a base instalada dos concorrentes |

## 4. Fases

| Fase | Entrega | Situação |
|---|---|---|
| 1 | Instrumentos de campo: diário de balcão, roteiro de conversas, gabarito do registrador, avaliação com "respostas contrárias à norma"; concorrentes reais na coleta | **feita** (`df57bb5`, `21441dd`, `6eae027`) |
| 2 | D1 + D2 para o **Registro de Imóveis**: tabela de regras a partir do CE 1.128 e do CNJ 123–128 lidos no corpus; ficha do §3º como saída principal | **feita** (`bb5b951`, ver [relatório 19](19_relatorio_fase2_motor_regras.md)) |
| 3 | D1 + D2 para o **Registro Civil**: ler no corpus o CNJ 116–117 e os dispositivos do CE equivalentes antes de escrever qualquer regra; filtro por especialidade RCPN | **feita** (`3d69a1e`, ver [relatório 20](20_relatorio_fase3_registro_civil.md)) |
| 4 | Posicionamento: "assistente de conformidade"; README sem "multa da ANPD" nem enquadramento pela LAI; retificação dos docs 06/07 | **feita** (`9a47a38`, ver [relatório 21](21_relatorio_fase4_posicionamento.md)) |
| 5 | Campo: 5 conversas, diário de 1 semana em 3 cartórios, gabarito, coleta dos concorrentes; resubmissão ao funil | depende do proponente |

## 5. O que não fazer agora

- Construir interface nova ou publicar material de marketing.
- Testar com dados reais de certidões.
- Afirmar diferencial ou desempenho sem gabarito e teste.
- Escrever regra jurídica que não esteja no texto da norma do corpus.

## 6. Escolha da atribuição

A decisão fica com o diário de balcão, que já separa RI e RCPN. Hipótese de trabalho: no RI o caso comum é simples (identificação sem finalidade); no RCPN as regras de dado sensível e de inteiro teor tendem a gerar mais dúvida. Hipótese, não conclusão.
