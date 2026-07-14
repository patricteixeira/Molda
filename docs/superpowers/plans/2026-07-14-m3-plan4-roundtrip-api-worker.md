# Plano M3.4 — round-trip na API e no worker

**Objetivo:** receber o PPTX editado sem confiar em paths do cliente, executar o
pipeline do M3 sob o lease transacional existente e persistir diagnóstico e
correção como jobs consultáveis.

## Contrato HTTP

- `POST /v1/jobs/{export_job_id}/roundtrips` aceita somente um PPTX íntegro e um
  job de export PPTX já concluído;
- os bytes editados entram no storage content-addressed e o job
  `roundtrip-lint` persiste baseline graph, Document Graph editado, relatório e
  Fix Plan;
- `POST /v1/jobs/{roundtrip_job_id}/fixes` não recebe operações do cliente: cria
  um job `roundtrip-fix` a partir do plano validado e persistido pelo servidor;
- a cópia corrigida volta ao mesmo storage com SHA-256, URL, filename e
  `FixResult` completo;
- uploads inválidos, jobs ausentes/incompatíveis e planos vazios falham antes de
  criar trabalho assíncrono.

## Worker e segurança

- os dois blobs são lidos por SHA-256 e materializados apenas no workdir isolado
  da tentativa;
- parser, linter e fixer rodam dentro do lease e confirmam posse antes de
  persistir ou publicar;
- jobs recuperados por outro worker não podem sobrescrever o resultado atual;
- o worker publica somente `out.pptx` regular e contido, ignora qualquer path
  externo e sempre remove o workdir;
- placeholders de texto vazios não geram falsos findings de tipografia ou cor.

## Aceite automatizado

O teste integrado exporta um PPTX nativo, simula renomeação e edição do Google
Slides, envia o arquivo, processa os dois jobs, baixa a cópia corrigida, valida o
OOXML e confirma que o texto editado e o blob-fonte permaneceram intactos.

## Próximo contrato

M3.5 adicionará upload, polling, relatório explicável e ação de correção ao
editor web, usando exatamente esses dois endpoints e o resultado persistido.
