"""SDK MIT para autores de adapters do brand-runtime."""

from brand_runtime_adapter.builder import (
    AdapterBuildError,
    AdapterIdentity,
    BrandPackageBuilder,
    BuiltPackage,
    SourceIdentity,
)

__version__ = "0.1.0"

__all__ = [
    "AdapterBuildError",
    "AdapterIdentity",
    "BrandPackageBuilder",
    "BuiltPackage",
    "SourceIdentity",
]
