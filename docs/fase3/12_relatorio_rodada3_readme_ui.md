# Relatório da 3ª rodada: README e interface alinhados ao código

> **Data:** 13/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Continuação de:** [11_relatorio_correcoes_rodada2.md](11_relatorio_correcoes_rodada2.md). O último push foi `6fd7fad`; todos os commits desde então estão **só locais**.

---

## 1. Commits desta rodada

| Commit | O que mudou |
|---|---|
| `65a8397` | **README alinhado ao código.** Saiu o exemplo `[CPF OMITIDO - ART. 1131 CGJ-CE]`. Os canais foram reescritos: Verde = identificação sem finalidade (CGJ-CE Art. 1.128 caput; CNJ 149 Art. 123); Amarelo = exigência prévia de identificação e finalidade, com ficha do §3º, sem tarja; Vermelho = nota devolutiva fundamentada (§4º). "Telefone" saiu do Vermelho. "Selo oficial" e "Carimbo Digital de Autenticidade" viraram "Hash SHA-256 de integridade do texto gerado. Não é assinatura digital nem certificação de autenticidade." O badge e a rubrica dizem "121 testes offline", sem "100%". O tarjador desativado entrou em Limitações conhecidas |
| `ff9a9a2` | **Textos da aba do Ato Pronto.** O painel de ajuda traz os canais do Art. 1.128. "Vinculante" virou "referenciada". "Proteção contra violações da LGPD…" virou "Apoio à decisão de balcão em Registro de Imóveis: publicidade registral, LGPD e LAI." Os títulos passaram a "Triagem de pedido" e "Exemplos frequentes", sem nenhuma "alfândega". O aviso "Sugestão de ato. A decisão e a responsabilidade são do Oficial Registrador." fica fixo no topo do painel, antes e depois de gerar |
| `aa67baf` | **Tema claro e sem emojis.** O `.streamlit/config.toml` passa a usar tema claro. Os emojis saíram de títulos, abas, expanders e botões; ficam 🟢🟡🔴 só onde aparecem com o nome do canal ao lado. O favicon virou ícone neutro, e as cores dos títulos dos canais foram escurecidas para atender WCAG AA |

---

## 2. Achados

### 2.1 Correção de número: a suíte offline tem 121 testes, não 125

O relatório 11 dizia "125 testes offline", e isso estava errado. A suíte completa tem 128 testes: 121 offline e 7 de rede. Os 7 de rede dependem da cota da Groq, e hoje 2 deles falham com 429.

### 2.2 Guarda do Art. 1.131 rodada sobre todo o repositório (79 arquivos versionados)

O README **não tem mais nenhuma ocorrência**. A guarda acusou 29 ocorrências fora dele, de três tipos:

| Tipo | Onde | Avaliação |
|---|---|---|
| **Uso invertido real** | `docs/fase3/06_entrega_radical_e_pensamento_divergente.md:94`: "Art. 17 da Lei 6.015 c/c Art. 1131, §10…" como fundamento | **Precisa corrigir.** É documento entregue à professora |
| Citação descritiva do erro | docs 08, 09, 10 e 11 | É registro de auditoria; manter |
| Resposta do modelo gravada | JSONs de `docs/fase3/benchmark/results/` | Alterar falsificaria o registro da execução; manter |

### 2.3 Contraste (WCAG AA, mínimo de 4,5:1)

| Par | Antes | Depois |
|---|---|---|
| Texto `#1F2328` sobre fundo `#FFFFFF` | — | 15,8:1 |
| Texto sobre painel `#F3F4F6` | — | 14,4:1 |
| Botão: branco sobre `#1F4E79` | — | 8,7:1 |
| Título do canal Verde | `#28a745`: 2,9:1 (falha) | `#1E6B34`: 6,1:1 |
| Título do canal Amarelo | `#e0a800`: 2,0:1 (falha) | `#7A5A00`: 6,1:1 |
| Título do canal Vermelho | `#dc3545`: 4,1:1 (falha) | `#A71D2A`: 6,7:1 |
| Título do canal INDEFINIDO | `#6c757d`: 4,2:1 (falha) | `#495057`: 7,4:1 |

### 2.4 Canal INDEFINIDO no tema claro

O teste usou `streamlit.testing.AppTest` com um pipeline falso, sem LLM e sem Chroma. Resultado:
- o rótulo "CANAL INDEFINIDO — Revisão Manual Necessária" aparece em cinza;
- a minuta e os dois downloads ficam desabilitados;
- o aviso de responsabilidade aparece antes e depois de gerar;
- não houve exceção.

---

## 3. Estado dos testes

| Grupo | Resultado |
|---|---|
| Suíte offline, commitada | **121 passando** |
| Guarda nova de UI (`tarj`, `suprim`, `supress`, `vinculante` em texto de interface), fora do commit | Os 2 testes que comprovam a guarda passam; a guarda em si **reprova 10 textos** e espera a decisão do item 4.1 |
| Testes de rede | 2 falham com 429 (cota diária da Groq) |

