"""Motor de regras do Registro Civil das Pessoas Naturais (RCPN): o canal sai da norma, não do LLM.

Base (texto literal conferido em teste): Prov. CNJ 149/2023, Arts. 113 a 121; Código de Normas CGJ-CE,
Arts. 255 a 262, 437, 468 e 471.

Diferença em relação ao Registro de Imóveis: aqui a PRÓPRIA norma exige autorização judicial em alguns
casos (ex.: terceiro pedindo inteiro teor com dado sensível de pessoa viva). Nesses casos o canal é
VERMELHO com `exige_autorizacao_judicial=True`: não é recusa do Oficial, é encaminhamento ao juízo.

Fatos que mudam o canal e que só o atendente sabe (dado sensível no assento, informação de menção
vedada, registrado falecido) entram como respostas; se faltar alguma, o caso é CONDICIONAL.
"""

from __future__ import annotations

from src.fase3.regras_ri import CE, CNJ, Cobertura, Fundamento, ResultadoRegra

# ---------------------------------------------------------------- fundamentos (texto literal)

CNJ_113 = Fundamento(CNJ, "Art. 113", "Art. 113",
                     "É livre o acesso às informações constantes nos livros de Registro Civil das Pessoas Naturais, "
                     "por meio de certidões de breve relato, com as informações regulamentadas em lei, neste Código de "
                     "Normas e em outras normas compatíveis, independentemente de requerimento ou de identificação do "
                     "requerente.")
CE_468 = Fundamento(CE, "Art. 468", "Art. 468",
                    "Qualquer pessoa poderá requerer certidão sem informar ao oficial de registro ou preposto o motivo "
                    "ou interesse do pedido.")
CE_256 = Fundamento(CE, "Art. 256, caput", "Art. 256",
                    "Nas certidões de breve relato deverão constar somente as informações previstas em lei ou ato "
                    "normativo, sendo que qualquer outra informação solicitada pela parte constante do registro ou "
                    "anotações e averbações posteriores somente poderá ser fornecida por meio de certidão por quesitos "
                    "ou por inteiro teor.")
CNJ_118 = Fundamento(CNJ, "Art. 118", "Art. 118",
                     "Não é necessário requerimento ou autorização judicial para emissão de certidão de óbito em "
                     "nenhuma de suas modalidades.")
CE_259 = Fundamento(CE, "Art. 259", "Art. 259",
                    "Não é necessário requerimento ou autorização judicial para emissão de certidão de óbito em nenhuma "
                    "de suas modalidades.")
CNJ_114 = Fundamento(CNJ, "Art. 114, caput", "Art. 114",
                     "As certidões de registro civil em geral, inclusive as de inteiro teor, requeridas pelos próprios "
                     "interessados, seus representantes legais, mandatários com poderes especiais, serão expedidas "
                     "independentemente de autorização do juiz corregedor permanente.")
CE_255 = Fundamento(CE, "Art. 255, caput", "Art. 255",
                    "As certidões de registro civil em geral, inclusive as de inteiro teor, requeridas pelos próprios "
                    "interessados, seus representantes legais, mandatários com poderes especiais, serão expedidas "
                    "independentemente de autorização do Juiz Corregedor Permanente.")
CNJ_114_P1 = Fundamento(CNJ, "Art. 114, §1º", "Art. 114",
                        "Nas hipóteses em que a emissão da certidão for requerida por terceiros e a certidão contiver "
                        "dados sensíveis, somente será feita a expedição mediante a autorização do juízo competente.")
CE_255_P1 = Fundamento(CE, "Art. 255, §1º", "Art. 255",
                       "Nas hipóteses em que a emissão da certidão for requerida por terceiros e a certidão contiver "
                       "dados sensíveis, somente será feita a expedição mediante a autorização do juízo competente.")
CNJ_114_P2 = Fundamento(CNJ, "Art. 114, §2º", "Art. 114",
                        "Após o falecimento do titular do dado sensível, as certidões de que trata o caput deste artigo "
                        "poderão ser fornecidas aos parentes em linha reta, independentemente de autorização judicial.")
CNJ_119 = Fundamento(CNJ, "Art. 119", "Art. 119",
                     "As restrições relativas aos dados sensíveis elencados pelo inciso II do art. 5.º da Lei n. "
                     "13.709/2018 não se aplicam ao caso de pessoa falecida.")
