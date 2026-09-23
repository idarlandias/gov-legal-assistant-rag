"""Pipeline RAG da Fase 3: mesmo fluxo de geração do RAGPipeline, com recuperação híbrida."""

from __future__ import annotations

from src.fase3.index import COLLECTION, open_collection
from src.fase3.retrieval import HybridRetriever
from src.pipeline.rag import RAGPipeline


class Fase3Pipeline(RAGPipeline):
    """Troca só o retrieve(): prompt, tools e chamada ao LLM continuam os do RAGPipeline."""

    def __init__(self, modo: str = "hibrido", **kwargs) -> None:
        # O super() abre a coleção com o embedding padrão; ela é substituída logo abaixo
        super().__init__(collection_name=COLLECTION, **kwargs)
        self.collection, self.embedder = open_collection()
        self.embed_model = self.embedder.name
        self.modo = modo
        self.retriever = HybridRetriever(self.collection, self.embedder)

    def retrieve(self, query: str, k: int = 5, domain: str | None = None) -> list[dict]:
        return self.retriever.search(query, k=k, modo=self.modo)
