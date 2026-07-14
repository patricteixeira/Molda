# Plano M4.1 — contrato portátil para adapters

**Objetivo:** abrir o ecossistema de importação sem carregar código comunitário
no core e sem depender já da API do Figma.

## Decisão

Adapters são processos externos que produzem um `Brand Package 0.1`. O pacote
usa a convenção de intake existente e acrescenta um manifesto integral com
identidade do adapter, origem não sensível, papéis, media types, tamanhos e
SHA-256. O engine valida a saída; a API nunca executa o adapter.

Essa fronteira é preferível como primeiro corte porque:

- serve ao futuro adapter Figma e a adapters em qualquer linguagem;
- preserva o modular monolith e o isolamento do core;
- não exige marketplace, sandbox de plugins ou distribuição de executáveis;
- permite contract tests públicos sob os schemas MIT;
- mantém pacotes informais existentes retrocompatíveis.

## Contratos

- `brand-package.schema.json`: manifesto público 0.1.0;
- `package-validation-report.schema.json`: recibo determinístico de
  conformidade;
- `brandrt package-validate`: verificação arquivo→arquivo para CI de adapters;
- `POST /v1/brands/imports`: valida o manifesto quando presente, antes de
  sanitização, storage ou banco.

## Aceite

- paths inseguros, colisões por caixa, symlinks e arquivos não declarados são
  recusados;
- tamanho e SHA-256 de todo arquivo são verificados;
- role, diretório, extensão e media type correspondem à convenção realmente
  consumida pelo intake;
- a mesma árvore em roots diferentes produz o mesmo `packageSha256`;
- um pacote declarado válido chega ao wizard; um hash adulterado não deixa
  draft, pacote nem blob;
- fixture pública e guia permitem a implementação sem ler código do app.

## Próximo recorte possível

O contrato permite um adapter DTCG/Style Dictionary de referência sem egress ou
um spike Figma quando houver acesso real à API. Instância pública multi-tenant,
biblioteca pública de kits e add-in PowerPoint continuam decisões separadas e
não devem ser acopladas a esta fronteira.
