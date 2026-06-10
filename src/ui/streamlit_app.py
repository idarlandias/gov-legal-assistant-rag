"""Streamlit UI — entrada principal do app. Pronta para deploy 1-click no Streamlit Cloud.

Voce nao precisa editar quase nada aqui — ja faz integracao com:
- src.pipeline.rag (TODOs 1-3)
- src.pipeline.cache (TODO 5)
- src.pipeline.routing (TODO 6)
- src.pipeline.tools (TODO 4, opcional)
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

# Adiciona o root do projeto no path para imports
_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

load_dotenv()

import streamlit as st  # noqa: E402

from src.observability.trace import trace, log_event  # noqa: E402
from src.pipeline.cache import ExactCache, SemanticCache  # noqa: E402
from src.pipeline.rag import build_rag_pipeline  # noqa: E402
from src.pipeline.routing import classify_complexity  # noqa: E402
from src.pipeline.security_skill import log_query, log_model_choice  # noqa: E402


# ---------------------------------------------------------------- Utilidades de formatação
def _format_answer(text: str) -> str:
    """Pós-processa a resposta do LLM para garantir formatação limpa em Markdown.
    
    Expande incisos inline (I - texto; II - texto) em listas com marcadores separados
    e garante quebras de linha entre parágrafos de artigos legais.
    """
    import re

    if not text:
        return text

    # 1. Substitui incisos romanos separados por ; ou , na mesma linha por listas
    # Detecta padrões como: "I - texto; II - texto; III - texto"
    inline_pattern = re.compile(
        r'(?:^|(?<=\n))'
        r'([IVXLC]+\s*[-—]\s*.+?)'
        r'(?:;\s*)'
        r'(?=[IVXLC]+\s*[-—])',
        re.MULTILINE
    )
    
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        # Detecta linha com múltiplos incisos romanos inline: "I - x; II - y"
        if re.search(r'[IVXLC]+\s*[-—]\s*.+;\s*[IVXLC]+\s*[-—]', line):
            # Divide em cada inciso
            parts = re.split(r';\s*(?=[IVXLC]+\s*[-—])', line)
            for part in parts:
                stripped = part.strip().rstrip(';')
                if stripped:
                    # Formata cada inciso como item de lista
                    inciso_match = re.match(r'^([IVXLC]+)\s*[-—]\s*(.+)$', stripped)
                    if inciso_match:
                        new_lines.append(f"- **{inciso_match.group(1)}** — {inciso_match.group(2)}")
                    else:
                        new_lines.append(f"- {stripped}")
        else:
            new_lines.append(line)

    result = '\n'.join(new_lines)
    
    # 2. Garante que parágrafos de lei (§ 1º, § 2º...) estejam em linhas próprias
    result = re.sub(r'([^\.])\s*(§\s*\d+[°º])', r'\1\n\n\2', result)
    
    # 3. Remove citações de arquivo que podem ter escapado do filtro do prompt
    result = re.sub(r'\[?[A-Za-z0-9_\-]+\.(?:pdf|txt|docx)\:?p?\d*\]?', '', result)
    
    return result.strip()


# ---------------------------------------------------------------- Streamlit UI
st.set_page_config(page_title="Assistente Jurídico RAG", page_icon="🏛️", layout="centered")

st.title("🏛️ Assistente Jurídico RAG")
st.caption("Consulta em linguagem natural para LGPD, Licitações (Lei 14.133/2021) e Transparência Pública")


# Inicializacao lazy de pipeline + caches
@st.cache_resource
def get_pipeline():
    return build_rag_pipeline(corpus_dir=str(_ROOT / "data" / "corpus"))


@st.cache_resource
def get_exact_cache():
    return ExactCache()


@st.cache_resource
def get_semantic_cache():
    return SemanticCache(threshold=0.93)


pipeline_error = None
with st.spinner("Inicializando pipeline RAG..."):
    try:
        pipeline = get_pipeline()
    except Exception as e:
        pipeline = None
        pipeline_error = e
    exact_cache = get_exact_cache()
    semantic_cache = get_semantic_cache()


# Sidebar — metricas e debug
with st.sidebar:
    st.header("Metricas")
    if pipeline:
        st.metric("Chunks indexados", pipeline.collection.count())
    else:
        st.metric("Chunks indexados", "Erro")
    st.metric("Exact cache", exact_cache.stats()["size"])
    st.metric("Semantic cache", semantic_cache.stats()["size"])

    if st.button("Limpar caches"):
        get_exact_cache.clear()
        get_semantic_cache.clear()
        st.success("Caches limpos. Recarregue a pagina.")

    if st.button("Reindexar Banco Vetorial"):
        if not pipeline:
            st.error("Não é possível reindexar: Pipeline RAG não foi inicializado.")
        else:
            with st.spinner("Apagando e reconstruindo banco vetorial..."):
                try:
                    # Limpa caches em memória do Streamlit
                    st.cache_resource.clear()
                    # Executa a limpeza e reindexação de forma segura deletando e recriando a coleção
                    count = pipeline.reset_database()
                    st.success(f"Reindexação concluída! {count} chunks indexados.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao limpar e reindexar o banco: {e}")
                    st.info("Caso o erro persista, tente reiniciar a aplicação no painel da nuvem.")

if pipeline_error:
    st.error("⚠️ Falha ao inicializar o banco de dados RAG!")
    st.error(f"Erro detalhado: {pipeline_error}")
    st.warning(
        "💡 **Dica de Solução:** Isso geralmente ocorre quando a sua chave `GEMINI_API_KEY` "
        "excedeu o limite diário de uso (cota de requisições de embeddings). "
        "Por favor, crie uma **nova chave de API** gratuita em [Google AI Studio](https://aistudio.google.com/) "
        "e atualize os Secrets no painel de controle do seu app no Streamlit Cloud."
    )


# Main — chat interface
domain_option = st.selectbox(
    "Filtro de Domínio (Routing):",
    options=["Auto (Detecção Automática)", "LGPD", "Licitações", "Transparência", "Procedimentos Internos", "Concursos públicos", "Código de Trânsito (CTB)"],
    index=0
)

domain_mapping = {
    "Auto (Detecção Automática)": "auto",
    "LGPD": "lgpd",
    "Licitações": "licitacoes",
    "Transparência": "transparencia",
    "Procedimentos Internos": "procedimentos",
    "Concursos públicos": "concursos",
    "Código de Trânsito (CTB)": "ctb"
}
selected_domain = domain_mapping[domain_option]

# Inicializacao das mensagens de chat
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Exibir histórico de chat
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Fontes citadas"):
                for source, page in msg["sources"]:
                    st.write(f"- `{source}:p{page}`")

# Caixa de atalhos/exemplos com base no domínio selecionado
if selected_domain == "procedimentos":
    st.info("🏛️ **Procedimentos Internos:** Pergunte sobre documentos e prazos para serviços de cartório, prefeitura e INSS simulado, com base nos manuais do corpus.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ex: Documentos para Auxílio-Doença"):
            st.session_state["query_input"] = "Quais documentos preciso para pedir auxílio-doença?"
            st.rerun()
    with col2:
        if st.button("Ex: Documentos para Certidão de Nascimento"):
            st.session_state["query_input"] = "Quais documentos preciso para tirar 2ª via da certidão de nascimento?"
            st.rerun()
elif selected_domain == "lgpd":
    st.info("🔒 **LGPD:** Pergunte sobre tratamento de dados, direitos do titular e obrigações do poder público.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ex: Consentimento no setor público"):
            st.session_state["query_input"] = "O setor público precisa de consentimento para tratar dados?"
            st.rerun()
    with col2:
        if st.button("Ex: Divulgação de CPF de beneficiários"):
            st.session_state["query_input"] = "Posso divulgar o CPF de beneficiários de programas sociais no Portal?"
            st.rerun()
elif selected_domain == "licitacoes":
    st.info("📄 **Licitações:** Pergunte sobre modalidades, prazos, penalidades e dispensa com base na Lei 14.133.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ex: Limites de dispensa por valor"):
            st.session_state["query_input"] = "Quais são os limites para dispensa de licitação por valor?"
            st.rerun()
    with col2:
        if st.button("Ex: Modalidade Diálogo Competitivo"):
            st.session_state["query_input"] = "Como funciona a modalidade diálogo competitivo na lei 14.133?"
            st.rerun()
elif selected_domain == "transparencia":
    st.info("📊 **Transparência Pública:** Pergunte sobre transparência ativa, passiva e portal da transparência.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ex: O que é transparência ativa"):
            st.session_state["query_input"] = "O que deve constar obrigatoriamente no portal de transparência ativa?"
            st.rerun()
    with col2:
        if st.button("Ex: Link de Despesas no Portal"):
            st.session_state["query_input"] = "Construa o link de despesas de saúde do ano de 2024 para o Brasil"
            st.rerun()
elif selected_domain == "concursos":
    st.info("🎓 **Concursos públicos:** Tutor de concursos públicos que explica conteúdo e questões com base nas apostilas salvas no corpus.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ex: Ato vs Fato Contábil"):
            st.session_state["query_input"] = "Explique a diferença entre ato e fato contábil conforme a aula."
            st.rerun()
    with col2:
        if st.button("Ex: O que é situação líquida"):
            st.session_state["query_input"] = "Resuma o que é situação líquida segundo o material de contabilidade."
            st.rerun()
elif selected_domain == "ctb":
    st.info("🚗 **Código de Trânsito Brasileiro (CTB):** Pergunte sobre regras de trânsito, infrações, multas e habilitação com base na Lei 9.503/1997.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ex: Limite de velocidade"):
            st.session_state["query_input"] = "Qual a velocidade máxima permitida em rodovias de pista dupla para carros?"
            st.rerun()
    with col2:
        if st.button("Ex: Infração por celular"):
            st.session_state["query_input"] = "Qual a gravidade da infração por dirigir manuseando o telefone celular?"
            st.rerun()
else:
    st.info("🤖 **Modo Automático:** O assistente tentará classificar a sua pergunta e rotear para o domínio e modelo corretos de forma autônoma.")

# Tratamento do atalho ou chat input
if "query_input" not in st.session_state:
    st.session_state["query_input"] = ""

user_query = st.chat_input("Digite sua pergunta sobre LGPD, licitações, transparência ou procedimentos...")

if st.session_state["query_input"]:
    user_query = st.session_state["query_input"]
    st.session_state["query_input"] = ""

if user_query:
    # Adicionar e exibir mensagem do usuário imediatamente
    st.session_state["messages"].append({
        "role": "user",
        "content": user_query,
        "domain": selected_domain
    })
    with st.chat_message("user"):
        st.markdown(user_query)

    # Executar pipeline
    with st.chat_message("assistant"):
        with trace("query_handle", query=user_query, domain=selected_domain) as ctx:
            trace_id = ctx["trace_id"]
            log_query(selected_domain, user_query)

            # 1. Exact Cache
            cached = exact_cache.get(user_query)
            if cached:
                st.success("Cache hit (exact)")
                st.markdown(cached)
                log_event("cache_hit", trace_id=trace_id, layer="exact")
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": cached,
                    "domain": selected_domain,
                    "sources": []
                })
            else:
                # 2. Semantic Cache
                try:
                    cached = semantic_cache.get(user_query)
                except NotImplementedError:
                    cached = None
                    st.warning("Semantic cache nao implementado (TODO 5). Caindo no LLM real.")

                if cached:
                    st.success("Cache hit (semantic)")
                    st.markdown(cached)
                    log_event("cache_hit", trace_id=trace_id, layer="semantic")
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": cached,
                        "domain": selected_domain,
                        "sources": []
                    })
                else:
                    # 3. Pipeline RAG + Routing
                    try:
                        decision = classify_complexity(user_query)
                        st.info(f"Routing: {decision.complexity} -> {decision.model}")
                        log_event("route_decision", trace_id=trace_id, **decision.__dict__)
                        log_model_choice(decision.model)
                    except NotImplementedError:
                        st.warning("Routing nao implementado (TODO 6). Usando modelo default.")

                    with st.spinner("Consultando corpus e gerando resposta..."):
                        if not pipeline:
                            st.error("Erro: O banco RAG não pôde ser carregado devido à falha de Rate Limit/Cota da chave da API.")
                            st.info("Por favor, atualize sua GEMINI_API_KEY no Streamlit Cloud.")
                            st.stop()
                        try:
                            result = pipeline.answer(user_query, domain=selected_domain)
                        except NotImplementedError as e:
                            st.error(f"Pipeline nao implementado: {e}")
                            st.stop()

                    formatted_answer = _format_answer(result["answer"])
                    st.markdown(formatted_answer)
                    if result.get("sources"):
                        with st.expander("📎 Fontes citadas"):
                            for source, page in result["sources"]:
                                st.write(f"- `{source}:p{page}`")

                    exact_cache.put(user_query, result["answer"])
                    semantic_cache.put(user_query, result["answer"])
                    log_event("answer_generated", trace_id=trace_id, sources=len(result.get("sources", [])))

                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": result["answer"],
                        "domain": selected_domain,
                        "sources": result.get("sources", [])
                    })
    st.rerun()


st.divider()
st.caption(
    "Assistente Jurídico RAG | Domínios: LGPD, Licitações, Transparência, Procedimentos Internos e Concursos Públicos. "
    "Métricas de performance e cache exibidas na barra lateral."
)
