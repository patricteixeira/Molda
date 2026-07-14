# Plano M3.1 — PPTX editado para Document Graph

**Objetivo:** iniciar o round-trip com um corte verificável: um PPTX editado no
Google Slides entra como arquivo imutável, passa pela validação OOXML e vira um
Document Graph versionado antes de qualquer decisão de conformidade.

## Fixture canônica

- `out/m2-gate0/proof-google-slides-edited.pptx`;
- SHA-256 `4e1f4a60f061dc47555e7a20b802cff665e2641abb99019ae57d0efeb0bc0225`;
- o arquivo é o mesmo binário preservado em `C:/Users/patri/Downloads/proof.pptx`;
- o parser nunca modifica nem regrava a fonte.

## Contrato fechado

- `Document Graph 0.1.0` registra identidade SHA-256, formato, tamanho e slides;
- cada node semântico registra slide, shape, role, slot, revisão, texto, estilo,
  cor e bounds em pontos;
- a origem da semântica é explícita: nome `br:*`, descrição preservada pelo
  editor ou tipo do placeholder como fallback;
- pacote com finding OOXML bloqueante não entra no grafo;
- arquivos sem nenhum objeto semântico são recusados, não interpretados por
  heurística silenciosa.

## Fora deste corte

- severidades de conformidade e comparação com Brand IR;
- fixer e geração de nova revisão;
- upload pela API e relatório no editor web;
- DOCX e adapter de editor embutido.

## Aceite

1. `brandrt roundtrip-parse editado.pptx --out document-graph.json` é
   determinístico para o mesmo arquivo.
2. A fixture real do Google Slides recupera heading, body e logo, incluindo as
   alterações de texto, fonte e cor já confirmadas pelo operador.
3. O schema público `document-graph.schema.json` valida a saída.
4. Os testes cobrem tags originais e descrições preservadas após renomeação do
   editor externo.
