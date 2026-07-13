# ADR 0009 — Fontshare como prévia externa consentida

**Status:** aceito (13/07/2026)

## Contexto

Manuais reais declaram famílias como Clash Display e General Sans. O intake
identifica corretamente esses nomes, mas elas não pertencem ao Google Fonts e
seus arquivos não podem ser deduzidos nem redistribuídos apenas porque aparecem
embutidos em um PDF. Os subsets do documento também são incompletos e a ITF
Free Font License proíbe sua extração, inclusive parcial.

O Fontshare oferece uma API CSS oficial que entrega a fonte diretamente de seus
servidores. Isso permite uma prévia fiel sem transformar o backend em servidor
de arquivos licenciados. A licença, porém, não autoriza o sistema a tratar esse
recurso externo como binário local redistribuível.

## Decisão

- Um snapshot administrativo contém somente nome, slug, tipo de licença e
  identidade das variantes das 100 famílias do catálogo oficial. Não contém
  binários nem URLs CDN.
- O intake consulta primeiro arquivo do pacote e Google Fonts. Para uma variante
  estática ITF FFL exata, registra `provider="fontshare-external"`, a URL CSS
  oficial allowlisted e `usagePolicy="restricted"`.
- O navegador não carrega o CSS automaticamente. A pessoa permite a conexão
  externa para a etapa, é informada sobre os dados técnicos expostos ao
  provedor e recebe um link para a
  [ITF FFL](https://www.fontshare.com/licenses/itf-ffl).
- A URL vinda do draft é revalidada no frontend: HTTPS, host
  `api.fontshare.com`, path `/v2/css`, uma variante `slug@código` e
  `display=swap`. Parâmetros ou origens adicionais são recusados.
- “Prévia oficial carregada” só aparece quando `document.fonts.load()` devolve
  ao menos uma face em estado `loaded` e `document.fonts.check()` confirma a
  família. Falha de rede é mostrada como indisponibilidade, nunca mascarada por
  fallback.
- O backend não baixa, proxifica, armazena ou publica a resposta Fontshare.
  Export PNG/PDF continua sem incorporar o arquivo restrito.
- A entrada manual de nome passa pelo mesmo catálogo e persiste no draft, mas
  nome não encontrado permanece apenas uma referência explícita.
- A rota manual limita cada draft a oito novas escolhas e quatro fontes
  materializadas, publica somente novos blobs e não relê o pacote original em
  uma repetição idempotente.

## Consequências

O leigo consegue confirmar visualmente Clash Display, General Sans e outras
famílias suportadas sem procurar arquivos. A prévia depende da rede e do
provedor, por isso não possui a reprodução offline do caminho Google Fonts.
Artefatos finais ainda precisam de um arquivo/licença compatível ou de uma
política de renderização autorizada; essa limitação é comunicada em vez de
ocultada.

Para uso SaaS multi-tenant e eventual renderização no servidor, permanece
necessária confirmação jurídica por escrito da ITF. A própria ITF descreve a
[API e o kit offline do Fontshare](https://www.indiantypefoundry.com/news/introducing-fontshare),
mas isso não substitui os limites contratuais da FFL.
