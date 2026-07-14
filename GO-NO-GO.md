# Gate 0 OOXML — decisão de 14/07/2026

## Decisão

**GO condicionado para continuar o M2; Gate 0 permanece aberto.**

A mecânica template-first está comprovada estruturalmente, por round-trip real
no LibreOffice e no Google Slides web, além de preview PPTX/DOCX em duas marcas
reais. O gate não pode ser declarado encerrado até o save/reopen no PowerPoint
Desktop.

## Evidência obtida

### Spike A — clonar e preencher layout

- VitaCannMed e Fofo's Massage Therapy geraram um PPTX e um DOCX a partir do
  mesmo Brand IR e dos contratos de conteúdo do M1.
- Cada PPTX preservou 1 master, 11 layouts e a relação do slide com `Title and
  Content`.
- Título e corpo permanecem texto; o logo permanece `picture` substituível.
- Shapes usam nome `br:<role>:<slot>` e descrição com role, revisão e slot.
- Cada DOCX preserva os estilos semânticos `Brand Heading` e `Brand Body`, além
  de uma imagem nativa.
- Nenhum dos quatro artefatos apresentou finding estrutural bloqueante.

### Spike B — round-trip

- Round-trip automatizado com `python-pptx`: role, texto, família e cor alterada
  foram reencontrados nas duas marcas; os arquivos continuaram válidos.
- Round-trip automatizado com `python-docx`: o título editado preservou o estilo
  `Brand Heading` nas duas marcas; os arquivos continuaram válidos.
- Round-trip real no LibreOffice 25.2.3, dentro da imagem isolada: os quatro
  arquivos abriram e foram regravados como PPTX/DOCX sem finding bloqueante.
- O LibreOffice reescreve nome e descrição de placeholders nativos. A inspeção
  passou a usar o tipo nativo do placeholder como terceiro sinal semântico;
  heading, body e logo foram reencontrados nas duas marcas após a regravação.
- Nos DOCX regravados, `Brand Heading`, `Brand Body` e a imagem nativa foram
  preservados nas duas marcas.
- Round-trip manual no Google Slides web: o operador alterou título, corpo,
  estilo e cor, salvou/exportou o PPTX e confirmou a edição. O arquivo voltou
  sem finding bloqueante, sem overflow e com heading, body e logo recuperados.
- O Google Slides renomeou os objetos para `Google Shape;…`, mas preservou as
  descrições semânticas. Também converteu a cor editada em `accent1` e deixou a
  família Arial herdada do tema; `native-inspect` passou a resolver color scheme
  e major/minor fonts em vez de exigir RGB e typeface explícitos.
- A evidência estruturada está em
  `docs/validation/2026-07-14-m2-google-slides-roundtrip.json`; o artefato local
  preservado é `out/m2-gate0/proof-google-slides-edited.pptx`, com SHA-256
  `4e1f4a60f061dc47555e7a20b802cff665e2641abb99019ae57d0efeb0bc0225`.
- **Pendente obrigatório:** abrir, editar, salvar e reabrir no PowerPoint
  Desktop. A busca por executável, App Paths e pacote instalado encontrou apenas
  o Microsoft Office Hub; o operador confirmou que não possui PowerPoint
  Desktop neste ambiente.

### Spike C — preview

- O renderer independente do toolkit de apresentações abriu e rasterizou os
  dois PPTX.
- O teste de canvas encontrou um overflow real na primeira versão VitaCannMed;
  o renderer passou a projetar os slots do Layout Spec nos placeholders nativos.
- Após a correção, VitaCannMed e Fofo's passaram sem overflow.
- A imagem `infra/docker/native-preview.Dockerfile` instala LibreOffice e expõe
  `brandrt native-preview`; a falha do conversor é warning não destrutivo.
- A imagem foi construída como `brandrt-native-preview:m2` e executada com rede
  desabilitada, filesystem somente leitura, capabilities removidas, limite de
  memória/PIDs e usuário não-root.
- VitaCannMed e Fofo's geraram PDF e PNG tanto de PPTX quanto de DOCX, sem
  diagnóstico. As quatro saídas foram inspecionadas visualmente, sem clipping,
  sobreposição ou corte de imagem.
- As fontes comerciais/referenciadas não estão instaladas na imagem; portanto,
  o LibreOffice usa fallback no preview. Os nomes corretos continuam gravados no
  OOXML e foram reencontrados após round-trip. A fidelidade tipográfica final
  depende da instalação licenciada dessas fontes no editor/conversor.

## Regressão e segurança

- Golden tests com XML canonicalizado cobrem theme, masters, layouts, slides,
  relações, styles e mídia.
- O corte M2.1 integra `pptx` e `docx` ao contrato API → job → worker → storage;
  a versão `v1` do template fica persistida no job e cada perfil social mantém
  seu aspect ratio nativo. O download serve MIME e filename próprios.
- Templates de produção são recursos imutáveis e reproduzíveis do pacote. O
  worker valida os quatro no boot, rasteriza SVG somente em diretório efêmero e
  recusa colisão do manifest com `out.<formato>`.
- O validador bloqueia path traversal, macros, executáveis, OLE/embeddings,
  relações externas, XML inválido e slide sem layout.
- O template original nunca é sobrescrito; toda escrita final usa arquivo
  temporário e substituição atômica.

## Matriz de editores desta rodada

| Editor/caminho | Abrir | Editar | Salvar | Reinspecionar | Resultado |
|---|---:|---:|---:|---:|---|
| python-pptx 1.0.2 | sim | sim | sim | sim | passou, evidência automatizada |
| python-docx 1.2.0 | sim | sim | sim | sim | passou, evidência automatizada |
| renderer independente de PPTX | sim | — | — | visual | passou, sem overflow |
| PowerPoint Desktop | pendente | pendente | pendente | pendente | obrigatório para fechar |
| Google Slides web | sim | sim | sim/export | sim/visual | passou, roles, tema e formato preservados |
| LibreOffice Impress 25.2.3 | sim | — | sim | sim | passou, roles e formato preservados |
| LibreOffice Writer 25.2.3 | sim | — | sim | sim/visual | passou, styles e imagem preservados |
| Preview isolado PDF/PNG | sim | — | sim | visual | quatro artefatos passaram |

## Próxima ação para fechar o gate

1. Obter acesso pontual a uma máquina ou colaborador com PowerPoint Desktop,
   abrir `out/m2-gate0/proof.pptx`, alterar título/fonte/cor e salvar como
   `proof-powerpoint-edited.pptx`.
2. Executar `brandrt native-inspect proof-powerpoint-edited.pptx` e anexar o
   JSON ao gate.
3. Se a comparação visual final exigir fidelidade tipográfica, instalar ou
   montar no ambiente de teste as fontes licenciadas das duas marcas e renovar
   os baselines.

Enquanto o PowerPoint Desktop estiver indisponível, é seguro evoluir contratos e
adapters do M2, mas não publicar a promessa de round-trip universal.
