# Relatório da 4ª rodada: regras do chat, guarda de UI e datas do corpus

> **Data:** 13/10/2026 · **Autor:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Continuação de:** [12_relatorio_rodada3_readme_ui.md](12_relatorio_rodada3_readme_ui.md). O último push foi `6fd7fad`; todos os commits desde então estão **só locais**.
> Das quatro tarefas desta rodada, as tarefas 1 e 2 estão concluídas; as tarefas 3 e 4 aguardam decisão (seção 4).

---

## 1. Commits desta rodada

| Commit | Tarefa | O que mudou |
|---|---|---|
| `598151c` | 1 (P0) | **Chat e Ato Pronto passam a usar as mesmas regras de decisão.** A nova constante `REGRAS_DECISAO` (`src/fase3/regras_prompt.py`) define DEFERIR / DEFERIR MEDIANTE EXIGÊNCIA PRÉVIA (identificação e finalidade, com ficha do CGJ-CE Art. 1.128 §3º) / INDEFERIR (nota devolutiva fundamentada), e inclui a proibição de suprimir dados do inteiro teor, com a certidão de situação jurídica atual (CNJ 149, Art. 125) como alternativa. O prompt do chat deixou de mandar "condicionar com tarjamento protetivo". `ato_pronto.py` ficou sem "alfândega" e sem "vinculante" |
| `c5820c1` | 2 | **Aba do tarjador fora da UI.** Saíram da interface o item de aba, o bloco de 106 linhas e a flag `MOSTRAR_ABA_TARJADOR`, também retirada da `.env.example`. O `src/fase3/tarjador.py` continua no repositório. O expander passou a se chamar "Fundamentação legal (referências recuperadas)". A guarda de UI entrou no commit com o escopo novo |

---

## 2. Achados

### 2.1 De onde vinham as sugestões de tarja no benchmark

As sugestões indevidas de tarja das perguntas #3, #8 e #16 vinham do prompt do **chat**, em `build_cartorio_prompt`. Esse prompt continuava com a tríade "integralmente / condicionado com tarjamento protetivo / indeferido" mesmo depois que o Ato Pronto foi corrigido no `799700c`.

O defeito de fundo era ter **dois prompts com regras escritas em duplicidade**. Agora os dois leem a mesma constante, e o teste `tests/test_regras_prompt_compartilhadas.py` garante que pipeline e Ato Pronto usam o mesmo objeto e que o chat não volta a citar tarja.

### 2.2 A guarda de UI agora olha a afirmação, não a palavra

| Termo | Quando reprova |
|---|---|
| `tarj*`, `vinculante` | sempre |
| `suprim*`, `supress*` | só quando a mesma string fala de certidão, matrícula, inteiro teor, CPF ou dado pessoal |
| automático/automática | nunca (descreve comportamento real) |

A guarda lê os literais com `ast` e ignora docstrings, comentários e identificadores. Ela **passa sem nenhuma ocorrência**, e um teste confirma que só a frase com contexto jurídico é reprovada. Também abri o app com `streamlit.testing.AppTest`: renderiza sem exceção e com as 3 abas.

### 2.3 Fica um exemplo com o Art. 1.131 no código

A descrição do campo `artigo` em `ato_pronto.py:67` usa "Art. 1131, §10" como exemplo de citação. Esse trecho não estava no escopo e não foi alterado.

---

## 3. Estado dos testes

| Grupo | Resultado |
|---|---|
| Suíte offline | **129 passando** (eram 121; entraram 4 testes de regras compartilhadas e 4 da guarda de UI) |
| Guarda do 1.131 + guarda de UI | limpas |
| Testes de rede | dependem da cota diária da Groq |

---

## 4. Decisões pendentes

### 4.1 Tarefa 3: datas encontradas no **texto** de cada documento (ainda não gravadas)

O campo `baixado_em` é 2026-09-23 para todas as fontes. A data de **Last-Modified não foi usada** em nenhuma.

| Fonte | O que o texto traz | `versao_norma` proposta |
|---|---|---|
| Código de Normas CGJ-CE | Nenhuma data de compilação. Nota de alteração mais recente: "Prov. nº 15/2026/CGJCE, DJeA de 08/09/26" | alterações até o Prov. 15/2026/CGJCE (DJeA 08/09/2026) |
| Provimento 15/2026/CGJCE | "Edição: 3855 Fortaleza - CE, emitido em 08 de Setembro de 2026" | DJe nº 3855, 08/09/2026 |
| Provimento CNJ 149/2023 | "Texto compilado a partir da redação dada pelo Provimento n. 150/2023 … e pelo Provimento n. 253/2026"; nota mais recente "Provimento CN n. 253, de 18.8.2026" | compilado até o Provimento CN 253, de 18/08/2026 |
| Lei 6.015/1973 | "Atualizada a partir da republicação", sem data. Nota mais recente: Lei nº 15.139, de 2025 | alterações até a Lei 15.139/2025 |
| Lei 8.935/1994 | Nota mais recente: Lei nº 15.509, de 2026 | alterações até a Lei 15.509/2026 |
| LGPD (Lei 13.709/2018) | Nota mais recente: Lei nº 15.352, de 2026 | alterações até a Lei 15.352/2026 |
| LAI (Lei 12.527/2011) | Nota mais recente: Lei nº 15.141, de 2025 | alterações até a Lei 15.141/2025 |
| Decreto 7.724/2012 | Nota mais recente: Decreto nº 11.527, de 2023 | alterações até o Decreto 11.527/2023 |
| Resolução CD/ANPD 15/2024 | "RESOLUÇÃO CD/ANPD Nº 15, DE 24 DE ABRIL DE 2024"; "Publicado em: 26/04/2024" | 2024-04-24 (critério: data do ato, da URL do DOU, confirmada no texto) |
| Guia ANPD — Agentes de Tratamento | "Histórico de versões: Versão 2.0 Abril 2022 / Versão 1.0 Maio 2021" | Versão 2.0, abril de 2022 |
| Guia ANPD — Segurança da Informação | "Histórico de versões - Versão 1.0 – outubro/2021" | Versão 1.0, outubro de 2021 |

**Ressalva:** as leis e o decreto do Planalto não trazem data de compilação. Para eles, "alterações até X" é a nota de alteração mais recente que aparece no texto, ou seja, a lei de maior número no ano mais recente citado. Isso não garante que o Planalto já tenha incorporado alterações posteriores.

**Decisão:** gravar a tabela como está, ou gravar "nao_identificada" para as 5 leis e o decreto do Planalto?

### 4.2 Tarefa 4: linha 221 do README ("CI/CD")

Há duas opções: remover a menção, ou adicionar `pytest` ao `auto_update.yml`. **Recomendação: remover a menção.** O workflow existe para outra finalidade, e se ele rodasse o pytest, os 7 testes de rede falhariam sempre que a cota da Groq acabasse.

### 4.3 O que roda depois das respostas

1. Tarefa 3: gravar o manifesto e montar a barra lateral ("Normas consultadas", sem logo externo, com "Diagnóstico técnico" recolhido).
2. Tarefa 4: correções do README e retificação do doc 06, linha 94, com nota de rodapé.
3. Fechamento: suíte offline, guarda sobre o repositório inteiro, `git log --oneline 6fd7fad..HEAD`, conferência de staging e **push**.

Por instrução expressa, os docs 08 a 11 e os JSONs de `benchmark/results/` não serão alterados.
