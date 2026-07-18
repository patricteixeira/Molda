# ADR 0012 — Campanhas como fonte compartilhada de conteúdo

## Status

Aceita em 2026-07-18.

## Contexto

Editar uma peça por vez obriga pessoas sem formação em design a repetir a mesma
decisão em post, story, apresentação e documento. Essa repetição gera versões
divergentes, aumenta o custo de revisão e enfraquece o valor recorrente do
Molda.

Os `LayoutSpec` já descrevem slots semânticos e os `Document` já preservam uma
instância de conteúdo validada pelo Guard. Faltava uma entidade que declarasse
qual mensagem alimenta várias instâncias e propagasse uma mudança como uma
única operação.

## Decisão

Uma `Campaign` é a fonte canônica de cinco campos: título, mensagem, data,
chamada para ação e imagem. Cada `CampaignPiece` liga a campanha a um layout e
a um `Document` estável. O binding persistido de cada slot usa um vocabulário
fechado (`headline`, `body`, `body-meta`, `meta`, `all` ou `image`).

A criação materializa todas as peças numa única transação. Uma atualização:

1. valida a imagem no storage content-addressed;
2. reinterpreta os bindings já persistidos;
3. atualiza o conteúdo dos mesmos documentos;
4. reexecuta o Guard por layout;
5. confirma tudo num único commit.

Não existe atualização parcial de uma peça pelo endpoint de campanha. Os IDs de
documento permanecem estáveis, permitindo que jobs e histórico continuem
referenciando a mesma peça. Findings do Guard são expostos; conteúdo nunca é
truncado ou reescrito silenciosamente.

## Consequências

- uma única edição mantém os formatos sincronizados;
- exportações continuam usando o pipeline e os contratos de documentos já
  existentes;
- layouts com poucos slots combinam mensagem e metadados de forma explícita;
- os formatos de uma campanha publicada permanecem fixos neste corte para não
  introduzir remoções destrutivas sem histórico;
- evolução futura pode versionar bindings e oferecer adição/arquivamento de
  peças sem alterar o contrato atual.

## Alternativas rejeitadas

- **Estado apenas no navegador:** não sobreviveria a outro dispositivo nem a
  trabalho em equipe.
- **Copiar e colar entre editores:** mantém a divergência que a feature precisa
  eliminar.
- **Templates livres por string:** ampliariam a superfície de erro e esconderiam
  regras de propagação. O vocabulário fechado é auditável.