A guarda de UI lê os literais de string com `ast`. Ela ignora docstrings, comentários e identificadores (chaves de `session_state`, `key=`, variáveis de ambiente). "supress" entrou porque "suprim" não casa com "supressão".

---

## 4. Decisões pendentes (dependem do usuário)

### 4.1 Textos da UI que a guarda reprova ou que contêm os termos varridos

| Linha em `streamlit_app.py` | Texto | Termo |
|---|---|---|
| 381 | "Fundamentação Legal Vinculante" (expander) | vinculante |
| 166 | aba "Tarjador Inteligente & Hash SHA-256" | tarj |
| 418–516 | aba do tarjador, escondida pela flag: "Aplicar Tarjamento", "Dados Tarjados", "Baixar Matrícula Tarjada", "aplica supressões", "tarjará automaticamente" | tarj, supress, automático |
| 530 e 541 | "Auto (Detecção Automática)" | automático, neutro |
| 671 | "Verificação automática de citações: em desenvolvimento" | automático, neutro |

Para a aba do tarjador há três opções: (a) remover o bloco da UI; (b) marcar o bloco como exceção na guarda; (c) reescrever os textos.

Fora da UI ainda aparecem "alfândega" e "vinculante" no prompt do LLM (`ato_pronto.py:197`) e nas descrições dos campos (`ato_pronto.py:5, 68, 91`). O chat ainda diz "condicionado com tarjamento protetivo" (`pipeline.py:24`).

### 4.2 Datas do manifesto da barra lateral

O arquivo `data/corpus_manifest.json` foi criado e ainda não está exibido nem commitado. As datas vêm de `data/corpus_fase3/manifest.json`, e nenhuma foi digitada à mão; a conferência por script bateu nas 11 fontes.

| Norma | Data | Critério |
|---|---|---|
| Código de Normas CGJ-CE | 2026-09-11 | Last-Modified |
| Provimento 15/2026/CGJCE | 2026-09-11 | Last-Modified |
| Provimento CNJ 149/2023 | 2026-08-20 | Last-Modified |
| Lei 6.015/1973 | 2026-04-23 | Last-Modified |
| Lei 8.935/1994 | 2026-09-22 | Last-Modified |
| LGPD (Lei 13.709/2018) | 2026-04-23 | Last-Modified |
| LAI (Lei 12.527/2011) | 2026-04-23 | Last-Modified |
| Decreto 7.724/2012 | 2026-04-23 | Last-Modified |
| Resolução CD/ANPD 15/2024 | 2024-04-24 | data do ato, tirada da URL do DOU |
| Guia ANPD — Agentes de Tratamento | **data não identificada** | — |
| Guia ANPD — Segurança da Informação | **data não identificada** | — |

**Atenção:** Last-Modified é a data em que o servidor oficial atualizou o arquivo, lida no download de 23/09/2026. **Não é a data do ato nem da última alteração da norma.** Falta decidir se é essa a data a exibir.

### 4.3 README: divergências listadas e ainda não alteradas

| Linha | Texto | Problema |
|---|---|---|
| 6 | "Decisão Operacional" | o código entrega sugestão |
| 24 | "criamos um Tarjador Inteligente… com Carimbo Criptográfico" | o tarjador está desativado |
| 49, 78 | "Mata o chat", "Zero-UI de chat" | a aba de chat existe |
| 52–56 | caixa do tarjador e título "CARIMBO DIGITAL SHA-256 (Blindagem Regulatória)" | desativado |
| 65–68 | "< 0.05 segundos", "tarjas oficiais" | desativado; tempo não medido |
| 106 e 108 | duas linhas quase iguais sobre o tarjador | duplicadas |
| 116–137 | diagrama com 4 abas e tarjador ligado ao retriever | hoje são 3 abas; o tarjador não usa o retriever |
| 174, 208 | "43 passed", "43 testes" | são 121 |
| 207 | "4 abas" | são 3 por padrão |
| 221 | "CI/CD" | o único workflow (`auto_update.yml`) não roda o pytest |

### 4.4 Outros pendentes

- Doc 06, linha 94: falta definir o fundamento substituto, ou se basta remover o "c/c Art. 1131, §10".
- O logo colorido da barra lateral (`st.image` do icons8) depende do prompt da barra lateral.
- **Push** dos 10 commits locais, de `799700c` até este relatório.

---

## 5. Itens abertos que continuam

- O canal do semáforo ainda é decidido pelo LLM; a tabela de decisão fixa (CE 1.128 / CNJ 123–128) não foi feita.
- O `chroma_bundle.zip` (65 MB) continua versionado, e o material de cursinho continua no histórico do git.
- Validação pedida pela professora: gabarito 0/25, respostas de concorrentes 0/75, entrevistas 0.
