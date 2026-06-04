import logging
import sys
from pathlib import Path
from urllib.request import Request, urlopen

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("project-download")

CORPUS_FILES = [
    {
        "filename": "LGPD-2023-ANPD.pdf",
        "url": "https://www2.senado.gov.br/bdsf/bitstream/handle/id/658231/Lei_geral_protecao_dados_pessoais_1ed.pdf",
        "description": "Lei Geral de Proteção de Dados (LGPD) - Senado Federal"
    },
    {
        "filename": "Lei_licitacoes_contratos_administrativos_4ed.pdf",
        "url": "https://www2.senado.gov.br/bdsf/bitstream/handle/id/656845/Lei_licitacoes_contratos_administrativos_4ed.pdf",
        "description": "Nova Lei de Licitações (Lei 14.133/2021) - Senado 4a Edição"
    },
    {
        "filename": "GTA_executivo_federal_7ed.pdf",
        "url": "https://www.gov.br/acessoainformacao/pt-br/central-de-conteudo/publicacoes/gta-7-guia-de-transparencia-ativa-final.pdf",
        "description": "Guia de Transparência Ativa da CGU - 7a Edição"
    }
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def download_file(entry: dict, dest_dir: Path) -> bool:
    dest = dest_dir / entry["filename"]
    if dest.exists() and dest.stat().st_size > 10000: # Verify size > 10KB
        log.info("Arquivo já existe: %s (%.1f MB)", dest.name, dest.stat().st_size / 1e6)
        return True

    log.info("Baixando %s...", entry["description"])
    try:
        req = Request(entry["url"], headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=60) as resp:
            data = resp.read()
        dest.write_bytes(data)
        log.info("Download concluído: %s (%.1f MB)", dest.name, len(data) / 1e6)
        return True
    except Exception as e:
        log.error("Erro ao baixar %s de %s: %s", entry["filename"], entry["url"], e)
        return False

def main():
    dest_dir = Path(__file__).resolve().parent / "corpus"
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    success = True
    for entry in CORPUS_FILES:
        res = download_file(entry, dest_dir)
        if not res:
            success = False
            
    if success:
        log.info("Todos os arquivos do corpus foram baixados com sucesso!")
        return 0
    else:
        log.warning("Alguns downloads falharam. Por favor, verifique a conexão e as URLs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
