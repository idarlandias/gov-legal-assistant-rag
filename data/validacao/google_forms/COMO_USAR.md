# Formulários online (Google Forms): passo a passo

São dois formulários, criados **uma única vez** na sua conta Google por um script pronto:

| Formulário | Para quem | Tempo |
|---|---|---|
| **Pesquisa: atendimento de pedidos de certidão no Registro Civil** | o Oficial (ou substituto) | 30 a 40 min, uma vez |
| **Diário de balcão: pedidos de certidão (1 semana)** | o escrevente, no celular | cerca de 20 s por pedido |

## 1. Criar os formulários (cerca de 2 minutos)

1. Abra **https://script.google.com** e clique em **Novo projeto**.
2. Apague o código que aparece e cole **todo** o conteúdo de [`criar_formularios.gs`](criar_formularios.gs). Salve com Ctrl+S.
3. No topo, confira se a função selecionada é **`criarFormularios`** e clique em **Executar**.
4. O Google pede autorização. Clique em **Revisar permissões**, escolha sua conta, depois **Avançado** e **Acessar projeto (não seguro)**, e por fim **Permitir**. O aviso aparece porque o script é seu e não foi publicado; ele só cria os formulários na sua própria conta.
5. Abra **Registro de execução** (embaixo). Lá estão quatro links:
   - **PESQUISA para o Oficial**: o link que você envia ao cartório;
   - **DIÁRIO DE BALCÃO para o escrevente**: o link do diário;
   - os dois links de **editar** e as duas **planilhas de respostas**: são só para você.

Se quiser, abra o link de editar e troque as cores e o tema no ícone de paleta. Não mude os **títulos das perguntas**, porque é por eles que o leitor encontra cada resposta.

## 2. Enviar ao cartório

Mensagem sugerida (WhatsApp ou e-mail):

> Bom dia! Sou Idarlan Magalhães, residente em Inteligência Artificial Aplicada a Ambientes Corporativos pela SiDi/Softex. Conforme conversamos, segue o formulário da pesquisa sobre o atendimento de pedidos de certidão no Registro Civil. São 13 situações fictícias de balcão, sem nenhum dado pessoal, e leva cerca de 30 a 40 minutos. Dá para responder pelo computador ou pelo celular, e o senhor (ou a senhora) pode voltar e editar depois de enviar: **[link da pesquisa]**
>
> Se for possível, peço também que o balcão registre os pedidos de certidão por uma semana neste formulário rápido (20 segundos por pedido, sem nomes): **[link do diário]**. Muito obrigado!

Dicas:
- O diário funciona melhor com o link **fixado** no celular ou no computador do balcão. Cada pedido é um envio, e no fim aparece "Enviar outra resposta".
- Combine um **apelido curto** para o cartório no diário (ex.: `russas_rcpn`), para separar os cartórios na análise.

## 3. Trazer as respostas para o projeto

1. Abra a **planilha de respostas** e vá em **Arquivo > Fazer download > Valores separados por vírgula (.csv)**.
2. Salve em `data/validacao/respostas/`. Essa pasta fica fora do GitHub, porque as respostas têm o nome do Oficial e dados reais.
3. Rode:

```bash
python scripts/folha_gabarito/ler_respostas_forms.py pesquisa data/validacao/respostas/pesquisa.csv
python scripts/folha_gabarito/ler_respostas_forms.py diario data/validacao/respostas/diario.csv
python scripts/avaliar_gabarito.py
python scripts/resumir_diario.py
```

Os dois primeiros comandos geram o gabarito e o diário. O terceiro mostra **quanto o motor de regras concorda com o Oficial**. O quarto mostra **quantas dúvidas por dia** cada cartório tem.

## Se o Oficial preferir outro formato

O PDF preenchível e a versão para imprimir continuam em `data/validacao/`, como reserva.
