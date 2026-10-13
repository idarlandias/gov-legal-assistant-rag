# Relatório pós-correções: CartórioSeguro AI (Fase 3)

> **Data:** 13/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Repositório:** https://github.com/idarlandias/gov-legal-assistant-rag
> **Continuação de:** [09_relatorio_para_analise.md](09_relatorio_para_analise.md) (auditoria) e [08_revisao_2026-10-13.md](08_revisao_2026-10-13.md).
> Este documento se basta: traz o que foi corrigido, os números medidos depois das correções e o que ainda está aberto.

---

## 0. O que se pede ao analista

1. Conferir se as correções da seção 2 resolvem os achados da auditoria (seção 1) ou só os escondem.
2. Avaliar se as métricas da seção 3 são confiáveis e o que elas **não** medem.
3. Priorizar os itens abertos da seção 5 até a resubmissão ao funil da professora (lacunas: *unfair advantage* concreta, evidência de fricção, validação com cartórios e concorrentes).

Restrição: não inventar normas. Toda afirmação jurídica deve vir do texto da seção 6 ou ser marcada "A CONFIRMAR COM OFICIAL/DPO".

---

## 1. Resumo da auditoria anterior (relatório 09)

| Achado | Gravidade |
|---|---|
| Tarjador e prompt do Ato Pronto citavam o **Art. 1.131 §10 do Código de Normas CGJ-CE** para omitir CPF; o §10 diz que a certidão de inteiro teor "conterá a reprodução de todo seu conteúdo" | Crítico |
| O fallback do Ato Pronto escolhia o canal (inclusive VERDE) por palavra-chave quando o JSON do LLM falhava | Crítico |
| README e app com métricas não medidas ("3,2 s / -93%", "-98% custo", "100% aderência") | Alto |
| Rótulo das fontes sem o nome da norma ("Art. 19:p0"), com numeração colidente entre 11 normas | Alto |
| Nenhuma verificação das citações do LLM (ex.: "Art. 1128" atribuído à Lei 6.015) | Alto |
| Resposta vazia do gpt-oss-20b contada como "respondida" no benchmark | Médio |

---

## 2. Correções aplicadas (8 commits, 13/10/2026)

| Commit | O que mudou |
|---|---|
| `3401a71` | README e app: métricas não medidas trocadas pelos números do benchmark; nova seção "Hipóteses não validadas" |
| `5623c00` | Ato Pronto: falha de rede, JSON ou schema vira **canal INDEFINIDO** ("FALHA NA ANÁLISE — REVISÃO MANUAL NECESSÁRIA"), sem fundamentação nem minuta; busca vazia não chama o LLM; UI cinza com botões desabilitados |
| `7469a81` | Tarjador sem nenhuma citação ao Art. 1.131: marcação neutra "[DADO SUPRIMIDO POR DETERMINAÇÃO DO OFICIAL]"; carimbo só com supressão, e com aviso "Hash SHA-256 de integridade… Não é assinatura digital nem certificação de autenticidade"; prompt sem o exemplo do inteiro teor com CPF nem a "informação verbal por telefone"; aba do tarjador escondida (`MOSTRAR_ABA_TARJADOR=false`); teste de grep que impede o 1.131 junto de omissão |
| `f67f244` | Rótulo "<norma> — <dispositivo>" no contexto do LLM, nas fontes, no Ato Pronto e no benchmark ("NORMA NÃO IDENTIFICADA" se faltar a norma); funciona no índice atual pelo `fonte_id`, sem reindexar |
| `848e955` | **Verificador determinístico de citações** (sem LLM): cada "Art. N" da resposta vira VERIFICADA, NORMA_DIVERGENTE ou NAO_RECUPERADA contra os trechos recuperados; taxa no benchmark, aviso na UI |
| `26168ce` | Resposta vazia (`finish_reason="length"` ou só espaços): **uma** nova tentativa com gpt-oss-120b e `max_tokens=8192`; se falhar de novo, `RespostaVaziaError` e status RESPOSTA_VAZIA; benchmark separa RESPONDIDA / NAO_ENCONTRADO / RESPOSTA_VAZIA / ERRO |
| `47a6adb` | Verificador: corrige falsos positivos de "norma divergente" (herança de norma só de títulos; norma entre parênteses após o artigo; "CNJ" isolado = Prov. 149) |
| (este) | Benchmark re-pontuado, planilha e relatórios 08, 09 e 10 |

Testes: **96, todos passando** (eram 43 antes da auditoria).

---

## 3. Números medidos

