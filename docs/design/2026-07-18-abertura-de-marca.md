# Abertura de Marca

Direção visual do Molda para uma ferramenta criativa de alto nível.

## Tese

O Molda não deve parecer um dashboard que recebeu uma camada de estilo. A interface é
um atelier preciso. O chassi permanece neutro para que a identidade ativa atravesse a
experiência por recortes cromáticos, provas reais e transições de continuidade.

Chamamos esse gesto de **Abertura de Marca**.

## Princípios

1. **A marca ocupa o centro.** A cor primária, o fundo, o texto e a tipografia da revisão
   ativa aparecem na interface sem transformar o produto em uma cópia daquela marca.
2. **A ferramenta orienta.** Escolhas autorais nunca recebem aparência de erro. Alertas
   visuais distinguem orientação criativa de bloqueio técnico.
3. **Motion explica relações.** Animações mostram entrada, continuidade, seleção e
   mudança de fase. Nenhum movimento existe apenas para decorar.
4. **O canvas vence o chrome.** No editor, a peça é sempre o elemento visual dominante.
5. **Uma assinatura, muitas rotas.** Instalador, kit, campanha, Word e editor pertencem
   ao mesmo sistema, mas preservam densidades adequadas a cada tarefa.

## Sistema visual

### Tipografia

- Outfit Variable: navegação, títulos, corpo, controles e mensagens.
- JetBrains Mono Variable: medidas, estados técnicos e metadados curtos.
- Máximo de duas famílias.
- Texto corrido entre 45 e 70 caracteres por linha quando a tarefa permitir.
- Títulos com `text-wrap: balance`; parágrafos com `text-wrap: pretty`.
- Algarismos técnicos usam números tabulares.

### Paleta do produto

O produto usa neutros frios com um único sinal vermelhão. O sinal identifica o Molda
antes de uma marca ser instalada. Depois da instalação, a Abertura de Marca recebe os
papéis cromáticos reais da revisão.

- Canvas claro: `#e7e7e2`
- Superfície clara: `#f2f2ed`
- Tinta clara: `#151719`
- Canvas escuro: `#0b0d0f`
- Superfície escura: `#131619`
- Tinta escura: `#f2f0e9`
- Sinal Molda claro: `#d85a3a`
- Tinta sobre o sinal claro: `#151719` (`4.66:1`)
- Sinal Molda escuro: `#ff6a45`
- Tinta sobre o sinal escuro: `#18100d` (`6.61:1`)

### Forma

- Controles: raio de `0.625rem`.
- Painéis funcionais: raio entre `0.625rem` e `0.875rem`.
- Abertura de Marca: cortes oblíquos e bordas duras.
- Círculos aparecem apenas quando comunicam continuidade, não como decoração repetida.

### Superfícies

- Elevação só quando comunica sobreposição ou foco.
- Grupos estáticos preferem espaço e uma única linha divisória.
- Sombras carregam o tom do canvas.
- A textura global é fixa, leve e não participa da rolagem.

## Assinatura dinâmica

`brandThemeStyle()` projeta seis propriedades CSS a partir do Brand IR:

- `--brand-primary`
- `--brand-background`
- `--brand-text`
- `--brand-on-primary`
- `--brand-signal`
- `--brand-on-signal`

Os valores originais nunca são alterados. A cor de contraste é calculada apenas para o
chassi do produto. `--brand-signal` escolhe o papel mais cromaticamente distintivo da
revisão, sem reescrever nenhum token. Aberturas e estados ativos usam esses papéis,
enquanto ações críticas continuam seguindo os contratos de acessibilidade do Molda.

## Motion

- Entrada de rota: opacidade e deslocamento curto.
- Abertura de Marca: compressão horizontal que recupera a escala natural.
- Campanha: a linha de continuidade entra em sequência para explicar a propagação.
- Word: a etapa ativa ganha espaço e as demais preservam contexto.
- Kit: provas reais crescem com a aproximação e recuam depois da leitura.
- `prefers-reduced-motion: reduce` remove transformações e preserva toda a informação.

## Aplicação por superfície

### Instalador

Assimetria editorial, foto real de materiais e uma única faixa de formatos. O texto
explica que o sistema orienta decisões, sem prometer proibições criativas.

### Kit

Cabeçalho fixo como índice da marca, matéria visual ativa e grade densa de provas reais.
Os fluxos Campanha e Word funcionam como portas de trabalho, sem numeração decorativa.

### Campanha

Uma linha visível conecta fonte, formatos e atualização. A biblioteca permanece compacta;
o formulário recebe o foco principal.

### Word

O fluxo de três colunas funciona como um acordeão de estado. Documento, plano e cópia
continuam visíveis, mas a fase atual recebe mais espaço.

### Editor

O chassi industrial permanece. A cor de interação vem da marca ativa e o canvas mantém
prioridade sobre painéis, motion e metadados. Em telas pequenas, o canvas aparece antes
das camadas e das propriedades para preservar a ordem da tarefa.

## Critérios de qualidade

- Nenhuma escolha criativa é bloqueada por aparência ou linguagem.
- Contraste WCAG AA para texto e controles.
- Foco visível e navegação por teclado preservados.
- Estados de carregamento, vazio, erro e sucesso presentes.
- Nenhum listener manual de rolagem.
- Animações usam transform e opacidade.
- Grade do kit sem células vazias.
- Nenhuma dependência visual nova.
- Responsividade verificada em desktop e mobile.
