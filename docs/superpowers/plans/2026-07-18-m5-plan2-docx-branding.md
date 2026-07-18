# Plano M5.2 — Aplicar marca a um Word existente

**Objetivo:** receber qualquer DOCX seguro, explicar a transformação e devolver
uma nova cópia editável com a identidade da revisão escolhida.

## Contrato do motor

- `DocxBrandPlan 0.1.0` registra fonte, SHA-256, revisão, contagens, operações e
  alertas;
- `DocxBrandResult 0.1.0` registra hashes, operações e prova de preservação;
- análise nunca escreve no arquivo de origem;
- aplicação exige exatamente o SHA e a revisão do plano;
- saída é temporária até validação OOXML, digest textual e inventário de mídia;
- schemas são publicados sob licença MIT;
- CLI oferece `docx-brand-plan` e `docx-brand-apply`.

## Fila HTTP

| Método | Rota | Resultado |
| --- | --- | --- |
| `POST` | `/v1/brand-revisions/{id}/docx-brandings` | job de análise |
| `POST` | `/v1/jobs/{analysis_id}/docx-brandings` | job de aplicação |
| `GET` | `/v1/jobs/{id}` | plano ou download validado |

O segundo endpoint não aceita plano fornecido pelo cliente. O worker usa apenas
o artefato persistido pelo job de análise.

## Interface

1. selecionar `.docx`, com promessa explícita de original intocado;
2. conferir contagens, operações e alertas;
3. consentir com “Aplicar e criar cópia”;
4. baixar o Word com prova de conteúdo preservado.

## Segurança e recuperação

- MIME é reconhecido pelos parts OOXML, não pelo header do upload;
- limites de tamanho e validação de pacote antecedem a leitura semântica;
- relações externas, macros e embeddings são bloqueantes;
- blobs e workdirs são content-addressed, isolados por lease e limpos no final;
- job falho nunca publica download parcial;
- texto ou mídia original ausente cancela a aplicação.

## Aceite

- um DOCX com texto, tabela e cabeçalho retorna plano legível;
- a cópia contém estilos Molda e logo, preserva texto/tabela/cabeçalho e reabre;
- modificar os bytes depois da análise é recusado;
- upload inválido e chamadas sem autorização falham fechados;
- motor, API/worker e interface têm testes de ponta a ponta.
