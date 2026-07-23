# Laboratório de Referências de Templates 0.1

O laboratório recebe templates autorais ou referências licenciadas em uma área
isolada do catálogo publicado. Ele prova integridade, registra proveniência,
compara estruturas raster e situa a gramática declarada diante das treze
famílias atuais. O resultado é uma triagem para crítica humana — nunca um novo
`TemplatePackage`.

## O que o auditor faz

- confere paths portáveis, inventário fechado, tamanhos e SHA-256;
- rejeita symlinks, colisões sem distinguir maiúsculas e arquivos não declarados;
- abre apenas a prévia PNG, JPEG ou WebP, sem animação e até 40 megapixels;
- preserva fontes HTML, CSS, JSON, PDF, SVG ou PPTX como bytes, sem executá-las;
- gera uma impressão visual de 64 bits em tons de cinza para apontar duplicatas
  exatas e estruturas que parecem apenas recoloridas;
- compara seis eixos, composição e superfície com as famílias do catálogo;
- publica um relatório determinístico sem timestamp nem path absoluto.

## Estrutura

```text
meu-corpus/
├── template-corpus.json
└── references/
    └── editorial-01/
        ├── template-reference.json
        ├── preview.png
        └── fonte.html
```

O manifesto raiz declara somente os manifestos individuais:

```json
{
  "schemaVersion": "0.1.0",
  "id": "atelier-patric",
  "titlePt": "Templates autorais de Patric",
  "owner": "Patric",
  "references": [
    "references/editorial-01/template-reference.json"
  ]
}
```

Cada referência declara todos os arquivos de seu próprio diretório:

```json
{
  "schemaVersion": "0.1.0",
  "id": "editorial-01",
  "titlePt": "Editorial de abertura",
  "intent": "reference",
  "provenance": {
    "author": "Patric",
    "ownership": "authored",
    "usagePolicy": "derivative-authoring"
  },
  "purposes": ["abertura de campanha", "manifesto curto"],
  "profiles": ["post-4x5"],
  "files": [
    {
      "path": "preview.png",
      "role": "preview",
      "mediaType": "image/png",
      "size": 184320,
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "path": "fonte.html",
      "role": "source",
      "mediaType": "text/html",
      "size": 4096,
      "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    }
  ],
  "grammar": {
    "axes": {
      "energy": 0.2,
      "geometry": 0.1,
      "density": -0.4,
      "formality": 0.5,
      "materiality": -0.2,
      "contrast": 0.6
    },
    "compositions": ["asymmetric"],
    "surfaces": ["paper-grain"],
    "hierarchy": "type-led",
    "alignment": "grid",
    "slotRoles": ["headline", "supporting-copy", "image"],
    "negativeSpace": 0.58
  }
}
```

Os hashes e tamanhos do exemplo são ilustrativos; o manifesto real deve registrar
os bytes exatos. Uma referência pública ou de autoria desconhecida aceita apenas
`usagePolicy: "analysis-only"`. Uma referência licenciada precisa de
`licenseId`.

## Execução

```powershell
cd packages/engine
.venv/Scripts/brandrt template-corpus-audit `
  C:\caminho\meu-corpus `
  --out C:\caminho\template-corpus-report.json
```

Sem `--out`, o relatório é impresso em `stdout`. Entrada inválida retorna código
`2` e não substitui um relatório anterior.

## Leitura da triagem

| Disposição | Significado |
| --- | --- |
| `needs-annotation` | a referência é íntegra, mas ainda não possui gramática |
| `negative-control` | exemplo reservado para provar redundância ou limites |
| `redundant` | os bytes da prévia repetem uma referência anterior |
| `family-variant` | assinatura próxima de uma família atual |
| `new-composition` | assinatura adjacente com distância estrutural útil |
| `family-gap` | distância que merece crítica; não cria família automaticamente |

A pontuação de vizinhança usa 75% dos seis eixos, 15% da composição e 10% da
superfície. `family-variant` começa em `0.82`; `new-composition`, em `0.68`.
Abaixo disso, o relatório marca `family-gap`. Esses limiares organizam a revisão,
não medem qualidade nem autoria.

## Protocolo para o primeiro lote

1. Separe uma prévia completa por modelo, sem moldura do aplicativo ou recorte.
2. Registre autoria, licença e usos permitidos antes da análise visual.
3. Marque modelos deliberadamente repetidos como `negative-control`.
4. Rode o auditor mesmo sem `grammar`; ele valida o pacote e lista
   `needs-annotation`.
5. Anote a gramática dos itens íntegros e rode o comando novamente.
6. Revise primeiro duplicatas e estruturas recoloridas; depois variantes,
   composições adjacentes e lacunas.
7. Só depois da crítica transforme uma seleção em `TemplatePackage`, com slots,
   avaliações e paridade de saída próprias.

Os três JSON Schemas públicos estão em `schemas/template-corpus-manifest.schema.json`,
`schemas/template-reference.schema.json` e
`schemas/template-corpus-report.schema.json`.
