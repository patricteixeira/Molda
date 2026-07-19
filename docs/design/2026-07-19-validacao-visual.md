# Validação visual da Mesa de Provas

Registro da inspeção das telas renderizadas em 19 de julho de 2026. A validação
aconteceu contra a imagem Docker de produção em `http://127.0.0.1:8080`, com API,
Postgres e worker reais.

## Matriz inspecionada

| Área | Desktop | Mobile | Resultado |
| --- | --- | --- | --- |
| Instalador | 1440 × 1000 | 390 × 844 | hierarquia íntegra, dropzone visível, sem overflow horizontal |
| Conferência da marca | 1440 × 1000 | 390 × 844 | texto, cor e fonte legíveis; ação atual e origem da sugestão sempre visíveis |
| Editor | 1440 × 1000 e 1280 × 720 | 390 × 844 | canvas antes dos painéis, seleção visível, arraste e resize acessíveis; catálogo completo sem overflow |
| Kit | 1440 × 1000 | 390 × 844 | catálogo sem cards equivalentes, provas preservam as cores da marca |
| Campanha | 1440 × 1000 | 390 × 844 | continuidade legível e workspace sem anatomia de dashboard |
| Word | 1440 × 1000 | 390 × 844 | três etapas como sequência documental, sem funil de cards |

Em todas as rotas, `scrollWidth` permaneceu igual à largura útil do documento.
O viewport temporário foi restaurado depois da inspeção.

## Interações verificadas

- A camada de texto foi arrastada diretamente no canvas. As coordenadas mudaram
  de `X 48 / Y 324` para `X 164 / Y 392` e a restauração voltou aos valores de
  origem.
- A seleção mantém contorno preto e branco sobre provas coloridas.
- O editor compacto ocupa exatamente a altura de 720 px: toolbar, workbench e
  exportação permanecem dentro do viewport.
- PNG e PPTX podem ser gerados em sequência. O link de download ocupa uma linha
  própria e não intercepta o próximo botão.
- A direção da marca recomenda quatro texturas, mas “Ver todas as 20 texturas”
  permanece disponível. “Curvas de nível”, fora das recomendações iniciais,
  foi aplicada ao canvas e persistiu depois de recarregar o editor.
- O filtro “Pontos e impressão” reduziu o catálogo a duas opções tanto no
  desktop quanto no celular. A faixa mantém 46 px de altura e rolagem
  horizontal no viewport estreito.
- Foco visível, skip link, labels, anúncios assíncronos e redução de movimento
  foram preservados.

## Problemas encontrados pela renderização

1. Regras antigas de `grid-area` comprimiam o upload na lateral. A nova camada
   neutraliza explicitamente as áreas herdadas.
2. Box shadows antigos projetavam azul e coral no chrome. A navegação e o editor
   agora são cromaticamente neutros.
3. O conteúdo natural do inspetor expandia o editor para 1677 px dentro de um
   viewport de 720 px. A página passou a obedecer `100vh`, com workbench e faixa
   de exportação dimensionados pelo grid.
4. O link de download do PNG sobrepunha a ação PPTX. A grade de exportação agora
   separa ações, status e download em linhas próprias.
5. O fundo coral do seletor de arquivos sobrevivia à nova tipografia. A ação
   passou a usar preto e branco e a auditoria cromática das cinco rotas terminou
   sem vazamentos do accent antigo fora das provas de marca.
6. A primeira tela dizia “Pergunta 1 de 8”, mas reunia quatro campos sem explicar
   a consequência das respostas. Ela virou o passo direto “Como é a sua
   marca?”, com rótulos comuns e um resumo das próximas escolhas.
7. A tela de conferência repetia a fotografia do instalador, embora a pessoa
   precisasse comparar opções. A lateral agora mostra o que falta conferir e os
   arquivos que sustentam a escolha atual.
8. O foco automático podia esconder o começo da pergunta e desenhar uma caixa
   indevida ao redor do título. O scroll passou a alinhar a mesa inteira, sem
   remover o foco semântico.
9. No celular, a abertura escondia a seleção de arquivos e a animação deixava a
   ação visível com pouco contraste. A abertura foi compactada e o formulário do
   instalador deixou de depender de animação para aparecer.
10. O editor móvel ainda herdava `max-height: 100vh` do desktop. As áreas
    “Itens” e “Ajustes” eram comprimidas a 7 px e 6 px, embora o conteúdo
    continuasse vazando por baixo da exportação. O limite foi removido no layout
    empilhado: as três áreas agora ocupam 395 px, 1932 px e 265 px em sequência,
    sem sobreposição.
11. A grade rolável do catálogo comprimira a faixa de filtros a 1 px. As linhas
    passaram a respeitar o tamanho do conteúdo; a faixa mede 46 px, o estado
    selecionado é visível e o documento continua sem overflow horizontal.

## Gates executados

- `npm run typecheck`
- `npm test -- --maxWorkers=1`: 129 testes aprovados em 23 arquivos
- `npm run build`
- `npm run e2e`: walking skeleton aprovado em 1 min 18 s
- renderer: Biome, typecheck, build, 78 testes e auditoria sem vulnerabilidades
- API: Ruff, 161 testes aprovados e 2 ignorados
- engine e SDK: Ruff, 333 testes aprovados e 1 ignorado com render obrigatório
- build Docker dos serviços `api`, `worker` e `web`
- inspeção manual das cinco rotas em desktop e mobile
- inspeção das decisões de texto, cor e fonte em desktop e mobile
- inspeção do catálogo de 20 texturas, recomendações, filtros e aplicação fora
  da curadoria inicial em desktop e mobile
- auditoria editorial das ações do instalador, editor, Kit, Campanha e Word
- auditoria cromática do chrome nas cinco rotas, sem azul, amarelo ou coral
  herdados fora dos materiais e previews da marca
- console do editor sem warnings ou erros durante a inspeção final

O E2E atravessa instalação, confirmação, publicação, Kit, seleção e arraste de
camadas, orientação, abertura do catálogo completo, aplicação de uma textura
fora das recomendações, export PNG, export PPTX e round-trip. A direção só é
considerada pronta enquanto esses contratos continuarem verdes.
