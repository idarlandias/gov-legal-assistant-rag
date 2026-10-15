"""Motor de regras do Registro de Imóveis: o canal sai da norma, não do LLM.

Cada fundamento traz o trecho LITERAL do dispositivo (um teste confere contra o corpus).
Base: Código de Normas CGJ-CE, Arts. 1.128, 1.129 e 1.131 §10; Prov. CNJ 149/2023, Arts. 123 a 128.

Regras de projeto:
- A tabela nunca devolve VERMELHO. A recusa é decisão do Oficial em nota fundamentada
  (CE Art. 1.128 §4º; CNJ Art. 123 §4º): o motor só alerta para essa possibilidade.
- CONDICIONAL: a norma muda o canal conforme um fato que o escrevente precisa confirmar.
  Sem a confirmação, nada é decidido.
- SEM_REGRA: o tipo de pedido não está coberto pelos artigos acima; o canal fica como sugestão do
  LLM e a UI avisa que não há regra determinística.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

CE = "Código de Normas CGJ-CE"
CNJ = "Provimento CNJ 149/2023"


class Cobertura(str, Enum):
    REGRA = "REGRA"
    CONDICIONAL = "CONDICIONAL"
    SEM_REGRA = "SEM_REGRA"


@dataclass(frozen=True)
class Fundamento:
    norma: str
    artigo: str      # ex.: "Art. 1.128, caput"
    chave: str       # dispositivo no corpus, ex.: "Art. 1128"
    trecho: str      # transcrição literal (conferida em teste)


@dataclass(frozen=True)
class ResultadoRegra:
    cobertura: Cobertura
    canal: str | None = None
    exige_identificacao: bool = True
    exige_finalidade: bool = False
    fundamentos: tuple[Fundamento, ...] = ()
    alertas: tuple[str, ...] = ()
    pergunta: str = ""           # só em CONDICIONAL
    se_sim: "ResultadoRegra | None" = field(default=None, repr=False)
    se_nao: "ResultadoRegra | None" = field(default=None, repr=False)

    @property
    def gera_ficha(self) -> bool:
        return self.cobertura == Cobertura.REGRA and self.exige_finalidade


# ---------------------------------------------------------------- fundamentos (texto literal)

CE_CAPUT = Fundamento(CE, "Art. 1.128, caput", "Art. 1128",
                      "Qualquer pessoa pode requerer certidão de registros em sentido estrito, averbações, matrículas, "
                      "transcrições ou inscrições específicas, desde que devidamente identificada, independentemente de "
                      "indicação da finalidade.")
CNJ_123 = Fundamento(CNJ, "Art. 123, caput", "Art. 123",
                     "Dependem de identificação do requerente e independem de indicação da finalidade os pedidos de "
                     "certidão de registros em sentido estrito, averbações, matrículas, transcrições ou inscrições "
                     "específicas, expedidas em qualquer modalidade.")
CE_INTEIRO_TEOR = Fundamento(CE, "Art. 1.131, §10", "Art. 1131",  # guarda-1131: ok (reproduz TODO o conteúdo)
                             "No âmbito do registro de imóveis, a certidão de inteiro teor da matrícula conterá a "
                             "reprodução de todo seu conteúdo")
CE_1129 = Fundamento(CE, "Art. 1.129", "Art. 1129",
                     "As certidões dos imóveis que já forem objeto de matrícula eletrônica, após a “primeira "
                     "qualificação eletrônica”, serão expedidas, independentemente de indicação de finalidade")
CNJ_125 = Fundamento(CNJ, "Art. 125, caput", "Art. 125",
                     "serão expedidas, independentemente de indicação de finalidade, em formato nato-digital "
                     "estruturado, contendo a situação jurídica atual do imóvel")
CE_P1 = Fundamento(CE, "Art. 1.128, §1º", "Art. 1128",
                   "Aplica-se o disposto no caput nos pedidos de certidão de documentos arquivados na Serventia, desde "
                   "que haja previsão legal ou normativa específica de seu arquivamento no registro.")
CNJ_123_P1 = Fundamento(CNJ, "Art. 123, §1º", "Art. 123",
                        "Também dependem de identificação do requerente e independem de indicação da finalidade os "
                        "pedidos de certidão de documentos arquivados no cartório, desde que haja previsão legal ou "
                        "normativa específica de seu arquivamento no registro.")
CE_P2_I = Fundamento(CE, "Art. 1.128, §2º, I", "Art. 1128",
                     "pedidos de certidão de documentos arquivados em cartório para a qual não haja previsão legal "
                     "específica de expedição")
CNJ_123_P2 = Fundamento(CNJ, "Art. 123, §2º", "Art. 123",
                        "Pedidos de certidão de documentos arquivados em cartório para a qual não haja previsão legal "
                        "específica de expedição dependem de identificação do requerente e indicação da finalidade")
CE_P2_II = Fundamento(CE, "Art. 1.128, §2º, II", "Art. 1128",
                      "pedidos de certidão, busca e informações apresentados em bloco, ainda que instruídos com a "
                      "numeração dos atos a serem certificados")
CNJ_123_P3 = Fundamento(CNJ, "Art. 123, §3º", "Art. 123",
                        "Pedidos de certidão, de busca e de informações apresentados em bloco, ainda que instruídos com "
                        "a numeração dos atos a serem certificados, dependem de identificação do requerente e indicação "
                        "da finalidade.")
CE_P2_III = Fundamento(CE, "Art. 1.128, §2º, III", "Art. 1128",
                       "pedidos de certidão de atos anteriores da cadeia dominial do imóvel")
CNJ_125_PU = Fundamento(CNJ, "Art. 125, parágrafo único", "Art. 125",
                        "A expedição de certidão de atos anteriores da cadeia filiatória do imóvel depende de "
                        "identificação segura do requerente e de indicação da finalidade.")
CE_P2_IV = Fundamento(CE, "Art. 1.128, §2º, IV", "Art. 1128",
                      "as requisições de buscas fundadas exclusivamente no indicador pessoal ou real")
CNJ_126 = Fundamento(CNJ, "Art. 126", "Art. 126",
                     "O atendimento a requisições de buscas fundadas exclusivamente no indicador pessoal ou real "
                     "pressupõe a identificação segura do solicitante, bem como a indicação da finalidade")
CE_P2_V = Fundamento(CE, "Art. 1.128, §2º, V", "Art. 1128",
                     "o fornecimento, pelo registrador, por qualquer meio, de informações sobre o registro não "
                     "veiculadas por certidão, exceto nos casos em que o solicitante figure no registro em questão")
CNJ_127 = Fundamento(CNJ, "Art. 127", "Art. 127",
                     "O fornecimento, pelo registrador, por qualquer meio, de informações sobre o registro não "
                     "veiculadas por certidão dependerá da segura identificação do solicitante e da indicação da sua "
                     "finalidade, exceto nos casos em que o solicitante figure no registro em questão.")
CE_P3 = Fundamento(CE, "Art. 1.128, §3º", "Art. 1128",
                   "Serão formadas fichas físicas ou digitais contendo os dados de identificação e indicação de "
                   "finalidade em todas as hipóteses do parágrafo anterior")
CNJ_128 = Fundamento(CNJ, "Art. 128", "Art. 128",
                     "Serão formados prontuários físicos ou digitais contendo os dados de identificação e indicação de "
                     "finalidade em todas as hipóteses em que estas tenham sido exigidas.")
CNJ_128_PU = Fundamento(CNJ, "Art. 128, parágrafo único", "Art. 128",
                        "O titular dos dados pessoais solicitados terá direito a requisitar as informações contidas nos "
                        "prontuários formados em virtude de buscas ou pedidos de informações e certidões")
CE_P4 = Fundamento(CE, "Art. 1.128, §4º", "Art. 1128",
                   "Caracterizada tentativa de tratamento de dados em desacordo com as finalidades do Registro de "
                   "Imóveis e com os princípios da Lei Geral de Proteção de Dados Pessoais, poderá o Oficial recusar "
                   "o fornecimento em nota fundamentada")
CNJ_124 = Fundamento(CNJ, "Art. 124", "Art. 124",
                     "não serão expedidas certidões cujo conteúdo envolva informações sobre dados pessoais extraídos "
                     "de mais de uma matrícula, assentamento do registro auxiliar, transcrição ou inscrição")

TODOS_FUNDAMENTOS = (CE_CAPUT, CNJ_123, CE_INTEIRO_TEOR, CE_1129, CNJ_125, CE_P1, CNJ_123_P1, CE_P2_I, CNJ_123_P2,
                     CE_P2_II, CNJ_123_P3, CE_P2_III, CNJ_125_PU, CE_P2_IV, CNJ_126, CE_P2_V, CNJ_127, CE_P3,
                     CNJ_128, CNJ_128_PU, CE_P4, CNJ_124)

FICHA = (CE_P3, CNJ_128)
ALERTA_RECUSA = ("Se ficar caracterizada tentativa de tratamento de dados em desacordo com as finalidades do Registro "
                 "de Imóveis, o Oficial pode recusar em nota fundamentada (CE Art. 1.128, §4º; CNJ Art. 123, §4º). "
                 "A recusa é decisão do Oficial, não do sistema.")
ALERTA_INTEIRO_TEOR = ("Dados pessoais na matrícula não mudam o canal: a certidão de inteiro teor reproduz todo o "
                       "conteúdo (CE Art. 1.131, §10). Se o requerente quiser conteúdo reduzido, ofereça a certidão de "  # guarda-1131: ok
                       "situação jurídica atual (CNJ Art. 125).")


def _verde(*fund: Fundamento, alertas: tuple[str, ...] = ()) -> ResultadoRegra:
    return ResultadoRegra(Cobertura.REGRA, "VERDE", exige_finalidade=False, fundamentos=fund, alertas=alertas)


def _amarelo(*fund: Fundamento, alertas: tuple[str, ...] = ()) -> ResultadoRegra:
    return ResultadoRegra(Cobertura.REGRA, "AMARELO", exige_finalidade=True, fundamentos=fund + FICHA,
                          alertas=alertas)


SEM_REGRA = ResultadoRegra(Cobertura.SEM_REGRA, exige_identificacao=False)

# Chaves = opções de tipo de pedido da UI (minúsculas), as mesmas de EXPANSAO_TIPO_PEDIDO
TABELA: dict[str, ResultadoRegra] = {
    "certidão de inteiro teor de matrícula": _verde(CE_CAPUT, CNJ_123, CE_INTEIRO_TEOR),
    "certidão de situação jurídica atual (vigente)": _verde(CE_CAPUT, CE_1129, CNJ_125),
    "histórico de ônus / cadeia filiatória / ônus cancelados": ResultadoRegra(
        Cobertura.CONDICIONAL,
        pergunta="O pedido é de atos ANTERIORES da cadeia dominial (matrículas ou transcrições anteriores do imóvel)? "
                 "Se for só a matrícula atual, inclusive ônus cancelados nela averbados, responda Não.",
        se_sim=_amarelo(CE_P2_III, CNJ_125_PU),
        se_nao=_verde(CE_CAPUT, CNJ_123, CE_INTEIRO_TEOR),
    ),
    "busca por indicador pessoal (pesquisa de bens por cpf/nome)": _amarelo(CE_P2_IV, CNJ_126),
    "cópia de título / documento arquivado no cartório": ResultadoRegra(
        Cobertura.CONDICIONAL,
        pergunta="Há previsão legal ou normativa específica de arquivamento desse documento no registro?",
        se_sim=_verde(CE_P1, CNJ_123_P1),
        se_nao=_amarelo(CE_P2_I, CNJ_123_P2, alertas=(ALERTA_RECUSA,)),
    ),
    "informação verbal no balcão ou por telefone": _amarelo(CE_P2_V, CNJ_127),
    "acesso em lote / convênio com empresa imobiliária ou fintech": _amarelo(
        CE_P2_II, CNJ_123_P3, CNJ_124,
        alertas=("Certidão com dados pessoais extraídos de mais de uma matrícula só cabe nas hipóteses com previsão "
                 "legal ou normativa expressa (CNJ Art. 124).", ALERTA_RECUSA)),
    "pedido de exclusão de dados da matrícula com base na lgpd": SEM_REGRA,
    "pedido de retificação de dado pessoal na matrícula": SEM_REGRA,
    "requisição por órgão público / polícia / prefeitura sem ordem judicial": SEM_REGRA,
}

# Quem "figura no registro" fica fora da exigência do §2º, V (informação não veiculada por certidão)
SOLICITANTE_FIGURA_NO_REGISTRO = "próprio titular / proprietário do imóvel"
INFORMACAO_TITULAR = _verde(CE_P2_V, CNJ_127, alertas=(
    "A exceção vale para quem figura no registro: confirme pela identificação que o solicitante é o titular.",))


def decidir(tipo_pedido: str, solicitante: str = "", dados_sensiveis: list[str] | None = None,
            condicao: bool | None = None) -> ResultadoRegra:
    """Canal pela norma. `condicao` responde a `pergunta` de um caso CONDICIONAL (None = não respondida)."""
    tipo = tipo_pedido.strip().lower()
    regra = TABELA.get(tipo, SEM_REGRA)
    if tipo == "informação verbal no balcão ou por telefone" and \
            solicitante.strip().lower() == SOLICITANTE_FIGURA_NO_REGISTRO:
        regra = INFORMACAO_TITULAR
    if regra.cobertura == Cobertura.CONDICIONAL and condicao is not None:
        regra = regra.se_sim if condicao else regra.se_nao
    if regra.cobertura == Cobertura.REGRA and dados_sensiveis and CE_INTEIRO_TEOR in regra.fundamentos:
        regra = ResultadoRegra(**{**regra.__dict__, "alertas": regra.alertas + (ALERTA_INTEIRO_TEOR,)})
    return regra
