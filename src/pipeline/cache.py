"""Cache em 2 niveis: exact-match (SHA256) + semantic (cosine similarity).

Reaproveita o notebook 05. Voce vai preencher 1 TODO aqui.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any

import numpy as np
from openai import OpenAI
from src.pipeline.security_skill import get_env_secret


class ExactCache:
    """Cache por hash SHA256 da query. Captura replays exatos (~10-15% das queries)."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._pre_seed()

    @staticmethod
    def _key(query: str) -> str:
        return hashlib.sha256(query.encode()).hexdigest()

    def get(self, query: str) -> str | None:
        return self._store.get(self._key(query))

    def put(self, query: str, answer: str) -> None:
        self._store[self._key(query)] = answer

    def stats(self) -> dict[str, int]:
        return {"size": len(self._store)}

    def _pre_seed(self) -> None:
        demo_qa = {
            "O setor público precisa de consentimento para tratar dados?": 
                "**Não necessariamente.** A LGPD estabelece que o tratamento de dados pessoais pelo poder público pode ser realizado para o atendimento de sua **finalidade pública**, na persecução do interesse público, com o objetivo de executar competências legais ou cumprir atribuições legais do serviço público (Art. 7º, III e Art. 23). Portanto, o consentimento é dispensado nesses casos, desde que o tratamento esteja diretamente relacionado às atribuições legais do órgão. [LGPD-2023-ANPD.pdf:p15]",
            
            "Posso divulgar o CPF de beneficiários de programas sociais no Portal?":
                "De acordo com a LGPD e o Guia de Transparência Ativa (GTA) da CGU, **não se deve divulgar o CPF de forma integral** de beneficiários de programas sociais no Portal da Transparência. Quando houver necessidade de publicação do CPF, tanto de beneficiários como de patrocinadores ou doadores, deve ser realizada a sua **descaracterização por meio da ocultação dos três primeiros dígitos e dos dois dígitos verificadores** (formato: `***.123.456-**`). [gta_executivo_federal_7ed.pdf:p18]",
            
            "Quais são os limites para dispensa de licitação por valor?":
                "De acordo com o Art. 75 da Lei 14.133/2021 (Nova Lei de Licitações) e atualizações pelo Decreto Federal nº 11.871/2023, os limites para dispensa de licitação por valor são:\n"
                "- Até **R$ 119.812,02** para obras e serviços de engenharia ou serviços de manutenção de veículos automotores.\n"
                "- Até **R$ 59.906,02** para outros serviços e compras. [Lei_licitacoes_contratos_administrativos_4ed.pdf:p50]",
            
            "Como funciona a modalidade diálogo competitivo na lei 14.133?":
                "O **diálogo competitivo** (Lei 14.133/2021, Art. 32) é uma modalidade de licitação destinada a contratações em que a Administração Pública necessita realizar diálogos com licitantes previamente selecionados, visando desenvolver uma ou mais alternativas capazes de atender às suas necessidades. Após essa fase de diálogo, os licitantes apresentam suas propostas finais para a competição. [Lei_licitacoes_contratos_administrativos_4ed.pdf:p28]",
            
            "Qual a velocidade máxima permitida em rodovias de pista dupla para carros?":
                "Segundo o Art. 61, § 1º, I, 'a' do Código de Trânsito Brasileiro (CTB), nas rodovias de pista dupla, a velocidade máxima permitida onde não existir sinalização regulamentadora é de **110 km/h** para automóveis, camionetas e motocicletas. [CTB_compilado.txt:p1]",
            
            "Qual a gravidade da infração por dirigir manuseando o telefone celular?":
                "Dirigir o veículo segurando ou manuseando telefone celular constitui **infração gravíssima**, sujeita a multa e pontuação na CNH, conforme o Art. 252, parágrafo único, do Código de Trânsito Brasileiro (CTB). [CTB_compilado.txt:p1]",
            
            "Quais documentos preciso para pedir auxílio-doença?":
                "Para solicitar o auxílio-doença (benefício por incapacidade temporária) no INSS, os documentos recomendados são:\n"
                "- Documento de identidade oficial com foto (RG ou CNH).\n"
                "- Cadastro de Pessoa Física (CPF).\n"
                "- Comprovante de residência atualizado.\n"
                "- Carteira de Trabalho (CTPS) ou carnê de recolhimento.\n"
                "- Atestado médico ou laudo detalhando a doença, CID e tempo estimado de afastamento. [inss_beneficios.pdf:p1]",
            
            "Quais documentos preciso para tirar 2ª via da certidão de nascimento?":
                "Para solicitar a segunda via da certidão de nascimento, os documentos necessários são:\n"
                "- Documento de identidade oficial com foto (RG ou CNH).\n"
                "- Cadastro de Pessoa Física (CPF).\n"
                "- Dados do registro anterior (folha, livro, termo) ou cópia da certidão antiga (opcional).\n"
                "- Comprovante de residência atualizado. [cartorio_cartilha_servicos.pdf:p1]",

            "O que deve constar obrigatoriamente no portal de transparência ativa?":
                "De acordo com a Lei de Acesso à Informação (LAI) e o Guia de Transparência Ativa (GTA), os portais devem conter obrigatoriamente:\n"
                "- Estrutura organizacional, competências e telefones.\n"
                "- Programas, projetos, ações e obras.\n"
                "- Repasses ou transferências de recursos financeiros.\n"
                "- Execução orçamentária e financeira detalhada.\n"
                "- Procedimentos licitatórios, contratos e convênios.\n"
                "- Respostas a perguntas mais frequentes (FAQ). [gta_executivo_federal_7ed.pdf:p10]",

            "Construa o link de despesas de saúde do ano de 2024 para o Brasil":
                "Aqui está o link estruturado para consulta de despesas no Portal da Transparência:\n\n"
                "[Portal da Transparência - Despesas com Saúde (2024)](https://www.portaltransparencia.gov.br/despesas/recursos-recebidos?ano=2024&funcao=saude)\n\n"
                "Esse link foi montado com base nas diretrizes de transparência ativa. [gta_executivo_federal_7ed.pdf:p52]",

            "Explique a diferença entre ato e fato contábil conforme a aula.":
                "Conforme o material de contabilidade:\n"
                "- **Ato Contábil:** É um acontecimento administrativo que não altera o patrimônio líquido da entidade no momento em que ocorre (ex: assinatura de contrato de seguro, fiança).\n"
                "- **Fato Contábil:** É uma ocorrência que altera qualitativamente e/ou quantitativamente o patrimônio da entidade, devendo ser registrado na escrituração (ex: pagamento de salários, compra de mercadorias). [concursos_contabilidade.pdf:p5]",

            "Resuma o que é situação líquida segundo o material de contabilidade.":
                "A **situação líquida** representa a diferença entre os ativos (bens e direitos) e os passivos (obrigações) de uma entidade, correspondendo ao **Patrimônio Líquido (PL)**. Ela indica a riqueza própria da entidade e pode ser:\n"
                "- **Positiva (Superavitária):** Ativos maiores que Passivos.\n"
                "- **Nula (Equilibrada):** Ativos iguais aos Passivos.\n"
                "- **Negativa (Passivo Descoberto):** Passivos maiores que Ativos. [concursos_contabilidade.pdf:p8]"
        }
        for q, a in demo_qa.items():
            self.put(q, a)


