"""Cache em 2 niveis: exact-match (SHA256) + semantic (cosine similarity).

Reaproveita o notebook 05. Voce vai preencher 1 TODO aqui.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any

import numpy as np
from openai import OpenAI
from src.pipeline.security_skill import get_env_secret


class ExactCache:
    """Cache por hash SHA256 da query. Captura replays exatos (~10-15% das queries)."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    @staticmethod
    def _key(query: str) -> str:
        return hashlib.sha256(query.encode()).hexdigest()

    def get(self, query: str) -> str | None:
        return self._store.get(self._key(query))

    def put(self, query: str, answer: str) -> None:
        self._store[self._key(query)] = answer

    def stats(self) -> dict[str, int]:
        return {"size": len(self._store)}


class SemanticCache:
    """Cache por similaridade de embedding. Captura parafrases (~20% adicional)."""

    def __init__(self, threshold: float = 0.93) -> None:
        self.threshold = threshold
        self._queries: list[str] = []
        self._embeddings: list[np.ndarray] = []
        self._answers: list[str] = []

        # Inicializa cliente para embeddings (mesmo provider do RAG)
        try:
            gemini_key = get_env_secret("GEMINI_API_KEY")
            self._client = OpenAI(
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            self._embed_model = os.environ.get("EMBED_MODEL", "gemini-embedding-001")
        except RuntimeError:
            try:
                openai_key = get_env_secret("OPENAI_API_KEY")
                self._client = OpenAI(api_key=openai_key)
                self._embed_model = "text-embedding-3-small"
            except RuntimeError:
                raise RuntimeError("Configure GEMINI_API_KEY ou OPENAI_API_KEY no .env")

    def _embed(self, text: str) -> np.ndarray | None:
        """Gera embedding com retry em caso de RateLimitError. Retorna None em falha."""
        import time
        from openai import RateLimitError
        
        for attempt in range(3):
            try:
                r = self._client.embeddings.create(model=self._embed_model, input=text)
                return np.array(r.data[0].embedding, dtype=float)
            except RateLimitError:
                if attempt < 2:
                    time.sleep(2 ** attempt)  # backoff: 1s, 2s
                    continue
                return None  # esgotou retries — cache miss gracioso
            except Exception:
                return None  # qualquer outro erro — cache miss gracioso
        return None

    # ------------------------------------------------------------------ TODO 5
    def get(self, query: str) -> str | None:
        """Retorna resposta cacheada se similar a query alguma anterior, OU None."""
        if not self._queries:
            return None

        # 1. Embedar a query
        e = self._embed(query)
        if e is None:
            return None  # cache miss gracioso

        # 2. Calcular similaridade cosseno contra todos os embeddings em cache
        sims = []
        norm_e = np.linalg.norm(e)
        if norm_e == 0:
            return None

        for em in self._embeddings:
            if em is None:
                sims.append(0.0)
                continue
            norm_em = np.linalg.norm(em)
            if norm_em == 0:
                sims.append(0.0)
            else:
                cos_sim = np.dot(e, em) / (norm_e * norm_em)
                sims.append(cos_sim)

        # 3. Pegar idx do maior
        idx = int(np.argmax(sims))

        # 4. Se sims[idx] >= self.threshold, retornar a resposta correspondente
        if sims[idx] >= self.threshold:
            return self._answers[idx]

        return None

    def put(self, query: str, answer: str) -> None:
        emb = self._embed(query)
        if emb is not None:
            self._queries.append(query)
            self._embeddings.append(emb)
            self._answers.append(answer)

    def stats(self) -> dict[str, Any]:
        return {"size": len(self._queries), "threshold": self.threshold}
