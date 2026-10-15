# Relatório: fase 2, motor de regras do Registro de Imóveis

> **Data:** 15/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Continuação de:** [18_plano_produto_pos_validacao.md](18_plano_produto_pos_validacao.md). Commit `bb5b951` (local). Último push: `5a71b20`.

## 1. O problema que a fase resolve

A validação de 15/10 apontou como maior risco a ferramenta **recomendar algo contra a norma**: tarjar a certidão de matrícula ou exigir motivo de quem pede. Até aqui, quem escolhia o canal era o LLM, e o prompt só tentava evitar o erro. Agora **o canal sai da norma**.

## 2. Como funciona

| Etapa | O que acontece |
|---|---|
| 1. Regra | `src/fase3/regras_ri.py` consulta a tabela (tipo de pedido × perfil de quem pede) e devolve canal, exigências e fundamentos com o **texto literal** do dispositivo |
| 2. CONDICIONAL | Quando a norma depende de um fato, a UI pergunta ao escrevente. Ex.: "há previsão legal de arquivamento do documento?". Sem resposta, nada é decidido e a IA não é chamada |
| 3. Redação | A IA recebe o canal já decidido e só redige veredito, instrução e minuta |
| 4. Conferência | Se a IA devolver outro canal, o resultado vira **INDEFINIDO** e a minuta é descartada; decide o Oficial |
| 5. Ficha | Quando a finalidade é exigida, o sistema monta, sem IA, a **ficha de identificação e finalidade** (CE 1.128 §3º / CNJ 128) para imprimir |

## 3. A tabela (todas as 10 opções da UI)

| Tipo de pedido | Canal | Base (trecho literal no sistema) |
|---|---|---|
| Certidão de inteiro teor de matrícula (qualquer requerente identificado) | **VERDE**, sem finalidade | CE 1.128 caput; CNJ 123 caput; CE 1.131 §10 (reproduz todo o conteúdo) <!-- guarda-1131: ok --> |
| Certidão de situação jurídica atual | **VERDE** | CE 1.128 caput; CE 1.129; CNJ 125 |
| Busca por indicador pessoal (CPF/nome) | **AMARELO** + ficha | CE 1.128 §2º IV; CNJ 126 |
| Informação verbal, por terceiro | **AMARELO** + ficha | CE 1.128 §2º V; CNJ 127 |
| Informação verbal, pelo titular | **VERDE** (exceção de quem figura no registro) | CE 1.128 §2º V, parte final; CNJ 127 |
| Acesso em lote / convênio | **AMARELO** + ficha + alertas | CE 1.128 §2º II; CNJ 123 §3º; CNJ 124 |
| Documento arquivado | **CONDICIONAL**: com previsão de arquivamento, VERDE; sem previsão, AMARELO | CE 1.128 §1º e §2º I; CNJ 123 §1º e §2º |
| Histórico / cadeia filiatória | **CONDICIONAL**: atos anteriores, AMARELO; matrícula atual, VERDE | CE 1.128 §2º III; CNJ 125 parágrafo único |
| Exclusão de dados (LGPD), retificação, órgão público sem ordem | **SEM_REGRA**: sugestão da IA, marcada na tela | nenhum dos artigos acima cobre o caso |

**A tabela nunca devolve VERMELHO.** A recusa é decisão do Oficial em nota fundamentada (CE 1.128 §4º; CNJ 123 §4º), e o sistema só alerta para essa possibilidade.

Marcar CPF ou regime de bens **não muda o canal** da certidão de matrícula. O sistema avisa que o inteiro teor reproduz todo o conteúdo e, se o requerente quiser conteúdo reduzido, sugere a certidão de situação jurídica atual.

## 4. Garantias (testes)

- **Trechos literais:** os 22 trechos da norma são conferidos contra o corpus, ignorando só acentos, espaços e pontuação. Na prova negativa, um trecho inventado foi reprovado.
- **Tabela completa:** cobre todas as opções da UI e nenhuma regra devolve VERMELHO.
- **Caso central da validação:** terceiro sem vínculo pedindo inteiro teor de matrícula com CPF marcado dá **VERDE, sem exigir finalidade**.
- **IA divergente:** vira INDEFINIDO, sem minuta.
- **Casos condicionais:** sem resposta, não chamam nem a busca nem a IA.
- **Ficha:** traz os campos a preencher, os artigos e o direito do titular de consultá-la (CNJ 128, parágrafo único).
- **UI:** `AppTest` de ponta a ponta mostrou o painel da regra, a ficha para baixar e a pergunta condicional.
- **Suíte offline:** **194 testes**, todos passando.

## 5. O que a fase não resolve

- O **acerto jurídico da tabela** ainda depende do **gabarito do registrador** (`data/validacao/gabarito_modelo.csv`). A tabela é transcrição fiel dos artigos, mas a interpretação, como o enquadramento de cada opção da UI, precisa ser validada.
- Os três tipos SEM_REGRA continuam com o LLM decidindo.
- O Registro Civil é a fase 3: primeiro ler no corpus o CNJ 116–117 e os dispositivos do CE equivalentes.
