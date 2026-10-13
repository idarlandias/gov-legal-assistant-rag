# Relatório: renomeação para Assistente Registral CE e pontuação em duas camadas

> **Data:** 13/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Continuação de:** [15_relatorio_pontuacao_e_renomeacao.md](15_relatorio_pontuacao_e_renomeacao.md). Último push: `ad8aeea`; os commits abaixo estão **só locais**.

---

## 1. Commits

| Commit | O que mudou |
|---|---|
| `795889b` | **Renomeação isolada.** As 12 ocorrências do nome exibido (categoria a) viraram "Assistente Registral CE" no README e na UI: `page_title`, os dois títulos, a matriz, o rodapé e a docstring. O README registra o nome antigo e o motivo da troca. Os docs 09 a 11 mantêm o nome antigo. Coleção do Chroma, chaves de `session_state`, slug do repositório e URL do Streamlit Cloud não mudaram |
| `b45b7cb` | **Opção A da pontuação.** Schema da coleta, pontuador em duas camadas, exportador, registrador, status da coleta, folha de perguntas, ordem de aplicação e o relatório de pontuação do RAG. Nenhum comparativo entre sistemas foi gerado |

### 1.1 Verificação da renomeação

- Suíte offline: passou.
- `AppTest` com o pipeline **real** (sem simulação): os dois títulos mostram "Assistente Registral CE", sem exceção nem erro.
- **O índice do Chroma carrega normalmente:** 4.359 chunks na coleção `fase3` e 6.507 no corpus legado.
- Ajustes de texto junto do nome:
  - `page_title`: "Assistente Registral CE — Ato Pronto de Balcão & Consulta Jurídica", para não repetir "Registral";
  - link do README: "Acessar o Assistente Registral CE";
  - caixa do README recentralizada.

---

## 2. Pontuação em duas camadas

### 2.1 Desenho

| Camada | O que mede | Contra o quê | Quem | Onde aparece |
|---|---|---|---|---|
| **1. Existência** | o artigo citado existe na norma citada | corpus inteiro (`dispositivos.jsonl`, 11 fontes, sem filtro de especialidade) | qualquer sistema | **única camada** permitida em saída comparativa |
| **2. Ancoragem** | o artigo estava entre os trechos recuperados | `trechos_recuperados` | só o RAG próprio | seção separada, nunca em comparativo |

As classes da camada 1 são EXISTE, ARTIGO_INEXISTENTE_NA_NORMA e NORMA_FORA_DO_CORPUS. O extrator é o mesmo do verificador v2.

Quando a citação **não declara a norma**, ela conta como EXISTE se o artigo existir em alguma norma do corpus. O total dessas citações é publicado à parte, como "sem norma declarada", para não inflar a classe EXISTE sem que isso apareça.

**Garantia da separação:**
- a tabela comparativa só aceita os campos de `CAMPOS_COMPARATIVOS`, todos de camada 1;
- um teste reprova qualquer termo de ancoragem nessa tabela;
- teste negativo: com o campo "verificadas" inserido de propósito na lista, **os dois testes de separação falharam**, como deveriam.

### 2.2 Resultado do RAG (execução de 13/10 11h35, 25 perguntas)

| Camada 1: existência | Valor |
|---|---|
| Citações de artigo | 55 |
| EXISTE | 52 (95%) |
| ARTIGO_INEXISTENTE_NA_NORMA | 2: #5 "Art. 1.103 do Provimento 15/2026/CGJCE" (o 1.103 é do Código de Normas); #25 "Art. 178 da LGPD" |
| NORMA_FORA_DO_CORPUS | 1: #14, Código Civil Art. 543 |
| Citações sem norma declarada | 14 |
| Respostas que citam norma estadual do CE | 13 de 25 |
| Respostas que citam o Prov. 15/2026 ou o Art. 1.103 | 2 |
| Recusas ou respostas sem dispositivo | 6 |
| Comprimento mediano | 172 palavras |

| Camada 2: ancoragem (só RAG) | Valor |
|---|---|
| VERIFICADA / NORMA_DIVERGENTE / NAO_RECUPERADA / FORA_DO_CORPUS | 47 / 1 / 6 / 1 (total 55) |
| Perguntas com ao menos uma citação ancorada | 18 de 25 |

A camada 2 reproduz exatamente o verificador v2 gravado na execução (47 de 55 e 18 de 25), e um teste confere isso. Detalhes em [pontuacao_rag_2026-10-13.md](pontuacao_rag_2026-10-13.md).

### 2.3 Ferramentas de coleta

| Arquivo | Função |
|---|---|
| `src/fase3/coleta.py` | Schema `RespostaColetada` (`pergunta_id`, `pergunta_texto`, `sistema`, `modelo_ou_plano`, `coletado_em` em ISO 8601 com -03:00, `resposta_integral`, `citacoes_declaradas`, `recusou_responder`, `observacao`). O texto da pergunta precisa ser idêntico ao oficial. `sistema` grava `assistente_registral_ce` e aceita `cartorioseguro` na leitura |
| `scripts/exportar_rag_coleta.py` | Converte uma execução do benchmark para o formato da coleta. As 25 respostas estão em `data/benchmark/respostas_externas/assistente_registral_ce/` |
| `scripts/registrar_resposta.py` | Grava resposta colada (de stdin ou arquivo), valida o schema, recusa sobrescrever sem `--force` e nunca trunca o texto. Só descarta o BOM do PowerShell/Notepad |
| `scripts/status_coleta.py` | Matriz sistemas × perguntas. Hoje: RAG 25/26 (falta a 26); Jus IA, Jurídico AI e LLM genérico com 0/26 |
| `data/benchmark/perguntas_coleta.md` | As 25 perguntas com texto idêntico ao `perguntas.json`, uma por bloco, e a 26 marcada como "externa ao benchmark". A 26 **não** foi adicionada ao `perguntas.json` |
| `data/benchmark/ordem_coleta.json` | Ordem de aplicação diferente por sistema, com seed 20261013 registrada no próprio arquivo e reproduzível (há teste) |

---

## 3. Desvios e observações

| Item | Observação |
|---|---|
| Campo extra `trechos_recuperados` | Não constava do schema definido. É opcional e só é aceito para o RAG próprio; sem ele a camada 2 não teria base |
| `dispositivos.jsonl` está no `.gitignore` | A camada 1 depende dele. Os testes da camada 1 usam um índice pequeno de exemplo, e o teste contra o corpus real é **pulado com aviso** quando o arquivo falta |
| Lei 6.015 compilada sem trechos revogados | Artigo revogado citado aparece como ARTIGO_INEXISTENTE_NA_NORMA (registrado nas limitações do relatório de pontuação) |
| Pergunta 26 no RAG | Ainda não respondida pelo RAG: rodá-la exige chamar a Groq, o que não foi pedido nesta etapa |
| Testes | A suíte offline passou de 137 para **165** testes (28 novos) |

---

## 4. Próximos passos

1. Coletar Jus IA, Jurídico AI e LLM genérico com `perguntas_coleta.md`, na ordem de `ordem_coleta.json`, usando `registrar_resposta.py`.
2. Rodar a pergunta 26 no RAG.
3. Com pelo menos dois sistemas coletados, gerar o comparativo (só camada 1) e a seção da pergunta 26.
4. Push dos commits locais (`e7933ce`, `795889b`, `b45b7cb` e este relatório), mediante autorização.
