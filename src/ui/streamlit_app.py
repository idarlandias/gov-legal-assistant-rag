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
    
    # Diagnóstico de chave ativa conforme provider
    import os
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "groq":
        key_name = "GROQ_API_KEY"
    elif provider == "deepseek":
        key_name = "DEEPSEEK_API_KEY"
    else:
        key_name = "GEMINI_API_KEY"
    try:
        from src.pipeline.security_skill import get_env_secret
        key = get_env_secret(key_name)
        masked_key = f"{key[:12]}...{key[-8:]}" if len(key) > 20 else "Chave curta"
        st.info(f"🔑 **Chave ativa detectada no contêiner ({key_name}):** `{masked_key}`")
    except Exception:
        st.info(f"🔑 **Chave ativa detectada no contêiner ({key_name}):** Não encontrada")

    st.warning(
        f"💡 **Dica de Solução:** Isso geralmente ocorre quando a sua chave `{key_name}` "
        "está ausente, incorreta ou excedeu o limite de uso. "
        "Por favor, verifique suas configurações e atualize os Secrets no painel de controle do seu app no Streamlit Cloud."
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
# Perguntas Frequentes (FAQ) sugeridas com base no domínio
faq_options = []
if selected_domain == "procedimentos":
    st.info("🏛️ **Procedimentos Internos:** Pergunte sobre documentos e prazos para serviços de cartório, prefeitura e INSS simulado.")
    faq_options = [
        "Selecione uma pergunta...",
        "Quais documentos preciso para pedir auxílio-doença?",
        "Quais documentos preciso para tirar 2ª via da certidão de nascimento?"
    ]
elif selected_domain == "lgpd":
    st.info("🔒 **LGPD:** Pergunte sobre tratamento de dados, direitos do titular e obrigações do poder público.")
    faq_options = [
        "Selecione uma pergunta...",
        "O setor público precisa de consentimento para tratar dados?",
        "Posso divulgar o CPF de beneficiários de programas sociais no Portal?"
    ]
elif selected_domain == "licitacoes":
    st.info("📄 **Licitações:** Pergunte sobre modalidades, prazos, penalidades e dispensa com base na Lei 14.133.")
    faq_options = [
        "Selecione uma pergunta...",
        "Quais são os limites para dispensa de licitação por valor?",
        "Como funciona a modalidade diálogo competitivo na lei 14.133?"
    ]
elif selected_domain == "transparencia":
    st.info("📊 **Transparência Pública:** Pergunte sobre transparência ativa, passiva e portal da transparência.")
    faq_options = [
        "Selecione uma pergunta...",
        "O que deve constar obrigatoriamente no portal de transparência ativa?",
        "Construa o link de despesas de saúde do ano de 2024 para o Brasil"
    ]
elif selected_domain == "concursos":
    st.info("🎓 **Concursos públicos:** Explicações com base nas apostilas do material de estudo.")
    faq_options = [
        "Selecione uma pergunta...",
        "Explique a diferença entre ato e fato contábil conforme a aula.",
        "Resuma o que é situação líquida segundo o material de contabilidade."
    ]
elif selected_domain == "ctb":
    st.info("🚗 **Código de Trânsito Brasileiro (CTB):** Pergunte sobre regras de trânsito, infrações e multas.")
    faq_options = [
        "Selecione uma pergunta...",
        "Qual a velocidade máxima permitida em rodovias de pista dupla para carros?",
        "Qual a gravidade da infração por dirigir manuseando o telefone celular?"
    ]
else:
    st.info("🤖 **Modo Automático:** O assistente tentará classificar a sua pergunta e rotear para o domínio e modelo corretos de forma autônoma.")

if faq_options:
    faq_index_key = f"faq_index_{selected_domain}"
    if faq_index_key not in st.session_state:
        st.session_state[faq_index_key] = 0

    selected_faq = st.selectbox(
        "💡 **Dúvidas frequentes recomendadas para este domínio:**", 
        options=faq_options, 
        index=st.session_state[faq_index_key]
    )
    if selected_faq != "Selecione uma pergunta...":
        st.session_state["query_input"] = selected_faq
        # Reseta o índice de seleção para a opção padrão (0) no próximo rerun
        st.session_state[faq_index_key] = 0
        st.rerun()

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
                        if pipeline:
                            pipeline.llm_model = decision.model
                        log_event("route_decision", trace_id=trace_id, **decision.__dict__)
                        log_model_choice(decision.model)
                    except NotImplementedError:
                        st.warning("Routing nao implementado (TODO 6). Usando modelo default.")
 
                    with st.spinner("Consultando corpus e gerando resposta..."):
                        if not pipeline:
                            st.error(f"Erro: O banco RAG não pôde ser carregado devido à falha de chave/cota da API.")
                            st.info("Por favor, atualize suas credenciais no Streamlit Cloud.")
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
