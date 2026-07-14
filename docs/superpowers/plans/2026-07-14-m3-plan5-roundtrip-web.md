# Plano M3.5 — conferência de round-trip no editor web

**Objetivo:** fechar o caminho de produto do round-trip PPTX sem levar a
linguagem interna do motor para a pessoa que editou a peça.

## Experiência

- a conferência aparece somente depois de uma exportação PPTX concluída e fica
  vinculada ao job que originou o baseline;
- o usuário traz a cópia salva pelo Google Slides ou PowerPoint e acompanha
  upload, análise e correção pelo mesmo fluxo assíncrono dos exports;
- findings técnicos viram sinais legíveis como `Texto mantido`, `Tipografia`,
  `Cor`, `Posição e tamanho` e `Estrutura protegida`;
- valores internos, tokens, famílias, coordenadas e cores hexadecimais não são
  expostos na superfície leiga;
- correções seguras sempre produzem uma nova cópia para download. O arquivo
  enviado nunca é sobrescrito.

## Estados e segurança

- somente `.pptx` é aceito pelo seletor;
- slots e novas exportações ficam congelados durante upload, polling ou
  correção;
- jobs falhos e o limite de cinco minutos voltam como mensagem em português;
- a UI pede um Fix Plan apenas ao servidor e nunca envia operações escolhidas
  pelo navegador;
- trocar de arquivo limpa análise, correção e seleção anteriores.

## Aceite automatizado

O teste de fluxo exporta um PPTX, envia uma edição simulada, confirma que texto
alterado é preservado e que uma mudança de cor é apresentada sem hex, solicita
a correção pelo job persistido e valida o link da nova cópia. Testes do cliente
HTTP fixam as três rotas usadas pela interface.

## Gate humano remanescente

A prova automatizada cobre o contrato completo. A matriz externa ainda pede um
round-trip real no PowerPoint Desktop; como o ambiente atual usa Google Slides
web, essa comprovação permanece registrada como gate humano e não bloqueia
trabalho independente do M4.
