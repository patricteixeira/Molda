# brand-runtime-adapter-sdk

SDK Python mínimo, sem dependências e sob licença MIT, para autores de adapters
que produzem o contrato público `Brand Package 0.1`.

O SDK não importa nem executa o engine AGPL. Ele apenas publica uma árvore de
arquivos e seu manifesto de integridade. A validação canônica continua sendo:

```bash
brandrt package-validate ./meu-pacote
```

## Builder

```python
from pathlib import Path

from brand_runtime_adapter import (
    AdapterIdentity,
    BrandPackageBuilder,
    SourceIdentity,
)

builder = BrandPackageBuilder(
    AdapterIdentity(
        id="org.exemplo.tokens",
        name="Meu adapter",
        version="1.0.0",
    ),
    SourceIdentity(kind="tokens-studio", label="Export local"),
)
builder.add_file(
    Path("export/tokens.json"),
    "tokens.json",
    role="tokens",
    media_type="application/json",
)
result = builder.build(Path("out/minha-marca"))
print(result.package_sha256)
```

O destino precisa não existir. A publicação usa staging no mesmo volume e
swap atômico; uma falha não deixa pacote parcial. O builder recusa symlinks,
paths não portáveis, colisões por caixa, combinações inválidas de role/path/MIME
e arquivos ou conjuntos acima de 200 MiB.

## Adapter DTCG de referência

O pacote também instala uma implementação offline que recebe tokens DTCG e um
logo nativo:

```bash
brandrt-adapter-dtcg tokens.json --logo logo.svg \
  --label "Export do sistema de tokens" --out out/minha-marca
```

Ele não usa rede nem recebe credenciais. O objetivo é demonstrar uma integração
completa; lacunas de fonte ou manual permanecem explícitas no wizard.

## Desenvolvimento no monorepo

Com o venv do engine disponível, os contract tests cruzados podem ser executados
sem instalar dependências adicionais:

```powershell
$env:PYTHONPATH = "packages/adapter-sdk-python/src"
packages/engine/.venv/Scripts/python -m pytest packages/adapter-sdk-python/tests -q
packages/engine/.venv/Scripts/python -m ruff check packages/adapter-sdk-python
```
