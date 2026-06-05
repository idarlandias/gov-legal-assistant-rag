import os
import json
import hashlib
import urllib3
import requests
from pathlib import Path

# Desativa avisos de SSL inseguro (para sites de órgãos públicos)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parents[2]
CORPUS_DIR = BASE_DIR / "data" / "corpus"
METADATA_FILE = BASE_DIR / "data" / "corpus_metadata.json"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Lista de documentos oficiais a monitorar
DOCS = [
    {
        "domain": "lgpd",
        "url": "https://www2.senado.gov.br/bdsf/bitstream/handle/id/658231/Lei_geral_protecao_dados_pessoais_1ed.pdf",
        "filename": "LGPD-2023-ANPD.pdf",
    },
    {
        "domain": "licitacoes",
        "url": "https://www2.senado.gov.br/bdsf/bitstream/handle/id/656845/Lei_licitacoes_contratos_administrativos_4ed.pdf",
        "filename": "Lei_licitacoes_contratos_administrativos_4ed.pdf",
    },
    {
        "domain": "transparencia",
        "url": "https://www.gov.br/acessoainformacao/pt-br/central-de-conteudo/publicacoes/gta-7-guia-de-transparencia-ativa-final.pdf",
        "filename": "gta_executivo_federal_7ed.pdf",
    },
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
    {
        "domain": "ctb",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm",
        "filename": "CTB_compilado.txt",
    },
]


def html_to_text(html_content: bytes) -> str:
    """Extrai texto limpo de uma página HTML/HTM."""
    import html.parser
    class HTMLTextStripper(html.parser.HTMLParser):
        def __init__(self):
            super().__init__()
            self.reset()
            self.fed = []
        def handle_data(self, d):
            self.fed.append(d)
        def get_data(self):
            return "".join(self.fed)
            
    # Tenta decodificar. O site do Planalto costuma usar iso-8859-1 (latin1)
    try:
        text = html_content.decode("utf-8")
    except UnicodeDecodeError:
        text = html_content.decode("iso-8859-1", errors="ignore")
        
    stripper = HTMLTextStripper()
    stripper.feed(text)
    return stripper.get_data()


def calculate_file_hash(filepath: Path) -> str:
    """Calcula o hash SHA256 de um arquivo local."""
    if not filepath.exists():
        return ""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_metadata() -> dict:
    """Carrega o arquivo de metadados do corpus."""
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler metadados ({e}). Iniciando novos metadados.")
    return {}


