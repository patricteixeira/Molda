# ADR 0011 — Arquétipos de composição selecionados por evidência

**Status:** aceito (14/07/2026)

## Contexto

A prova do M1 com três marcas reais revelou que cor, fonte e logo ainda podiam
produzir os mesmos dez layouts canônicos. Digital Artisan já publicava uma
gramática editorial completa; Fofo's Massage Therapy e VitaCannMed terminavam
com geometrias idênticas, apesar de seus manuais prescreverem relações próprias.

Fofo's declara o lótus como ornamento divisor e um filete dourado com ponto ou
lótus central. VitaCannMed declara grade de 8 px, cantos arquitetônicos e
restritos e profundidade sugerida, nunca dramatizada. Esses fatos demonstraram
uma necessidade de schema; não são estilos inferidos da aparência das páginas.

## Decisão

- `compositionRules.layoutStyle` recebe um vocabulário fechado:
  `ornamental-divider` e `restrained-clinical-grid`.
- O extrator só seleciona um arquétipo quando encontra a prescrição textual
  completa correspondente. Menções incidentais a linha, grade ou ouro não
  bastam.
- Declarações concordantes acumulam evidência. Declarações conflitantes anulam
  a seleção em vez de escolher silenciosamente uma delas.
- Cada arquétipo acrescenta uma prova 4:5 ao kit. Retângulos, círculos, slots e
  tokens já pertencentes ao Layout Spec materializam a composição; nenhum CSS
  livre ou primitiva específica de marca foi adicionado.
- O renderer valida o novo campo com a mesma política `extra=forbid` do motor.
  A mudança semântica do gerador troca o domínio da revisão de `kit-v2` para
  `kit-v3`, impedindo que um bundle antigo reapareça sob o mesmo id.

## Consequências

Marcas sem declaração completa continuam recebendo apenas os dez layouts
canônicos. Marcas com evidência suficiente ganham uma prova autoral sem expor
coordenadas ao usuário. Novos arquétipos continuam exigindo vocabulário tipado,
extrator conservador, contrato compartilhado, testes e validação com material
real.