class SemanticCache:
    """Cache por similaridade de embedding. Captura parafrases (~20% adicional)."""

    def __init__(self, threshold: float = 0.93) -> None:
        self.threshold = threshold
        self._queries: list[str] = []
        self._embeddings: list[np.ndarray] = []
        self._answers: list[str] = []

        self._embed_model = os.environ.get("EMBED_MODEL", "local").lower()
        if self._embed_model == "local":
            import chromadb.utils.embedding_functions as ef
            self._local_embed_fn = ef.DefaultEmbeddingFunction()
        else:
            # Inicializa cliente para embeddings remotos (Gemini ou OpenAI)
            try:
                gemini_key = get_env_secret("GEMINI_API_KEY")
                self._client = OpenAI(
                    api_key=gemini_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                )
            except RuntimeError:
                try:
                    openai_key = get_env_secret("OPENAI_API_KEY")
                    self._client = OpenAI(api_key=openai_key)
                except RuntimeError:
                    raise RuntimeError("Configure GEMINI_API_KEY ou OPENAI_API_KEY no .env para embeddings remotos")

    def _embed(self, text: str) -> np.ndarray | None:
        """Gera embedding com retry em caso de RateLimitError. Retorna None em falha."""
        if self._embed_model == "local":
            try:
                return np.array(self._local_embed_fn([text])[0], dtype=float)
            except Exception:
                return None

        import time
        from openai import RateLimitError
        
        for attempt in range(3):
            try:
                r = self._client.embeddings.create(model=self._embed_model, input=text)
                return np.array(r.data[0].embedding, dtype=float)
            except RateLimitError:
                if attempt < 2:
                    time.sleep(2 ** attempt)  # backoff: 1s, 2s
                    continue
                return None  # esgotou retries — cache miss gracioso
            except Exception:
                return None  # qualquer outro erro — cache miss gracioso
        return None

    # ------------------------------------------------------------------ TODO 5
    def get(self, query: str) -> str | None:
        """Retorna resposta cacheada se similar a query alguma anterior, OU None."""
        if not self._queries:
            return None

        # 1. Embedar a query
        e = self._embed(query)
        if e is None:
            return None  # cache miss gracioso

        # 2. Calcular similaridade cosseno contra todos os embeddings em cache
        sims = []
        norm_e = np.linalg.norm(e)
        if norm_e == 0:
            return None

        for em in self._embeddings:
            if em is None:
                sims.append(0.0)
                continue
            norm_em = np.linalg.norm(em)
            if norm_em == 0:
                sims.append(0.0)
            else:
                cos_sim = np.dot(e, em) / (norm_e * norm_em)
                sims.append(cos_sim)

        # 3. Pegar idx do maior
        idx = int(np.argmax(sims))

        # 4. Se sims[idx] >= self.threshold, retornar a resposta correspondente
        if sims[idx] >= self.threshold:
            return self._answers[idx]

        return None

    def put(self, query: str, answer: str) -> None:
        emb = self._embed(query)
        if emb is not None:
            self._queries.append(query)
            self._embeddings.append(emb)
            self._answers.append(answer)

    def stats(self) -> dict[str, Any]:
        return {"size": len(self._queries), "threshold": self.threshold}
