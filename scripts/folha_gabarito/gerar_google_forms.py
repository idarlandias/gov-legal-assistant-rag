"""Gera o Google Apps Script que cria os dois formulários online (pesquisa do Oficial e diário de balcão).

Uso:
    python scripts/folha_gabarito/gerar_google_forms.py
Depois: script.google.com > Novo projeto > colar data/validacao/google_forms/criar_formularios.gs >
Executar "criarFormularios" > autorizar. Os links aparecem no registro de execução.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import forms_config as fc  # noqa: E402

CASOS = RAIZ / "data" / "validacao" / "casos_rcpn.json"
SAIDA = RAIZ / "data" / "validacao" / "google_forms" / "criar_formularios.gs"


def _rotulos(pares):
    return [rotulo for _, rotulo in pares]


def itens_pesquisa(casos: list[dict]) -> list[dict]:
    itens = [{"tipo": "texto_info", "titulo": "Como responder",
              "ajuda": "Cada página traz uma situação fictícia de balcão. Marque a decisão que tomaria, quem decide "
                       "no dia a dia e, se puder, a norma e o artigo. Se a situação depender de um fato não "
                       "informado, diga isso no item 4. Não há resposta certa sugerida."}]
    for c in casos:
        n = c["id"]
        itens += [
            {"tipo": "secao", "titulo": f"Caso {n}", "ajuda": c["pergunta"]},
            {"tipo": "escolha", "titulo": fc.t_decisao(n), "opcoes": _rotulos(fc.DECISOES)},
            {"tipo": "escolha", "titulo": fc.t_quem(n), "opcoes": _rotulos(fc.QUEM_DECIDE)},
            {"tipo": "paragrafo", "titulo": fc.t_fundamentos(n),
             "ajuda": "Se não lembrar o número do artigo, descreva a regra."},
            {"tipo": "paragrafo", "titulo": fc.t_como(n)},
            {"tipo": "paragrafo", "titulo": fc.t_erro(n)},
        ]
    itens.append({"tipo": "secao", "titulo": "Perguntas rápidas sobre o atendimento",
                  "ajuda": "Estimativas bastam; não é preciso consultar registros."})
    itens += [{"tipo": "paragrafo", "titulo": fc.t_b(i)} for i in range(1, len(fc.PERGUNTAS_B) + 1)]
    itens += [
        {"tipo": "secao", "titulo": "Validação", "ajuda": "Identificação de quem respondeu."},
        {"tipo": "texto", "titulo": fc.VALIDACAO["nome"]},
        {"tipo": "texto", "titulo": fc.VALIDACAO["funcao"]},
        {"tipo": "texto", "titulo": fc.VALIDACAO["cartorio"],
         "ajuda": "Nome oficial do cartório, como na placa ou no carimbo."},
        {"tipo": "texto", "titulo": fc.VALIDACAO["municipio"]},
        {"tipo": "escolha", "titulo": fc.VALIDACAO["autorizacao"], "opcoes": _rotulos(fc.AUTORIZACAO),
         "obrigatorio": True},
        {"tipo": "caixa", "titulo": fc.VALIDACAO["declaracao"], "opcoes": [fc.TEXTO_DECLARACAO], "obrigatorio": True},
    ]
    return itens


def itens_diario() -> list[dict]:
    d = fc.DIARIO
    return [
        {"tipo": "data", "titulo": d["data"], "obrigatorio": True},
        {"tipo": "texto", "titulo": d["cartorio"], "obrigatorio": True},
        {"tipo": "escolha", "titulo": d["atribuicao"], "opcoes": _rotulos(fc.DIARIO_ATRIBUICAO), "obrigatorio": True},
        {"tipo": "escolha", "titulo": d["canal"], "opcoes": _rotulos(fc.DIARIO_CANAL), "obrigatorio": True},
        {"tipo": "texto", "titulo": d["tipo"],
         "ajuda": "Ex.: breve relato de nascimento, inteiro teor de casamento, certidão de matrícula, busca por nome."},
        {"tipo": "texto", "titulo": d["perfil"], "ajuda": "Ex.: próprio registrado, parente, terceiro, advogado, "
                                                          "órgão público. Nunca escreva nomes."},
        {"tipo": "escolha", "titulo": d["duvida"], "opcoes": _rotulos(fc.DIARIO_DUVIDA), "obrigatorio": True},
        {"tipo": "escolha", "titulo": d["quem"], "opcoes": _rotulos(fc.DIARIO_QUEM), "obrigatorio": True},
        {"tipo": "numero", "titulo": d["tempo"]},
        {"tipo": "escolha", "titulo": d["desfecho"], "opcoes": _rotulos(fc.DIARIO_DESFECHO), "obrigatorio": True},
    ]


JS = r"""// Gerado por scripts/folha_gabarito/gerar_google_forms.py: não edite à mão.
//
// COMO USAR (uma vez, cerca de 2 minutos):
//   1. Abra https://script.google.com e clique em "Novo projeto".
//   2. Apague o conteúdo e cole TODO este arquivo. Salve (Ctrl+S).
//   3. No topo, escolha a função "criarFormularios" e clique em "Executar".
//   4. Autorize o acesso à sua conta Google (é o seu próprio script).
//   5. Abra "Registro de execução": lá estão os links dos dois formulários e das planilhas de respostas.
//
// Os formulários ficam na SUA conta. Nenhum dado é enviado para outro lugar.

const PESQUISA = __PESQUISA__;
const DIARIO = __DIARIO__;

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
"""


def gerar(saida: Path = SAIDA, casos_path: Path = CASOS) -> Path:
    casos = json.loads(casos_path.read_text(encoding="utf-8"))["casos"]
    pesquisa = {"titulo": fc.TITULO_PESQUISA, "descricao": fc.APRESENTACAO, "barra": True,
                "confirmacao": "Respostas enviadas. Muito obrigado pela colaboração!",
                "itens": itens_pesquisa(casos)}
    diario = {"titulo": fc.TITULO_DIARIO, "barra": False,
              "descricao": "Um envio por pedido de certidão, durante uma semana. Leva cerca de 20 segundos. "
                           "Não escreva nome, CPF, número de matrícula ou de protocolo.\n\n"
                           f"Pesquisa de {fc.AUTOR} · {fc.QUALIFICACOES[0]}",
              "confirmacao": "Registrado. Para o próximo pedido, clique em \"Enviar outra resposta\".",
              "itens": itens_diario()}
    js = JS.replace("__PESQUISA__", json.dumps(pesquisa, ensure_ascii=False, indent=2)).replace(
        "__DIARIO__", json.dumps(diario, ensure_ascii=False, indent=2))
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(js, encoding="utf-8", newline="\n")
    return saida


if __name__ == "__main__":
    print("gerado:", gerar())
