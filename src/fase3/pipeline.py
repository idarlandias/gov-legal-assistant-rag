"""Pipeline RAG da Fase 3: recuperação híbrida + acervo normativo especializado do RI/CE."""

from __future__ import annotations

from src.fase3.corpus import GERAL, REGISTRO_IMOVEIS
from src.fase3.index import COLLECTION, open_collection
from src.fase3.retrieval import HybridRetriever
from src.pipeline.rag import RAGPipeline

# Recorte vertical: Registro de Imóveis + normas comuns a todas as serventias (LGPD, LAI,
# Lei 6.015 Título I, CNJ Livro I...). Registro Civil, Notas, Protesto e RTD ficam de fora.
ESPECIALIDADES_RI = frozenset({REGISTRO_IMOVEIS, GERAL})


def build_cartorio_prompt(context: str, query: str) -> str:
    """Prompt ancorado nas normas notariais e registrais do Ceará, CNJ 149/2023, Lei 6.015/73 e LGPD."""
    sanitized = query.replace("CONTEXTO:", "").replace("PERGUNTA:", "").strip()
    return f"""Você é o Assessor Técnico Especialista em Registro de Imóveis do Ceará e Compliance Registral (CGJ-CE, Provimento CNJ 149/2023, Lei 6.015/1973 e LGPD).

Responda à consulta jurídica de balcão com base EXCLUSIVAMENTE no contexto normativo abaixo.

DIRETRIZES DE RESPOSTA OBRIGATÓRIAS:
1. Responda diretamente e com segurança técnica: indique se o ato registral deve ser praticado integralmente, condicionado com tarjamento protetivo ou indeferido via Nota Devolutiva.
2. Cite SEMPRE o dispositivo legal ou normativo específico correspondente (artigo, parágrafo ou inciso do Código de Normas da CGJ-CE, do Provimento CNJ 149/2023, da Lei 6.015/1973 ou da LGPD).
3. NUNCA cite provimentos já revogados (ex.: Provimento CNJ 134/2022). O Provimento vigente do CNJ é o 149/2023.
4. Se a informação não constar expressamente no contexto fornecido, responda exatamente: "Não encontrado no corpus."

CONTEXTO NORMATIVO VIGENTE:
{context}

PERGUNTA:
{sanitized}

RESPOSTA JURÍDICA E OPERACIONAL:"""


class Fase3Pipeline(RAGPipeline):
    """Pipeline especializado da Fase 3 com recuperação híbrida e prompt do Foro Extrajudicial."""

    def __init__(self, modo: str = "hibrido", especialidades: frozenset[str] | None = ESPECIALIDADES_RI,
                 **kwargs) -> None:
        # O super() abre a coleção com o embedding padrão; ela é substituída logo abaixo
        super().__init__(collection_name=COLLECTION, **kwargs)
        self.collection, self.embedder = open_collection()
        self.embed_model = self.embedder.name
        self.modo = modo
        self.especialidades = set(especialidades) if especialidades else None
        self.retriever = HybridRetriever(self.collection, self.embedder)

    def retrieve(self, query: str, k: int = 5, domain: str | None = None) -> list[dict]:
        return self.retriever.search(query, k=k, modo=self.modo, especialidades=self.especialidades)

    def answer(self, question: str, k: int = 5, domain: str | None = None) -> dict:
        """Pipeline completo da Fase 3: busca híbrida + contexto com dispositivos oficiais + prompt cartorial."""
        hits = self.retrieve(question, k=k)
        if not hits:
            return {"answer": "Não encontrado no corpus.", "sources": []}

        context = "\n\n---\n\n".join(
            f"[{h.get('dispositivo') or h['source']}:p{h['page']}]\n{h['text']}" for h in hits
        )

        prompt = build_cartorio_prompt(context=context, query=question)
        messages = [{"role": "user", "content": prompt}]

        is_reasoner = "reasoner" in self.llm_model.lower() or "deepseek-r1" in self.llm_model.lower()
        api_kwargs = {
            "model": self.llm_model,
            "messages": messages,
        }
        if not is_reasoner:
            api_kwargs["temperature"] = 0.0

        response = self._call_chat_completions(**api_kwargs)
        answer_text = response.choices[0].message.content or ""

        return {
            "answer": answer_text,
            "sources": [(h.get("dispositivo") or h["source"], h["page"]) for h in hits],
        }

    def gerar_ato_pronto(self, pedido, k: int = 5):
        """Emite o Ato Pronto (veredito, minuta e auditoria LGPD) para balcão de Registro de Imóveis."""
        from src.fase3.ato_pronto import processar_ato_pronto
        return processar_ato_pronto(self, pedido=pedido, k=k)

    def tarjar_matricula(self, texto: str, solicitante: str = "Terceiro sem vínculo comprovado", protocolo: str = "PROT-BALCAO"):
        """Inspeciona texto registral, aplica tarjamento legal e gera carimbo com hash SHA-256."""
        from src.fase3.tarjador import tarjar_texto_matricula
        return tarjar_texto_matricula(texto_matricula=texto, solicitante=solicitante, protocolo=protocolo)
