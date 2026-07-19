# ADR 0015 — Direção criativa local e geometria livre

- Status: aceito
- Data: 2026-07-18
- Decisores: produto e engenharia do Molda

## Contexto

Identificar apenas cores, fontes e logo não basta para orientar uma criação.
Duas marcas podem usar os mesmos tipos de componente e ainda pedir relações
opostas de escala, ritmo, densidade, materialidade e espaço vazio. Oferecer a
ambas a mesma grade com outra paleta transforma identidade em decoração.

O editor também limitava toda camada ao retângulo do canvas. Isso impedia
gestos comuns em direção de arte, como ampliar um símbolo até ele virar campo
gráfico, sangrar uma imagem ou posicionar parte de uma marca fora do corte.

Como o Molda é open source e self-hosted, o fluxo principal não pode depender
de uma API paga pelo mantenedor nem enviar materiais de marca a um serviço
externo sem uma decisão explícita da instância.

## Decisão

### Identidade semântica confirmada

1. O intake procura localmente, nos PDFs fornecidos, trechos sobre essência,
   propósito, personalidade, valores, voz e restrições de expressão.
2. Esses trechos são candidatos com evidência, não uma verdade inferida. A
   pessoa revisa e pode reescrever todos os campos antes da publicação.
3. O Brand IR 0.4 preserva a identidade confirmada e deriva uma direção
   explicável em seis eixos contínuos: energia, geometria, densidade,
   formalidade, materialidade e contraste.
4. Cada direção cita os termos confirmados que a sustentam. Sinal insuficiente
   não produz um preset genérico: a interface informa que precisa conhecer
   melhor a marca.
5. O core é determinístico, offline e não requer chave de API. Provedores
   externos poderão existir como adapters opcionais, configurados e pagos por
   quem opera a instância, sem alterar o contrato local.

### Sugestão que muda estrutura

A direção não troca apenas cor e fonte. Ela parametriza composição, contraste
de escala, espaço negativo, densidade, sangria e uma superfície procedural. Ao
ser aplicada, pode deslocar e redimensionar logo e texto, mudar a hierarquia e
adicionar uma textura coerente com os sinais confirmados da marca.

O vocabulário de superfície é fechado e portátil. Ele nasceu com grão de
papel, ritmo linear, grade técnica, campo de pontos e anéis concêntricos e foi
ampliado pelo
[ADR 0016](0016-catalogo-aberto-de-texturas-procedurais.md) para vinte opções
com paridade de preview, Guard e exportação.

Essas opções são primitivas, não estilos de marca. Cor, escala, peso, ângulo,
opacidade e relação com as camadas são derivados da direção específica. A
pessoa pode escolher qualquer textura, ajustar ou remover tudo.

### Sangria e liberdade autoral

- Layouts-base continuam dentro do canvas e da área segura.
- Overrides do editor aceitam coordenadas negativas e dimensões maiores que o
  canvas, até o limite técnico de 32.768 px por valor.
- O canvas é o corte final: conteúdo excedente é recortado no preview e no
  arquivo exportado.
- Sair do canvas gera orientação, nunca bloqueio criativo.
- A geometria livre é preservada no rascunho, no renderer e no PPTX nativo.

## Consequências

- O round-trip não reabre decisões autorais já presentes no artefato exportado.
  Somente um novo desvio externo em relação ao baseline produz recomendação de
  marca, sempre como aviso revisável.

- Brand IR e schemas públicos avançam para 0.4, mantendo leitura de revisões
  0.1–0.3.
- Content Spec passa a aceitar uma superfície procedural opcional.
- O PPTX rasteriza somente a superfície; texto, imagem e logo permanecem
  objetos nativos e editáveis.
- A direção automática não é aplicada ao fluxo DOCX A4, cuja estrutura e
  paginação exigem um contrato próprio.
- Nenhuma chave, resposta de modelo ou custo por requisição é necessário para
  criar, editar e exportar com a direção de marca.

## Alternativas rejeitadas

- **Um conjunto universal de templates recoloridos:** não lê a identidade e
  produz marcas estruturalmente iguais.
- **Bloquear desvios do usuário:** contradiz o
  [ADR 0014](0014-guard-orienta-sem-policiar.md).
- **API de IA obrigatória:** cria custo operacional, risco de segredo e uma
  dependência incompatível com o núcleo self-hosted.
- **CSS livre como contrato:** prejudica portabilidade, validação e exportação
  determinística.
