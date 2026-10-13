"""O rótulo de toda fonte recuperada precisa dizer a norma: há "Art. 123" em mais de uma."""

from unittest.mock import MagicMock

from src.fase3.ato_pronto import PedidoBalcao, processar_ato_pronto
from src.fase3.corpus import Dispositivo
from src.fase3.index import build_chunks
from src.fase3.pipeline import Fase3Pipeline
from src.fase3.retrieval import HybridRetriever, norma_do_chunk, rotulo_fonte
from src.fase3.sources import FONTES_POR_ID

CNJ_123 = {"text": "Art. 123. Dependem de identificação...", "source": "Provimento CNJ 149/2023, Art. 123",
           "page": 55, "norma": "Provimento CNJ 149/2023", "dispositivo": "Art. 123"}
CE_123 = {"text": "Art. 123. Outro conteúdo...", "source": "Código de Normas CGJ-CE, Art. 123",
          "page": 40, "norma": "Código de Normas CGJ-CE", "dispositivo": "Art. 123"}
SEM_NORMA = {"text": "Art. 19. ...", "source": "Art. 19", "page": 0, "dispositivo": "Art. 19"}


def test_rotulo_tem_norma_e_dispositivo():
    assert rotulo_fonte(CNJ_123) == "Provimento CNJ 149/2023 — Art. 123"


def test_numeracao_colidente_gera_rotulos_distintos():
    assert rotulo_fonte(CNJ_123) != rotulo_fonte(CE_123)


def test_sem_norma_o_rotulo_avisa_em_vez_de_omitir():
    assert rotulo_fonte(SEM_NORMA) == "NORMA NÃO IDENTIFICADA — Art. 19"


def test_norma_do_chunk_usa_metadado_ou_fonte_id():
    assert norma_do_chunk({"norma": "Lei 6.015/1973"}) == "Lei 6.015/1973"
    # índice antigo, sem o campo `norma`: deriva do registro de fontes
    assert norma_do_chunk({"fonte_id": "codigo_normas_ce"}) == FONTES_POR_ID["codigo_normas_ce"].sigla
    assert norma_do_chunk({"fonte_id": "desconhecida"}) is None
    assert norma_do_chunk({}) is None


def test_chunk_novo_carrega_campo_norma():
    fonte = FONTES_POR_ID["lei_6015_1973"]
    chunks = build_chunks(fonte, [Dispositivo(fonte.id, "Art. 17", "", 0, "Qualquer pessoa pode requerer certidão.")])
    assert chunks[0].metadata["norma"] == "Lei 6.015/1973"


class _ColecaoAntiga:
    """Simula o índice atual (schema 2), cujos chunks não têm o campo `norma`."""

    def get(self, include):
        return {"ids": ["c1"], "documents": ["certidão de inteiro teor"],
                "metadatas": [{"source": "Código de Normas CGJ-CE, Art. 1128", "page": 218,
                               "fonte_id": "codigo_normas_ce", "dispositivo": "Art. 1128",
                               "especialidade": "registro_imoveis"}]}


def test_busca_preenche_norma_mesmo_em_indice_antigo():
    hit = HybridRetriever(_ColecaoAntiga(), embedder=None).search("certidão", k=1, modo="bm25")[0]
    assert hit["norma"] == "Código de Normas CGJ-CE"
    assert rotulo_fonte(hit) == "Código de Normas CGJ-CE — Art. 1128"


def _resposta(conteudo: str) -> MagicMock:
    r = MagicMock()
    r.choices = [MagicMock(message=MagicMock(content=conteudo))]
    return r


def test_answer_usa_rotulo_no_contexto_e_nas_fontes():
    pipe = object.__new__(Fase3Pipeline)  # sem carregar modelo nem Chroma
    pipe.retrieve = MagicMock(return_value=[CNJ_123, SEM_NORMA])
    pipe.llm_model = "mock"
    pipe._call_chat_completions = MagicMock(return_value=_resposta("ok"))

    out = pipe.answer("pergunta")
    prompt = pipe._call_chat_completions.call_args.kwargs["messages"][0]["content"]
    assert "[Provimento CNJ 149/2023 — Art. 123]" in prompt
    assert "[NORMA NÃO IDENTIFICADA — Art. 19]" in prompt
    assert out["sources"] == [("Provimento CNJ 149/2023 — Art. 123", 55), ("NORMA NÃO IDENTIFICADA — Art. 19", 0)]


def test_ato_pronto_usa_rotulo_no_contexto_e_nas_fontes():
    pipe = MagicMock()
    pipe.llm_model = "mock"
    pipe.retrieve.return_value = [CE_123]
    pipe._call_chat_completions.return_value = _resposta("sem json")  # cai em INDEFINIDO; não importa aqui

    saida = processar_ato_pronto(pipe, PedidoBalcao(tipo_pedido="Certidão", solicitante="Terceiro"))
    prompt = pipe._call_chat_completions.call_args.kwargs["messages"][0]["content"]
    assert "[Código de Normas CGJ-CE — Art. 123]" in prompt
    assert saida.fontes_corpus == ["Código de Normas CGJ-CE — Art. 123 (pág. 40)"]
