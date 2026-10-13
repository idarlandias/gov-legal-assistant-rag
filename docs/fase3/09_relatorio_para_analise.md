# Relatório para análise: CartórioSeguro AI (Fase 3 da Residência SiDi)

> **Data:** 13/10/2026 · **Autor do projeto:** Idarlan Magalhães (Residência em IA SiDi/Softex)
> **Repositório:** https://github.com/idarlandias/gov-legal-assistant-rag (HEAD `20aeca4`)
> Este documento se basta: traz contexto, critérios de avaliação, dados medidos, texto literal das normas e trechos do código. A análise não depende de acesso ao repositório.

---

## 0. O que se pede ao analista

1. **Validar ou refutar** os achados da seção 7, principalmente o crítico (7.1).
2. **Avaliar a proposta da seção 9**: trocar a decisão do LLM por uma tabela de regras baseada no Art. 1.128 do Código de Normas do CE.
3. **Julgar o alinhamento com os critérios da professora** (seção 2): o que a auditoria cética provavelmente rebaixaria?
4. **Responder às perguntas abertas** da seção 10.
5. Priorizar o que fazer até a resubmissão ao funil.

Restrição: não inventar normas. Toda afirmação jurídica deve vir do texto literal da seção 6 ou ser marcada como "a confirmar com oficial/DPO".

---

## 1. Contexto

- **Programa:** Residência Tecnológica em IA (SiDi/Softex). Este é o projeto da Fase 3.
- **Origem:** na Fase 2, um RAG jurídico **horizontal** (LGPD, Lei 14.133, transparência, CTB) com chat em Streamlit.
- **Recorte da Fase 3:** cartórios de **Registro de Imóveis (RI) no Ceará**, na interseção **publicidade registral × LAI × LGPD**. Pergunta-tipo: "terceiro pede certidão ou informação sobre a matrícula X. Posso fornecer? Integral, limitado ou nego? Com base em quê?"
- **Usuário-alvo:** o escrevente de balcão do cartório. Interior do CE, Vale do Jaguaribe (Limoeiro do Norte, Russas, Morada Nova).
- **Stack:**
  - Python e Streamlit;
  - ChromaDB com embedding `intfloat/multilingual-e5-small` em ONNX;
  - BM25 e fusão RRF;
  - LLM via Groq (`openai/gpt-oss-20b` barato, `openai/gpt-oss-120b` premium, com roteamento por complexidade);
  - Pydantic.

---

## 2. Critérios da professora

### 2.1 Parecer do funil (Discovery + Auditoria Cética), set/2026
- **A dor é real.** A AGU e o governo de MG já enfrentaram a ambiguidade LAI × LGPD (exemplo do CPF).
- **Etapa 1 vermelha:** nenhuma *unfair advantage* declarada; RAG jurídico é replicável por quem tem o mesmo corpus público.
- **Etapa 6 vermelha:** baixa fricção para resolver por outros meios, que já existem: DPO obrigatório por Provimento CNJ, ANOREG+, Jus IA e Jurídico AI (comprados por tribunais).
- **Regra do elo mais fraco:** uma etapa vermelha impede nota verde.
- **Lacunas a preencher:**
  1. qual é a *unfair advantage* concreta;
  2. por que um cartório escolheria isso em vez do Jus IA;
  3. evidência de que o caminho atual (DPO ou assistente genérico) custa caro ou falha, com tempo, erro ou reclamações;
  4. um recorte vertical com base curada.
- **Próximos passos dela:**
  - testar o Jus IA e o Jurídico AI com perguntas reais;
  - conversar com um DPO de cartório;
  - **"narrow first, build second"**.
- **Resubmissão:** só com **informação nova de mercado**, não com documentação reorganizada.
- **Recado direto:** "pensar em um diferencial competitivo que as demais plataformas não tenham… ou melhorar o que já existe, ficando mais barato ou mais eficiente."

