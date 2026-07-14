"""Adapter offline de referência: DTCG + logo para Brand Package 0.1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from brand_runtime_adapter import __version__
from brand_runtime_adapter.builder import (
    AdapterBuildError,
    AdapterIdentity,
    BrandPackageBuilder,
    BuiltPackage,
    SourceIdentity,
)


def _validate_tokens(path: Path) -> None:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 10 * 2**20:
            raise AdapterBuildError("Informe um arquivo DTCG regular de até 10 MiB.")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except AdapterBuildError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AdapterBuildError("O arquivo DTCG não contém JSON UTF-8 válido.") from exc
    if not isinstance(payload, dict):
        raise AdapterBuildError("A raiz do arquivo DTCG precisa ser um objeto JSON.")


def build_dtcg_package(
    tokens: Path,
    logo: Path,
    out_dir: Path,
    *,
    label: str | None = None,
) -> BuiltPackage:
    """Empacota tokens e logo sem egress, credencial ou dependência do core."""
    tokens = Path(tokens)
    logo = Path(logo)
    _validate_tokens(tokens)
    suffix = logo.suffix.casefold()
    if suffix not in {".svg", ".png"}:
        raise AdapterBuildError("O logo do adapter DTCG precisa ser SVG ou PNG.")
    media_type = "image/svg+xml" if suffix == ".svg" else "image/png"
    builder = BrandPackageBuilder(
        AdapterIdentity(
            id="org.brandruntime.dtcg",
            name="Brand Runtime DTCG Adapter",
            version=__version__,
        ),
        SourceIdentity(kind="dtcg", label=label),
    )
    builder.add_file(tokens, "tokens.json", role="tokens", media_type="application/json")
    builder.add_file(
        logo,
        f"assets/logos/logo{suffix}",
        role="logo",
        media_type=media_type,
    )
    return builder.build(out_dir)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brandrt-adapter-dtcg",
        description="Produz um Brand Package 0.1 a partir de tokens DTCG e logo.",
    )
    parser.add_argument("tokens", type=Path, help="Arquivo JSON no formato DTCG.")
    parser.add_argument("--logo", required=True, type=Path, help="Logo SVG ou PNG.")
    parser.add_argument("--out", required=True, type=Path, help="Novo diretório do pacote.")
    parser.add_argument("--label", help="Descrição não sensível da origem.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Executa o adapter e imprime um recibo pequeno em JSON."""
    args = _parser().parse_args(argv)
    try:
        result = build_dtcg_package(args.tokens, args.logo, args.out, label=args.label)
    except AdapterBuildError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "packageDir": str(result.package_dir),
                "fileCount": result.file_count,
                "totalBytes": result.total_bytes,
                "packageSha256": result.package_sha256,
            },
            ensure_ascii=False,
        )
    )
    return 0


def cli() -> None:
    """Entry point instalado do adapter de referência."""
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
