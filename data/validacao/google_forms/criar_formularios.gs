// Gerado por scripts/folha_gabarito/gerar_google_forms.py: não edite à mão.
//
// COMO USAR (uma vez, cerca de 2 minutos):
//   1. Abra https://script.google.com e clique em "Novo projeto".
//   2. Apague o conteúdo e cole TODO este arquivo. Salve (Ctrl+S).
//   3. No topo, escolha a função "criarFormularios" e clique em "Executar".
//   4. Autorize o acesso à sua conta Google (é o seu próprio script).
//   5. Abra "Registro de execução": lá estão os links dos dois formulários e das planilhas de respostas.
//
// Os formulários ficam na SUA conta. Nenhum dado é enviado para outro lugar.

const PESQUISA = {
  "titulo": "Pesquisa: atendimento de pedidos de certidão no Registro Civil",
  "descricao": "Idarlan Magalhães\nResidente em Inteligência Artificial Aplicada a Ambientes Corporativos · SiDi/Softex\nDesenvolvedor de sistemas e aplicações web\nidarlandias@gmail.com  ·  github.com/idarlandias  ·  linkedin.com/in/idarlandias\n\nPrezado(a) Oficial,\n\nEstudo como funciona, na prática, o atendimento de pedidos de certidão no Registro Civil quando o pedido envolve dados pessoais: quem pode pedir, o que exigir do requerente e quando a expedição depende de autorização judicial. Estou desenvolvendo uma ferramenta de apoio ao balcão que mostra ao atendente o que a norma exige para cada tipo de pedido. Ela não decide nada: a decisão e a responsabilidade continuam sendo do Oficial. Antes de qualquer uso, preciso saber se ela acerta, e para isso preciso da resposta de quem conhece a rotina e a norma.\n\nO formulário tem 13 situações de balcão (cerca de 30 a 40 minutos) e 7 perguntas rápidas (5 minutos).\n\nGarantias: todos os casos são fictícios e nenhum dado pessoal é pedido; as respostas serão usadas apenas nesta pesquisa; não é venda nem avaliação do cartório; não existe resposta \"errada\": vale a sua prática e a sua leitura da norma; pode deixar itens em branco ou parar a qualquer momento.\n\nMuito obrigado pela colaboração.",
  "barra": true,
  "confirmacao": "Respostas enviadas. Muito obrigado pela colaboração!",
  "itens": [
    {
      "tipo": "texto_info",
      "titulo": "Como responder",
      "ajuda": "Cada página traz uma situação fictícia de balcão. Marque a decisão que tomaria, quem decide no dia a dia e, se puder, a norma e o artigo. Se a situação depender de um fato não informado, diga isso no item 4. Não há resposta certa sugerida."
    },
    {
      "tipo": "secao",
      "titulo": "Caso 101",
      "ajuda": "Uma pessoa sem parentesco com o registrado pede, no balcão, a certidão de nascimento em breve relato de um vizinho. Como atender e o que exigir?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 101 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 101 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 101 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 101 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 101 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 102",
      "ajuda": "Um terceiro, sem parentesco, pede a certidão de óbito de uma pessoa. É preciso requerimento escrito ou autorização judicial?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 102 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 102 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 102 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 102 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 102 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 103",
      "ajuda": "A própria registrada, maior de idade, pede a sua certidão de nascimento em inteiro teor. Como atender e o que exigir?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 103 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 103 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 103 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 103 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 103 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 104",
      "ajuda": "Um terceiro pede a certidão de casamento em inteiro teor de um casal vivo. O assento não contém dado sensível nem informação de menção vedada na certidão. Como atender e o que exigir?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 104 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 104 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 104 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 104 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 104 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 105",
      "ajuda": "Um terceiro pede a certidão de nascimento em inteiro teor de uma pessoa viva. O assento contém dado sensível (LGPD, art. 5º, II) e nenhuma informação de menção vedada. A certidão pode ser emitida no balcão?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 105 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 105 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 105 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 105 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 105 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 106",
      "ajuda": "O filho de uma pessoa falecida pede a certidão de nascimento em inteiro teor do pai. O assento contém dado sensível (LGPD, art. 5º, II) e nenhuma informação de menção vedada. Como atender e o que exigir?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 106 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 106 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 106 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 106 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 106 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 107",
      "ajuda": "Um terceiro pede a certidão de nascimento em inteiro teor de uma pessoa viva. O assento contém averbação de reconhecimento de filho e nenhum dado sensível. A certidão pode ser emitida no balcão?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 107 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 107 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 107 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 107 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 107 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 108",
      "ajuda": "Um terceiro pede certidão por quesitos com uma única informação do assento, que não é dado restrito, sensível nem sigiloso. Como atender e o que exigir?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 108 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 108 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 108 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 108 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 108 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 109",
      "ajuda": "Um terceiro pede certidão dos documentos apresentados no processo de habilitação de casamento de um casal vivo. Os documentos não são públicos de publicidade geral. Como atender?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 109 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 109 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 109 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 109 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 109 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 110",
      "ajuda": "Um terceiro pede certidão dos documentos apresentados na habilitação de casamento de uma pessoa já falecida. Como atender e o que exigir?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 110 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 110 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 110 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 110 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 110 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 111",
      "ajuda": "Um terceiro quer saber se existe, no cartório, registro de nascimento de uma determinada pessoa, consultando os índices. É preciso justificar ou fazer requerimento?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 111 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 111 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 111 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 111 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 111 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 112",
      "ajuda": "Um terceiro pede que o cartório busque, além dos índices, em documentos arquivados, informações sobre uma pessoa. Como atender e o que exigir?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 112 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 112 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 112 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 112 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 112 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Caso 113",
      "ajuda": "O próprio registrado pede a sua certidão de nascimento em breve relato, mas o registro está bloqueado por determinação judicial. Como atender?"
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 113 · 1. Decisão",
      "opcoes": [
        "Deferir (atender sem exigência adicional)",
        "Deferir com exigência prévia (requerimento, identificação, motivo ou outro documento)",
        "Indeferir em nota fundamentada",
        "Encaminhar ao juízo competente (autorização judicial)",
        "Apenas informar / orientar",
        "Não se aplica ao Registro Civil"
      ]
    },
    {
      "tipo": "escolha",
      "titulo": "Caso 113 · 2. Quem decide no balcão",
      "opcoes": [
        "Escrevente",
        "Oficial ou substituto"
      ]
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 113 · 3. Fundamentos (norma e artigo)",
      "ajuda": "Se não lembrar o número do artigo, descreva a regra."
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 113 · 4. Como atender (o que dizer e o que exigir)"
    },
    {
      "tipo": "paragrafo",
      "titulo": "Caso 113 · 5. O que seria um erro grave neste caso"
    },
    {
      "tipo": "secao",
      "titulo": "Perguntas rápidas sobre o atendimento",
      "ajuda": "Estimativas bastam; não é preciso consultar registros."
    },
    {
      "tipo": "paragrafo",
      "titulo": "B1. Quantos pedidos de certidão o cartório atende por dia, em média?"
    },
    {
      "tipo": "paragrafo",
      "titulo": "B2. Desses, quantos fazem o atendente parar para consultar alguém ou a norma?"
    },
    {
      "tipo": "paragrafo",
      "titulo": "B3. Em que tipos de pedido a dúvida é mais comum?"
    },
    {
      "tipo": "paragrafo",
      "titulo": "B4. Quando há dúvida, quem decide: o escrevente, o substituto ou o Oficial?"
    },
    {
      "tipo": "paragrafo",
      "titulo": "B5. O cartório registra quem pediu a certidão e para quê? Onde (livro, sistema, planilha)?"
    },
    {
      "tipo": "paragrafo",
      "titulo": "B6. Que sistema o cartório usa? Ele tem algum recurso de inteligência artificial?"
    },
    {
      "tipo": "paragrafo",
      "titulo": "B7. A última correição apontou algo sobre dados pessoais ou certidões?"
    },
    {
      "tipo": "secao",
      "titulo": "Validação",
      "ajuda": "Identificação de quem respondeu."
    },
    {
      "tipo": "texto",
      "titulo": "Seu nome"
    },
    {
      "tipo": "texto",
      "titulo": "Função (Oficial, substituto, escrevente)"
    },
    {
      "tipo": "texto",
      "titulo": "Cartório (nome da serventia)",
      "ajuda": "Nome oficial do cartório, como na placa ou no carimbo."
    },
    {
      "tipo": "texto",
      "titulo": "Município"
    },
    {
      "tipo": "escolha",
      "titulo": "Uso do seu nome na pesquisa",
      "opcoes": [
        "Podem citar meu nome, função e cartório.",
        "Prefiro não ser identificado(a): citar apenas a função e o município.",
        "Não autorizo citar nenhuma informação; usar as respostas apenas de forma agregada."
      ],
      "obrigatorio": true
    },
    {
      "tipo": "caixa",
      "titulo": "Declaração",
      "opcoes": [
        "Declaro que as respostas refletem meu entendimento das normas aplicáveis e da rotina do atendimento na data de envio."
      ],
      "obrigatorio": true
    }
  ]
};
const DIARIO = {
  "titulo": "Diário de balcão: pedidos de certidão (1 semana)",
  "barra": false,
  "descricao": "Um envio por pedido de certidão, durante uma semana. Leva cerca de 20 segundos. Não escreva nome, CPF, número de matrícula ou de protocolo.\n\nPesquisa de Idarlan Magalhães · Residente em Inteligência Artificial Aplicada a Ambientes Corporativos · SiDi/Softex",
  "confirmacao": "Registrado. Para o próximo pedido, clique em \"Enviar outra resposta\".",
  "itens": [
    {
      "tipo": "data",
      "titulo": "Data do pedido",
      "obrigatorio": true
    },
    {
      "tipo": "texto",
      "titulo": "Cartório (apelido curto, ex.: russas_rcpn)",
      "obrigatorio": true
    },
    {
      "tipo": "escolha",
      "titulo": "Atribuição",
      "opcoes": [
        "Registro Civil",
        "Registro de Imóveis",
        "Outra"
      ],
      "obrigatorio": true
    },
    {
      "tipo": "escolha",
      "titulo": "Por onde chegou o pedido",
      "opcoes": [
        "Balcão",
        "Telefone",
        "E-mail",
        "WhatsApp",
        "Online"
      ],
      "obrigatorio": true
    },
    {
      "tipo": "texto",
      "titulo": "Tipo de pedido",
      "ajuda": "Ex.: breve relato de nascimento, inteiro teor de casamento, certidão de matrícula, busca por nome."
    },
    {
      "tipo": "texto",
      "titulo": "Quem pediu",
      "ajuda": "Ex.: próprio registrado, parente, terceiro, advogado, órgão público. Nunca escreva nomes."
    },
    {
      "tipo": "escolha",
      "titulo": "Gerou dúvida? (precisou parar para consultar alguém ou a norma)",
      "opcoes": [
        "Sim",
        "Não"
      ],
      "obrigatorio": true
    },
    {
      "tipo": "escolha",
      "titulo": "Quem decidiu",
      "opcoes": [
        "Escrevente",
        "Substituto",
        "Oficial",
        "Consulta externa",
        "Ninguém precisou decidir"
      ],
      "obrigatorio": true
    },
    {
      "tipo": "numero",
      "titulo": "Tempo do atendimento (minutos)"
    },
    {
      "tipo": "escolha",
      "titulo": "Resultado",
      "opcoes": [
        "Emitida",
        "Emitida com exigência",
        "Exigência pendente",
        "Recusada em nota",
        "Só orientado",
        "Encaminhado ao juiz",
        "Requerente desistiu"
      ],
      "obrigatorio": true
    }
  ]
};

