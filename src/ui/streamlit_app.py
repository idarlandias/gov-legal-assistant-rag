"""Streamlit UI — CartórioSeguro AI & Assistente Jurídico RAG.

Oferece duas experiências principais:
1. 🚦 Balcão Registral (Fase 3): Gerador de Ato Pronto de Balcão baseado na analogia da alfândega
   (Canais Verde, Amarelo e Vermelho) com veredito, minuta pronta e auditoria LGPD (ROPA).
2. 💬 Assistente Jurídico Geral: Chat em linguagem natural para LGPD, licitações e transparência.
3. 📊 Benchmark & Compliance: Painel de casos práticos e validação de balcão.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

# Adiciona o root do projeto no path para imports
_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

load_dotenv()

import streamlit as st  # noqa: E402

from src.observability.trace import log_event, trace  # noqa: E402
from src.pipeline.cache import ExactCache, SemanticCache  # noqa: E402
from src.pipeline.rag import build_rag_pipeline  # noqa: E402
from src.pipeline.routing import classify_complexity  # noqa: E402
from src.pipeline.security_skill import log_model_choice, log_query  # noqa: E402


# ---------------------------------------------------------------- Utilidades de formatação
def _format_answer(text: str) -> str:
    """Pós-processa a resposta do LLM para garantir formatação limpa em Markdown."""
    if not text:
        return text

    lines = text.split("\n")
    new_lines = []
    for line in lines:
        if re.search(r"[IVXLC]+\s*[-—]\s*.+;\s*[IVXLC]+\s*[-—]", line):
            parts = re.split(r";\s*(?=[IVXLC]+\s*[-—])", line)
            for part in parts:
                stripped = part.strip().rstrip(";")
                if stripped:
                    inciso_match = re.match(r"^([IVXLC]+)\s*[-—]\s*(.+)$", stripped)
                    if inciso_match:
                        new_lines.append(f"- **{inciso_match.group(1)}** — {inciso_match.group(2)}")
                    else:
                        new_lines.append(f"- {stripped}")
        else:
            new_lines.append(line)

    result = "\n".join(new_lines)
    result = re.sub(r"([^\.])\s*(§\s*\d+[°º])", r"\1\n\n\2", result)
    result = re.sub(r"\[?[A-Za-z0-9_\-]+\.(?:pdf|txt|docx)\:?p?\d*\]?", "", result)
    return result.strip()


# ---------------------------------------------------------------- Inicialização de Recursos
st.set_page_config(
    page_title="CartórioSeguro AI — Balcão Registral & RAG Jurídico",
    page_icon="🏛️",
    layout="wide",
)


@st.cache_resource
def get_pipeline():
    return build_rag_pipeline(corpus_dir=str(_ROOT / "data" / "corpus"))


@st.cache_resource
def get_fase3_pipeline():
    from src.fase3.pipeline import Fase3Pipeline
    return Fase3Pipeline()


@st.cache_resource
def get_exact_cache():
    return ExactCache()


@st.cache_resource
def get_semantic_cache():
    return SemanticCache(threshold=0.93)


exact_cache = get_exact_cache()
semantic_cache = get_semantic_cache()


# ---------------------------------------------------------------- Barra Lateral (Métricas e Status)
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/courthouse.png", width=64)
    st.title("CartórioSeguro AI")
    st.caption("Residência SiDi · Fase 3 — Recorte Vertical de Registro de Imóveis (CE)")
    st.divider()

    st.subheader("⚙️ Status do Acervo")
    try:
        fase3_pipe = get_fase3_pipeline()
        chunks_fase3 = fase3_pipe.collection.count()
        st.metric("Corpus Fase 3 (Oficial RI/CE)", f"{chunks_fase3:,} chunks")
        st.success("Coleção `fase3` ativa (E5 + BM25)")
    except Exception as e:
        st.error(f"Erro no pipeline Fase 3: {e}")

    try:
        rag_pipe = get_pipeline()
        chunks_legado = rag_pipe.collection.count()
        st.metric("Corpus Geral (Legado)", f"{chunks_legado:,} chunks")
    except Exception:
        pass

    st.divider()
    st.subheader("⚡ Caches e Latência")
    st.metric("Exact Cache", exact_cache.stats()["size"])
    st.metric("Semantic Cache", semantic_cache.stats()["size"])

    if st.button("🧹 Limpar Caches"):
        get_exact_cache.clear()
        get_semantic_cache.clear()
        st.success("Caches limpos com sucesso!")

    st.divider()
    st.caption("Normas Ativas: Código de Normas CGJ-CE · Prov. CNJ 149/2023 · Lei 6.015/73 · LGPD")


# ---------------------------------------------------------------- Cabeçalho Principal
st.title("🏛️ CartórioSeguro AI")
st.markdown(
    "**Decisão Operacional & Compliance Registral** — Proteção contra violações da LGPD e incidentes na Corregedoria do TJCE."
)

tab_balcao, tab_chat, tab_benchmark = st.tabs([
    "🚦 Balcão Registral (Ato Pronto — Fase 3)",
    "💬 Consulta Especializada (Chat RAG)",
    "📊 Casos de Balcão & Validação",
])


# ==============================================================================
# TAB 1: GERADOR DE ATO PRONTO (A INOVAÇÃO RADICAL DA FASE 3)
# ==============================================================================
with tab_balcao:
    st.subheader("⚡ Triagem Operacional de Balcão (Analogia da Alfândega)")
    st.markdown(
        "Emita atos prontos com veredito direto, fundamentação vinculante no Código de Normas do Ceará e no Provimento CNJ 149/2023, "
        "minuta pronta para despacho ou Nota Devolutiva e registro de auditoria LGPD (ROPA)."
    )

    col_form, col_result = st.columns([1.1, 1.4], gap="large")

    with col_form:
        st.markdown("### 📋 Dados da Solicitação")

        tipo_pedido = st.selectbox(
            "1. Tipo de Solicitação:",
            options=[
                "Certidão de Inteiro Teor de Matrícula",
                "Certidão de Situação Jurídica Atual (Vigente)",
                "Histórico de Ônus / Cadeia Filiatória / Ônus Cancelados",
                "Busca por Indicador Pessoal (Pesquisa de Bens por CPF/Nome)",
                "Cópia de Título / Documento Arquivado no Cartório",
                "Informação Verbal no Balcão ou por Telefone",
                "Pedido de Exclusão de Dados da Matrícula com base na LGPD",
                "Pedido de Retificação de Dado Pessoal na Matrícula",
                "Requisição por Órgão Público / Polícia / Prefeitura sem Ordem Judicial",
                "Acesso em Lote / Convênio com Empresa Imobiliária ou Fintech",
            ],
            index=0,
        )

        solicitante = st.selectbox(
            "2. Perfil do Requerente / Solicitante:",
            options=[
                "Próprio Titular / Proprietário do Imóvel",
                "Terceiro sem comprovação de vínculo ou interesse jurídico",
                "Cônjuge / Herdeiro com interesse documentado",
                "Advogado constituído com procuração específica",
                "Autoridade Policial / Delegacia (Ofício sem ordem judicial)",
                "Prefeitura Municipal / Fiscal de Tributos (IPTU)",
                "Poder Judiciário / Ministério Público (Requisição oficial)",
                "Instituição Financeira / Credor em execução",
            ],
            index=1,
        )

        dados_sensiveis = st.multiselect(
            "3. Dados Pessoais / Sensíveis Envolvidos:",
            options=[
                "CPF completo",
                "RG / Documentos de identificação",
                "Estado Civil / Regime de Bens",
                "Filiação / Adoção sigilosa",
                "Dados de Saúde / Interdição / Curatela",
                "Menor de idade / Incapaz",
                "Ônus reais já cancelados (penhoras baixadas)",
            ],
            default=["CPF completo", "Estado Civil / Regime de Bens"],
        )

        with st.expander("➕ Detalhes Adicionais e Protocolo (Opcional)"):
            protocolo_input = st.text_input("Número do Protocolo:", value="PROT-2026/0842")
            detalhes_input = st.text_area(
                "Particularidades do caso concreto:",
                placeholder="Ex.: Requerente alega que precisa do CPF para ajuizar ação de cobrança...",
                height=80,
            )

        btn_gerar = st.button("⚡ Processar Balcão (Gerar Ato Pronto)", type="primary", use_container_width=True)

    with col_result:
        st.markdown("### 📜 Ato Registral Emitido")

        if btn_gerar:
            with st.spinner("Consultando acervo da CGJ-CE e Prov. CNJ 149/2023..."):
                try:
                    from src.fase3.ato_pronto import PedidoBalcao

                    fase3_pipe = get_fase3_pipeline()
                    pedido = PedidoBalcao(
                        tipo_pedido=tipo_pedido,
                        solicitante=solicitante,
                        dados_sensiveis=dados_sensiveis,
                        detalhes_caso=detalhes_input,
                        protocolo=protocolo_input,
                    )
                    resultado = fase3_pipe.gerar_ato_pronto(pedido)

                    # Exibição do Semáforo da Alfândega
                    if resultado.canal.value == "VERDE":
                        canal_cor = "#28a745"
                        canal_bg = "#eafaf1"
                        canal_icone = "🟢"
                        canal_titulo = "CANAL VERDE — Liberação Ordinária Autorizada"
                    elif resultado.canal.value == "AMARELO":
                        canal_cor = "#e0a800"
                        canal_bg = "#fef9e7"
                        canal_icone = "🟡"
                        canal_titulo = "CANAL AMARELO — Liberação com Tarjamento Obrigatório"
                    else:
                        canal_cor = "#dc3545"
                        canal_bg = "#fdf2e9"
                        canal_icone = "🔴"
                        canal_titulo = "CANAL VERMELHO — Bloqueio / Nota Devolutiva Obrigatória"

                    st.markdown(
                        f"""
                        <div style="background-color: {canal_bg}; border-left: 6px solid {canal_cor}; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                            <h4 style="margin: 0; color: {canal_cor};">{canal_icone} {canal_titulo}</h4>
                            <p style="margin: 4px 0 0 0; font-size: 1.15em; font-weight: bold; color: #222;">Veredito: {resultado.veredito}</p>
                            <p style="margin: 8px 0 0 0; color: #444;"><strong>Orientação de Balcão:</strong> {resultado.instrucao_balcao}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Minuta Pronta
                    st.markdown("#### 📝 Minuta Formal do Ato")
                    st.text_area(
                        "Texto pronto para copiar no sistema do cartório:",
                        value=resultado.minuta_ato,
                        height=220,
                        key="minuta_box",
                    )
                    st.download_button(
                        "📥 Baixar Minuta (.txt)",
                        data=resultado.minuta_ato,
                        file_name=f"ato_{protocolo_input.replace('/', '_')}.txt",
                        mime="text/plain",
                    )

                    # Fundamentação e Auditoria
                    col_fund, col_audit = st.columns(2)
                    with col_fund:
                        with st.expander("⚖️ Fundamentação Legal Vinculante", expanded=True):
                            for fund in resultado.fundamentacao:
                                st.markdown(f"- **{fund.norma} ({fund.artigo})**: {fund.aplicacao}")

                    with col_audit:
                        with st.expander("🛡️ Registro de Auditoria LGPD (ROPA)", expanded=True):
                            st.markdown(f"- **Finalidade:** {resultado.auditoria_lgpd.finalidade}")
                            st.markdown(f"- **Base Legal:** {resultado.auditoria_lgpd.base_legal_lgpd}")
                            st.markdown(f"- **Salvaguardas:** {resultado.auditoria_lgpd.salvaguardas_adotadas}")
                            st.markdown(f"- **Conformidade:** {resultado.auditoria_lgpd.conformidade_cnj_149}")

                    st.caption(
                        f"⏱️ Tempo de resposta: {resultado.latencia_s}s · Fontes consultadas: {len(resultado.fontes_corpus)} dispositivos oficiais"
                    )

                except Exception as e:
                    st.error(f"Erro ao processar o ato pronto: {e}")
        else:
            st.info(
                "👈 **Selecione os parâmetros do pedido ao lado e clique em Processar Balcão.**\n\n"
                "A analogia da alfândega classifica a demanda instantaneamente:\n"
                "- 🟢 **Canal Verde:** Pedidos com dever legal de publicidade sem excesso de dados pessoais.\n"
                "- 🟡 **Canal Amarelo:** Pedidos deferíveis mediante tarjamento protetivo (CPF, filiação, etc.).\n"
                "- 🔴 **Canal Vermelho:** Pedidos ilegais, excessivos ou sem ordem judicial, gerando Nota Devolutiva."
            )


