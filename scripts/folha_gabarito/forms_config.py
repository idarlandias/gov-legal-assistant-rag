"""Textos e vocabulário dos formulários online (Google Forms), compartilhados pelo gerador e pelo leitor.

Cada opção exibida no formulário tem um código: é o código que vai para o gabarito
(scripts/avaliar_gabarito.py) e para o diário de balcão (scripts/resumir_diario.py).
"""

from __future__ import annotations

AUTOR = "Idarlan Magalhães"
QUALIFICACOES = ("Residente em Inteligência Artificial Aplicada a Ambientes Corporativos · SiDi/Softex",
                 "Desenvolvedor de sistemas e aplicações web")
CONTATOS = ("idarlandias@gmail.com", "github.com/idarlandias", "linkedin.com/in/idarlandias")

TITULO_PESQUISA = "Pesquisa: atendimento de pedidos de certidão no Registro Civil"
TITULO_DIARIO = "Diário de balcão: pedidos de certidão (1 semana)"

APRESENTACAO = (
    f"{AUTOR}\n" + "\n".join(QUALIFICACOES) + "\n" + "  ·  ".join(CONTATOS) + "\n\n"
    "Prezado(a) Oficial,\n\n"
    "Estudo como funciona, na prática, o atendimento de pedidos de certidão no Registro Civil quando o pedido envolve "
    "dados pessoais: quem pode pedir, o que exigir do requerente e quando a expedição depende de autorização judicial. "
    "Estou desenvolvendo uma ferramenta de apoio ao balcão que mostra ao atendente o que a norma exige para cada tipo "
    "de pedido. Ela não decide nada: a decisão e a responsabilidade continuam sendo do Oficial. Antes de qualquer uso, "
    "preciso saber se ela acerta, e para isso preciso da resposta de quem conhece a rotina e a norma.\n\n"
    "O formulário tem 13 situações de balcão (cerca de 30 a 40 minutos) e 7 perguntas rápidas (5 minutos).\n\n"
    "Garantias: todos os casos são fictícios e nenhum dado pessoal é pedido; as respostas serão usadas apenas nesta "
    "pesquisa; não é venda nem avaliação do cartório; não existe resposta \"errada\": vale a sua prática e a sua "
    "leitura da norma; pode deixar itens em branco ou parar a qualquer momento.\n\n"
    "Muito obrigado pela colaboração."
)

# (código, texto exibido)
DECISOES = [
    ("DEFERIR", "Deferir (atender sem exigência adicional)"),
    ("DEFERIR_COM_EXIGENCIA", "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)"),
    ("INDEFERIR_NOTA", "Indeferir em nota fundamentada"),
    ("ENCAMINHAR_JUIZ", "Encaminhar ao juízo competente (autorização judicial)"),
    ("INFORMAR", "Apenas informar / orientar"),
    ("NAO_SE_APLICA", "Não se aplica ao Registro Civil"),
]
QUEM_DECIDE = [("escrevente", "Escrevente"), ("oficial", "Oficial ou substituto")]
PERGUNTAS_B = [
    "Quantos pedidos de certidão o cartório atende por dia, em média?",
    "Desses, quantos fazem o atendente parar para consultar alguém ou a norma?",
    "Em que tipos de pedido a dúvida é mais comum?",
    "Quando há dúvida, quem decide: o escrevente, o substituto ou o Oficial?",
    "O cartório registra quem pediu a certidão e para quê? Onde (livro, sistema, planilha)?",
    "Que sistema o cartório usa? Ele tem algum recurso de inteligência artificial?",
    "A última correição apontou algo sobre dados pessoais ou certidões?",
]
AUTORIZACAO = [
    ("nome", "Podem citar meu nome, função e cartório."),
    ("funcao_municipio", "Prefiro não ser identificado(a): citar apenas a função e o município."),
    ("agregado", "Não autorizo citar nenhuma informação; usar as respostas apenas de forma agregada."),
]

# Diário: rótulos das opções → códigos de scripts/resumir_diario.py
DIARIO_ATRIBUICAO = [("RCPN", "Registro Civil"), ("RI", "Registro de Imóveis"), ("OUTRA", "Outra")]
DIARIO_DUVIDA = [("sim", "Sim"), ("nao", "Não")]
DIARIO_QUEM = [("escrevente", "Escrevente"), ("substituto", "Substituto"), ("oficial", "Oficial"),
               ("consulta_externa", "Consulta externa"), ("nao_se_aplica", "Ninguém precisou decidir")]
DIARIO_DESFECHO = [("emitida", "Emitida"), ("emitida_com_exigencia", "Emitida com exigência"),
                   ("exigencia_pendente", "Exigência pendente"), ("recusada_nota", "Recusada em nota"),
                   ("orientado", "Só orientado"), ("encaminhado_juiz", "Encaminhado ao juiz"),
                   ("desistiu", "Requerente desistiu")]
DIARIO_CANAL = [("balcao", "Balcão"), ("telefone", "Telefone"), ("email", "E-mail"), ("whatsapp", "WhatsApp"),
                ("online", "Online")]


# ---------------------------------------------------------------- títulos das perguntas (= colunas do CSV)

def t_decisao(n: int) -> str:
    return f"Caso {n} · 1. Decisão"


def t_quem(n: int) -> str:
    return f"Caso {n} · 2. Quem decide no balcão"


def t_fundamentos(n: int) -> str:
    return f"Caso {n} · 3. Fundamentos (norma e artigo)"


def t_como(n: int) -> str:
    return f"Caso {n} · 4. Como atender (o que dizer e o que exigir)"


def t_erro(n: int) -> str:
    return f"Caso {n} · 5. O que seria um erro grave neste caso"


def t_b(i: int) -> str:
    return f"B{i}. {PERGUNTAS_B[i - 1]}"


VALIDACAO = {"nome": "Seu nome", "funcao": "Função (Oficial, substituto, escrevente)",
             "cartorio": "Cartório (nome da serventia)", "municipio": "Município",
             "autorizacao": "Uso do seu nome na pesquisa", "declaracao": "Declaração"}
TEXTO_DECLARACAO = ("Declaro que as respostas refletem meu entendimento das normas aplicáveis e da rotina do "
                    "atendimento na data de envio.")

DIARIO = {"data": "Data do pedido", "cartorio": "Cartório (apelido curto, ex.: russas_rcpn)",
          "atribuicao": "Atribuição", "canal": "Por onde chegou o pedido", "tipo": "Tipo de pedido",
          "perfil": "Quem pediu", "duvida": "Gerou dúvida? (precisou parar para consultar alguém ou a norma)",
          "quem": "Quem decidiu", "tempo": "Tempo do atendimento (minutos)", "desfecho": "Resultado"}