CE_260 = Fundamento(CE, "Art. 260", "Art. 260",
                    "As restrições relativas aos dados sensíveis elencados pelo inciso II do art. 5º da Lei nº "
                    "13.709/2018 não se aplicam ao caso de pessoa falecida.")
CNJ_117 = Fundamento(CNJ, "Art. 117, caput", "Art. 117",
                     "A emissão de certidão em inteiro teor sempre depende de requerimento escrito com firma reconhecida "
                     "do requerente ou com assinatura digital nos padrões ICP-Brasil, no padrão do sistema gov.br ou com "
                     "assinatura confrontada com o documento de identidade original.")
CNJ_117_P3 = Fundamento(CNJ, "Art. 117, §3º", "Art. 117",
                        "O requerimento de certidão em inteiro teor deverá conter a identificação do requerente, o "
                        "motivo em virtude do qual se requer a certidão sob a forma de inteiro teor e o grau de "
                        "parentesco com o registrado, caso exista, bem como o fato de ser este falecido ou não.")
CE_258 = Fundamento(CE, "Art. 258, caput e §3º", "Art. 258",
                    "O requerimento de certidão em inteiro teor deverá conter a identificação do requerente, o motivo "
                    "em virtude do qual se requer a certidão sob a forma de inteiro teor e o grau de parentesco com o "
                    "registrado, caso exista, bem como o fato de ser este falecido ou não.")
CNJ_116 = Fundamento(CNJ, "Art. 116, caput", "Art. 116",
                     "As solicitações de certidões por quesitos, ou informações solicitadas independentemente da "
                     "expedição de certidões, receberão o mesmo tratamento destinado às certidões solicitadas em inteiro "
                     "teor quando os dados solicitados forem restritos, sensíveis ou sigilosos.")
CE_257 = Fundamento(CE, "Art. 257, caput", "Art. 257",
                    "As solicitações de certidões por quesitos ou informações solicitadas independentemente da "
                    "expedição de certidões, receberão o mesmo tratamento destinado às certidões solicitadas em inteiro "
                    "teor quando os dados solicitados forem restritos, sensíveis ou sigilosos.")
CE_471_P2 = Fundamento(CE, "Art. 471, §2º", "Art. 471",
                       "Se a certidão de nascimento em inteiro teor for requerida por terceiros e havendo no assento "
                       "informações cuja menção é vedada pela lei, o requerimento constará o motivo da solicitação e "
                       "será submetido ao juízo com competência em registros público")
CE_471_P3 = Fundamento(CE, "Art. 471, §3º", "Art. 471",
                       "O procedimento dos §§1º e 2º será aplicado no caso de emissão de certidão em inteiro teor de "
                       "casamento ou óbito cujos assentos constem informações vedadas pela legislação em vigor.")
CNJ_120 = Fundamento(CNJ, "Art. 120, caput", "Art. 120",
                     "A emissão e o fornecimento de certidão sobre procedimentos preparatórios ou documentos "
                     "apresentados para a realização de atos no Registro Civil das Pessoas Naturais somente poderão ser "
                     "realizados a pedido do próprio interessado ou do titular do documento, seus representantes legais "
                     "e mandatários com poderes especiais ou mediante autorização judicial ou, ainda, quando o documento "
                     "solicitado for público com publicidade geral e irrestrita.")
CE_261 = Fundamento(CE, "Art. 261, caput", "Art. 261",
                    "A emissão e o fornecimento de certidão sobre procedimentos preparatórios ou documentos apresentados "
                    "para a realização de atos no Registro Civil das Pessoas Naturais somente poderão ser realizados a "
                    "pedido do próprio interessado ou do titular do documento")
CNJ_120_PU = Fundamento(CNJ, "Art. 120, parágrafo único", "Art. 120",
                        "Após o falecimento do titular, a certidão de que trata o caput deste artigo poderá ser "
                        "fornecida ao solicitante que apresentar a certidão de óbito.")
CNJ_121 = Fundamento(CNJ, "Art. 121, caput", "Art. 121",
                     "É facultado a qualquer interessado, independentemente de justificação ou de requerimento, "
                     "realizar buscas nos índices dos Registros Civis das Pessoas Naturais")
CE_262 = Fundamento(CE, "Art. 262, caput", "Art. 262",
                    "É facultado a qualquer interessado, independentemente de justificação ou de requerimento, realizar "
                    "buscas nos índices dos Registros Civis das Pessoas Naturais")
