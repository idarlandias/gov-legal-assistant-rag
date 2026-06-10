# Walkthrough — Assistente Jurídico RAG

Implementamos com sucesso a Skill do **Assistente Jurídico RAG** (`gov-legal-assistant-rag`) para a administração pública brasileira, utilizando o template estruturado do portfólio.

---

## 🛠️ 1. O que foi Implementado

### 1. Ingestão de Corpus e Downloads
* **`download_corpus.py` (Script de Download):** Criado para buscar os PDFs oficiais e legítimos da LGPD (Senado), Lei 14.133 (Senado) e o Guia de Transparência Ativa (CGU).
* **`ingest_and_index` (RAG Pipeline - TODO 1):**
  * Leitura e processamento de textos dos PDFs usando `pypdf`.
  * Classificação automática do domínio (`lgpd`, `licitacoes`, `transparencia` ou `procedimentos`) e preenchimento de metadados específicos para cada chunk de texto.
  * Indexação segura no **ChromaDB** em lotes de 90 chunks para respeitar os limites de requisições do Gemini.
  * Suporte para subdiretórios recursivos via `rglob` para capturar os manuais de procedimentos em `data/corpus/procedimentos/`.

### 2. Retrieval & Generation com Filtro
* **`retrieve` (TODO 2):** Implementado suporte para buscas semânticas tradicionais e filtragem opcional via metadados por domínio (`where={"dominio": ...}`).
* **`answer` (TODO 3):** Implementado o fluxo principal de RAG (Retrieve + Augment + Generate) usando prompt de ancoragem estrita e citations.

### 3. Ferramentas de Domínio & Function Calling
* **`tools.py` (TODO 4):**
  * `cite_lgpd_article` e `cite_14133_article`: Ferramentas que consultam diretamente o ChromaDB pelo texto oficial exato do artigo solicitado para evitar alucinações de numeração de lei.
  * `simular_enquadramento`: Regra de decisão determinística baseada no Art. 75 da Lei 14.133 para verificar dispensa por valor.
  * `build_transparency_link`: Gerador dinâmico de links para pesquisas com filtros de ano e função orçamentária no Portal da Transparência.
  * `listar_documentos`: Refatorada de expressões regulares rígidas para um **mini-pipeline de extração estruturada via LLM (Gemini Flash-Lite)**. A ferramenta agora faz a busca vetorial no domínio `procedimentos`, consolida os trechos mais relevantes do manual e envia para o Gemini Flash-Lite extrair e organizar um JSON com a lista de requisitos de documentos (indicando obrigatoriedade). Isso tornou o sistema robusto contra mudanças de formatação nos manuais públicos de produção real.
* **Function Calling Loop (TODO 3 - Integração):** O pipeline agora detecta chamadas de ferramentas geradas pelo modelo Gemini, executa-as via `run_tool_call`, injeta o retorno no histórico e devolve a resposta final consolidada ao usuário.

### 4. Otimização de Custo & Latência
* **`SemanticCache.get` (TODO 5):** Cache semântico usando similaridade de cosseno nos embeddings das queries de entrada. Retorna respostas instantâneas e gratuitas para consultas semanticamente parecidas (acima de `0.93` de similaridade).
* **`classify_complexity` (TODO 6):** Roteamento inteligente de modelos (cheap-first) que analisa complexidade (tamanho de texto e palavras-chave específicas) para direcionar queries simples ao `gemini-2.5-flash-lite` (mais barato) e consultas robustas ao `gemini-2.5-pro` (premium).

### 5. Streamlit UI
* **`streamlit_app.py`:** 
  * Customização completa do título, pitch e ícone do app focados na administração pública.
  * Dropdown para seleção de domínio de interesse (Auto, LGPD, Licitações, Transparência, Procedimentos Internos).
  * Conversão integral do layout para uma **Interface de Chat** interativa (`st.chat_message` + `st.chat_input`), mantendo total compatibilidade com o pipeline RAG.
  * Adição de blocos de contexto informativo e botões rápidos com atalhos de consulta com exemplos para os 4 domínios (LGPD, Licitações, Transparência e Procedimentos Internos).
  * Exibição das fontes citadas e informações sobre as chamadas de ferramentas.

### 6. Encapsulamento com Docker
* **`Dockerfile` & `.dockerignore`:** Criados na raiz do repositório para isolar e empacotar toda a aplicação e suas dependências de produção de forma portátil e limpa, permitindo injeção dinâmica da chave de API e build rápido via `uv`.

