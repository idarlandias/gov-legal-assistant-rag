# Relatório: pontuação da coleta e renomeação do produto (pré-execução)

> **Data:** 13/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Continuação de:** [14_relatorio_rodada5_fechamento.md](14_relatorio_rodada5_fechamento.md). Último push: `ad8aeea`.
> **Situação:** nenhuma alteração de código foi feita. As duas tarefas pararam antes da edição: a primeira por falta de dados, a segunda porque a instrução manda mostrar a classificação antes de editar.

---

## 1. Tarefa de pontuação da coleta: bloqueada por falta de dados

A tarefa pede para pontuar as respostas em `respostas_externas/`, com a camada 1 (existência da citação) na tabela comparativa e a camada 2 (ancoragem) em seção separada. Antes de escrever qualquer código, verifiquei se os dados existem:

| Premissa da tarefa | O que existe no repositório |
|---|---|
| Pasta `data/benchmark/respostas_externas/` com respostas coletadas | **Não existe**, nem versionada nem no disco. Também não existe em outro caminho |
| Respostas de Jus IA, Jurídico AI e LLM genérico | **0 de 75 coletadas**, como já constava dos relatórios 10 a 14 |
| Pergunta 26 | **Não existe**: `docs/fase3/benchmark/perguntas.json` tem 25 perguntas (ids 1 a 25) |
| Metodologia da coleta (sessão nova por pergunta, seed, data, sistemas sem acesso) | Não há registro de coleta realizada |
| Respostas do próprio RAG | Existem: `docs/fase3/benchmark/results/`, sendo a execução mais recente `rag-fase3-20261013-113528.json` (25 perguntas) |

**Risco de seguir assim:** a tabela comparativa sairia com três colunas "sem acesso", e a seção de Metodologia descreveria uma coleta que não aconteceu. Seria um registro falso.

### 1.1 Caminhos possíveis

| Opção | O que é feito | Observação |
|---|---|---|
| **A (recomendada)** | Construir agora o `scripts/pontuar_coleta.py`, o formato dos arquivos de resposta (com `sistema = "assistente_registral_ce"`, aceitando `"cartorioseguro"` na leitura) e o teste que reprova métrica de ancoragem na tabela comparativa. Rodar só com o RAG, a partir do JSON de 13/10 11h35; concorrentes como "não coletado" | A Metodologia sai como **protocolo a seguir**, não como coleta feita. A pergunta 26 fica como seção vazia até o texto dela ser fornecido |
| B | Aguardar as respostas coletadas e o texto da pergunta 26, e então fazer tudo de uma vez | Nada fica pronto antes da coleta |
| C | Adiar a tarefa até a coleta | — |

### 1.2 Desenho já definido para quando a tarefa rodar

- **Camada 1, existência:** cada citação extraída pelo mesmo extrator do verificador v2 é conferida contra o corpus inteiro (`data/corpus_fase3/dispositivos.jsonl`) e classificada como EXISTE, ARTIGO_INEXISTENTE_NA_NORMA ou NORMA_FORA_DO_CORPUS. Vale para os 4 sistemas e é a **única** camada da tabela comparativa.
- **Camada 2, ancoragem:** VERIFICADA / NAO_RECUPERADA contra os trechos recuperados. Só existe para o RAG, porque os concorrentes não expõem contexto, e vai em seção separada.
- **Teste de separação:** falha se a tabela comparativa contiver qualquer métrica de ancoragem.

---

## 2. Tarefa de renomeação: classificação das ocorrências

A busca cobriu todas as variantes (CartórioSeguro, CartorioSeguro, cartorioseguro, cartorio_seguro, CARTORIOSEGURO) em todo o repositório versionado: **16 ocorrências**.

### 2.1 Categoria (a): nome exibido ao usuário, a alterar (11 + 1)

| Arquivo:linha | Texto |
|---|---|
| README.md:1 | `# 🏛️ CartórioSeguro AI (gov-legal-assistant-rag)` |
| README.md:5 | `# 🏛️ CartórioSeguro AI` |
| README.md:30 | `[Acessar CartórioSeguro AI](…streamlit.app/)` |
| README.md:47 | `CARTÓRIOSEGURO AI` (caixa de funcionalidades) |
| README.md:62 | `No CartórioSeguro AI:` |
| README.md:71 | coluna `**CartórioSeguro AI (Fase 3)**` da matriz |
| src/ui/streamlit_app.py:65 | `page_title="CartórioSeguro AI — Balcão Registral & RAG Jurídico"` (aba do navegador) |
| src/ui/streamlit_app.py:116 | `st.title("CartórioSeguro AI")` (barra lateral) |
| src/ui/streamlit_app.py:157 | `st.title("CartórioSeguro AI")` (cabeçalho) |
| src/ui/streamlit_app.py:555 | coluna `**CartórioSeguro AI (Fase 3)**` da matriz da aba de benchmark |
| src/ui/streamlit_app.py:596 | rodapé `"CartórioSeguro AI · Desenvolvido na Residência SiDi…"` |
| src/ui/streamlit_app.py:1 | docstring do módulo. Não aparece na tela, mas descreve o produto; **proposta: tratar como (a)** |

### 2.2 Categoria (b): identificadores de código

**Nenhuma ocorrência.**
- A coleção do Chroma se chama `fase3`.
- As chaves de `session_state` não usam o nome.
- O slug do repositório e a URL do Streamlit Cloud são `gov-legal-assistant-rag`.

Nenhum identificador com o nome aparece na tela, então a troca não afeta o índice nem os caches.

### 2.3 Categoria (c): texto histórico, a manter (4)

| Arquivo | Ocorrências |
|---|:-:|
| docs/fase3/09_relatorio_para_analise.md | 2 |
| docs/fase3/10_relatorio_pos_correcoes.md | 1 |
| docs/fase3/11_relatorio_correcoes_rodada2.md | 1 |

Os docs 06, 07, 08 e 12 a 14 e os JSONs de `benchmark/results/` não contêm o nome.

### 2.4 Passo 6 (schema do campo "sistema")

O campo não existe, porque a pasta de coleta não existe. Se a opção A for aprovada, o formato será criado já com `assistente_registral_ce`, aceitando `cartorioseguro` na leitura. Isso iria no commit da pontuação, para que o commit da renomeação fique isolado, como pedido.

---

## 3. Decisões pendentes

1. Tarefa de pontuação: **opção A, B ou C**?
2. A classificação da renomeação está aprovada, **incluindo a docstring como (a)**?

Com as respostas, a renomeação sai em commit único. Depois vêm a suíte offline, o AppTest da UI e a confirmação de que o índice do Chroma continua carregando.
