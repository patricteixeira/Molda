"""Linter explicável para documentos editados fora do brand-runtime."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from brand_runtime.ir.models import BrandIR, CamelModel
from brand_runtime.roundtrip.models import BoundsPt, DocumentGraph, DocumentNode

Severity = Literal["info", "warning", "error", "locked"]


class RoundtripFinding(CamelModel):
    """Mudança ou violação reencontrada, sem alterar o documento."""

    code: str
    severity: Severity
    message_pt: str
    node_id: str | None = None
    slot_id: str | None = None
    expected: Any = None
    actual: Any = None
    fixable: bool = False


class RoundtripSummary(CamelModel):
    """Contagens estáveis para API e interface web."""

    status: Literal["pass", "review", "blocked"]
    total: int = Field(ge=0)
    info: int = Field(ge=0)
    warning: int = Field(ge=0)
    error: int = Field(ge=0)
    locked: int = Field(ge=0)
    fixable: int = Field(ge=0)


class RoundtripReport(CamelModel):
    """Relatório determinístico consumido pelos futuros fixer e web app."""

    schema_version: Literal["0.1.0"] = "0.1.0"
    baseline_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    edited_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    summary: RoundtripSummary
    findings: list[RoundtripFinding]


def _key(node: DocumentNode) -> tuple[int, str]:
    return node.slide_index, node.slot_id or f"role:{node.role}"


def _finding(
    code: str,
    severity: Severity,
    message: str,
    *,
    node: DocumentNode | None = None,
    expected: Any = None,
    actual: Any = None,
    fixable: bool = False,
) -> RoundtripFinding:
    return RoundtripFinding(
        code=code,
        severity=severity,
        message_pt=message,
        node_id=node.id if node else None,
        slot_id=node.slot_id if node else None,
        expected=expected,
        actual=actual,
        fixable=fixable,
    )


def _bounds_changed(before: BoundsPt, after: BoundsPt, tolerance_pt: float = 0.05) -> bool:
    return any(
        abs(getattr(before, field) - getattr(after, field)) > tolerance_pt
        for field in ("x", "y", "width", "height")
    )


def _brand_findings(
    node: DocumentNode,
    baseline_node: DocumentNode,
    ir: BrandIR,
) -> list[RoundtripFinding]:
    if (
        node.kind != "text"
        or node.role not in ir.roles
        or node.text is None
        or not node.text.strip()
    ):
        return []
    role = ir.roles[node.role]
    expected_font = ir.fonts[role.font].family
    expected_color = ir.colors[role.color].value
    minimum_pt = role.min_size_px * 0.75
    maximum_pt = role.max_size_px * 0.75
    findings: list[RoundtripFinding] = []
    if node.font_family != expected_font and node.font_family != baseline_node.font_family:
        findings.append(
            _finding(
                "brand-font",
                "warning",
                "A fonte saiu do papel semântico previsto pela marca.",
                node=node,
                expected=expected_font,
                actual=node.font_family,
                fixable=True,
            )
        )
    if node.color != expected_color and node.color != baseline_node.color:
        findings.append(
            _finding(
                "brand-color",
                "warning",
                "A cor saiu do token previsto para este papel.",
                node=node,
                expected=expected_color,
                actual=node.color,
                fixable=True,
            )
        )
    outside_recommended_range = (
        node.font_size_pt is None or not minimum_pt <= node.font_size_pt <= maximum_pt
    )
    if outside_recommended_range and node.font_size_pt != baseline_node.font_size_pt:
        findings.append(
            _finding(
                "brand-font-size",
                "warning",
                "O tamanho saiu da faixa recomendada para este papel.",
                node=node,
                expected={"minimumPt": minimum_pt, "maximumPt": maximum_pt},
                actual=node.font_size_pt,
                fixable=True,
            )
        )
    return findings


def _summary(findings: list[RoundtripFinding]) -> RoundtripSummary:
    counts = {
        severity: sum(item.severity == severity for item in findings)
        for severity in ("info", "warning", "error", "locked")
    }
    status = "blocked" if counts["error"] or counts["locked"] else "review" if findings else "pass"
    return RoundtripSummary(
        status=status,
        total=len(findings),
        fixable=sum(item.fixable for item in findings),
        **counts,
    )


def lint_roundtrip(
    baseline: DocumentGraph,
    edited: DocumentGraph,
    ir: BrandIR | None = None,
) -> RoundtripReport:
    """Compara pelo slot e, quando disponível, aplica a autoridade do Brand IR."""
    expected_nodes = {_key(node): node for node in baseline.nodes}
    actual_nodes = {_key(node): node for node in edited.nodes}
    findings: list[RoundtripFinding] = []

    if baseline.source.slide_count != edited.source.slide_count:
        findings.append(
            _finding(
                "slide-count",
                "locked",
                "A quantidade de slides foi alterada.",
                expected=baseline.source.slide_count,
                actual=edited.source.slide_count,
            )
        )

    for key, expected in expected_nodes.items():
        actual = actual_nodes.get(key)
        if actual is None:
            findings.append(
                _finding(
                    "missing-node",
                    "locked",
                    f"O objeto obrigatório «{expected.slot_id or expected.role}» foi removido.",
                    expected=expected.role,
                )
            )
            continue
        if actual.role != expected.role or actual.kind != expected.kind:
            findings.append(
                _finding(
                    "semantic-contract",
                    "locked",
                    "O tipo ou papel semântico do objeto foi alterado.",
                    node=actual,
                    expected={"role": expected.role, "kind": expected.kind},
                    actual={"role": actual.role, "kind": actual.kind},
                )
            )
        if actual.brand_revision_id != expected.brand_revision_id:
            findings.append(
                _finding(
                    "brand-revision",
                    "locked",
                    "O objeto pertence a outra revisão da marca.",
                    node=actual,
                    expected=expected.brand_revision_id,
                    actual=actual.brand_revision_id,
                )
            )
        for attribute, code, label, severity, fixable in (
            ("text", "text-changed", "texto", "info", False),
            ("font_family", "font-changed", "fonte", "warning", True),
            ("font_size_pt", "font-size-changed", "tamanho da fonte", "warning", True),
            ("color", "color-changed", "cor", "warning", True),
        ):
            before = getattr(expected, attribute)
            after = getattr(actual, attribute)
            if before != after:
                findings.append(
                    _finding(
                        code,
                        severity,
                        f"A edição externa alterou {label}.",
                        node=actual,
                        expected=before,
                        actual=after,
                        fixable=fixable,
                    )
                )
        if _bounds_changed(expected.bounds_pt, actual.bounds_pt):
            findings.append(
                _finding(
                    "geometry-changed",
                    "warning",
                    "A edição externa alterou posição ou tamanho.",
                    node=actual,
                    expected=expected.bounds_pt,
                    actual=actual.bounds_pt,
                    fixable=True,
                )
            )
        if ir is not None:
            findings.extend(_brand_findings(actual, expected, ir))

    for key, actual in actual_nodes.items():
        if key not in expected_nodes:
            findings.append(
                _finding(
                    "unexpected-node",
                    "warning",
                    "Foi encontrado um objeto sem correspondente no arquivo original.",
                    node=actual,
                    actual={"role": actual.role, "kind": actual.kind},
                )
            )

    return RoundtripReport(
        baseline_sha256=baseline.source.sha256,
        edited_sha256=edited.source.sha256,
        summary=_summary(findings),
        findings=findings,
    )
