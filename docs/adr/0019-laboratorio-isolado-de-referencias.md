# ADR 0019 — Laboratório isolado de referências de templates

- Status: aceito
- Data: 2026-07-23
- Decisores: produto e engenharia do Molda

## Contexto

O catálogo publicado possui treze famílias e contratos executáveis de slots,
qualidade e exportação. Um novo conjunto de cerca de trinta templates autorais
pode ampliar o repertório, mas importar esses arquivos diretamente misturaria
referência visual, fonte executável e composição pronta para produção.

Uma semelhança superficial também não prova diversidade. Mudanças de cor, texto
ou imagem podem esconder a mesma estrutura. No extremo oposto, toda diferença
não deve virar uma família nova: isso aumentaria o catálogo sem ampliar sua
capacidade expressiva.

## Decisão

Criar o `Template Corpus 0.1` como domínio irmão, e não extensão, de
`TemplatePackage`.

Cada referência conserva:

- autoria, licença e política de uso;
- uma prévia raster obrigatória;
- perfis e propósitos;
- arquivos-fonte declarados, tratados somente como bytes;
- uma gramática humana opcional com seis eixos, composição, superfície,
  hierarquia, alinhamento, papéis de slot e espaço negativo.

O auditor trabalha offline e de forma determinística. Ele valida inventário e
hashes, rejeita paths inseguros e imagens patológicas, calcula uma impressão
visual em tons de cinza e compara a gramática com as assinaturas usadas pelo
recomendador atual.

O relatório pode classificar uma referência como anotação pendente, controle
negativo, redundante, variante de família, nova composição ou lacuna de família.
Toda saída declara `promotionPolicy: manual-review-required`. Nenhuma classe
promove, gera ou altera um `TemplatePackage`.

## Consequências

- O material autoral pode chegar antes da modelagem final sem contaminar o
  catálogo executável.
- HTML, CSS e PPTX são preservados para inspeção posterior, mas não entram numa
  superfície de execução do motor.
- Recolorações estruturalmente próximas aparecem como suspeita de redundância,
  não como prova matemática de cópia.
- A gramática continua sendo uma leitura crítica humana; o auditor não inventa
  intenção a partir de pixels.
- Uma lacuna precisa de revisão comparativa, slots, avaliações e prova de saída
  antes de justificar nova família.
- O corpus não é endpoint da API, não é importado pelo wizard e não faz parte do
  pacote self-hosted de produção neste corte.

## Alternativas rejeitadas

- **Importar as trinta referências no catálogo:** apagaria a fronteira entre
  inspiração e contrato executável.
- **Usar somente embeddings ou visão externa:** adicionaria rede, custo,
  opacidade e resultados não reproduzíveis ao gate de integridade.
- **Classificar apenas por nome e paleta:** não detectaria estruturas repetidas.
- **Criar uma família para cada template:** confundiria quantidade com repertório.
- **Promover automaticamente por pontuação:** transformaria uma heurística de
  triagem em decisão autoral.