### 3.1 Evolução no benchmark (25 perguntas de balcão, gpt-oss-20b/120b via Groq, mesmo roteamento do app)

| Execução | Respondidas | "Não encontrado" | Respostas vazias | Latência média | Tokens entrada / saída |
|---|---:|---:|---:|---:|---:|
| Fase 2 (RAG horizontal), 23/09 | 5 | 20 | 0 | 6,8 s | 45 mil / 7 mil |
| Fase 3 híbrido sem filtro, 23/09 | 16 | 8 | 1 | 9,2 s | 53 mil / 18 mil |
| Fase 3 + filtro RI, 13/10 10h10 | 19 | 5 | 1 | 7,6 s | 39 mil / 23 mil |
| Fase 3, 13/10 11h13 (antes da nova tentativa) | 16 | 5 | **4** | 8,6 s | 40 mil / 27 mil |
| **Fase 3, 13/10 11h35 (nova tentativa + verificador)** | **19** | **6** | **0** | **7,5 s** | 42 mil / 24 mil |

- As respostas vazias eram todas do gpt-oss-20b batendo exatamente em 2.048 tokens de saída. Antes do `26168ce`, elas contavam como "respondidas".
- Na execução das 11h35, a nova tentativa disparou uma vez (#18) e o 120b respondeu.
- **"Não encontrado" (6):** #2, #6, #7, #10, #11, #17.
- **Custo medido:** cerca de R$ 0,0045 por pergunta (preço do 120b como teto, câmbio 5,50).

### 3.2 Verificação de citações (execução das 11h35, re-pontuada com o verificador **v2**)

| Métrica (verificador v2) | Valor |
|---|---|
| Citações distintas (artigo + norma) | 55 |
| VERIFICADA | **47** → **taxa_verificavel = 85%** (sobre citações) |
| **cobertura_fundamentada** | **18/25 = 72%** (perguntas com ao menos 1 citação verificada ÷ total de perguntas) |
| NORMA_DIVERGENTE | 1 |
| NAO_RECUPERADA (falha de recuperação) | 6 |
| FORA_DO_CORPUS (norma inexistente no corpus) | 1 (#14, Código Civil Art. 543) |
| Perguntas sem nenhuma citação | 6 |

> Toda taxa de citações depende das regras do verificador; este documento usa a **v2** (`VERIFICADOR_VERSAO` em `src/fase3/verificador_citacoes.py`).

**Não verificadas:**
- #25: "Assegurar a conformidade com a LGPD (Art. 178)". O 178 recuperado é do Código CGJ-CE, e a LGPD tem 65 artigos → **NORMA_DIVERGENTE**.
- #4: LGPD Art. 7; #19: LGPD Art. 18 → artigos citados sem estarem nos trechos recuperados.
- #14: Código Civil Art. 543 → norma fora do corpus.
- #5 e #23: Art. 1.103, que é do Código CE (o Provimento 15/2026 o alterou), mas não veio entre os trechos recuperados; #23: Art. 817.

**Por que a execução foi re-pontuada.** Ela foi gravada com o verificador do `848e955`, que acusava 4 "normas divergentes", 3 delas falsos positivos do próprio verificador. Uma nova execução bateu no **limite diário da Groq** (200 mil tokens/dia no gpt-oss-20b; erro 429 em 13 de 25 perguntas) e foi descartada. A re-pontuação é determinística e sem LLM: são as **mesmas respostas**, com os trechos reconstruídos dos rótulos "Norma — Art. N:pP" gravados (`results/rag-fase3-20261013-113528-reverificado.json`; o original fica ao lado).

### 3.3 O que essas métricas NÃO medem

- **"Respondida" ≠ "correta".** Não há gabarito validado por oficial ou DPO. As notas da rubrica estão em branco.
- **"VERIFICADA" só diz** que o artigo citado estava nos trechos recuperados, atribuído à mesma norma. Não diz que o artigo afirma o que a resposta diz.
- **Concorrentes:** as respostas do Jus IA, do Jurídico AI e de um LLM genérico continuam sem coleta (0 de 75).

---

## 4. Riscos operacionais descobertos

- **Limite da Groq:** 200 mil tokens/dia no gpt-oss-20b. Uma execução completa do benchmark gasta cerca de 65 mil tokens, ou seja, umas 3 execuções por dia, já contando o uso do app. Para demonstração ao vivo ou teste com cartórios, isso é um ponto único de falha.
- **Ato Pronto:** com resposta vazia, a função ainda repete a chamada sem `response_format`. Pode chegar a 4 chamadas antes de virar INDEFINIDO.
- **Chat da Fase 2** (coleção `docs`): `RespostaVaziaError` aparece como erro na tela (antes era texto vazio silencioso).

---

## 5. Itens ainda abertos (da auditoria 08/09)

| # | Item | Situação |
|---|---|---|
| 1 | **Canal do semáforo ainda decidido pelo LLM.** Proposta: tabela de decisão fixa baseada no CE Art. 1.128 e no CNJ 149 Arts. 123–128 (seção 6), com o LLM só redigindo a minuta | Não iniciado |
| 2 | Prompt do Canal AMARELO ainda define "TARJAMENTO OBRIGATÓRIO de dados pessoais excessivos" (sem norma que sustente a tarja no inteiro teor) | Aberto |
| 3 | Tarjador: "titular" por substring (falha aberta), filiação não detectada, CPF sem dígito verificador | Aberto (aba escondida) |
| 4 | Busca do Ato Pronto: a consulta é a concatenação dos rótulos da UI; o CNJ 123 e o CE 1.128 nem sempre vêm. Uma consulta com vocabulário da norma ("certidão de matrícula identificação do requerente finalidade") os trouxe no top 5 | Aberto |
| 5 | Teste `test_ato_pronto_output_model_validate` ainda usa payload com "Art. 1131, §10" e aplicação inventada | Aberto |
| 6 | `data/chroma_bundle.zip` (65 MB) versionado no git; material de cursinho ainda no histórico | Aberto |
| 7 | README ainda tem afirmações não medidas fora da lista corrigida ("Tarjador inédito", "R$ 150–500/mês" dos concorrentes, "Nenhum assistente jurídico no Brasil…") | Aberto |
| 8 | **Validação pedida pela professora:** gabarito (0/25), concorrentes (0/75), entrevistas com cartórios (0) | **Não iniciado. É o que destrava o Gate 1** |

---

## 6. Normas-chave (texto do corpus oficial)

- **CE Art. 1.131, §10:** "No âmbito do registro de imóveis, a certidão de inteiro teor da matrícula conterá a reprodução de todo seu conteúdo e será suficiente para fins de comprovação de propriedade, direitos, ônus reais e restrições sobre o imóvel, independentemente de certificação específica pelo Oficial."
- **CE Art. 1.128:**
  - **caput:** qualquer pessoa identificada pode requerer certidão, independentemente de finalidade;
  - **§2º I–V:** dependem de identificação **e finalidade**: documento arquivado sem previsão de expedição; pedidos em bloco; cadeia dominial; busca por indicador pessoal ou real; informação fora de certidão (salvo se o solicitante figurar no registro);
  - **§3º:** fichas de identificação e finalidade, que o titular pode requisitar;
  - **§4º:** recusa em nota fundamentada quando o tratamento contraria as finalidades do RI e a LGPD.
- **Provimento CNJ 149/2023:**
  - **Art. 123:** identificação, sem finalidade, para certidões;
  - **Art. 124:** vedadas certidões com dados pessoais de mais de uma matrícula, salvo previsão;
  - **Art. 125:** certidão da situação jurídica atual, sem finalidade; cadeia filiatória exige finalidade;
  - **Art. 126:** busca por indicador pessoal ou real exige identificação segura e finalidade;
  - **Art. 127:** informação fora de certidão exige identificação e finalidade, salvo quem figura no registro;
  - **Art. 128:** prontuários de identificação e finalidade; o titular pode requisitá-los.
- **Lei 6.015/1973, Art. 17:** "Qualquer pessoa pode requerer certidão do registro sem informar ao oficial ou ao funcionário o motivo ou interesse do pedido."

---

## 7. Perguntas abertas para o analista

1. As correções 2.1–2.7 eliminam o risco jurídico ou só o escondem? (ex.: a aba do tarjador escondida vs. corrigida)
2. A taxa de 85% de citações verificadas (verificador v2; cobertura fundamentada de 72% das perguntas) é um indicador defensável perante a auditoria cética, sabendo que ela não mede a correção do conteúdo?
3. Com o limite de 200 mil tokens/dia da Groq, qual é a estratégia de infraestrutura para o teste com 3 cartórios (outro provedor, cache, modelo local)?
4. Vale implementar a tabela de decisão (item 5.1) antes da validação com cartórios, ou validar primeiro com o produto atual?
5. Qual é o menor conjunto de evidências que preenche as 4 lacunas do parecer da professora em 2 a 3 semanas?