CNJ_121_PU = Fundamento(CNJ, "Art. 121, parágrafo único", "Art. 121",
                        "A realização de buscas com base em outras fontes, além dos índices de registros dos livros do "
                        "cartório, somente será autorizada mediante requerimento escrito fundamentado, sujeito à "
                        "análise de finalidade pelo oficial do registro civil das pessoas naturais")
CE_262_PU = Fundamento(CE, "Art. 262, parágrafo único", "Art. 262",
                       "A realização de buscas baseadas em outras fontes, além dos índices de registros dos livros do "
                       "cartório, somente será autorizada mediante requerimento escrito fundamentado, sujeito à análise "
                       "de finalidade pelo Oficial do Registro Civil das Pessoas Naturais")
CE_437 = Fundamento(CE, "Art. 437, parágrafo único", "Art. 437",
                    "Bloqueado o registro, o oficial de registro não poderá praticar nenhum ato ou expedir certidão, "
                    "salvo autorização judicial.")

TODOS_FUNDAMENTOS = (CNJ_113, CE_468, CE_256, CNJ_118, CE_259, CNJ_114, CE_255, CNJ_114_P1, CE_255_P1, CNJ_114_P2,
                     CNJ_119, CE_260, CNJ_117, CNJ_117_P3, CE_258, CNJ_116, CE_257, CE_471_P2, CE_471_P3, CNJ_120,
                     CE_261, CNJ_120_PU, CNJ_121, CE_262, CNJ_121_PU, CE_262_PU, CE_437)

# ---------------------------------------------------------------- opções da UI

BREVE_RELATO = "Certidão de breve relato (nascimento ou casamento)"
OBITO = "Certidão de óbito (qualquer modalidade)"
INTEIRO_TEOR = "Certidão de inteiro teor (nascimento ou casamento)"
QUESITOS = "Certidão por quesitos ou informação avulsa"
PROCEDIMENTO = "Certidão de procedimento preparatório ou documento apresentado (ex.: habilitação de casamento)"
BUSCA_INDICES = "Busca nos índices do cartório"
BUSCA_OUTRAS = "Busca em outras fontes além dos índices"
TIPOS_RCPN = (BREVE_RELATO, OBITO, INTEIRO_TEOR, QUESITOS, PROCEDIMENTO, BUSCA_INDICES, BUSCA_OUTRAS)

PROPRIO = "Próprio registrado, representante legal ou mandatário com poderes especiais"
PARENTE = "Parente em linha reta"
TERCEIRO = "Terceiro"
SOLICITANTES_RCPN = (PROPRIO, PARENTE, TERCEIRO)

PERGUNTA_SENSIVEL = "O assento contém dado sensível (LGPD, art. 5º, II: saúde, origem racial, vida sexual etc.)?"
PERGUNTA_VEDADA = ("O assento contém informação de menção vedada na certidão (CE Art. 471: concepção "
                   "extraconjugal, reconhecimento de filho, estado civil dos pais, natureza da filiação, lugar do "
                   "casamento dos pais)?")
PERGUNTA_FALECIDO = "O registrado (ou o titular do documento) é falecido?"

ALERTA_PARENTE = ("Parente em linha reta é tratado como terceiro, salvo após o falecimento do titular do dado sensível "
                  "(CNJ Art. 114, §2º).")
ALERTA_BREVE_RELATO = ("A certidão de breve relato traz só as informações previstas em lei; qualquer outra informação "
                       "só por certidão por quesitos ou por inteiro teor (CE Art. 256).")
INTEIRO_TEOR_REQUERIMENTO = (CNJ_117, CNJ_117_P3, CE_258)


def _r(canal: str, *fund: Fundamento, finalidade: bool = False, judicial: bool = False, documento: str = "",
       alertas: tuple[str, ...] = (), identificacao: bool = True) -> ResultadoRegra:
    return ResultadoRegra(Cobertura.REGRA, canal, exige_identificacao=identificacao, exige_finalidade=finalidade,
                          fundamentos=fund, alertas=alertas, exige_autorizacao_judicial=judicial, documento=documento)


def _faltam(*pares: tuple[bool | None, str]) -> ResultadoRegra | None:
    perguntas = [p for valor, p in pares if valor is None]
    if not perguntas:
        return None
    return ResultadoRegra(Cobertura.CONDICIONAL, pergunta=" ".join(perguntas))


