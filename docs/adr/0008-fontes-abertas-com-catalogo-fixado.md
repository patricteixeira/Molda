# ADR 0008 — Fontes abertas por catálogo fixado e aquisição isolada

**Status:** aceito (13/07/2026)

## Contexto

O intake já reconhecia famílias citadas no manual, mas só conseguia renderizar
a tipografia real quando o instalador entregava TTF/OTF no pacote. Isso
transferia ao usuário leigo a tarefa de localizar, baixar e importar uma fonte.

Usar diretamente CSS/CDN durante preview e export resolveria a descoberta, mas
quebraria a reprodução offline e a igualdade entre tela e arquivo. Baixar uma
fonte apenas porque ela é gratuita também é incorreto: licenças abertas e
licenças gratuitas restritas permitem usos diferentes.

## Decisão

- O intake possui um `FontResolver` de provedores. Uma fonte adquirida continua
  entrando no Brand IR como `source="file"`; catálogo nunca é fonte de render.
- O primeiro provedor é um snapshot completo do repositório oficial
  [`google/fonts`](https://github.com/google/fonts), fixado no commit
  `ec0464b978de222073645d6d3366f3fdf03376d8`.
- O catálogo contém família, variantes, eixos, paths, licença, hashes dos
  metadados/licença e o OID Git de cada binário. Atualizá-lo é uma operação
  administrativa explícita, produzida por
  `tools/sync_google_fonts_catalog.py` e revisada por diff.
- O binário necessário é baixado durante o intake que o solicita, conferido
  byte a byte contra o objeto da árvore fixada, validado com `fontTools`,
  testado contra o perfil de cobertura `pt-BR-ui-v1` e armazenado no CAS por
  SHA-256 junto com sua licença.
- Preview e export usam exclusivamente os bytes locais da revisão. Atualização
  upstream nunca altera uma revisão existente.
- O Brand IR 0.2 registra `FontResource`: provedor, formato, referência upstream,
  licença, política de uso, cobertura e eixos variáveis.
- Somente intenção declarada em DTCG ou em seção tipográfica reconhecida do
  manual é resolvida automaticamente. Fonte apenas observada/embutida no PDF
  permanece evidência até confirmação.

## Limite de segurança

A API e o worker continuam sem acesso direto à internet. Um proxy interno
`font-fetch` é o único processo com egress e possui upstream imutável para
`raw.githubusercontent.com/google/fonts/<commit>`. Ele não aceita host, URL ou
credencial vindos do documento. Redirects, resposta grande, binário inválido,
variante divergente, cobertura incompleta e licença ausente falham fechados.

O fluxo não usa Google API key. Portanto nenhuma chave tipográfica existe no
navegador, no Brand IR, no Compose ou no repositório público.

O `gitBlobOid` usa SHA-1 porque esse é o algoritmo do repositório upstream e do
próprio commit que ancora o snapshot. Ele garante igualdade com o objeto da
árvore; o CAS local usa SHA-256. Registrar também SHA-256 upstream para todos os
binários é um hardening futuro, não uma dependência do runtime.

## Política por licença

- OFL, Apache e Ubuntu Font License presentes no catálogo: aquisição local
  permitida, sempre preservando o texto individual da licença.
- Fonte comercial ou licença desconhecida: arquivo licenciado ou biblioteca
  privada; nenhuma substituição silenciosa.
- ITF Free Font License do Fontshare: não re-hospedar automaticamente. Famílias
  como Clash Display e General Sans exigem um caminho específico compatível com
  a licença antes de entrarem como recurso local.

## Consequências

O leigo não baixa fontes abertas suportadas. A aquisição durante o intake
depende do upstream fixado; indisponibilidade não invalida o fluxo, que continua com
`FONT_FILE_MISSING` e um diagnóstico acionável. O catálogo adiciona cerca de
1,8 MiB ao pacote da API, evitando chaves, enumeração remota e mudanças
silenciosas.
