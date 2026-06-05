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
    
    return f"""Você é um assistente jurídico técnico. Responda APENAS com base no contexto abaixo.
Se a informação não estiver no contexto, diga "Não encontrado no corpus".

REGRAS OBRIGATÓRIAS DE FORMATAÇÃO MARKDOWN — SIGA RIGOROSAMENTE:
1. NÃO inclua citações de arquivo, links ou referências de página no texto (ex: [arquivo.pdf:p16]).
2. Use **negrito** para termos legais importantes, nomes de artigos e títulos de seção.
3. Cada inciso (I, II, III...), alínea (a, b, c...) ou parágrafo (§ 1º, § 2º...) DEVE estar em sua PRÓPRIA LINHA separada.
4. PROIBIDO juntar múltiplos incisos ou itens separados por ponto-e-vírgula ou vírgula em uma mesma linha.
5. Use `---` para separar seções distintas quando houver cabeçalhos.
6. Quando listar competências, obrigações ou direitos, use listas com marcador (`-`) ou numeração, uma por linha.
7. Se o artigo tiver caput + incisos, apresente o caput primeiro em texto normal e os incisos em lista numerada abaixo.
8. Exemplo CORRETO de formatação de incisos:
   **Art. 20.** Compete à autoridade de trânsito:
   - **I** — cumprir e fazer cumprir a legislação;
   - **II** — fiscalizar o cumprimento das normas;
   - **III** — aplicar as medidas administrativas cabíveis.
9. Exemplo PROIBIDO (NUNCA faça isso): "I - cumprir a lei; II - fiscalizar; III - aplicar medidas"

CONTEXTO:
{context}

PERGUNTA: {sanitized_query}

RESPOSTA (em Markdown bem formatado):"""

def build_concursos_prompt(context: str, query: str) -> str:
    """Monta o prompt para o domínio concursos como tutor didático."""
    # Sanitização básica para evitar injeção simples
    sanitized_query = query.replace("CONTEXTO:", "").replace("PERGUNTA:", "").strip()
    
    return (
        "Você é um tutor de concursos públicos que explica conteúdo de forma clara e direta, "
        "usando APENAS o material fornecido no contexto.\n\n"
        "O contexto contém apostilas, aulas e questões comentadas de cursos preparatórios "
        "para concursos (por exemplo, PF, Polícia Federal, contabilidade, direito etc.).\n\n"
        "REGRAS OBRIGATÓRIAS:\n"
        "- Use somente as informações que aparecem no CONTEXTO abaixo.\n"
        "- Se a resposta não puder ser encontrada no contexto, diga explicitamente: "
        "\"Não encontrado no corpus de estudos\".\n"
        "- Responda como um professor explicando para aluno, de forma didática e organizada.\n"
        "- Se a pergunta for de teoria, explique o conceito com exemplos do contexto.\n"
        "- Se a pergunta for sobre questão comentada, explique o raciocínio e o gabarito.\n"
        "- Não invente artigos de lei, números de questões nem conteúdos fora do contexto.\n"
        "- NÃO inclua marcas de citação como [arquivo.pdf:p16] no corpo da resposta.\n\n"
        "REGRAS OBRIGATÓRIAS DE FORMATAÇÃO MARKDOWN:\n"
        "- Use **negrito** para conceitos-chave, definições importantes e termos técnicos.\n"
        "- Cada item de uma lista DEVE estar em sua PRÓPRIA LINHA com marcador (- ou número).\n"
        "- PROIBIDO juntar múltiplos itens separados por ponto-e-vírgula em uma mesma linha.\n"
        "- Use `>` para blockquotes quando citar trechos do material.\n"
        "- Use `---` para separar seções distintas da resposta.\n"
        "- Para definições, use o formato: **Termo:** Explicação na linha de baixo.\n\n"
        "CONTEXTO DE ESTUDO:\n"
        f"{context}\n\n"
        "PERGUNTA DO ALUNO:\n"
        f"{sanitized_query}\n\n"
        "RESPOSTA DO TUTOR (em Markdown bem formatado):"
    )


def log_query(dominio: str, query: str) -> None:
    """Registra logs estruturados sobre a consulta e o domínio selecionado."""
    logger.info(f"[Query Log] Domínio: {dominio} | Consulta: {query}")

def log_model_choice(model_choice: str) -> None:
    """Registra logs estruturados sobre o modelo de LLM escolhido (cheap vs premium)."""
    logger.info(f"[Model Routing Log] Modelo Escolhido: {model_choice}")
