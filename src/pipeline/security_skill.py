"""Módulo de segurança, secrets, prompt management e logging."""

from __future__ import annotations

import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("security_skill")

def get_env_secret(key_name: str) -> str:
    """Obtém um secret do ambiente de forma segura. Em produção, usa as variáveis da plataforma."""
    val = os.getenv(key_name)
    if not val:
        raise RuntimeError(f"Erro Crítico: Variável de ambiente '{key_name}' não configurada! Por favor, defina-a.")
    return val

def build_secure_prompt(context: str, query: str) -> str:
    """Monta o prompt seguro com ancoragem estrita e mitigação de injeção de prompt."""
    # Sanitização básica para evitar injeção simples
    sanitized_query = query.replace("CONTEXTO:", "").replace("PERGUNTA:", "").strip()
    
    return f"""Voce e um assistente tecnico. Responda APENAS com base no contexto abaixo.
Se a informacao nao estiver no contexto, diga "Nao encontrado no corpus".
Sempre cite a fonte usando o formato [arquivo:pagina].

CONTEXTO:
{context}

PERGUNTA: {sanitized_query}

RESPOSTA:"""

def build_concursos_prompt(context: str, query: str) -> str:
    """Monta o prompt para o domínio concursos como tutor didático."""
    # Sanitização básica para evitar injeção simples
    sanitized_query = query.replace("CONTEXTO:", "").replace("PERGUNTA:", "").strip()
    
    return (
        "Você é um tutor de concursos públicos que explica conteúdo de forma clara e direta, "
        "usando APENAS o material fornecido no contexto.\n\n"
        "O contexto contém apostilas, aulas e questões comentadas de cursos preparatórios "
        "para concursos (por exemplo, PF, Polícia Federal, contabilidade, direito etc.).\n\n"
        "REGRAS:\n"
        "- Use somente as informações que aparecem no CONTEXTO abaixo.\n"
        "- Se a resposta não puder ser encontrada no contexto, diga explicitamente: "
        "\"Não encontrado no corpus de estudos\".\n"
        "- Quando possível, responda em 2 a 5 frases objetivas, como um professor explicando para aluno.\n"
        "- Se a pergunta for de teoria, foque em explicar o conceito com base nas definições e exemplos do contexto.\n"
        "- Se a pergunta for sobre uma questão comentada, explique o raciocínio e o gabarito com base no comentário do material.\n"
        "- Não invente artigos de lei, números de questões nem conteúdos que não estejam no contexto.\n"
        "- Não copie blocos muito longos de texto; prefira resumir com suas próprias palavras, mantendo a ideia correta.\n\n"
        "CONTEXTO DE ESTUDO:\n"
        f"{context}\n\n"
        "PERGUNTA DO ALUNO:\n"
        f"{sanitized_query}\n\n"
        "RESPOSTA DO TUTOR:"
    )


def log_query(dominio: str, query: str) -> None:
    """Registra logs estruturados sobre a consulta e o domínio selecionado."""
    logger.info(f"[Query Log] Domínio: {dominio} | Consulta: {query}")

def log_model_choice(model_choice: str) -> None:
    """Registra logs estruturados sobre o modelo de LLM escolhido (cheap vs premium)."""
    logger.info(f"[Model Routing Log] Modelo Escolhido: {model_choice}")
