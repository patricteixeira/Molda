# API do brand-runtime

API HTTP do walking skeleton para intake, revisões, documentos e exports.

## Desenvolvimento

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/pip install -e ../../packages/engine
.venv/Scripts/pip install -e ".[dev]"
.venv/Scripts/pip freeze --exclude-editable  # materializar esta saída no requirements-lock.txt

# Postgres de dev/teste (porta 5433) — requer Docker Desktop:
docker compose -f compose.dev.yml up -d
# alternativa sem compose:
#   docker run --name brandrt-pg -e POSTGRES_USER=brandrt -e POSTGRES_PASSWORD=brandrt \
#     -e POSTGRES_DB=brandrt -p 127.0.0.1:5433:5432 -d postgres:16-alpine

.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

Se as tabelas conhecidas divergirem entre branches, reinicie também o volume de desenvolvimento:

```bash
docker compose -f compose.dev.yml down -v
docker compose -f compose.dev.yml up -d
```

## Variáveis de ambiente

| Variável | Obrigatoriedade e padrão |
| --- | --- |
| `BRANDRT_DATABASE_URL` | Obrigatória em runtime; sem padrão. |
| `BRANDRT_DATA_DIR` | Opcional; padrão `./var`. |
| `BRANDRT_BOOTSTRAP_TOKEN` | Opcional; semeia um token de convite durante a subida. |
| `BRANDRT_TEST_DATABASE_URL` | Somente testes; padrão `postgresql+psycopg://brandrt:brandrt@127.0.0.1:5433/brandrt`. |
| `BRANDRT_FAKE_EXPORTER` | Opcional; ativa o exporter de desenvolvimento/teste com `1` ou `true`. |
| `BRANDRT_RENDER_DIST` | Opcional na API; build do renderer exigido pelo worker real. |
| `BRANDRT_FONT_FETCH_BASE_URL` | Opcional; endpoint interno e restrito para aquisição do catálogo fixado. Ausente desativa a aquisição automática. |
| `BRANDRT_MAX_UPLOAD_BYTES` | Opcional; padrão `104857600` (100 MiB). |
| `BRANDRT_MAX_IMAGE_PIXELS` | Opcional; padrão `40000000`. |

O entry point `brand-api` referencia `brand_api.cli`, criado junto da app factory.

## Rodando a API

Com o ambiente instalado e o Postgres de desenvolvimento ativo, configure o servidor e o
worker em PowerShell:

```powershell
$env:BRANDRT_DATABASE_URL = "postgresql+psycopg://brandrt:brandrt@127.0.0.1:5433/brandrt"
$env:BRANDRT_BOOTSTRAP_TOKEN = "dev-token"
$env:BRANDRT_FAKE_EXPORTER = "1"
.venv/Scripts/brand-api serve
```

A API estará disponível em `http://127.0.0.1:8000`. Em outro terminal, com as mesmas
variáveis de ambiente, execute o consumidor da fila:

```powershell
.venv/Scripts/brand-api worker
```

Para processar no máximo um item e encerrar, use `brand-api worker --once`. O exporter fake
é destinado apenas ao desenvolvimento e aos testes: ele prova o fluxo sem iniciar Chromium.

## Export real (Plano 2)

Instale a dependência opcional, o Chromium e produza o build do renderer:

```powershell
.venv/Scripts/pip install -e "../../packages/engine[export]"
.venv/Scripts/python -m playwright install chromium
Push-Location ../../packages/render
npm ci
npm run build
Pop-Location
```

Remova `BRANDRT_FAKE_EXPORTER` e aponte o worker para o diretório que contém
`render.html`:

```powershell
Remove-Item Env:BRANDRT_FAKE_EXPORTER -ErrorAction SilentlyContinue
$env:BRANDRT_RENDER_DIST = (Resolve-Path ../../packages/render/dist)
.venv/Scripts/brand-api worker
```

O processo HTTP não importa Playwright nem exige `BRANDRT_RENDER_DIST`; somente o worker
real valida e inicializa esse adapter.

## Export nativo (M2.1)

O mesmo endpoint assíncrono aceita quatro formatos. A matriz é fechada:

| Formato | Perfis aceitos |
| --- | --- |
| `png` | todos os perfis |
| `pdf` | `doc-a4` |
| `pptx` | `post-1x1`, `post-4x5`, `story-9x16` |
| `docx` | `doc-a4` |

Jobs PPTX/DOCX persistem `nativeTemplateVersion: "v1"`. O worker seleciona o
template do mesmo aspect ratio, deriva o tema pelo Brand IR, preenche os slots e
valida o pacote OOXML antes de publicar. O resultado do job inclui `format` e
`filename`, além de `sha256` e `url`.

Os quatro templates são recursos do pacote em
`src/brand_api/native_templates/v1`. Para reconstruí-los ou verificar que os
binários versionados correspondem ao builder:

```powershell
python ../../tools/build_native_templates.py
python ../../tools/build_native_templates.py --check
```

## Resolução automática de fontes abertas

No Docker Compose da raiz, `BRANDRT_FONT_FETCH_BASE_URL` já aponta para o proxy
interno `font-fetch`. A API continua sem acesso direto à internet: o proxy só
alcança o commit do repositório Google Fonts registrado na ADR 0008.

