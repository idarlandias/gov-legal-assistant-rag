"""Pipeline RAG da Fase 3: mesmo fluxo de geração do RAGPipeline, com recuperação híbrida."""

from __future__ import annotations

from src.fase3.corpus import GERAL, REGISTRO_IMOVEIS
from src.fase3.index import COLLECTION, open_collection
from src.fase3.retrieval import HybridRetriever
from src.pipeline.rag import RAGPipeline

# Recorte vertical: Registro de Imóveis + normas comuns a todas as serventias (LGPD, LAI,
# Lei 6.015 Título I, CNJ Livro I...). Registro Civil, Notas, Protesto e RTD ficam de fora.
ESPECIALIDADES_RI = frozenset({REGISTRO_IMOVEIS, GERAL})


class Fase3Pipeline(RAGPipeline):
    """Troca só o retrieve(): prompt, tools e chamada ao LLM continuam os do RAGPipeline."""

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

    def gerar_ato_pronto(self, pedido, k: int = 5):
        """Emite o Ato Pronto (veredito, minuta e auditoria LGPD) para balcão de Registro de Imóveis."""
        from src.fase3.ato_pronto import processar_ato_pronto
        return processar_ato_pronto(self, pedido=pedido, k=k)

