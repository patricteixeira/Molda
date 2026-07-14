# Plano M3.2 — linter de round-trip

**Objetivo:** comparar um Document Graph editado com o grafo exato do artefato
exportado e, quando disponível, com o Brand IR autoritativo.

## Decisões

- objetos são correlacionados por slide + slot, não por shape id ou nome que o
  editor externo pode reescrever;
- texto alterado é informativo; fonte, cor, tamanho e geometria alterados pedem
  revisão; remoção, troca de papel/revisão e quantidade de slides bloqueiam;
- o Brand IR eleva fonte, cor ou tamanho fora do papel semântico a erro;
- todo finding preserva esperado, atual e `fixable`; nenhum fix ocorre no linter;
- relatório e schema usam versão `0.1.0` e ordem determinística.

## Fixture real

Baseline: `docs/validation/2026-07-14-m3-proof-baseline-document-graph.json`.

Editado: `docs/validation/2026-07-14-m3-google-slides-document-graph.json`.

Relatório: `docs/validation/2026-07-14-m3-google-slides-roundtrip-report.json`.

O resultado esperado é `review`: duas mudanças de texto (`info`), a cor do
heading e a geometria do logo (`warning`, corrigíveis), sem erro ou locked.

## Próximo contrato

M3.3 consumirá apenas findings `fixable`, produzirá um Fix Plan separado e
aplicará as operações em uma cópia identificada por novo SHA-256.