### 2.2 Dinâmica de ideação (set/out 2026) e respostas do aluno
- **Atividades:**
  - Prática 1, Usos Alternativos (fluência, flexibilidade, originalidade);
  - os 4 traços do pensamento divergente (fluência, flexibilidade, originalidade, elaboração);
  - atividade-ponte de mindset (erro como veredito × como dado);
  - pergunta de incubação: "qual seria uma forma radicalmente diferente de entregar o valor do seu projeto?"
- **Respostas do aluno:**
  - **Incubação:** "matar a interface de chat". Gerador de **Ato Pronto**: o escrevente marca o pedido, o solicitante e os dados sensíveis, e recebe veredito, fundamentação do CE, minuta e log de auditoria LGPD.
  - **Analogia:** **alfândega de aeroporto**. Canal Verde libera; Amarelo emite com tarja; Vermelho bloqueia e gera nota devolutiva. "O sistema tem que ser uma triagem de risco rápida, não uma enciclopédia."
  - **Sprint de 5 fases:** mapear (25 casos), divergir, decidir (Ato Pronto), **prototipar ("não vou codar um sistema inteiro agora")** e testar com 3 cartórios, em teste cego contra o Jus IA e o ChatGPT.

---

## 3. Linha do tempo

| Data | Entrega |
|---|---|
| 23/09 | Planejamento da Fase 3; benchmark (25 perguntas + planilha + script); corpus oficial (11 fontes, 4.359 trechos); busca híbrida E5 + BM25; filtro por especialidade |
| 05/10 | Entregas da dinâmica de ideação (docs 06 e 07) |
| 06/10 | `ato_pronto.py` (semáforo + minuta + ROPA via LLM), `tarjador.py` (regex de PII + carimbo SHA-256), UI em 4 abas, deploy no Streamlit Cloud com banco pré-indexado (65 MB no git), README "CartórioSeguro AI", 43 testes |
| 13/10 | Esta revisão: benchmark com filtro, sonda do Ato Pronto, leitura das normas |

---

## 4. Arquitetura atual

```
Corpus oficial (11 fontes) → segmentação por artigo + trilha de títulos + especialidade
  Lei 6.015/73 · LGPD · LAI · Decreto 7.724/12 · Lei 8.935/94 · Provimento CNJ 149/2023 (compilado ago/2026)
  Código de Normas Notarial e Registral do CE (set/2026) · Prov. 15/2026/CGJCE · Res. ANPD 15/2024 · 2 guias ANPD
    ↓
ChromaDB "fase3" (E5 multilíngue) + BM25 pt-BR → RRF (k=60) → filtro especialidade ∈ {registro_imoveis, geral}
    ↓
(a) answer(): prompt "Assessor Técnico de RI do CE" → resposta em texto
(b) gerar_ato_pronto(): pedido estruturado → LLM devolve JSON {canal, veredito, fundamentação, minuta, auditoria_lgpd}
(c) tarjar_matricula(): regex CPF/RG/regime/filiação → texto tarjado + carimbo SHA-256 (sem LLM)
```

**Classificação de especialidade:** o cabeçalho mais alto (Livro, Título, Capítulo ou Seção) que menciona uma especialidade define o artigo. Exemplo: CE Arts. 1.086 a 1.685 = Registro de Imóveis; CNJ 149 Arts. 123 a 128 = "Seção XIV — Do Registro de Imóveis e a Proteção de Dados".

---

## 5. Dados medidos

### 5.1 Evolução no benchmark (25 perguntas de balcão, sem gabarito validado)

| Execução | "Não encontrado" | Respostas citando artigo | Latência média | Tokens de entrada (total) |
|---|---:|---:|---:|---:|
| Fase 2 (RAG horizontal, MiniLM) | 20 | 4 | 6,8 s | 45 mil |
| Fase 3, corpus oficial, MiniLM | 14 | 9 | 8,1 s | 48 mil |
| Fase 3, E5 denso | 10 | 13 | 8,2 s | 52 mil |
| Fase 3, E5 + BM25 (híbrido) | 8 | 16 | 9,2 s | 53 mil |
| **Fase 3, híbrido + filtro RI + prompt cartorial (13/10)** | **5** | **19** | **7,6 s** | **39 mil** |

