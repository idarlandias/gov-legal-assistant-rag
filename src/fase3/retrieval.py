"""Recuperação híbrida da Fase 3: embedding multilíngue (E5 em ONNX) + BM25, fundidos por RRF.

Por que: o embedding padrão do Chroma (all-MiniLM-L6-v2) é treinado em inglês e não
recuperava artigos óbvios (Lei 6.015, Art. 17 ficou fora do top 300 na pergunta 1).
O E5 multilíngue entende português; o BM25 garante o casamento literal de números de
lei/provimento ("15/2026", "6.015") que embeddings tendem a ignorar.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any

import numpy as np

EMBED_REPO = "intfloat/multilingual-e5-small"  # MIT, 384 dim, ~450 MB em ONNX fp32
EMBED_ONNX = "onnx/model.onnx"
EMBED_TOKENIZER = "onnx/tokenizer.json"


# ---------------------------------------------------------------- embedding E5 (ONNX, sem torch)

class E5Embedder:
    """multilingual-e5 via onnxruntime. E5 exige os prefixos "query: " e "passage: "."""

    def __init__(self, repo: str = EMBED_REPO, max_len: int = 512, batch_size: int = 32) -> None:
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer

        self.name = repo
        self.batch_size = batch_size
        self.tok = Tokenizer.from_file(hf_hub_download(repo, EMBED_TOKENIZER))
        self.tok.enable_truncation(max_len)
        self.tok.enable_padding(pad_id=self.tok.token_to_id("<pad>"), pad_token="<pad>")
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.sess = ort.InferenceSession(hf_hub_download(repo, EMBED_ONNX), opts,
                                         providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.sess.get_inputs()}

    def _embed(self, texts: list[str], progress=None) -> np.ndarray:
        out = np.zeros((len(texts), 384), dtype=np.float32)
        # ordena por tamanho: lotes com comprimentos parecidos desperdiçam menos padding
        ordem = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        for start in range(0, len(ordem), self.batch_size):
            idx = ordem[start:start + self.batch_size]
            enc = self.tok.encode_batch([texts[i] for i in idx])
            ids = np.array([e.ids for e in enc], dtype=np.int64)
            mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
            feeds = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self.inputs:
                feeds["token_type_ids"] = np.zeros_like(ids)
            hidden = self.sess.run(None, feeds)[0]  # (lote, seq, 384)
            m = mask[..., None].astype(np.float32)
            vec = (hidden * m).sum(1) / np.clip(m.sum(1), 1e-9, None)  # mean pooling
            out[idx] = vec / np.linalg.norm(vec, axis=1, keepdims=True)
            if progress:
                progress(min(start + self.batch_size, len(texts)), len(texts))
        return out

    def embed_passages(self, texts: list[str], progress=None) -> np.ndarray:
        return self._embed([f"passage: {t}" for t in texts], progress)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([f"query: {text}"])[0]


class E5ChromaFunction:
    """Adaptador para o Chroma: se alguém usar query_texts na coleção, o vetor ainda é E5."""

    def __init__(self, embedder: E5Embedder) -> None:
        self.embedder = embedder

    def __call__(self, input: list[str]) -> list[np.ndarray]:  # noqa: A002 (assinatura do Chroma)
        return list(self.embedder.embed_passages(list(input)))

    @staticmethod
    def name() -> str:
        return "multilingual-e5-onnx"

    def is_legacy(self) -> bool:
        return False

    def get_config(self) -> dict:
        return {}

    @staticmethod
    def build_from_config(config: dict) -> "E5ChromaFunction":
        return E5ChromaFunction(E5Embedder())


# ---------------------------------------------------------------- BM25

STOPWORDS = set("""
a o as os um uma uns umas de do da dos das em no na nos nas por pelo pela pelos pelas para
com sem sob sobre entre ate e ou nem que se ao aos à às é ser foi sao são seu sua seus suas
este esta estes estas esse essa esses essas isto isso aquele aquela lhe lhes me te nos vos
eu tu ele ela eles elas mais menos muito ja tambem como quando onde qual quais quem cujo
nao sim ha pode posso devo deve tem ter the
""".split())


def _sem_acento(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def tokenize(text: str, prefixo: int = 6) -> list[str]:
    """Minúsculas, sem acento, sem stopwords; "6.015"→"6015"; radical = 6 primeiras letras.

    O corte por prefixo é um stemmer barato para português: certidão/certidões → "certid".
    """
    t = _sem_acento(text.lower())
    t = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", t)  # ponto de milhar em número de lei/artigo
    out = []
    for tok in re.findall(r"[a-z]+|\d+", t):
        if tok in STOPWORDS or (len(tok) < 2 and not tok.isdigit()):
            continue
        out.append(tok if tok.isdigit() else tok[:prefixo])
    return out


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.tf: list[Counter] = [Counter(tokenize(d)) for d in docs]
        self.len = np.array([sum(c.values()) for c in self.tf], dtype=np.float32)
        self.avg = float(self.len.mean()) if len(docs) else 0.0
        self.postings: dict[str, list[int]] = defaultdict(list)
        for i, c in enumerate(self.tf):
            for term in c:
                self.postings[term].append(i)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - len(p) + 0.5) / (len(p) + 0.5)) for t, p in self.postings.items()}

    def scores(self, query: str) -> dict[int, float]:
        acc: dict[int, float] = defaultdict(float)
        for term in set(tokenize(query)):
            idf = self.idf.get(term)
            if idf is None:
                continue
            for i in self.postings[term]:
                f = self.tf[i][term]
                norm = self.k1 * (1 - self.b + self.b * self.len[i] / self.avg)
                acc[i] += idf * f * (self.k1 + 1) / (f + norm)
        return acc

    def top(self, query: str, n: int) -> list[int]:
        s = self.scores(query)
        return sorted(s, key=lambda i: -s[i])[:n]


# ---------------------------------------------------------------- fusão

def rrf(rankings: list[list[str]], k: int = 60, pesos: list[float] | None = None) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion: soma 1/(k + posição) de cada lista."""
    pesos = pesos or [1.0] * len(rankings)
    acc: dict[str, float] = defaultdict(float)
    for w, ranking in zip(pesos, rankings):
        for pos, doc_id in enumerate(ranking):
            acc[doc_id] += w / (k + pos + 1)
    return sorted(acc.items(), key=lambda x: -x[1])


