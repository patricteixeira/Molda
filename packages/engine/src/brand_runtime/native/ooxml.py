"""Validação defensiva e goldens canônicos de pacotes OOXML."""

from __future__ import annotations

import hashlib
import json
import posixpath
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

from lxml import etree

Severity = Literal["info", "warning", "error"]
_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_PRESENTATION_REL = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
)
_MAX_ENTRIES = 4_000
_MAX_UNCOMPRESSED_BYTES = 256 * 1024 * 1024
_BLOCKED_SUFFIXES = {".exe", ".dll", ".com", ".bat", ".cmd", ".js", ".vbs"}
_VOLATILE_PARTS = {"docProps/core.xml"}


@dataclass(frozen=True, slots=True)
class NativeDiagnostic:
    """Finding estrutural sem acoplar o core a um editor específico."""

    code: str
    severity: Severity
    message: str
    part: str | None = None

    @property
    def blocking(self) -> bool:
        """Erros impedem publicação; warnings preservam o arquivo para diagnóstico."""
        return self.severity == "error"


@dataclass(frozen=True, slots=True)
class OoxmlManifest:
    """Snapshot canônico de partes relevantes, independente do metadata do ZIP."""

    package_type: Literal["pptx", "docx"]
    part_hashes: dict[str, str]

    def to_json(self) -> str:
        """Serializa de forma estável para uso em golden tests."""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


class OoxmlError(ValueError):
    """Pacote ausente, ilegível ou incompatível com a operação solicitada."""


def _package_type(path: Path) -> Literal["pptx", "docx"]:
    suffix = path.suffix.lower()
    if suffix == ".pptx":
        return "pptx"
    if suffix == ".docx":
        return "docx"
    raise OoxmlError("Use um arquivo .pptx ou .docx sem macros.")


def _safe_part_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    return (
        bool(normalized)
        and not normalized.startswith("/")
        and not path.is_absolute()
        and ".." not in path.parts
        and ":" not in path.parts[0]
        and posixpath.normpath(normalized) == normalized.rstrip("/")
    )


def _xml_parser() -> etree.XMLParser:
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        remove_blank_text=True,
        recover=False,
        huge_tree=False,
    )


def _canonical_part(name: str, payload: bytes) -> bytes:
    if name.endswith((".xml", ".rels")):
        root = etree.fromstring(payload, parser=_xml_parser())
        return etree.tostring(root, method="c14n2", with_comments=False)
    return payload


def _required_parts(package_type: Literal["pptx", "docx"]) -> set[str]:
    common = {"[Content_Types].xml", "_rels/.rels"}
    if package_type == "pptx":
        return common | {"ppt/presentation.xml", "ppt/_rels/presentation.xml.rels"}
    return common | {"word/document.xml", "word/styles.xml"}