**Atenção:** "respondeu" ≠ "acertou". Não há gabarito nem notas (ver 7.4).

### 5.2 Por pergunta (NE = "Não encontrado no corpus")

| # | Categoria | Pergunta | Fase 2 | F3 híbrido | F3 + filtro RI | Início da resposta (F3 + filtro RI) |
|---|---|---|:-:|:-:|:-:|---|
| 1 | Certidão | Um terceiro sem vínculo pede certidão de inteiro teor de uma matrícula. Posso emitir sem exigir motivo? | NE | resp. | resp. | Decisão: Emitir a certidão de inteiro teor integralmente, sem exigência de justificativa do requerente. |
| 2 | Certidão | A certidão de inteiro teor deve exibir o CPF completo dos proprietários? | NE | NE | NE | Não encontrado no corpus. |
| 3 | Certidão | Pedido de certidão da matrícula com o histórico de todos os ônus, incluindo penhoras já canceladas. Emito integralmente? | NE | resp. | resp. | Decisão: Emissão condicionada com tarjamento protetivo (exigência de identificação segura e indicação da finalidade). |
| 4 | Busca | Buscar "todos os imóveis em nome de fulano" informando só o nome. Posso? | NE | resp. | resp. | Indeferir via Nota Devolutiva. Código de Normas CGJ‑CE, Art. 1.128, § 2º |
| 5 | Busca | Busca por CPF solicitada por um credor para localizar bens do devedor. Procedimento? | NE | resp. | resp. | Requerimento ao Oficial do Registro de Imóveis... |
| 6 | Informação verbal | Pedido, por telefone, do nome do proprietário de um imóvel. Posso informar? | NE | NE | resp. | Não pode informar. Cita **Art. 12 do Decreto 7.724/2012** (regulamento da LAI do Executivo federal) |
| 7 | Informação verbal | Vizinho pergunta se o imóvel ao lado tem hipoteca. Posso responder no balcão? | NE | resp. | NE | Não encontrado no corpus. |
| 8 | Poder público | Prefeitura pede lista de imóveis com proprietários e CPFs para cobrança de IPTU. Forneço? | NE | resp. | resp. | Fornecer a lista **condicionado com tarjamento protetivo** |
| 9 | Poder público | Polícia pede por ofício dados de proprietário sem ordem judicial. Como proceder? | resp. | NE | resp. | Indeferido via Nota Devolutiva. Art. 1128, § 4º, CGJ‑CE |
| 10 | Poder público | MP requisita certidões em massa. Há limite ou exigência de fundamentação? | NE | NE | resp. | Pode solicitar, mas deve observar finalidade... |
| 11 | Transparência | CPF do proprietário pode aparecer em portal de transparência ou resposta via LAI? | NE | NE | resp. | Indeferido via Nota Devolutiva. LAI, Art. 11, § 3º |
| 12 | Transparência | Pedido via LAI sobre emolumentos arrecadados pela serventia. É dever responder? | NE | resp. | resp. | Sim... Art. 10, § 2º |
| 13 | Dado sensível | Matrícula com averbação de interdição/curatela. Certidão pode ser emitida sem restrição? | NE | resp. | resp. | Não é possível emitir inteiro teor sem incluir essa averbação... |
| 14 | Dado sensível | Averbação envolvendo menor (doação a incapaz). Devo tarjar algo? | NE | resp. | resp. | Não é necessário tarjar. Art. 1267, § 1º CGJ‑CE |
| 15 | Dado sensível | Cópia de título arquivado com dados de saúde de uma das partes. Forneço? | resp. | resp. | resp. | Indeferir mediante Nota Devolutiva |
| 16 | Tratamento | Posso enviar certidão por e-mail/WhatsApp? Que cuidados LGPD valem? | NE | resp. | resp. | Pode, mas "**condicionado com tarjamento**" |
| 17 | Tratamento | Por quanto tempo devo guardar os dados de quem pediu certidão? | NE | NE | NE | Não encontrado no corpus. |
| 18 | Tratamento | Titular pede, com base na LGPD, exclusão dos seus dados da matrícula. Como respondo? | NE | NE | NE | Não encontrado no corpus (LGPD Art. 18 estava entre os recuperados) |
| 19 | Tratamento | Titular pede relatório de quem consultou sua matrícula. Tenho obrigação? | resp. | resp. | **vazio** | **Resposta vazia**: o gpt-oss-20b gastou os 2.048 tokens de saída raciocinando; o script contou como "respondida" |
| 20 | Tratamento | Titular pede correção de dado errado na matrícula: retificação ou pedido LGPD? | resp. | resp. | resp. | Retificação do assentamento registral (Art. 1.386 CGJ‑CE) |
| 21 | Compartilhamento | Empresa quer acesso em lote/API a dados de matrículas. Posso firmar convênio? | NE | NE | resp. | Indeferido. Art. 148 CNJ 149/2023 |
| 22 | Compartilhamento | Compartilhamento com ONR/SREI e centrais: base legal adicional ou consentimento? | resp. | resp. | resp. | Art. 101, CNJ 149/2023 |
| 23 | Norma CE | O que mudou com o Provimento 15/2026/CGJCE na qualificação das partes? | NE | resp. | resp. | Alterou a redação do Art. 1.103 do Código de Normas |
| 24 | Norma CE | Requisitos do Código de Normas do CE para emitir certidão digital? | NE | resp. | resp. | Tabela de requisitos com dispositivos do CGJ‑CE |
| 25 | Incidente | Certidão com dados pessoais enviada ao e-mail errado. Obrigações da serventia? | NE | resp. | NE | Não encontrado no corpus |

