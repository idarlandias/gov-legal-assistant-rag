import os
import zipfile
import urllib3
from pathlib import Path
import requests

# Desativa avisos de SSL inseguro (para sites de prefeituras/tribunais antigos)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parent
CORPUS_DIR = BASE_DIR / "data" / "corpus"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

DOCS = [
    # Domínio: lgpd
    {
        "domain": "lgpd",
        "url": "https://www2.senado.gov.br/bdsf/bitstream/handle/id/658231/Lei_geral_protecao_dados_pessoais_1ed.pdf",
        "filename": "LGPD-2023-ANPD.pdf",
    },
    # Domínio: licitacoes
    {
        "domain": "licitacoes",
        "url": "https://www2.senado.gov.br/bdsf/bitstream/handle/id/656845/Lei_licitacoes_contratos_administrativos_4ed.pdf",
        "filename": "Lei_licitacoes_contratos_administrativos_4ed.pdf",
    },
    # Domínio: transparencia
    {
        "domain": "transparencia",
        "url": "https://www.gov.br/acessoainformacao/pt-br/central-de-conteudo/publicacoes/gta-7-guia-de-transparencia-ativa-final.pdf",
        "filename": "gta_executivo_federal_7ed.pdf",
    },
    # Domínio: procedimentos
    {
        "domain": "procedimentos",
        "url": "https://www.tjba.jus.br/portal/wp-content/uploads/2017/10/manual_praticas_cartorarias_1_grau.pdf",
        "filename": "manual_praticas_cartorarias_1_grau.pdf",
    },
    {
        "domain": "procedimentos",
        "url": "https://www.oabsp.org.br/upload/2587661560.pdf",
        "filename": "cartilha_inss_digital_oabsp.pdf",
    },
    {
        "domain": "procedimentos",
        "url": "https://www.prefeitura.sp.gov.br/cidade/secretarias/upload/licenciamento/manual_usuario_licenciamento.pdf",
        "filename": "cartilha_licenciamento_alvara_prefeitura_sp.pdf",
    },
]


def download_doc(domain: str, url: str, filename: str) -> Path:
    dest_dir = CORPUS_DIR / domain
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    print(f"Baixando [{domain}] {url}...")
    headers = {"User-Agent": USER_AGENT}
    
    try:
        # Faz download usando requests com timeout e sem SSL estrito
        response = requests.get(url, headers=headers, verify=False, timeout=60)
        response.raise_for_status()
        
        dest_path.write_bytes(response.content)
        print(f"Salvo em {dest_path} (Tamanho: {len(response.content)/1e6:.2f} MB)")
    except Exception as e:
        print(f"ERRO ao baixar {url}: {e}")
        print("Tentando buscar arquivo local de fallback...")
        
        import shutil
        fallback_paths = []
        
        # Fallbacks na raiz de data/corpus
        fallback_paths.append(CORPUS_DIR / filename)
        if filename == "gta_executivo_federal_7ed.pdf":
            fallback_paths.append(CORPUS_DIR / "GTA_executivo_federal_7ed.pdf")
            
        # Fallbacks para licenciamento da prefeitura
        if filename == "cartilha_licenciamento_alvara_prefeitura_sp.pdf":
            fallback_paths.append(CORPUS_DIR / "procedimentos" / "prefeitura_servicos_municipais.pdf")
            fallback_paths.append(CORPUS_DIR / "prefeitura_servicos_municipais.pdf")

        copied = False
        for fb_path in fallback_paths:
            if fb_path.exists():
                print(f"Usando arquivo local de fallback: {fb_path}")
                shutil.copy(fb_path, dest_path)
                print(f"Copiado com sucesso para {dest_path} (Tamanho: {dest_path.stat().st_size/1e6:.2f} MB)")
                copied = True
                break
                
        if not copied:
            if dest_path.exists():
                print(f"Arquivo de destino já existe: {dest_path}. Mantendo versão existente.")
            else:
                raise e
                
    return dest_path


def main():
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = []

    for doc in DOCS:
        try:
            path = download_doc(doc["domain"], doc["url"], doc["filename"])
            downloaded.append(path)
        except Exception as e:
            print(f"ERRO ao baixar {doc['url']}: {e}\n")

    if not downloaded:
        print("Nenhum arquivo baixado. Verifique as URLs e sua conexão.")
        return

    zip_path = BASE_DIR / "corpus_completo.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in downloaded:
            # Salva o arquivo no zip com caminho relativo a partir de data/
            z.write(p, p.relative_to(BASE_DIR))

    print(f"\nZIP gerado em: {zip_path}")


if __name__ == "__main__":
    main()