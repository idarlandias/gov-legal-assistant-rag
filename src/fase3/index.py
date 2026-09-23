"""Chunking por dispositivo e indexação do corpus da Fase 3 numa coleção Chroma própria."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.fase3.corpus import CORPUS_DIR, ROOT, Dispositivo, load_manifest, save_manifest, segment, to_jsonl
from src.fase3.sources import FONTES, Fonte

CHROMA_DIR = ROOT / "data" / "chroma"
COLLECTION = "fase3"
DOMINIO = "fase3"
JSONL = CORPUS_DIR / "dispositivos.jsonl"

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200, chunk_overlap=150, separators=["\n\n", "\n", ". ", " ", ""]
)


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict


def citacao(fonte: Fonte, d: Dispositivo) -> str:
    """Rótulo que o LLM vê no contexto e deve citar: "Lei 6.015/1973, Art. 17"."""
    return f"{fonte.sigla}, {d.dispositivo}"


def build_chunks(fonte: Fonte, dispositivos: list[Dispositivo]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for i, d in enumerate(dispositivos):
        cab = citacao(fonte, d) + (f" ({d.secao})" if d.secao else "")
        partes = _splitter.split_text(d.texto) or [d.texto]
        for j, parte in enumerate(partes):
            sufixo = f" [parte {j + 1}/{len(partes)}]" if len(partes) > 1 else ""
            chunks.append(Chunk(
                id=f"{fonte.id}-{i:05d}-{j:02d}",
                # cabeçalho no texto: o embedding "sabe" de qual lei e artigo é o trecho
                text=f"{cab}{sufixo}\n{parte}",
                metadata={
                    "source": citacao(fonte, d),
                    "page": d.pagina,
                    "dominio": DOMINIO,
                    "fonte": fonte.url,
                    "tipo_documento": fonte.tipo,
                    "esfera": fonte.esfera,
                    "fonte_id": fonte.id,
                    "dispositivo": d.dispositivo,
                    "secao": d.secao,
                },
            ))
    return chunks


def build_all(fontes: list[Fonte] = FONTES) -> tuple[list[Chunk], dict[str, dict]]:
    """Segmenta todas as fontes, grava dispositivos.jsonl e devolve chunks + estatísticas."""
    todos: list[Dispositivo] = []
    chunks: list[Chunk] = []
    stats: dict[str, dict] = {}
    for fonte in fontes:
        ds = segment(fonte)
        if not ds:
            raise RuntimeError(f"{fonte.id}: nenhum texto extraído (PDF escaneado ou página mudou?)")
        cs = build_chunks(fonte, ds)
        todos.extend(ds)
        chunks.extend(cs)
        stats[fonte.id] = {
            "dispositivos": len(ds),
            "artigos": sum(d.dispositivo.startswith("Art.") for d in ds),
            "chunks": len(cs),
            "caracteres": sum(len(d.texto) for d in ds),
        }
    JSONL.write_text(to_jsonl(todos), encoding="utf-8")
    return chunks, stats


def index(chunks: list[Chunk], collection, embeddings, batch: int = 500) -> int:
    for start in range(0, len(chunks), batch):
        lote = chunks[start:start + batch]
        collection.add(
            ids=[c.id for c in lote],
            documents=[c.text for c in lote],
            metadatas=[c.metadata for c in lote],
            embeddings=embeddings[start:start + batch],
        )
    return collection.count()


def open_collection(embedder=None, create: bool = False):
    """Abre a coleção fase3 com o E5 e recusa índice feito com outro modelo.

    Os dois modelos geram vetores de 384 dimensões: consultar com o modelo errado não dá erro,
    só devolve lixo. Por isso o nome do modelo fica gravado nos metadados da coleção.
    """
    import chromadb

    from src.fase3.retrieval import EMBED_REPO, E5ChromaFunction, E5Embedder

    embedder = embedder or E5Embedder()
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = E5ChromaFunction(embedder)
    if create:
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass  # coleção ainda não existia
        col = client.create_collection(COLLECTION, embedding_function=ef,
                                       metadata={"embed_model": EMBED_REPO})
    else:
        col = client.get_collection(COLLECTION, embedding_function=ef)
        modelo = (col.metadata or {}).get("embed_model")
        if modelo != EMBED_REPO:
            raise RuntimeError(f"Coleção '{COLLECTION}' foi indexada com '{modelo}', não '{EMBED_REPO}'. "
                               "Rode: python scripts/fase3/build_corpus.py index")
    return col, embedder


def rebuild(fontes: list[Fonte] = FONTES, progress=print) -> dict[str, dict]:
    """Recria a coleção fase3 do zero a partir de raw/ e registra estatísticas no manifest."""
    from src.fase3.retrieval import EMBED_REPO, E5Embedder

    chunks, stats = build_all(fontes)
    ids = [c.id for c in chunks]
    if len(ids) != len(set(ids)):
        raise RuntimeError("IDs de chunk duplicados")

    embedder = E5Embedder()
    passo = max(1, len(chunks) // 10)
    embeddings = embedder.embed_passages(
        [c.text for c in chunks],
        progress=lambda feitos, total: feitos % passo < embedder.batch_size
        and progress(f"  embeddings {feitos}/{total}"),
    )
    collection, _ = open_collection(embedder, create=True)
    total = index(chunks, collection, embeddings.tolist())
    if total != len(chunks):
        raise RuntimeError(f"Chroma tem {total} chunks, esperado {len(chunks)}")

    manifest = load_manifest()
    for fid, st in stats.items():
        manifest.setdefault(fid, {})["indice"] = {**st, "embed_model": EMBED_REPO}
    save_manifest(manifest)
    return stats