**Padrão a notar:** o prompt atual manda indicar se o ato é "integral, **condicionado com tarjamento protetivo** ou indeferido". As respostas passaram a sugerir tarja onde nenhuma norma recuperada a prevê: #3, #8 e #16.

### 5.3 Sonda do Ato Pronto (13/10, 3 casos com resposta indicada pela norma)

| Caso | Norma que indica a resposta | Saída do sistema | Latência |
|---|---|---|---:|
| Terceiro pede certidão de matrícula (inteiro teor), CPF envolvido | CNJ 149 Art. 123 e CE Art. 1.128, caput: identificação, **sem finalidade** | **AMARELO / DEFERIDO COM TARJAMENTO** | 14 s |
| Busca de todos os imóveis em nome de alguém, sem motivo | CNJ Art. 126 e CE Art. 1.128 §2º IV: identificação + finalidade | VERMELHO / INDEFERIDO | 33 s |
| Nome do proprietário por telefone | CNJ Art. 127 e CE Art. 1.128 §2º V: identificação + finalidade | VERMELHO / INDEFERIDO | 62 s |

- **Latências altas:** 14 a 62 s, por causa de novas tentativas após o limite de requisições da Groq.
- **Citações:** o modelo atribuiu o "Art. 1128" à **Lei 6.015** (ele é do Código do CE). Também citou a LGPD, Art. 7º, II, e "CNJ 149 Livro I" sem nenhum dos dois estar entre os trechos recuperados.
- **Recuperação:** no caso 1, o CNJ Art. 123 e o CE Art. 1.128 não vieram entre os 5 trechos recuperados.

---

## 6. Texto literal das normas-chave (extraído do corpus oficial)

