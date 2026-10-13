# Relatório da 2ª rodada de correções: CartórioSeguro AI (Fase 3)

> **Data:** 13/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Continuação de:** [10_relatorio_pos_correcoes.md](10_relatorio_pos_correcoes.md). O último push foi `6fd7fad`; os commits abaixo estão **só locais**.
> Este documento registra o que mudou depois do relatório 10, os números atuais e o que depende de decisão.

---

## 1. Commits desta rodada

| Commit | O que mudou |
|---|---|
| `799700c` | **Canal AMARELO redefinido:** fornecimento mediante EXIGÊNCIA PRÉVIA (identificação do requerente e indicação da finalidade, CE Art. 1.128 §2º I–V, com abertura da ficha do §3º), sem tarja. Regra explícita no prompt proibindo suprimir dados do inteiro teor e indicando a certidão de situação jurídica atual (CNJ 149, Art. 125) como alternativa. Vereditos viram "SUGESTÃO: DEFERIR / DEFERIR MEDIANTE EXIGÊNCIA PRÉVIA / INDEFERIR (NOTA DEVOLUTIVA)"; veredito com tarja vira INDEFINIDO. Aviso fixo na UI: "Sugestão de ato. A decisão e a responsabilidade são do Oficial Registrador." Snapshot do prompt em teste |
| `abd3c79` | **Consulta do Ato Pronto expandida:** dicionário explícito para as 10 opções da UI, com o vocabulário das normas; top-k de 5 para 8; log da consulta e dos trechos recuperados. A regressão roda no índice real |
| `c3e47a9` | **Guarda do Art. 1.131 ampliada** para `src/` e `tests/`, por linha ou bloco, com termos de omissão e de restrição. Payload de teste com fundamento inventado substituído por um caso correto |
| `716810c` | **README e UI sem afirmações de mercado sem fonte** (passam a "não medido", com método de validação em "Hipóteses não validadas"); nova seção "Limitações conhecidas" |
| `30f6ba7` | **Verificador de citações versionado (v2)**, categoria FORA_DO_CORPUS, métrica cobertura_fundamentada, entrada agnóstica à origem (dicts, tuplas ou rótulos), `--reverificar` sem LLM |

---

## 2. Achados relevantes desta rodada

### 2.1 Recuperação do Ato Pronto (medido no índice real)

| Consulta | CNJ 149 Art. 123 no top-k | CE Art. 1.128 no top-k |
|---|:-:|:-:|
| Concatenação dos rótulos da UI (antes), k=5 | não | não |
| Concatenação dos rótulos da UI (antes), k=8 | não | não |
| **Expansão normativa (agora), k=8** | **sim** | **sim** |

Caso de teste: "Certidão de Inteiro Teor de Matrícula", solicitante "Terceiro sem comprovação de vínculo ou interesse jurídico". O teste roda contra o índice real e, se o índice ou o modelo não estiverem disponíveis, é **pulado com aviso explícito**, não aprovado em silêncio.

### 2.2 Por que a guarda do 1.131 não pegava o payload de teste

Eram duas causas somadas:
1. A guarda só varria `src/fase3`.
2. O payload usava o §10 para **vedar** ("Veda o fornecimento…", INDEFERIDO), e não para omitir.

O teste negativo mostrou que **só com as palavras omit, tarj, suprim e CPF, a guarda continuaria cega** a esse payload. Por isso foram incluídos termos de restrição (veda, recusa, indefere). O §10 manda reproduzir todo o conteúdo, então nunca sustenta restrição.

### 2.3 Verificador de citações v2 (re-pontuação sem LLM da execução de 13/10 11h35)

| Métrica (verificador v2) | Valor |
|---|---|
| **taxa_verificavel** (sobre citações) | **47/55 = 85%** |
| **cobertura_fundamentada** (perguntas com ≥1 citação verificada ÷ 25 perguntas) | **18/25 = 72%** |
| NORMA_DIVERGENTE | 1 (#25, "LGPD (Art. 178)", sendo o 178 do Código CE) |
| NAO_RECUPERADA (falha de busca) | 6 |
| FORA_DO_CORPUS (norma inexistente no corpus) | 1 (#14, Código Civil Art. 543) |

As duas métricas medem coisas diferentes. A taxa diz se o que foi citado estava ancorado no contexto. A cobertura diz quantas perguntas tiveram ao menos um fundamento ancorado. **Nenhuma das duas mede se o conteúdo jurídico está correto**; isso depende do gabarito.

---

## 3. Estado dos testes

| Grupo | Resultado |
|---|---|
| Testes offline (sem chamar a Groq) | **125 passando** |
| Testes de rede (`test_domains`, `test_smoke`) | **2 falhando com 429**: a organização usou 198.355 dos 200.000 tokens/dia do gpt-oss-20b. Chamadas pequenas passam (verificado), perguntas reais não. Falham igual no código anterior às mudanças: não é regressão |

**Sobre a chave nova da Groq:** a cota diária é **da organização e por modelo**, não da chave. Uma chave nova na mesma organização divide o mesmo teto. Para testar hoje, o caminho é usar outro modelo (o `openai/gpt-oss-120b` tem cota própria), esperar a janela de 24 h, contratar o Dev Tier ou configurar um provedor reserva.

---

## 4. Decisões pendentes (dependem do usuário)

| # | Item | Onde |
|---|---|---|
| 1 | **README ainda mostra `[CPF OMITIDO - ART. 1131 CGJ-CE]`**, o fundamento invertido, público no GitHub | README, linha 53 |
| 2 | README ainda descreve o Canal Amarelo como "Tarjamento Obrigatório… aplicação automática de tarjas" e o Vermelho com "buscas informais por telefone", em contradição com o `799700c` | README, linhas 62–63 |
| 3 | README fala em "selo oficial" e "Carimbo Digital de Autenticidade", em contradição com o aviso "não é assinatura nem certificação de autenticidade" | README, linhas 55 e 69 |
| 4 | Ocorrências do grep para decidir uma a uma: "100%: 43 testes" (rubrica) e o badge "43 Passed" (hoje são 125) | README, linhas 15 e 220 |
| 5 | O prompt do **chat** ainda manda indicar "condicionado com tarjamento protetivo" (as sugestões de tarja do benchmark #3, #8 e #16 vêm daí) | `src/fase3/pipeline.py`, `build_cartorio_prompt` |
| 6 | Push dos 5 commits locais (`799700c` → `30f6ba7`) | — |
| 7 | Estratégia de provedor/cota para o teste com cartórios | — |

---

## 5. Itens abertos que continuam do relatório 10

- **Canal do semáforo ainda decidido pelo LLM.** A tabela de decisão fixa baseada no CE Art. 1.128 e no CNJ 149 Arts. 123–128 ainda não foi implementada.
- **Tarjador:** "titular" decidido por substring, filiação não detectada, CPF sem dígito verificador. A aba está escondida.
- **`chroma_bundle.zip`** (65 MB) versionado e material de cursinho ainda no histórico do git.
- **Validação pedida pela professora:** gabarito 0/25, concorrentes 0/75, entrevistas 0. O verificador agnóstico (`30f6ba7`) já permite pontuar as respostas dos concorrentes assim que forem coletadas.