def _inteiro_teor(solicitante: str, sensivel: bool | None, vedada: bool | None, falecido: bool | None,
                  fundamentos_extra: tuple[Fundamento, ...] = ()) -> ResultadoRegra:
    requerimento = fundamentos_extra + INTEIRO_TEOR_REQUERIMENTO
    if solicitante == PROPRIO:
        return _r("AMARELO", CNJ_114, CE_255, *requerimento, finalidade=True, documento="requerimento_inteiro_teor")
    alertas = (ALERTA_PARENTE,) if solicitante == PARENTE else ()
    if vedada:  # vale mesmo após o óbito (CE Art. 471, §3º)
        return _r("VERMELHO", CE_471_P2, CE_471_P3, *requerimento, finalidade=True, judicial=True,
                  documento="requerimento_inteiro_teor", alertas=alertas)
    if sensivel and falecido is False:
        return _r("VERMELHO", CNJ_114_P1, CE_255_P1, *requerimento, finalidade=True, judicial=True,
                  documento="requerimento_inteiro_teor", alertas=alertas)
    # O óbito só importa quando há dado sensível (CNJ Art. 119)
    falta = _faltam((vedada, PERGUNTA_VEDADA), (sensivel, PERGUNTA_SENSIVEL),
                    (falecido if sensivel else False, PERGUNTA_FALECIDO))
    if falta is not None:
        return falta
    # Aqui: sem informação vedada, e sem dado sensível ou com o registrado falecido
    base = (CNJ_119, CE_260, CNJ_114_P2) if sensivel else ()
    return _r("AMARELO", *base, *requerimento, finalidade=True, documento="requerimento_inteiro_teor", alertas=alertas)


def decidir(tipo_pedido: str, solicitante: str = "", dado_sensivel: bool | None = None,
            informacao_vedada: bool | None = None, registrado_falecido: bool | None = None,
            registro_bloqueado: bool = False) -> ResultadoRegra:
    """Canal pela norma do Registro Civil. Respostas None = não informadas (podem gerar CONDICIONAL)."""
    if registro_bloqueado:
        return _r("VERMELHO", CE_437, judicial=True)
    tipo = tipo_pedido.strip()
    if tipo == BREVE_RELATO:
        return _r("VERDE", CNJ_113, CE_468, CE_256, identificacao=False, alertas=(ALERTA_BREVE_RELATO,))
    if tipo == OBITO:
        return _r("VERDE", CNJ_118, CE_259, identificacao=False)
    if tipo == INTEIRO_TEOR:
        return _inteiro_teor(solicitante, dado_sensivel, informacao_vedada, registrado_falecido)
    if tipo == QUESITOS:
        if solicitante == PROPRIO:
            return _r("VERDE", CNJ_114, CE_255, CE_468)
        falta = _faltam((dado_sensivel, "Os dados pedidos são restritos, sensíveis ou sigilosos?"))
        if falta is not None:
            return falta
        if not dado_sensivel:
            return _r("VERDE", CE_468, identificacao=False)
        # dados restritos, sensíveis ou sigilosos: mesmo tratamento do inteiro teor (CNJ 116; CE 257)
        return _inteiro_teor(solicitante, True, informacao_vedada, registrado_falecido,
                             fundamentos_extra=(CNJ_116, CE_257))
    if tipo == PROCEDIMENTO:
        if solicitante == PROPRIO:
            return _r("VERDE", CNJ_120, CE_261)
        falta = _faltam((registrado_falecido, PERGUNTA_FALECIDO))
        if falta is not None:
            return falta
        if registrado_falecido:
            return _r("AMARELO", CNJ_120_PU, alertas=("Exigir a apresentação da certidão de óbito do titular.",))
        return _r("VERMELHO", CNJ_120, CE_261, judicial=True,
                  alertas=("Exceção: documento público com publicidade geral e irrestrita (CNJ Art. 120).",))
    if tipo == BUSCA_INDICES:
        return _r("VERDE", CNJ_121, CE_262, identificacao=False)
    if tipo == BUSCA_OUTRAS:
        return _r("AMARELO", CNJ_121_PU, CE_262_PU, finalidade=True, documento="requerimento_busca",
                  alertas=("O indeferimento pelo Oficial pode ser revisto pelo juiz competente (CNJ Art. 121, "
                           "parágrafo único).",))
    return ResultadoRegra(Cobertura.SEM_REGRA, exige_identificacao=False)