### 6.1 Código de Normas do CE: Art. 1.128 (Título VII, RI > Cap. IV "Das certidões e das informações")
> **Art. 1.128.** Qualquer pessoa pode requerer certidão de registros em sentido estrito, averbações, matrículas, transcrições ou inscrições específicas, desde que devidamente identificada, independentemente de indicação da finalidade.
> **§ 1º** Aplica-se o disposto no caput nos pedidos de certidão de documentos arquivados na Serventia, desde que haja previsão legal ou normativa específica de seu arquivamento no registro.
> **§ 2º** Dependem de identificação do requerente e indicação da finalidade: **I** - pedidos de certidão de documentos arquivados em cartório para a qual não haja previsão legal específica de expedição; **II** - pedidos de certidão, busca e informações apresentados em bloco, ainda que instruídos com a numeração dos atos a serem certificados; **III** - pedidos de certidão de atos anteriores da cadeia dominial do imóvel; **IV** - as requisições de buscas fundadas exclusivamente no indicador pessoal ou real; **V** - o fornecimento, pelo registrador, por qualquer meio, de informações sobre o registro não veiculadas por certidão, exceto nos casos em que o solicitante figure no registro em questão.
> **§ 3º** Serão formadas fichas físicas ou digitais contendo os dados de identificação e indicação de finalidade em todas as hipóteses do parágrafo anterior, podendo o titular dos dados pessoais solicitados requisitar as informações contidas nas fichas formadas em virtude de buscas ou pedidos de informações e certidões.
> **§ 4º** Caracterizada tentativa de tratamento de dados em desacordo com as finalidades do Registro de Imóveis e com os princípios da Lei Geral de Proteção de Dados Pessoais, poderá o Oficial recusar o fornecimento em nota fundamentada, do que caberá revisão pelo juízo competente.

### 6.2 Código de Normas do CE: Art. 1.131, § 10
> **§ 10.** No âmbito do registro de imóveis, a certidão de inteiro teor da matrícula conterá a reprodução de todo seu conteúdo e será suficiente para fins de comprovação de propriedade, direitos, ônus reais e restrições sobre o imóvel, independentemente de certificação específica pelo Oficial.

### 6.3 Provimento CNJ 149/2023, Seção XIV "Do Registro de Imóveis e a Proteção de Dados"
> **Art. 123.** Dependem de identificação do requerente e independem de indicação da finalidade os pedidos de certidão de registros em sentido estrito, averbações, matrículas, transcrições ou inscrições específicas, expedidas em qualquer modalidade. § 1.º Também dependem de identificação do requerente e independem de indicação da finalidade os pedidos de certidão de documentos arquivados no cartório, desde que haja previsão legal ou normativa específica de seu arquivamento no registro. [...]
> **Art. 124.** Ressalvadas as hipóteses que tenham previsão legal ou normativa expressa, como as certidões de filiação de imóveis, ou de propriedade com negativa de ônus e alienações, ou outras compatíveis com as finalidades dos registros de imóveis e com os princípios da LGPD, não serão expedidas certidões cujo conteúdo envolva informações sobre dados pessoais extraídos de mais de uma matrícula, assentamento do registro auxiliar, transcrição ou inscrição.
> **Art. 125.** As certidões dos imóveis que já forem objeto de matrícula eletrônica, após a "primeira qualificação eletrônica", serão expedidas, independentemente de indicação de finalidade, em formato nato-digital estruturado, contendo a situação jurídica atual do imóvel, ou seja, a sua descrição, a titularidade e os ônus reais não cancelados. Parágrafo único. A expedição de certidão de atos anteriores da cadeia filiatória do imóvel depende de identificação segura do requerente e de indicação da finalidade.
> **Art. 126.** O atendimento a requisições de buscas fundadas exclusivamente no indicador pessoal ou real pressupõe a identificação segura do solicitante, bem como a indicação da finalidade, de tudo mantendo-se o registro em meio físico ou virtual.
> **Art. 127.** O fornecimento, pelo registrador, por qualquer meio, de informações sobre o registro não veiculadas por certidão dependerá da segura identificação do solicitante e da indicação da sua finalidade, exceto nos casos em que o solicitante figure no registro em questão.
> **Art. 128.** Serão formados prontuários físicos ou digitais contendo os dados de identificação e indicação de finalidade em todas as hipóteses em que estas tenham sido exigidas. Parágrafo único. O titular dos dados pessoais solicitados terá direito a requisitar as informações contidas nos prontuários formados em virtude de buscas ou pedidos de informações e certidões para os quais foi exigida a identificação do solicitante e a indicação de finalidade.

