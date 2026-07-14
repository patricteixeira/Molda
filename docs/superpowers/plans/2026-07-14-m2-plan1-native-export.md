# Plano M2.1 — export nativo pela API e worker

**Objetivo:** transformar os spikes OOXML do Gate 0 em um corte de produto
executável pelo mesmo contrato assíncrono já usado por PNG e PDF.

## Contrato fechado

- `pptx` é aceito para `post-1x1`, `post-4x5` e `story-9x16`;
- `docx` é aceito somente para `doc-a4`;
- o job persiste `nativeTemplateVersion`, além de `format`;
- cada perfil social usa um template PPTX com o mesmo aspect ratio do canvas;
- os templates são recursos versionados e imutáveis do pacote da API;
- o worker deriva uma cópia tematizada por Brand IR e nunca sobrescreve a fonte;
- o arquivo só é publicado no storage após Guard estático e validação OOXML.

## Implementação

1. Registro explícito `v1` para três templates PPTX e um DOCX.
2. Builder determinístico dos recursos binários, com comando de verificação.
3. `NativeOfficeExporter` para `derive theme -> template-fill -> validate`.
4. Dispatcher único do worker para PNG/PDF e PPTX/DOCX.
5. API com matriz de formato/perfil e MIME real no download por SHA-256.
6. Testes unitários do registro e dos adapters, mais fluxo API -> job -> worker ->
   storage para ambos os formatos nativos.

## Aceite

- PPTX e DOCX baixados pela API são pacotes OOXML válidos e editáveis;
- PPTX preserva master/layout e o aspect ratio do perfil solicitado;
- DOCX preserva estilos semânticos e placeholders integralmente preenchidos;
- o job registra a versão exata do template usado;
- templates-fonte permanecem byte a byte inalterados;
- PNG/PDF e as garantias transacionais do worker não regridem.

## Limite consciente

O Gate 0 continua condicionado até o round-trip obrigatório no PowerPoint
desktop. Este corte habilita o produto e a automação sem ampliar essa promessa.
