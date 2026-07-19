# Mesa de Provas

Direção visual monocromática do Molda para um espaço de criação, não uma página
de venda nem um painel técnico.

## Leitura de design

Redesign completo de um produto criativo para pessoas leigas, com linguagem de
mesa editorial. A interface deve parecer um lugar onde materiais são reunidos,
comparados e transformados em provas reais.

- Variância: 8. A composição quebra a simetria quando a tarefa pede.
- Movimento: 4. O movimento explica entrada, seleção e continuidade.
- Densidade: 5. A operação é compacta, mas o canvas mantém espaço para respirar.

## O que foi descartado

`Abertura de Marca` chamava a interface de atelier, mas conservava sinais de
SaaS e devtool: hero dividido, fotografia aspiracional, card de conversão,
accent cromático, cantos arredondados, sombras, etiquetas monoespaçadas e
status de infraestrutura na navegação.

Esses sinais não serão refinados. Eles deixam de compor o produto.

## Tese

O Molda começa pela matéria que a pessoa já possui. O produto não precisa se
vender na primeira tela. Precisa tornar claro, em poucos segundos, que manual,
logo, fontes, imagens e tokens podem ser colocados sobre uma mesma superfície e
transformados em trabalho vivo.

O chrome do produto é monocromático. As cores de uma marca aparecem somente
onde são conteúdo: provas, canvas, amostras e arquivos exportados. A interface
não se fantasia com a cor da marca instalada.

## Sistema tipográfico

- Newsreader Variable: frases-manifesto e títulos editoriais curtos.
- Archivo Variable: navegação, formulários, instruções e controles.
- `ui-monospace`: somente medidas, coordenadas e valores técnicos.
- Texto corrido entre 45 e 70 caracteres por linha.
- Títulos nunca dependem apenas de tamanho; posição, peso e espaço constroem a
  hierarquia.
- Caixa alta fica restrita a rótulos funcionais muito curtos e recebe
  espaçamento de letras.

## Linguagem para pessoas leigas

- Cada tela responde com palavras comuns: o que encontramos, o que a pessoa
  precisa escolher e o que acontece depois.
- Termos internos como `evidência`, `token`, `runtime`, `layout` e `Brand IR`
  não aparecem na interface sem uma explicação em linguagem comum.
- `Fonte`, `logo`, `cor`, `imagem`, `arquivo` e `modelo` são preferidos aos
  equivalentes técnicos.
- Instruções usam frases curtas, verbos diretos e uma ação por vez.
- A pessoa sempre pode corrigir, continuar ou voltar aos arquivos. A interface
  orienta, mas não proíbe escolhas da marca.

## Cor e matéria

- Papel: `#f1f0e9`.
- Folha: `#fbfaf4`.
- Tinta: `#11110f`.
- Grafite: `#595a55`.
- Regra: `#b9bab4`.
- Mesa: `#d7d6cf`.

Não existe accent do produto. Seleção usa inversão preto e branco. Foco usa
contorno duplo. Alertas continuam semanticamente distintos, mas sem transformar
orientação criativa em erro.

Sombras são reservadas ao canvas ou a uma folha realmente sobreposta. Painéis,
formulários e grupos usam espaço, alinhamento e uma única regra.

## Forma

- Cantos retos em superfícies, botões, inputs e áreas de trabalho.
- Círculos apenas quando o controle nativo ou a função exigirem.
- Nenhuma pílula decorativa.
- Nenhum card usado apenas para agrupar conteúdo.
- Linhas existem para organizar tarefas reais, não para simular uma grade de
  design.

## Instalador

O instalador é uma superfície de trabalho.

- O título é `Traga o que já existe.`
- A área inteira de trabalho recebe arquivos.
- O botão de seleção é uma alternativa acessível ao gesto de soltar.
- Formatos aceitos aparecem como informação marginal, sem marquee.
- Materiais reunidos formam um índice de trabalho, não uma lista dentro de um
  card.
- A fotografia existente funciona como evidência de origem, nunca como imagem
  aspiracional de hero.
- Detalhes de runtime e infraestrutura deixam a navegação principal.

## Editor

O editor é uma mesa gráfica clara.

- O canvas é o primeiro objeto na ordem de leitura e o centro de gravidade.
- Camadas funcionam como índice editorial.
- Propriedades funcionam como caderno de medidas.
- A seleção do canvas usa contorno preto e branco para sobreviver às cores da
  peça.
- Coordenadas negativas, sangria, resize e arraste permanecem livres.
- A direção derivada da identidade aparece como leitura explicada, não preset.
- Texturas aparecem como amostras visuais: primeiro as que combinam com a
  marca, depois o catálogo completo organizado por matéria, linhas, grades,
  pontos e movimento.
- A recomendação nunca esconde nem desabilita uma textura.
- Exportação é uma continuação da mesa, não uma seção comercial.

## Propagação

Somente depois de Instalador e Editor funcionarem visualmente em preto e branco,
a linguagem se propaga:

- Kit: índice de provas com variação de escala, sem grade de cards equivalentes.
- Campanha: uma fonte compartilhada e suas saídas, sem biblioteca de dashboard.
- Word: passagem do documento original para o documento aplicado, sem três
  painéis comerciais.

## Movimento

- Entrada: opacidade e deslocamento curto da folha ativa.
- Upload: os materiais entram como índice, sem partículas nem espetáculo.
- Seleção: inversão imediata e deslocamento máximo de 1 px no pressionar.
- Campanha: a atualização percorre fonte e peças na ordem real do fluxo.
- `prefers-reduced-motion` preserva toda a informação sem transições.

## Critérios de validação

- A tela não pode ser confundida com e-commerce, fintech ou landing page SaaS
  depois de trocar a copy.
- A composição precisa funcionar sem cor de destaque.
- Instalador e editor devem ser avaliados renderizados em desktop e mobile.
- O canvas aparece antes dos painéis na ordem do DOM e na leitura mobile.
- Contraste WCAG AA, foco visível e teclado permanecem íntegros.
- Nenhuma rota, nome de campo, `data-testid`, contrato de API ou formato de
  exportação muda por causa do redesign.
- Loading, vazio, erro e sucesso continuam presentes.
- A alteração só fica pronta depois do E2E real e da inspeção das capturas.