def validate_ooxml(path: Path) -> list[NativeDiagnostic]:
    """Valida segurança básica, XML e relações estruturais sem modificar o arquivo."""
    package_type = _package_type(path)
    if not path.is_file():
        raise OoxmlError(f"O arquivo «{path}» não foi encontrado.")

    diagnostics: list[NativeDiagnostic] = []
    try:
        with zipfile.ZipFile(path) as package:
            infos = package.infolist()
            names = {info.filename for info in infos}
            if len(infos) > _MAX_ENTRIES:
                diagnostics.append(
                    NativeDiagnostic(
                        "ooxml.too_many_parts",
                        "error",
                        f"O pacote contém {len(infos)} partes; o limite é {_MAX_ENTRIES}.",
                    )
                )
            total_size = sum(info.file_size for info in infos)
            if total_size > _MAX_UNCOMPRESSED_BYTES:
                diagnostics.append(
                    NativeDiagnostic(
                        "ooxml.uncompressed_too_large",
                        "error",
                        "O tamanho descompactado excede o limite de segurança.",
                    )
                )

            for info in infos:
                name = info.filename
                if not _safe_part_name(name):
                    diagnostics.append(
                        NativeDiagnostic(
                            "ooxml.unsafe_part_name",
                            "error",
                            "O pacote contém um nome de parte inseguro.",
                            name,
                        )
                    )
                lower = name.lower()
                if (
                    PurePosixPath(lower).suffix in _BLOCKED_SUFFIXES
                    or "vbaproject" in lower
                    or "/embeddings/" in f"/{lower}"
                ):
                    diagnostics.append(
                        NativeDiagnostic(
                            "ooxml.active_content",
                            "error",
                            "Macros, executáveis e objetos incorporados não são aceitos no P0.",
                            name,
                        )
                    )

            for required in sorted(_required_parts(package_type) - names):
                diagnostics.append(
                    NativeDiagnostic(
                        "ooxml.required_part_missing",
                        "error",
                        "Uma parte obrigatória do pacote não foi encontrada.",
                        required,
                    )
                )

            for name in sorted(names):
                if not name.endswith((".xml", ".rels")):
                    continue
                try:
                    root = etree.fromstring(package.read(name), parser=_xml_parser())
                except (etree.XMLSyntaxError, ValueError) as error:
                    diagnostics.append(
                        NativeDiagnostic(
                            "ooxml.invalid_xml",
                            "error",
                            f"XML inválido: {error}.",
                            name,
                        )
                    )
                    continue
                if name.endswith(".rels"):
                    for relation in root.findall(f"{{{_REL_NS}}}Relationship"):
                        if relation.get("TargetMode") == "External":
                            diagnostics.append(
                                NativeDiagnostic(
                                    "ooxml.external_relationship",
                                    "error",
                                    "Relações externas não são aceitas no P0.",
                                    name,
                                )
                            )

            if package_type == "pptx":
                slide_names = sorted(
                    name
                    for name in names
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                )
                layout_names = {
                    name
                    for name in names
                    if name.startswith("ppt/slideLayouts/slideLayout") and name.endswith(".xml")
                }
                master_names = {
                    name
                    for name in names
                    if name.startswith("ppt/slideMasters/slideMaster") and name.endswith(".xml")
                }
                if not layout_names or not master_names:
                    diagnostics.append(
                        NativeDiagnostic(
                            "pptx.template_structure_missing",
                            "error",
                            "A apresentação precisa preservar ao menos um master e um layout.",
                        )
                    )
                for slide_name in slide_names:
                    rels_name = f"ppt/slides/_rels/{PurePosixPath(slide_name).name}.rels"
                    if rels_name not in names:
                        diagnostics.append(
                            NativeDiagnostic(
                                "pptx.slide_relationships_missing",
                                "error",
                                "O slide não possui arquivo de relações.",
                                slide_name,
                            )
                        )
                        continue
                    root = etree.fromstring(package.read(rels_name), parser=_xml_parser())
                    has_layout = any(
                        relation.get("Type") == _PRESENTATION_REL
                        for relation in root.findall(f"{{{_REL_NS}}}Relationship")
                    )
                    if not has_layout:
                        diagnostics.append(
                            NativeDiagnostic(
                                "pptx.slide_layout_missing",
                                "error",
                                "O slide não referencia um layout nativo.",
                                slide_name,
                            )
                        )
    except (zipfile.BadZipFile, OSError) as error:
        raise OoxmlError("Não foi possível abrir o pacote OOXML.") from error
    return diagnostics


def canonical_ooxml_manifest(
    path: Path,
    *,
    include_volatile: bool = False,
) -> OoxmlManifest:
    """Produz hashes de XML C14N e binários para regressão estrutural."""
    package_type = _package_type(path)
    if not path.is_file():
        raise OoxmlError(f"O arquivo «{path}» não foi encontrado.")
    try:
        with zipfile.ZipFile(path) as package:
            hashes: dict[str, str] = {}
            for name in sorted(package.namelist()):
                if name.endswith("/") or (not include_volatile and name in _VOLATILE_PARTS):
                    continue
                payload = _canonical_part(name, package.read(name))
                hashes[name] = hashlib.sha256(payload).hexdigest()
    except (zipfile.BadZipFile, OSError, etree.XMLSyntaxError) as error:
        raise OoxmlError("Não foi possível canonicalizar o pacote OOXML.") from error
    return OoxmlManifest(package_type=package_type, part_hashes=hashes)