---

## 🔬 2. Resultados da Verificação

Rodamos os testes automatizados com sucesso na raiz do projeto após a refatoração:

```bash
uv run pytest
```

### Log de Saída do Pytest:
```text
tests\test_smoke.py ...                                                  [100%]
======================= 3 passed, 2 warnings in 10.03s ========================
```
* **test_pipeline_indexa_chunks:** Passou (leitura e indexação corretas no banco Chroma).
* **test_retrieve_top_k:** Passou (retrieval de chunks similares validado).
* **test_answer_retorna_resposta_com_fonte:** Passou (geração de resposta ancorada e citação de fontes OK).

---

## 🔒 3. Segurança & Observabilidade Consolidadas

1. **Gestão Segura de Chaves**:
   * O módulo `src/pipeline/security_skill.py` foi estabelecido como a única fonte para segredos usando a função `get_env_secret`.
   * Atualizamos o pipeline de RAG (`rag.py`), o cache semântico (`cache.py`) e a classificação de rotas (`routing.py`) para consumir chaves de forma centralizada e resiliente a falhas.
2. **Mitigação de Prompt Injection**:
   * Centralizado no método `build_secure_prompt` que higieniza e ancora as instruções passadas para o LLM.
3. **Resolução de Bugs em Logs de Observabilidade**:
   * Corrigimos um bug silencioso no context manager de `trace.py`, onde as chaves desempacotadas de kwargs geravam conflito de duplicação do parâmetro `trace_id` (lançando `TypeError`). A chamada foi isolada de forma defensiva limpando o dicionário de kwargs.
4. **Logs Estruturados**:
   * O `streamlit_app.py` agora emite no terminal logs claros e estruturados do domínio selecionado e do roteamento do modelo de forma assíncrona.

---

## 🎓 4. Extensão: Domínio Concursos Públicos (Tutor Didático)

Adicionamos com sucesso o suporte ao novo domínio **`concursos`** para funcionar como um assistente de estudos a partir de apostilas e aulas preparatórias em PDF.

### O que foi desenvolvido nesta extensão:
* **Ingestão Inteligente por Pasta (`rag.py`):** Estendemos o processador do RAG para identificar e inferir o domínio `concursos` a partir da estrutura de pastas `data/corpus/concursos/` e classificar o tipo de documento como `apostila`.
* **Prompt com Foco Didático e Direitos Autorais (`security_skill.py`):** Criamos a função `build_concursos_prompt`. O prompt instrui a IA a agir como um tutor acolhedor e conciso (respostas de 2 a 5 frases), proíbe a cópia verbatim de blocos muito longos de texto (respeito a direitos autorais) e aplica a ancoragem estrita (retornando `"Não encontrado no corpus de estudos"` se a resposta não estiver nos PDFs fornecidos).
* **UI com Sugestões Rápidas (`streamlit_app.py`):** Adicionamos a opção *"Concursos públicos"* no seletor de domínios, com textos informativos específicos e atalhos rápidos para perguntas sugeridas sobre atos/fatos contábeis e situação líquida patrimonial.
* **Testes de Isolamento e Validação (`tests/test_domains.py`):** Criamos um novo arquivo de testes que valida no framework `pytest` se as buscas de cada domínio estão isoladas do ChromaDB e se as regras de ancoragem do tutor estão operacionais.

### 🔬 Resultados dos Testes de Integração Atualizados:
Rodamos a suíte de testes completa, validando 100% de sucesso nos domínios novos e antigos:
```bash
uv run pytest tests/ -v
```

**Log do console:**
```text
tests/test_domains.py::test_isolamento_dominio_lgpd PASSED              [ 14%]
tests/test_domains.py::test_isolamento_dominio_licitacoes PASSED        [ 28%]
tests/test_domains.py::test_concursos_resposta_negativa_fora_de_escopo PASSED [ 42%]
tests/test_domains.py::test_concursos_comportamento_didatico_se_tiver_dados PASSED [ 57%]
tests/test_smoke.py::test_pipeline_indexa_chunks PASSED                  [ 71%]
tests/test_smoke.py::test_retrieve_top_k PASSED                          [ 85%]
tests/test_smoke.py::test_answer_retorna_resposta_com_fonte PASSED       [100%]

============================== 7 passed in 7.02s ==============================
```





