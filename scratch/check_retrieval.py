from dotenv import load_dotenv
load_dotenv()
import sys
sys.path.insert(0, ".")
from src.pipeline.rag import RAGPipeline

def main():
    p = RAGPipeline()
    res = p.retrieve('Qual o conceito de contabilidade?', domain='concursos', k=5)
    out_lines = []
    for r in res:
        out_lines.append(f"=== {r['source']} p. {r['page']} (dist: {r['distance']:.4f}) ===")
        out_lines.append(r['text'])
        out_lines.append("\n" + "="*40 + "\n")
        
    out = "\n".join(out_lines)
    with open('scratch/res_teste.txt', 'w', encoding='utf-8') as f:
        f.write(out)
    print("Concluído! Trechos salvos em scratch/res_teste.txt.")

if __name__ == "__main__":
    main()
