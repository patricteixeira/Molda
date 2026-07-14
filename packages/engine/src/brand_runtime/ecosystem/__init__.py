"""Contratos portáteis do ecossistema de adapters."""

from brand_runtime.ecosystem.package import (
    MANIFEST_FILENAME,
    AdapterIdentity,
    BrandPackageFile,
    BrandPackageManifest,
    BrandPackageSource,
    PackageValidationError,
    PackageValidationReport,
    validate_brand_package,
)

__all__ = [
    "MANIFEST_FILENAME",
    "AdapterIdentity",
    "BrandPackageFile",
    "BrandPackageManifest",
    "BrandPackageSource",
    "PackageValidationError",
    "PackageValidationReport",
    "validate_brand_package",
]