O fluxo é não bloqueante. Correspondência exata declarada no manual ou em DTCG
é baixada, validada, recebe licença e cobertura e entra no draft como arquivo
local. Falha de rede mantém o candidato apenas referenciado e acrescenta um
diagnóstico; nunca inventa uma substituição. Não há Google API key para
configurar ou armazenar.

O catálogo é atualizado administrativamente, fora do runtime. Execute a partir
da raiz do repositório:

```powershell
python -m pip install -r tools/requirements-font-catalog.txt
python tools/sync_google_fonts_catalog.py `
  --checkout C:\caminho\google-fonts `
  --revision <sha-completo> `
  --output apps/api/src/brand_api/fonts/google-fonts.catalog.json
```

Famílias ITF FFL do Fontshare usam outro modo de entrega. A API mantém apenas
um snapshot reduzido de metadados (família, slug, licença e variantes), nunca
bytes ou URLs CDN. O draft recebe uma referência `fontshare-external` e o app
web, após permissão explícita para a conexão externa, carrega o CSS diretamente
de `api.fontshare.com`. Essa permissão não é
registrada como aceite jurídico da ITF FFL 1.0. A API e o worker continuam sem
egress para esse provedor.

Para atualizar administrativamente o catálogo de metadados:

```powershell
python tools/sync_fontshare_catalog.py
```

O wizard também aceita um nome digitado em
`POST /v1/drafts/{draft_id}/fonts/resolve`. A rota reutiliza a variante já
declarada quando possível, tenta o resolvedor de fonte aberta e, por último,
escolhe a variante catalogada mais próxima do peso do papel e registra uma
referência Fontshare exata quando aplicável. Nome não encontrado continua como
escolha explícita, sem inventar arquivo ou família substituta. Cada draft aceita
até oito novas escolhas manuais e quatro fontes adquiridas localmente; após o
teto local, a escolha continua registrável sem novo download e Fontshare segue
disponível como prévia externa quando houver variante exata.

## Fluxo completo (curl)

O exemplo abaixo pressupõe um pacote `marca.zip`, a API e o worker já ativos. Todas as
requisições sob `/v1` carregam o convite no header; o token nunca vai na URL.

```powershell
$base = "http://127.0.0.1:8000"
$auth = "Authorization: Bearer dev-token"

# 1. Importar pacote e receber as perguntas do wizard.
$import = curl.exe -sS -X POST "$base/v1/brands/imports" `
  -H $auth -F "package=@marca.zip;type=application/zip" | ConvertFrom-Json

# 2. Confirmar as escolhas e compilar uma revisão imutável.
function First-Candidate([string] $id) {
  (($import.questions | Where-Object id -eq $id).candidates)[0].value
}
$answers = @{
  values = @{
    "color.primary" = $(First-Candidate "color.primary")
    "color.background" = "#FFFFFF"
    "color.text" = "#1A1A1A"
    "font.heading" = $(First-Candidate "font.heading")
    "font.body" = $(First-Candidate "font.body")
    "logo.primary" = $(First-Candidate "logo.primary")
  }
}
$compileBody = @{ answers = $answers; brandName = "ACME" } | ConvertTo-Json -Depth 8
$compiled = curl.exe -sS -X POST "$base/v1/drafts/$($import.draftId)/compile" `
  -H $auth -H "Content-Type: application/json" -d $compileBody | ConvertFrom-Json

# 3. Consultar o kit persistido.
$kit = curl.exe -sS "$base/v1/brand-revisions/$($compiled.brandRevisionId)/kit" `
  -H $auth | ConvertFrom-Json

# 4. Criar um documento; os checks estáticos voltam na mesma resposta.
$documentBody = @{
  layoutId = "statement-post-1x1"
  brandRevisionId = $compiled.brandRevisionId
  values = @{ headline = @{ kind = "text"; text = "Lançamento em agosto" } }
} | ConvertTo-Json -Depth 8
$document = curl.exe -sS -X POST "$base/v1/documents" `
  -H $auth -H "Content-Type: application/json" -d $documentBody | ConvertFrom-Json

# 5. Reexecutar o Guard e enfileirar o export.
$job = curl.exe -sS -X POST "$base/v1/documents/$($document.documentId)/exports" `
  -H $auth -H "Content-Type: application/json" -d '{"format":"png"}' `
  | ConvertFrom-Json

# 6. Consultar até status=succeeded ou failed.
do {
  $status = curl.exe -sS "$base/v1/jobs/$($job.jobId)" -H $auth | ConvertFrom-Json
  if ($status.status -in @("queued", "running")) { Start-Sleep -Seconds 1 }
} while ($status.status -in @("queued", "running"))
$status
if ($status.status -eq "failed") { throw $status.error }

# 7. Quando concluído, baixar o blob content-addressed.
curl.exe -sS "$base$($status.result.url)" -H $auth -o export.png
```

Um `409` no passo 5 inclui `detail` e `checks` na raiz da resposta: corrija o documento
antes de criar outro job. Um job que falha durante a medição mantém os checks do renderer
em `GET /v1/jobs/{id}` e nunca publica um blob de resultado.
