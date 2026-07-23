"""Testes do contrato estático de release."""

from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from tools.release_check import (
    ROOT,
    declared_versions,
    validate_release,
    validate_shell_portability,
)


class ReleaseCheckTests(unittest.TestCase):
    """Protege o corte público contra versões e documentação divergentes."""

    def test_current_release_contract_is_complete(self) -> None:
        """O checkout deve estar pronto para produzir os artefatos atuais."""
        versions = declared_versions(ROOT)
        current = versions["packages/engine/pyproject.toml"]
        self.assertEqual(validate_release(ROOT, current), [])

    def test_all_public_packages_share_the_release_version(self) -> None:
        """Componentes distribuídos juntos avançam sob uma versão única."""
        self.assertEqual(len(set(declared_versions(ROOT).values())), 1)

    def test_prerelease_string_is_rejected_by_the_stable_release_gate(self) -> None:
        """O workflow estável não publica tags RC por engano."""
        errors = validate_release(Path("missing"), "0.1.0-rc.1")
        self.assertIn("não é SemVer estável", errors[0])

    def test_shell_entrypoints_are_portable_across_windows_checkouts(self) -> None:
        """A regra Git e os bytes dos scripts devem preservar o shebang Linux."""
        self.assertEqual(validate_shell_portability(ROOT), [])

    def test_crlf_shell_entrypoint_is_rejected(self) -> None:
        """Um script convertido pelo autocrlf não pode atravessar o gate."""
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".gitattributes").write_bytes(b"*.sh text eol=lf\n")
            (root / "entrypoint.sh").write_bytes(b"#!/bin/sh\r\nexit 0\r\n")

            errors = validate_shell_portability(root)

        self.assertEqual(errors, ["entrypoint.sh contém CRLF; esperado LF."])


if __name__ == "__main__":
    unittest.main()