### 6.4 Lei 6.015/1973, Art. 17, caput
> **Art. 17.** Qualquer pessoa pode requerer certidão do registro sem informar ao oficial ou ao funcionário o motivo ou interesse do pedido.

---

## 7. Achados

### 7.1 Crítico: fundamento legal invertido no tarjador e no prompt
- O tarjador escreve no texto da certidão `[CPF OMITIDO - ART. 1131 CGJ-CE]` e registra o motivo "Art. 1131, §10 CGJ-CE c/c Prov. CNJ 149/2023 (Omissão de CPF a terceiros)".
- O carimbo de conformidade imprime "Fundamentação: Código de Normas CGJ-CE (Art. 1131, §10)".
- **O §10 diz o oposto** (ver 6.2): a certidão de inteiro teor reproduz **todo** o conteúdo.
- O prompt do Ato Pronto define, sem norma que o sustente, que "terceiro requerendo certidão de inteiro teor com CPF [...] fornece a certidão, porém tarjando dados". Na sonda, o modelo seguiu o prompt (AMARELO/tarja) contra o CNJ Art. 123 e o CE Art. 1.128 caput.
- **Não encontrei no corpus** nenhuma norma que autorize tarjar dados na certidão de inteiro teor da matrícula. A forma de limitar que aparece é outra: o **tipo** de certidão (situação jurídica atual, CNJ Art. 125) e a **exigência de finalidade** em casos específicos (CE Art. 1.128 §2º). *A confirmar com oficial/DPO.*

### 7.2 Defeitos de código (verificados com testes manuais)

| # | Onde | Defeito | Evidência |
|---|---|---|---|
| 1 | tarjador | "É o próprio titular?" é decidido por substring (`"titular" in solicitante` ou `"proprietário" in solicitante`). Falha aberta: nada é tarjado | "Terceiro sem vínculo com o titular", "Advogado do proprietário", "Credor do proprietário" → 0 tarjas |
| 2 | tarjador | Regex de filiação falha em texto realista | "filho de Ana Lima e Pedro Souza, residente…" → não detectado |
| 3 | tarjador | Qualquer sequência de 11 dígitos vira CPF (sem dígito verificador) | código INCRA "12345678901" tarjado |
| 4 | tarjador | O carimbo afirma "Tarjamento Obrigatório Aplicado" mesmo com zero tarjas. Fala em "Código de Autenticidade" e "comprovação jurídica", mas é um SHA-256 sem chave nem assinatura (prova integridade, não autenticidade). O hash é do texto tarjado; a docstring diz original | — |
| 5 | tarjador | `REGEX_ONUS_CANCELADO` definida e não usada (a docstring promete "ônus cancelados") | — |
| 6 | ato_pronto | Se o JSON falhar, o *fallback* escolhe o canal por palavra-chave (pode dar VERDE) e inventa uma fundamentação genérica, sem sinalizar falha | — |
| 7 | ato_pronto | Os artigos citados não são conferidos com os trechos recuperados | Art. 1128 atribuído à Lei 6.015 |
| 8 | ato_pronto | Sem proteção para busca vazia (chama o LLM sem contexto) | — |
| 9 | ato_pronto | A consulta de recuperação é só a concatenação dos rótulos da UI; não traz CNJ 123 nem CE 1.128 no caso mais comum | sonda, caso 1 |
| 10 | pipeline | O rótulo de fonte perdeu o nome da norma (`Art. 19:p0`; de qual das 11 normas?) | benchmark de 13/10 |
| 11 | LLM | O gpt-oss-20b pode esgotar os tokens raciocinando e devolver resposta vazia; ninguém detecta | #19 |
| 12 | deploy | Banco pré-indexado (65 MB) versionado no git; `.git` com 230 MB; cada reindexação soma mais 65 MB | — |

### 7.3 Afirmações públicas sem medição (README e aba Benchmark do app)

