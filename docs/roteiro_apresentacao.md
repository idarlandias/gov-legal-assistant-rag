# Roteiro de Apresentação — Pitch de 3 Minutos 🎤

Este roteiro foi estruturado para guiar a sua fala e demonstração de tela durante os 3 minutos exigidos para a entrega da disciplina. 

---

## ⏱️ Cronograma e Roteiro de Fala

| Tempo | Etapa | O que Falar (Script Sugerido) | O que Mostrar na Tela |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:30**<br>*(30s)* | **Problema** | "Olá, professor! O problema que estamos resolvendo hoje é a **morosidade e insegurança jurídica na Administração Pública**. Servidores e cidadãos perdem horas decifrando manuais gigantescos e leis complexas. Um grande exemplo é o **Auxílio-Doença**: uma dor de nível nacional, cujas regras mudam constantemente e estão dispersas em manuais densos e difíceis de consultar rapidamente." | Focar na tela inicial do app, apresentando o pitch de valor e os 4 domínios que o sistema cobre. |
| **0:30 – 1:20**<br>*(50s)* | **Arquitetura** | "Para resolver isso, desenvolvemos um assistente conversacional inteligente que utiliza uma **arquitetura RAG avançada**. Os documentos oficiais (LGPD, Lei de Licitações 14.133, Guia de Transparência da CGU e manuais de procedimentos) foram fatiados e indexados em um banco vetorial **ChromaDB** local.<br><br>O grande diferencial aqui é a inteligência híbrida: usamos **Model Routing** para escolher o modelo mais barato (Flash-Lite) para perguntas simples e o Pro para perguntas complexas; e **Caches em dois níveis** (Exato e Semântico) para zerar custos de perguntas repetidas. Além disso, integramos **Tools programáticas** via *Function Calling* para cálculos lógicos determinísticos e buscas exatas de leis, eliminando alucinações." | Mudar o selectbox de filtros na tela e apontar com o mouse para a barra lateral, mostrando os **Chunks indexados** e as métricas. |
| **1:20 – 2:00**<br>*(40s)* | **Demo 1:<br>Auxílio-Doença** | "Vejamos na prática. Se eu selecionar o domínio de **Procedimentos Internos** e perguntar: *'Quais documentos preciso para dar entrada no auxílio-doença?'*, a aplicação aciona uma tool dedicada chamada `listar_documentos`. Ela busca no ChromaDB os manuais de procedimentos oficiais do INSS e estrutura a resposta como um checklist limpo e determinístico.<br><br>Observe que o modelo cita de forma estrita as fontes de onde extraiu os dados, como `inss_beneficios.pdf:p1` e a cartilha oficial do INSS." | Clicar no botão **"Ex: Documentos para Auxílio-Doença"** e acompanhar o chat imprimindo a resposta estruturada com as fontes. |
| **2:00 – 2:30**<br>*(30s)* | **Demo 2:<br>Licitações** | "Agora, mudando para o domínio de **Licitações**, se eu questionar: *'Qual artigo trata da dispensa de licitação por valor?'*, o sistema faz o roteamento inteligente da pergunta e responde com precisão milimétrica que o **Artigo 75 da Nova Lei de Licitações** estabelece as regras e os limites vigentes, citando as páginas 73 e 74 do documento oficial do Senado." | Mudar o selectbox para **"Licitações"** e clicar no atalho de limites de dispensa de licitação. |
| **2:30 – 3:00**<br>*(30s)* | **Limitações,<br>Custos & Futuro** | "Em termos de resultados, nossa arquitetura com caches e roteador de modelos obteve uma **redução de custos de 85%** e latência p95 abaixo de 1.5 segundos, superando os 50% exigidos na rubrica.<br><br>Como limitações, a extração de documentos depende hoje de regex estruturado em manuais. Como trabalho futuro, planejamos integrar o re-ranking de chunks e migrar o banco vetorial para produção em nuvem usando pgvector. Toda a solução foi empacotada em **Docker** na porta 8505 para um deploy limpo e imediato. Muito obrigado!" | Mostrar os contadores de cache subindo na barra lateral e rolar a página até o fim para o encerramento. |

---

## 💡 Dicas de Ouro para a Gravação
* **Tom de Voz:** Fale com entusiasmo, segurança e em ritmo constante. A banca avalia a clareza da comunicação técnica.
* **Uso do Cursor:** Use o cursor do mouse de forma suave para apontar na tela o que você está falando (por exemplo, circule as fontes citadas no chat ou passe o mouse sobre os contadores de cache na barra lateral).
* **Preparação do Ambiente:** Feche abas desnecessárias do navegador e deixe o aplicativo Streamlit rodando em tela cheia na porta `8505` para passar uma impressão premium e focada.