function criarFormularios() {
  const pesquisa = criarFormulario_(PESQUISA);
  const diario = criarFormulario_(DIARIO);
  diario.form.setShowLinkToRespondAgain(true);
  Logger.log('PESQUISA para o Oficial (envie este link): ' + pesquisa.form.getPublishedUrl());
  Logger.log('   editar: ' + pesquisa.form.getEditUrl() + '   respostas: ' + pesquisa.planilha.getUrl());
  Logger.log('DIÁRIO DE BALCÃO para o escrevente (envie este link): ' + diario.form.getPublishedUrl());
  Logger.log('   editar: ' + diario.form.getEditUrl() + '   respostas: ' + diario.planilha.getUrl());
}

function criarFormulario_(def) {
  const form = FormApp.create(def.titulo);
  form.setDescription(def.descricao);
  form.setConfirmationMessage(def.confirmacao);
  form.setProgressBar(def.barra);
  form.setCollectEmail(false);
  form.setAllowResponseEdits(true);
  def.itens.forEach(function (it) {
    var item;
    switch (it.tipo) {
      case 'secao':
        form.addPageBreakItem().setTitle(it.titulo).setHelpText(it.ajuda || '');
        return;
      case 'texto_info':
        form.addSectionHeaderItem().setTitle(it.titulo).setHelpText(it.ajuda || '');
        return;
      case 'escolha':
        item = form.addMultipleChoiceItem().setChoiceValues(it.opcoes);
        break;
      case 'caixa':
        item = form.addCheckboxItem().setChoiceValues(it.opcoes);
        break;
      case 'paragrafo':
        item = form.addParagraphTextItem();
        break;
      case 'texto':
        item = form.addTextItem();
        break;
      case 'numero':
        item = form.addTextItem().setValidation(
          FormApp.createTextValidation().requireNumber().setHelpText('Digite só o número de minutos.').build());
        break;
      case 'data':
        item = form.addDateItem();
        break;
      default:
        throw new Error('tipo desconhecido: ' + it.tipo);
    }
    item.setTitle(it.titulo);
    if (it.ajuda) item.setHelpText(it.ajuda);
    if (it.obrigatorio) item.setRequired(true);
  });
  const planilha = SpreadsheetApp.create(def.titulo + ' (respostas)');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, planilha.getId());
  return { form: form, planilha: planilha };
}