| Afirmação | Situação |
|---|---|
| "~3,2 segundos no balcão (-93%)" | medido: 7,6 s (benchmark) e 14 a 62 s (Ato Pronto, com limite de requisições) |
| "Redução de 93% no tempo e 98% no custo comprovada em benchmark" | não existe medição do tempo de balcão nem do preço dos concorrentes |
| "Aderência Regulatória 100% CGJ-CE / CNJ" | não medida; ver 7.1 |
| "Garantia anti-alucinação" | contradita por 7.1 e 7.2 #7 |
| Tempo do DPO "20 a 40 min (ou dias)" | sem entrevista que sustente |
| "< R$ 0,02 por consulta" | **se sustenta:** cerca de R$ 0,004 (≈1,6 mil tokens de entrada por pergunta, gpt-oss-120b na Groq, câmbio 5,50) |

### 7.4 Estado da validação pedida pela professora

| Item | Situação |
|---|---|
| Gabarito do oficial/DPO nas 25 perguntas | 0 de 25 |
| Respostas coletadas do Jus IA / Jurídico AI / LLM genérico | 0 de 75 |
| Notas da rubrica (veredito, fundamentação, norma CE, acionável, sem alucinação) | 0 |
| Entrevistas com cartórios | nenhuma registrada |

---

## 8. Trechos de código relevantes

**Prompt do Ato Pronto (`src/fase3/ato_pronto.py`), definição dos canais:**
```text
- Canal VERDE: Pedido seguro [...] (ex: próprio titular requerendo sua matrícula, terceiro pedindo certidão de situação jurídica atual sem dados excessivos).
- Canal AMARELO: Fornecimento permitido, mas com TARJAMENTO OBRIGATÓRIO de dados pessoais excessivos (ex: terceiro requerendo certidão de inteiro teor com CPF, documentos, regime de bens ou filiação de outras pessoas — fornece a certidão, porém tarjando dados que não dizem respeito à publicidade real).
- Canal VERMELHO: Bloqueio ou Exigência Formal (ex: busca ampla por CPF sem justificativa legal; pedido de exclusão de dados da matrícula com base na LGPD [...]; informação verbal por telefone; dados sob segredo judicial). Deve gerar NOTA DEVOLUTIVA formal fundamentada.
```

**Tarjador (`src/fase3/tarjador.py`):**
```python
e_proprio_titular = "titular" in solicitante.lower() or "proprietário" in solicitante.lower()
...
motivo = ("Art. 17 da Lei 6.015/73 (Acesso pelo próprio titular)" if e_proprio_titular
          else "Art. 1131, §10 CGJ-CE c/c Prov. CNJ 149/2023 (Omissão de CPF a terceiros)")
...
subst = "[CPF OMITIDO - ART. 1131 CGJ-CE]"
```

**Fallback do Ato Pronto:**
```python
except Exception as e:
    canal_fallback = CanalRisco.AMARELO
    if any(w in conteudo_bruto.lower() for w in ["negar", "devolutiva", "indeferid", "vedado", "proibido"]):
        canal_fallback = CanalRisco.VERMELHO
    elif any(w in conteudo_bruto.lower() for w in ["deferido integral", "liberado", "sem restrição"]):
        canal_fallback = CanalRisco.VERDE
    saida = AtoProntoOutput(canal=canal_fallback, veredito="ANÁLISE DE BALCÃO REALIZADA", ...)
```

---

## 9. Proposta de melhoria (a avaliar)

### 9.1 Tabela de decisão baseada no CE Art. 1.128, com o LLM só redigindo
O Art. 1.128 é norma **estadual** (reforça a hipótese H2, "norma do CE atualizada") e cobre o semáforo inteiro. Proposta: canal, veredito e fundamento saem de uma **tabela fixa e testável**. O LLM só redige a minuta, com os dispositivos já escolhidos.

