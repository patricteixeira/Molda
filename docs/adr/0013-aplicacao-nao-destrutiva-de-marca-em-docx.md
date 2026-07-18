# ADR 0013 — Aplicação não destrutiva de marca em DOCX

## Status

Aceita em 2026-07-18.

## Contexto

O export DOCX do M2 cria um documento novo a partir de slots. Equipes também
possuem propostas, relatórios e documentos operacionais existentes que não
podem ser recriados do zero. Para uma pessoa leiga, “usar a marca no Word” deve
significar enviar o arquivo atual, entender as mudanças e receber outra cópia
editável — não operar XML, estilos ou templates.

## Decisão

O fluxo possui duas ações assíncronas separadas:

1. `docx-brand-analyze` valida OOXML e gera um `DocxBrandPlan` vinculado ao
   SHA-256 do arquivo e à revisão de marca;
2. `docx-brand-apply` aceita somente o plano persistido pelo primeiro job,
   reaplica as verificações e grava uma nova cópia.

O motor:

- reconhece títulos por estilos nativos do Word e por uma heurística limitada
  ao primeiro parágrafo curto sem estilo de título;
- cria os estilos editáveis `Molda Título` e `Molda Texto`;
- atualiza família, tamanho e cor sem remover negrito, itálico, links, listas ou
  conteúdo;
- uniformiza margens, respiros e tabelas;
- adiciona o logo apenas a cabeçalhos que ainda não possuem imagem;
- rasteriza no workdir logos SVG já sanitizados;
- salva atomicamente e valida o pacote OOXML resultante;
- compara um digest de todo o texto visível e exige que todas as mídias
  originais permaneçam no pacote.

O original nunca é sobrescrito. Relações externas, macros, embeddings,
executáveis, XML inválido, zip traversal e pacotes acima dos limites do P0 são
recusados pela validação OOXML existente.

## Consequências

- o resultado continua sendo um `.docx` editável no Word ou Google Docs;
- a interface consegue explicar o plano antes de criar qualquer cópia;
- a mesma operação está disponível na CLI e por JSON Schemas públicos;
- o corte preserva texto e mídia, mas não promete equivalência pixel a pixel
  para recursos não suportados pelo `python-docx`;
- documentos assinados digitalmente não são aceitos como fluxo de preservação
  de assinatura, pois qualquer mudança visual invalidaria a assinatura.

## Alternativas rejeitadas

- **Converter para PDF:** elimina a edição que torna o Word útil.
- **Substituir o documento por um template Molda:** perde estrutura e conteúdo
  do arquivo existente.
- **Aplicar sem plano:** impede consentimento informado e torna mudanças
  difíceis de auditar.
