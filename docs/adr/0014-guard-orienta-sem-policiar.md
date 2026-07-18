# ADR 0014 — O Guard orienta sem policiar criação

- Status: aceito
- Data: 2026-07-18
- Decisores: produto e engenharia do Molda
- Substitui: a política de bloqueio criativo descrita nos planos M1

## Contexto

O Molda existe para tornar um sistema de marca utilizável por pessoas que não
dominam design. Isso exige orientação clara, mas não transfere ao software a
autoria da peça. A versão anterior usava o mesmo estado `blocked` tanto para
preferências da identidade quanto para falhas técnicas. Como consequência, um
texto longo, contraste baixo ou uso incomum de uma cor podiam impedir uma
exportação tecnicamente possível.

Essa política confundia recomendação com permissão e fazia o produto parecer o
dono da marca do usuário.

## Decisão

O Molda orienta; o usuário decide.

1. Nomes e conteúdos autorais aceitam qualquer texto Unicode não vazio. O
   sistema não tenta decidir se um nome é bom, legível ou coerente.
2. A interface oferece prioritariamente componentes, tokens e layouts presentes
   no design system da marca.
3. Desvios de identidade são `warning`: ficam visíveis, explicam a consequência
   e oferecem uma ação de ajuste, mas nunca impedem salvar ou exportar.
4. `blocked` é reservado a operações que não conseguem produzir um artefato
   íntegro ou seguro.
5. O Molda nunca altera, trunca ou substitui silenciosamente uma decisão autoral.

### Matriz operacional

| Situação | Estado | Exportação |
| --- | --- | --- |
| Texto acima da recomendação ou com overflow | `warning` | permitida |
| Contraste baixo | `warning` | permitida |
| Cor de acento acima da proporção declarada | `warning` | permitida |
| Logo menor que o mínimo recomendado | `warning` | permitida |
| Imagem abaixo da resolução recomendada | `warning` | permitida |
| Campo editorial vazio ou destaque incomum | `warning` | permitida |
| Arquivo ausente, ilegível ou com hash divergente | `blocked` | recusada |
| Documento ligado a layout/revisão incompatível | `blocked` | recusada |
| Referência ou tipo que o renderer não consegue resolver | `blocked` | recusada |
| Upload malicioso ou pacote estruturalmente inválido | erro técnico | recusada |

## Experiência

O painel se chama **Orientações da marca** e declara explicitamente: “Você pode
ajustar estas escolhas ou exportar assim mesmo.” A ação sugerida leva ao campo
relevante, mas o botão de exportação continua disponível.

## Consequências

- O status do Guard passa a ser `pass | fixed | warning | blocked`.
- Exportadores e API interrompem somente `blocked`.
- Jobs preservam todas as orientações no verdict e no histórico.
- Layouts e componentes continuam limitados ao vocabulário compilado da marca;
  isso reduz erros sem controlar o conteúdo do usuário.
- Planos históricos que descrevem bloqueio por overflow, contraste, proporção ou
  resolução mínima devem ser lidos à luz deste ADR.
