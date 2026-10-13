# Relatório da 5ª rodada: fechamento e push

> **Data:** 13/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Continuação de:** [13_relatorio_rodada4_chat_ui_manifesto.md](13_relatorio_rodada4_chat_ui_manifesto.md).
> **Push feito:** `6fd7fad..4c9df1e` em `main`, com 16 commits, todos de `idarlandias@gmail.com` e nenhum com co-autor.

---

## 1. Commits desta rodada

| Commit | Tarefa | O que mudou |
|---|---|---|
| `9d8b5bd` | A | No campo `artigo` (`ato_pronto.py`), o exemplo de citação deixou de ser "Art. 1131, §10" e passou a ser "Art. 1.128, §2º, IV". Era a última citação do 1.131 no código fora do comentário liberado pela guarda |
| `ba7c290` | B | `data/corpus_manifest.json` com 11 fontes e os campos `norma`, `baixado_em`, `versao_norma` e `criterio`, sem nada vindo do Last-Modified. Barra lateral com a seção "Normas consultadas" (nome, versão e critério em tooltip) e o aviso de vigência. O logo remoto do icons8 saiu. Chunks, corpus legado e caches foram para o expander "Diagnóstico técnico", fechado por padrão. Teste: falha com menos de 11 fontes ou com campo vazio |
| `4c9df1e` | C | Correções do README listadas no relatório 12, seção 4.3, e retificação do doc 06, linha 94, com nota de rodapé |

### 1.1 Desvios do texto pedido, com motivo

| Item | Pedido | Feito | Motivo |
|---|---|---|---|
| Contagem de testes no README | "129 testes offline" | **137** | A tarefa B acrescentou 8 testes; o badge e a rubrica também foram atualizados para 137 |
| Doc 06, linha 94 | remover só "c/c Art. 1131, §10" | removido também "do Código de Normas TJCE" | Sem isso, a frase ficaria "Art. 17 da Lei 6.015 do Código de Normas TJCE", o que é errado; o complemento pertencia à citação do 1.131 |
| `versao_norma` da Res. ANPD 15/2024 | texto da coluna do relatório 13 | "2024-04-24" | O trecho entre parênteses daquela coluna era o critério, que agora vai no campo `criterio` |
| Campo `norma` | nome completo | nome tirado do cabeçalho de cada documento | Para não inventar nomes. O do Código de Normas CE veio do Prov. 15/2026: "Código de Normas do Serviço Notarial e Registral do Estado do Ceará (Provimento nº 04/2023/CGJCE)" |

---

## 2. Fechamento

| Verificação | Resultado |
|---|---|
| Suíte offline | **137 passando** |
| Barra lateral, renderizada com `AppTest` | 11 normas, o aviso, o expander "Diagnóstico técnico" e nenhuma imagem; sem exceção |
| Guarda de UI (`src/ui`) | **limpa** |
| Guarda do 1.131 sobre o repositório (87 arquivos) | 31 ocorrências; nenhuma em `src/`, `tests/`, no README nem no doc 06 (ver 2.1) |
| `git status` | árvore limpa, nada em staging; `chroma_bundle.zip` intocado |

### 2.1 Onde estão as 31 ocorrências do 1.131

Todas estão em textos que **descrevem o erro** ou em **registros de execução**, não em uso do dispositivo como fundamento:
- docs 08 a 11 (auditoria; não alterar, por instrução);
- doc 12, linha 12, e o índice `docs/fase3/README.md`, linhas 26 e 29: descrevem a correção;
- JSONs de `docs/fase3/benchmark/results/`: respostas do modelo gravadas; alterá-los falsificaria a execução.

A guarda de UI aplicada a todo o `src/` (fora do escopo dela) acusa 4 linhas. Nenhuma é texto de interface:
- o validador do veredito (`ato_pronto.py:111/113`);
- a própria regra de proibição (`regras_prompt.py:8`);
- o módulo `tarjador.py`, mantido por decisão.

---

## 3. Pendências que sobraram (não alteradas por estarem fora do escopo pedido)

| Onde | Texto | Observação |
|---|---|---|
| README, linhas 61–65 | seção "Tarjador Inteligente & Carimbo Criptográfico SHA-256" ("o atendente cola o texto da matrícula…") | A aba foi retirada da UI e a seção ainda descreve o fluxo |
| README, linhas 50, 56, 131 | "Analogia da Alfândega" | O termo saiu da UI, mas segue no README |
| README, linha 208 | "tarjador.py # Tarjador de PII + Carimbo SHA-256" | descreve um arquivo que existe; pode ficar |
| Doc 06, linhas 93, 125 e 126 | "FORNECER COM TARJAMENTO", "DEFERIDO COM TARJAMENTO", "Fundamentação Vinculante" | documento de ideação entregue; só a linha 94 foi retificada |

---

## 4. Itens abertos de rodadas anteriores

- O canal do semáforo ainda é decidido pelo LLM; a tabela de decisão fixa (CE 1.128 / CNJ 123–128) não foi feita.
- O `chroma_bundle.zip` (65 MB) continua versionado, e o material de cursinho continua no histórico do git.
- Validação pedida pela professora: gabarito 0/25, respostas de concorrentes 0/75, entrevistas 0.

---

## 5. Protocolo dos pushes

Repositório `https://github.com/idarlandias/gov-legal-assistant-rag.git`, branch `main`.

| # | Intervalo | Commits | Commit no topo | Data do commit no topo | Conteúdo |
|---|---|:-:|---|---|---|
| 1 | `6fd7fad..4c9df1e` | 16 | `4c9df1eaebec7c5c59b1e025468802bde4b25bbe` | 2026-10-13 13:44:27 -0300 | 2ª a 5ª rodadas de correções, de `799700c` a `4c9df1e` |
| 2 | `4c9df1e..1381f31` | 1 | `1381f319248d571ceb29c691a8c101d648fc9c11` | 2026-10-13 13:45:57 -0300 | este relatório, sem a seção 5 |

| Conferência | Resultado |
|---|---|
| Autor de todos os commits | Idarlan Magalhaes <idarlandias@gmail.com>, sem co-autor |
| Hash local × remoto após o push 2 (`git ls-remote origin refs/heads/main`) | idênticos (`1381f31…`) |
| Staging antes dos pushes | vazio; `chroma_bundle.zip` intocado |
| Force push | não usado |

A inclusão desta seção 5 é um commit próprio, posterior ao push 2. O hash desse commit aparece no histórico do git (`git log`); ele não pode constar aqui porque é calculado a partir do próprio conteúdo do arquivo.
