# Validação de fechamento do M1 com três marcas reais

**Data:** 14/07/2026  
**Critério:** o kit deve ser distinguível de template genérico com pelo menos
três marcas reais, e todas as violações semeadas devem ser interceptadas pelo
Guard.

## Materiais

| Marca | Material exercitado | SHA-256 principal |
|---|---|---|
| Digital Artisan | manual PDF e duas variações SVG do símbolo | `93b5cde38cf37f79cfec52f5e35fdab5eb102fc9a3f35206cbffe6a563021e5b` |
| Fofo's Massage Therapy | manual PDF de 9 páginas e logo raster | `93e0464bfa22aa931901e070c3cb35f5200b050fab3b771551cfe8bdc51db09f` |
| VitaCannMed | design system de 7 páginas e logo PNG oficial | `fc97915b06979fddad650b51c9d9662d1a0b09d107b85883a7cc8ec8bc91a57c` |

Os arquivos de marca permaneceram fora do repositório. O anexo PDF original da
VitaCannMed deixou de estar disponível depois da renderização. A validação local
preservou as sete páginas como uma reconstrução visual
(`7cb832ac1c2a10bee163e7e44cb670c460f967afea13de489e3e135da5da3e93`)
e repôs a camada textual com transcrição literal das declarações visíveis. Essa
transcrição não adiciona decisões ausentes no guia.

## Resultado do intake e do kit

| Marca | Regras comprovadas | Kit | Prova distintiva |
|---|---|---:|---|
| Digital Artisan | modos claro/escuro, 60/30/10, acento, diagonal e numeração | 12 layouts | `editorial-light-post-4x5` e `editorial-dark-post-4x5` |
| Fofo's | divisor dourado com ponto ou lótus central | 11 layouts | `signature-ornamental-post-4x5` |
| VitaCannMed | grade clínica de 8 px com profundidade restrita | 11 layouts | `signature-clinical-post-4x5` |

As provas foram autorizadas pelo Guard e exportadas pelo renderer Chromium. Os
PNGs resultantes têm hashes distintos:

- Digital Artisan: `6364620994f70687f0d318caaee54ba984d50a869fdb6b353feec560d77dee69`;
- Fofo's: `f4eb5263e6a421fa2258d79d14d9024fadd1586bc2e60d57708428521401b3b1`;
- VitaCannMed: `6bbed8b8f88138473046148f5eebf92f1ee5bc8fe8c896d955b4a8735fa7f6be`.

A inspeção visual confirmou três estruturas, não apenas três recolorações: campo
diagonal numerado, eixo central ornamental e grade clínica assimétrica.

## Guard e regressão

Dezoito mutações começam em documentos válidos e exigem um bloqueio específico:
contrato de layout/revisão, slot desconhecido, tipo, obrigatoriedade, overflow,
destaque, referências, tamanho do logo, proporção de acento, contraste, arquivo
ausente ou corrompido, baixa resolução e SHA-256 divergente.

Verificações locais desta mudança:

- engine: Ruff format/check e `233 passed, 1 skipped`;
- renderer: Biome, TypeScript, build Vite e `71 passed`;
- app web: TypeScript, build Vite e `92 passed`;
- API: Ruff format/check passou; a suíte dependente de PostgreSQL não rodou
  localmente porque o Docker daemon não estava disponível.

## Limites registrados

Fofo's e VitaCannMed não forneceram binários das famílias confirmadas no pacote
de validação. O Brand IR registra essas fontes como `referenced-only`, e o
renderer sinaliza fallback; não há substituição silenciosa. A prova fecha o
critério de composição do M1, mas um pacote instalável de produção ainda deve
entregar ou resolver as fontes com licença e integridade registradas.