class HybridRetriever:
    def __init__(self, collection, embedder: E5Embedder, candidatos: int = 50, rrf_k: int = 60) -> None:
        self.collection = collection
        self.embedder = embedder
        self.candidatos = candidatos
        self.rrf_k = rrf_k
        data = collection.get(include=["documents", "metadatas"])
        self.ids: list[str] = data["ids"]
        self.docs: dict[str, str] = dict(zip(data["ids"], data["documents"]))
        self.metas: dict[str, dict] = dict(zip(data["ids"], data["metadatas"]))
        self.bm25 = BM25(data["documents"])

    def dense(self, query: str, n: int) -> list[str]:
        qv = self.embedder.embed_query(query)
        res = self.collection.query(query_embeddings=[qv.tolist()], n_results=n, include=[])
        return res["ids"][0]

    def sparse(self, query: str, n: int) -> list[str]:
        return [self.ids[i] for i in self.bm25.top(query, n)]

    def search(self, query: str, k: int = 5, modo: str = "hibrido") -> list[dict[str, Any]]:
        if modo == "denso":
            fused = [(i, 0.0) for i in self.dense(query, k)]
        elif modo == "bm25":
            fused = [(i, 0.0) for i in self.sparse(query, k)]
        else:
            fused = rrf([self.dense(query, self.candidatos), self.sparse(query, self.candidatos)],
                        k=self.rrf_k)
        return [
            {"id": i, "text": self.docs[i], "source": self.metas[i]["source"],
             "page": self.metas[i]["page"], "distance": -score, **{
                 key: self.metas[i].get(key) for key in ("fonte_id", "dispositivo")}}
            for i, score in fused[:k]
        ]
