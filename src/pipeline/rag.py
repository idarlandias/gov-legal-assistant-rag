"""RAG pipeline — chunk, embed, index, retrieve, generate.

Reaproveita as funcoes do notebook 02. Voce vai preencher 3 TODOs aqui.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from openai import OpenAI
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.pipeline.tools import TOOLS, run_tool_call
from src.pipeline.security_skill import get_env_secret, build_secure_prompt, build_concursos_prompt


def _make_client() -> tuple[OpenAI, str]:
    """Inicializa cliente OpenAI-compatible conforme provider escolhido no .env."""
    try:
        api_key = get_env_secret("GEMINI_API_KEY")
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        embed_api_base = "https://generativelanguage.googleapis.com/v1beta/openai/"
    except RuntimeError:
        try:
            api_key = get_env_secret("OPENAI_API_KEY")
            client = OpenAI(api_key=api_key)
            embed_api_base = None
        except RuntimeError:
            raise RuntimeError("Configure GEMINI_API_KEY ou OPENAI_API_KEY no .env")
    return client, embed_api_base


class RAGPipeline:
    """Pipeline RAG end-to-end com Chroma local."""

    def __init__(
        self,
        corpus_dir: str = "data/corpus",
        persist_dir: str = "data/chroma",
        collection_name: str = "docs",
        llm_model: str | None = None,
        embed_model: str | None = None,
    ) -> None:
        self.client, embed_api_base = _make_client()
        self.llm_model = llm_model or os.environ.get("LLM_MODEL", "gemini-2.5-flash-lite")
        self.embed_model = embed_model or os.environ.get("EMBED_MODEL", "gemini-embedding-001")

        try:
            api_key = get_env_secret("GEMINI_API_KEY")
        except RuntimeError:
            try:
                api_key = get_env_secret("OPENAI_API_KEY")
            except RuntimeError:
                raise RuntimeError("Configure GEMINI_API_KEY ou OPENAI_API_KEY no .env")

        embed_kwargs: dict[str, Any] = {
            "api_key": api_key,
            "model_name": self.embed_model,
        }
        if embed_api_base:
            embed_kwargs["api_base"] = embed_api_base
        self.embed_fn = OpenAIEmbeddingFunction(**embed_kwargs)

        self.corpus_dir = Path(corpus_dir)
        self.persist_dir = persist_dir
        self.collection_name = collection_name

        import shutil
        from chromadb.config import Settings
        os.makedirs(persist_dir, exist_ok=True)
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(allow_reset=True)
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name, embedding_function=self.embed_fn
            )
            # Valida se o banco consegue contar (verifica corrupção ou incompatibilidade)
            self.collection.count()
        except Exception as e:
            print(f"Aviso: Falha ao carregar ChromaDB ({e}). Limpando cache e recriando do zero...")
            try:
                if os.path.exists(persist_dir):
                    shutil.rmtree(persist_dir)
            except Exception as rm_err:
                print(f"Erro ao remover diretorio do banco: {rm_err}")
                
            os.makedirs(persist_dir, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(allow_reset=True)
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name, embedding_function=self.embed_fn
            )

    # ------------------------------------------------------------------ TODO 1
    def ingest_and_index(self) -> int:
        """Le PDFs de `corpus_dir`, faz chunking e indexa em Chroma.

        Retorna numero de chunks indexados.

        Ja deixei a estrutura do ciclo. Voce completa as 3 partes marcadas.
        """
        # SEU CODIGO AQUI — TODO 1.A
        docs: list[dict] = []
        for pdf_path in sorted(self.corpus_dir.rglob("*.pdf")):
            reader = PdfReader(pdf_path)
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    docs.append(
                        {
                            "text": text,
                            "source": pdf_path.name,
                            "page": page_idx + 1,
                            "filepath": str(pdf_path),
                        }
                    )
        
        # Suporte a arquivos TXT (como o CTB do Planalto)
        for txt_path in sorted(self.corpus_dir.rglob("*.txt")):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    text = f.read()
                if text.strip():
                    docs.append(
                        {
                            "text": text,
                            "source": txt_path.name,
                            "page": 1,
                            "filepath": str(txt_path),
                        }
                    )
            except Exception as e:
                print(f"Erro ao ler TXT {txt_path}: {e}")

        # SEU CODIGO AQUI — TODO 1.B
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks: list[dict] = []
        for doc in docs:
            filename = doc["source"]
            filepath = doc.get("filepath", "")
            # Classificacao do dominio e metadados com base no nome do arquivo ou caminho
            if "procedimentos" in filepath.lower() or "procedimentos" in filename.lower():
                dominio = "procedimentos"
                fonte = filename
                tipo_doc = "manual_servico"
            elif "ctb" in filepath.lower() or "ctb" in filename.lower():
                dominio = "ctb"
                fonte = "https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm"
                tipo_doc = "lei"
            elif "concursos" in filepath.lower() or "concursos" in filename.lower():
                dominio = "concursos"
                fonte = filename
                tipo_doc = "apostila"
            elif "LGPD" in filename or "13709" in filename:
                dominio = "lgpd"
                fonte = "https://www2.senado.gov.br/bdsf/handle/id/658231"
                tipo_doc = "lei"
            elif "licitacoes" in filename.lower() or "14133" in filename:
                dominio = "licitacoes"
                fonte = "https://www2.senado.gov.br/bdsf/handle/id/656845"
                tipo_doc = "lei"
            elif "gta" in filename.lower() or "transparencia" in filename.lower():
                dominio = "transparencia"
                fonte = "https://www.gov.br/acessoainformacao/pt-br/central-de-conteudo/publicacoes/gta-7-guia-de-transparencia-ativa-final.pdf"
                tipo_doc = "guia"
            else:
                dominio = "auto"
                fonte = "desconhecido"
                tipo_doc = "manual"

            for i, chunk_text in enumerate(splitter.split_text(doc["text"])):
                chunks.append(
                    {
                        "id": f"{filename}-p{doc['page']}-c{i}",
                        "text": chunk_text,
                        "source": filename,
                        "page": doc["page"],
                        "dominio": dominio,
                        "fonte": fonte,
                        "tipo_documento": tipo_doc,
                    }
                )

        # SEU CODIGO AQUI — TODO 1.C
        import time
        import sys
        BATCH = 45
        for start in range(0, len(chunks), BATCH):
            lote = chunks[start : start + BATCH]
            
            retries = 5
            wait_time = 12
            success = False
            while retries > 0 and not success:
                try:
                    self.collection.add(
                        ids=[c["id"] for c in lote],
                        documents=[c["text"] for c in lote],
                        metadatas=[
                            {
                                "source": c["source"],
                                "page": c["page"],
                                "dominio": c["dominio"],
                                "fonte": c["fonte"],
                                "tipo_documento": c["tipo_documento"],
                            }
                            for c in lote
                        ],
                    )
                    success = True
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "rate_limit" in err_str.lower() or "exhausted" in err_str.lower() or "limit" in err_str.lower():
                        print(f"Rate limit atingido na nuvem. Aguardando {wait_time} segundos... (Tentativas: {retries})")
                        time.sleep(wait_time)
                        wait_time = wait_time * 2 + 2
                        retries -= 1
                    else:
                        raise e
            
            if not success:
                raise RuntimeError("Falha de Rate Limit ao indexar no Streamlit Cloud.")
                
            time.sleep(1.0)

        return self.collection.count()

    # ------------------------------------------------------------------ TODO 2
    def retrieve(self, query: str, k: int = 5, domain: str | None = None) -> list[dict]:
        """Busca top-k chunks similares a query, opcionalmente filtrando por dominio."""
        query_kwargs = {
            "query_texts": [query],
            "n_results": k
        }
        if domain and domain.lower() != "auto":
            query_kwargs["where"] = {"dominio": domain.lower()}

        result = self.collection.query(**query_kwargs)

        if not result or not result.get("documents") or not result["documents"][0]:
            return []

        return [
            {
                "text": result["documents"][0][i],
                "source": result["metadatas"][0][i]["source"],
                "page": result["metadatas"][0][i]["page"],
                "distance": result["distances"][0][i],
            }
            for i in range(len(result["documents"][0]))
        ]

    # ------------------------------------------------------------------ TODO 3
    def answer(self, question: str, k: int = 5, domain: str | None = None) -> dict:
        """Pipeline completo: retrieve + augment + generate. Retorna {answer, sources}."""
        # Roteamento determinístico para citação exata de artigos do CTB (evita fragmentação de incisos)
        is_ctb_query = (domain == "ctb") or (
            domain == "auto" and any(keyword in question.lower() for keyword in ["ctb", "trânsito", "transito", "rodoviário", "rodoviario", "multa", "velocidade"])
        )
        if is_ctb_query:
            import re
            match = re.search(r'\b(?:art\.|artigo)\s*(\d+(?:-[a-zA-Z]+)?)\b', question, re.IGNORECASE)
            if match:
                art_num = match.group(1)
                from src.pipeline.tools import cite_ctb_article
                art_text = cite_ctb_article(art_num)
                if "não encontrado" not in art_text.lower():
                    prompt = build_secure_prompt(context=art_text, query=question)
                    messages = [{"role": "user", "content": prompt}]
                    response = self.client.chat.completions.create(
                        model=self.llm_model,
                        messages=messages,
                        temperature=0.0
                    )
                    return {
                        "answer": response.choices[0].message.content or "",
                        "sources": [("CTB_compilado.txt", 1)]
                    }

        hits = self.retrieve(question, k=k, domain=domain)

        # 1. Montar contexto concatenando os textos dos hits com cabecalho [source:page]
        context = "\n\n---\n\n".join(f"[{h['source']}:p{h['page']}]\n{h['text']}" for h in hits)

        # 2. Construir prompt seguro dependendo do dominio
        if domain == "concursos":
            prompt = build_concursos_prompt(context=context, query=question)
        else:
            prompt = build_secure_prompt(context=context, query=question)

        # 3. Chamar self.client.chat.completions.create com suporte a tools
        messages = [{"role": "user", "content": prompt}]
        api_kwargs = {
            "model": self.llm_model,
            "messages": messages,
            "temperature": 0.0,
        }
        if TOOLS:
            api_kwargs["tools"] = TOOLS

        response = self.client.chat.completions.create(**api_kwargs)
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)

        if tool_calls:
            # Adiciona a mensagem do assistente com as tool calls solicitadas
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            })

            # Executa cada uma das tool calls e adiciona a mensagem do tipo tool correspondente
            for tool_call in tool_calls:
                result_str = run_tool_call(tool_call.function.name, tool_call.function.arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": result_str
                })

            # Segunda chamada para o LLM gerar a resposta com base nos retornos das tools
            second_response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=0.0
            )
            answer_text = second_response.choices[0].message.content or ""
        else:
            answer_text = message.content or ""

        # 4. Retornar {"answer": resposta, "sources": [(s, p) for h in hits]}
        return {
            "answer": answer_text,
            "sources": [(h["source"], h["page"]) for h in hits],
        }


PROMPT_TEMPLATE = """Voce e um assistente tecnico. Responda APENAS com base no contexto abaixo.
Se a informacao nao estiver no contexto, diga "Nao encontrado no corpus".
Sempre cite a fonte usando o formato [arquivo:pagina].

CONTEXTO:
{context}

PERGUNTA: {question}

RESPOSTA:"""


def build_rag_pipeline(corpus_dir: str = "data/corpus") -> RAGPipeline:
    """Factory: cria pipeline e indexa corpus se ainda nao indexado."""
    pipeline = RAGPipeline(corpus_dir=corpus_dir)
    if pipeline.collection.count() == 0:
        pipeline.ingest_and_index()
    return pipeline