| Entrada (tipo de pedido × situação) | Canal | Ação no balcão | Fundamento |
|---|---|---|---|
| Certidão de matrícula, registro, averbação ou transcrição (qualquer requerente identificado) | VERDE | Emitir; exigir só identificação | CE 1.128 caput; CNJ 123; Lei 6.015 art. 17 |
| Certidão de documento arquivado **com** previsão de arquivamento | VERDE | Emitir com identificação | CE 1.128 §1º; CNJ 123 §1º |
| Certidão de documento arquivado **sem** previsão de expedição | AMARELO | Exigir identificação + finalidade; abrir ficha | CE 1.128 §2º I e §3º |
| Pedidos em bloco (certidão, busca, informação) | AMARELO | Exigir finalidade; abrir ficha | CE 1.128 §2º II e §3º |
| Atos anteriores da cadeia dominial | AMARELO | Exigir finalidade; abrir ficha | CE 1.128 §2º III; CNJ 125 parágrafo único |
| Busca por indicador pessoal ou real (nome/CPF) | AMARELO | Exigir identificação segura + finalidade; abrir ficha | CE 1.128 §2º IV; CNJ 126 |
| Informação fora de certidão (verbal, telefone, e-mail) | AMARELO (VERDE se o solicitante figura no registro) | Exigir identificação + finalidade | CE 1.128 §2º V; CNJ 127 |
| Certidão com dados pessoais de mais de uma matrícula, sem previsão | VERMELHO | Recusar | CNJ 124 |
| Finalidade incompatível com o RI ou com a LGPD | VERMELHO | Recusar em **nota fundamentada** (cabe revisão judicial) | CE 1.128 §4º |
| Titular pede relação de quem consultou | VERDE | Fornecer as fichas formadas | CE 1.128 §3º; CNJ 128 parágrafo único |

Consequências:
- a "ficha de auditoria/ROPA" passa a ter **base legal direta** (CE 1.128 §3º e CNJ 128), não só a LGPD, Art. 37;
- o "tarjador" deixa de afirmar dever legal. Pode virar um assistente de revisão ou de geração da certidão de **situação jurídica atual** (CNJ 125), se a norma permitir no balcão;
- cada linha da tabela vira um caso de teste;
- num teste cego, a resposta é **determinística e explicável**. Esse é o argumento contra o Jus IA.

### 9.2 Outras correções
1. Conferir as citações do LLM contra os trechos recuperados (norma + número). Marcar o que não bater.
2. *Fallback* = "revisão manual necessária", nunca um canal.
3. Tarjador:
   - `solicitante` como enum;
   - CPF validado pelo dígito verificador;
   - testes de filiação;
   - carimbo fiel ao que foi feito, e "integridade" em vez de "autenticidade".
4. Detectar resposta vazia ou truncada (`finish_reason == "length"`): nova tentativa com o 120b ou mais `max_tokens`.
5. Rótulo de fonte "norma + artigo" no contexto e na saída.
6. README e app com os números medidos; o resto como "hipótese a validar".
7. Banco pré-indexado fora do git (GitHub Release, baixado no boot).

---

## 10. Perguntas abertas para o analista

1. Existe base normativa (CNJ, CGJ-CE, ANPD) para **tarjar** dados pessoais numa certidão de inteiro teor de matrícula pedida por terceiro identificado? Se não, o "tarjador" deve ser descartado, redesenhado ou mantido só como ferramenta interna?
2. A tabela da seção 9.1 está correta e completa à luz das normas da seção 6? Que casos do balcão ela não cobre (ex.: segredo de justiça, dados de saúde em título arquivado, requisição do MP ou da polícia, prefeitura e IPTU)?
3. Uma tabela de decisão fixa + LLM só para redação fortalece ou enfraquece a tese de *unfair advantage* perante a auditoria cética? (Risco: "é só uma tabela"; força: verificável, estadual, explicável.)
4. Dada a regra do elo mais fraco, qual é a ordem ótima até a resubmissão: corrigir o produto primeiro ou coletar a validação primeiro (gabarito, concorrentes, entrevistas)?
5. Qual métrica deve substituir as afirmações não medidas (tempo, custo, aderência) e como medi-la em 2 a 3 semanas com 3 cartórios do Vale do Jaguaribe?
6. O que mais a auditoria cética provavelmente apontaria neste estado do projeto?