# ==============================================================================
# TAB 2: CONSULTA JURÍDICA LIVRE (CHAT RAG)
# ==============================================================================
with tab_chat:
    st.subheader("💬 Consulta Especializada em Linguagem Natural")
    st.caption("Pesquise dúvidas teóricas ou cenários complexos no acervo legal completo.")

    domain_option = st.selectbox(
        "Domínio Temático:",
        options=[
            "Auto (Detecção Automática)",
            "Registro de Imóveis & Cartórios (Fase 3)",
            "LGPD",
            "Licitações (Lei 14.133)",
            "Transparência Pública",
            "Código de Trânsito (CTB)",
        ],
        index=0,
    )

    domain_mapping = {
        "Auto (Detecção Automática)": "auto",
        "Registro de Imóveis & Cartórios (Fase 3)": "fase3",
        "LGPD": "lgpd",
        "Licitações (Lei 14.133)": "licitacoes",
        "Transparência Pública": "transparencia",
        "Código de Trânsito (CTB)": "ctb",
    }
    selected_domain = domain_mapping[domain_option]

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📎 Fontes citadas"):
                    for source, page in msg["sources"]:
                        st.write(f"- `{source}:p{page}`")

    user_query = st.chat_input("Ex.: O terceiro pode obter certidão de matrícula com CPF sem justificar motivo?")

    if user_query:
        st.session_state["messages"].append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            if selected_domain == "fase3":
                with st.spinner("Consultando normas da CGJ-CE e CNJ 149/2023..."):
                    pipe_fase3 = get_fase3_pipeline()
                    res = pipe_fase3.answer(user_query, k=5)
                    ans_text = _format_answer(res["answer"])
                    st.markdown(ans_text)
                    sources = res.get("sources", [])
                    if sources:
                        with st.expander("📎 Dispositivos Normativos"):
                            for s, p in sources:
                                st.write(f"- `{s}:p{p}`")
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": ans_text,
                        "sources": sources,
                    })
            else:
                with trace("query_handle", query=user_query, domain=selected_domain) as ctx:
                    trace_id = ctx["trace_id"]
                    log_query(selected_domain, user_query)

                    cached = exact_cache.get(user_query)
                    if cached:
                        st.success("⚡ Cache hit (exato)")
                        st.markdown(cached)
                        log_event("cache_hit", trace_id=trace_id, layer="exact")
                        st.session_state["messages"].append({
                            "role": "assistant",
                            "content": cached,
                            "sources": [],
                        })
                    else:
                        rag_pipeline = get_pipeline()
                        try:
                            decision = classify_complexity(user_query)
                            rag_pipeline.llm_model = decision.model
                            log_event("route_decision", trace_id=trace_id, **decision.__dict__)
                            log_model_choice(decision.model)
                        except Exception:
                            pass

                        with st.spinner("Processando resposta..."):
                            res = rag_pipeline.answer(user_query, domain=selected_domain)

                        ans_text = _format_answer(res["answer"])
                        st.markdown(ans_text)
                        sources = res.get("sources", [])
                        if sources:
                            with st.expander("📎 Fontes citadas"):
                                for s, p in sources:
                                    st.write(f"- `{s}:p{p}`")

                        exact_cache.put(user_query, res["answer"])
                        semantic_cache.put(user_query, res["answer"])
                        st.session_state["messages"].append({
                            "role": "assistant",
                            "content": ans_text,
                            "sources": sources,
                        })
        st.rerun()


