import sys
from pathlib import Path
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import time
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, ".")
from src.pipeline.rag import RAGPipeline

def main():
    pipeline = RAGPipeline()
    print("Total de chunks antes:", pipeline.collection.count())
    print("Limpando chunks do dominio 'concursos' para evitar duplicidades...")
    pipeline.collection.delete(where={"dominio": "concursos"})
    print("Total de chunks apos limpeza:", pipeline.collection.count())

    concursos_dir = Path("data/corpus/concursos")
    if not concursos_dir.exists() or not list(concursos_dir.rglob("*.pdf")):
        print("Nenhum PDF encontrado na pasta concursos.")
        return

    docs = []
    for pdf_path in sorted(concursos_dir.rglob("*.pdf")):
        print(f"Lendo PDF: {pdf_path.name}")
        reader = PdfReader(pdf_path)
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                docs.append({
                    "text": text,
                    "source": pdf_path.name,
                    "page": page_idx + 1,
                    "filepath": str(pdf_path)
                })

    print(f"Lidas {len(docs)} páginas de concursos.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for doc in docs:
        filename = doc["source"]
        for i, chunk_text in enumerate(splitter.split_text(doc["text"])):
            chunks.append({
                "id": f"{filename}-p{doc['page']}-c{i}",
                "text": chunk_text,
                "source": filename,
                "page": doc["page"],
                "dominio": "concursos",
                "fonte": filename,
                "tipo_documento": "apostila",
            })

    print(f"Gerados {len(chunks)} chunks de concursos.")

    BATCH = 30 # Lote seguro
    for start in range(0, len(chunks), BATCH):
        lote = chunks[start : start + BATCH]
        
        retries = 5
        wait_time = 6
        success = False
        while retries > 0 and not success:
            try:
                pipeline.collection.add(
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
                print(f"Indexados mais {len(lote)} chunks...")
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "rate_limit" in err_str.lower() or "exhausted" in err_str.lower() or "limit" in err_str.lower():
                    print(f"Rate limit atingido. Aguardando {wait_time} segundos para tentar novamente... (Tentativas restantes: {retries})")
                    time.sleep(wait_time)
                    wait_time = wait_time * 2 + 2
                    retries -= 1
                else:
                    print(f"Erro inesperado ao adicionar lote: {e}")
                    raise e
                    
        if not success:
            print("Falha ao indexar lote apos varias tentativas devido a Rate Limit.")
            sys.exit(1)
            
        time.sleep(5.0) # Evita 429 da API Gemini (15 RPM de embeddings)

    print("Total de chunks depois:", pipeline.collection.count())

if __name__ == "__main__":
    main()
