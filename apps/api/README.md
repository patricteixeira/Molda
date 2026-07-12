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
| `BRANDRT_MAX_UPLOAD_BYTES` | Opcional; padrão `104857600` (100 MiB). |
| `BRANDRT_MAX_IMAGE_PIXELS` | Opcional; padrão `40000000`. |

O entry point `brand-api` referencia `brand_api.cli`, criado junto da app factory.