# ==============================================================================
# TAB 3: BENCHMARK & VALIDAÇÃO
# ==============================================================================
with tab_benchmark:
    st.subheader("📊 Validação Empírica — Os 25 Casos de Balcão (Fase 3)")
    st.markdown(
        "Amostra dos casos críticos de conflito entre Publicidade Registral (Lei 6.015/73), Normas da CGJ-CE e LGPD. "
        "Utilizados no teste cego contra assistentes genéricos de mercado."
    )

    benchmark_json_path = _ROOT / "docs" / "fase3" / "benchmark" / "perguntas.json"
    if benchmark_json_path.exists():
        try:
            dados_bench = json.loads(benchmark_json_path.read_text(encoding="utf-8"))
            perguntas = dados_bench.get("perguntas", [])
            st.dataframe(
                [
                    {
                        "ID": p.get("id"),
                        "Categoria": p.get("categoria"),
                        "Pergunta Prática de Balcão": p.get("pergunta"),
                    }
                    for p in perguntas
                ],
                use_container_width=True,
                height=450,
            )
            st.info(
                f"Total de {len(perguntas)} casos catalogados. "
                "Para rodar a bateria completa de testes comparativos, utilize: `python scripts/benchmark/run_rag_benchmark.py --xlsx`."
            )
        except Exception as e:
            st.warning(f"Erro ao carregar perguntas do benchmark: {e}")
    else:
        st.info("Arquivo de perguntas do benchmark não localizado em docs/fase3/benchmark/perguntas.json.")


st.divider()
st.caption(
    "CartórioSeguro AI · Desenvolvido na Residência SiDi · Tecnologias: ChromaDB, Multilingual E5 (ONNX), BM25, Pydantic, Streamlit."
)