def save_metadata(metadata: dict):
    """Salva os metadados do corpus no disco."""
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def check_and_update() -> bool:
    """Verifica e baixa atualizações para os documentos configurados.

    Retorna True se algum documento foi atualizado ou inserido de fato.
    """
    metadata = load_metadata()
    any_updated = False
    headers = {"User-Agent": USER_AGENT}

    for doc in DOCS:
        domain = doc["domain"]
        url = doc["url"]
        filename = doc["filename"]
        dest_dir = CORPUS_DIR / domain
        dest_path = dest_dir / filename

        # Chave identificadora única no metadados
        meta_key = f"{domain}/{filename}"
        doc_meta = metadata.get(meta_key, {})

        print(f"\nVerificando [{domain}] {filename}...")

        # 1. Faz requisição HEAD para ler os cabeçalhos remotos
        remote_last_modified = None
        remote_etag = None
        remote_length = None
        
        try:
            head_resp = requests.head(url, headers=headers, verify=False, timeout=15)
            if head_resp.status_code == 200:
                remote_last_modified = head_resp.headers.get("Last-Modified")
                remote_etag = head_resp.headers.get("ETag")
                remote_length = head_resp.headers.get("Content-Length")
        except Exception as e:
            print(f"Aviso: Não foi possível obter cabeçalhos HEAD de {url}: {e}")

        # Se o arquivo não existir localmente ou houver indícios de alteração nos headers, prossegue para download
        needs_download = False
        if not dest_path.exists():
            print("  -> Arquivo local não existe. Download obrigatório.")
            needs_download = True
        elif doc_meta.get("hash") != calculate_file_hash(dest_path):
            print("  -> Hash local não bate com o metadados. Corrigindo.")
            needs_download = True
        elif remote_last_modified and doc_meta.get("last_modified") != remote_last_modified:
            print(f"  -> Last-Modified alterado: {doc_meta.get('last_modified')} -> {remote_last_modified}")
            needs_download = True
        elif remote_etag and doc_meta.get("etag") != remote_etag:
            print(f"  -> ETag alterado: {doc_meta.get('etag')} -> {remote_etag}")
            needs_download = True

        if not needs_download:
            print("  -> Documento já está atualizado. Nenhuma ação necessária.")
            continue

        # 2. Faz o download do arquivo temporariamente para calcular hash
        print(f"  -> Baixando arquivo de {url}...")
        try:
            get_resp = requests.get(url, headers=headers, verify=False, timeout=45)
            get_resp.raise_for_status()
            
            # Se for um arquivo HTML (como o do Planalto), extrai apenas o texto
            is_html = url.endswith(".htm") or url.endswith(".html") or "planalto.gov.br" in url
            downloaded_content = get_resp.content
            
            if is_html:
                plain_text = html_to_text(downloaded_content)
                downloaded_content_to_save = plain_text.encode("utf-8")
            else:
                downloaded_content_to_save = downloaded_content

            downloaded_hash = hashlib.sha256(downloaded_content_to_save).hexdigest()
            local_hash = calculate_file_hash(dest_path)

            if downloaded_hash == local_hash:
                print("  -> O conteúdo do arquivo baixado é idêntico ao local. Apenas atualizando cabeçalhos nos metadados.")
                metadata[meta_key] = {
                    "url": url,
                    "last_modified": remote_last_modified or doc_meta.get("last_modified"),
                    "etag": remote_etag or doc_meta.get("etag"),
                    "length": remote_length or doc_meta.get("length"),
                    "hash": downloaded_hash
                }
                continue

            # Se o conteúdo for diferente, salva no destino
            dest_dir.mkdir(parents=True, exist_ok=True)
            if is_html:
                dest_path.write_text(plain_text, encoding="utf-8")
            else:
                dest_path.write_bytes(downloaded_content)
            
            # Atualiza metadados com as informações da versão atualizada
            metadata[meta_key] = {
                "url": url,
                "last_modified": remote_last_modified or get_resp.headers.get("Last-Modified"),
                "etag": remote_etag or get_resp.headers.get("ETag"),
                "length": remote_length or get_resp.headers.get("Content-Length"),
                "hash": downloaded_hash
            }
            print(f"  -> Sucesso! Arquivo atualizado e salvo.")
            any_updated = True

        except Exception as e:
            print(f"  -> ERRO ao baixar/atualizar {filename}: {e}")
            if dest_path.exists():
                print(f"  -> O arquivo local existe. Gerando metadados com base no arquivo local atual para evitar novas tentativas desnecessárias.")
                local_hash = calculate_file_hash(dest_path)
                metadata[meta_key] = {
                    "url": url,
                    "last_modified": doc_meta.get("last_modified"),
                    "etag": doc_meta.get("etag"),
                    "length": doc_meta.get("length"),
                    "hash": local_hash
                }

    # Salva o arquivo de metadados se houve qualquer checagem bem-sucedida
    save_metadata(metadata)
    return any_updated


if __name__ == "__main__":
    import sys
    print("Iniciando verificador de leis e PDFs...")
    has_changes = check_and_update()
    if has_changes:
        print("\n[MUDANÇA DETECTADA] Um ou mais PDFs foram atualizados.")
        sys.exit(0)  # Retorna 0 para indicar execução ok com atualizações
    else:
        print("\n[SEM ALTERAÇÕES] Todos os PDFs estão atualizados com as fontes.")
        sys.exit(0)
