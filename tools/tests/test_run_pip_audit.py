"""Tests for the pip-audit retry policy used by CI."""

from __future__ import annotations

import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import Mock

from tools.run_pip_audit import MAX_ATTEMPTS, run_pip_audit


def audit_result(
    returncode: int, *, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    """Build a completed process matching subprocess.run's text-mode result."""
    return subprocess.CompletedProcess(
        args=["python", "-m", "pip_audit"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class PipAuditRetryTests(unittest.TestCase):
    """Verify that retries are restricted to transient network failures."""

    def test_returns_immediately_after_success(self) -> None:
        """Do not retry a successful audit."""
        runner = Mock(return_value=audit_result(0, stdout="No known vulnerabilities found\n"))
        sleeper = Mock()

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            returncode = run_pip_audit(
                ["-r", "requirements-lock.txt"], runner=runner, sleeper=sleeper
            )

        self.assertEqual(returncode, 0)
        self.assertEqual(runner.call_count, 1)
        sleeper.assert_not_called()

    def test_does_not_retry_a_vulnerability_finding(self) -> None:
        """Preserve vulnerability findings as immediate CI failures."""
        runner = Mock(return_value=audit_result(1, stdout="Found 1 known vulnerability\n"))
        sleeper = Mock()

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            returncode = run_pip_audit(
                ["-r", "requirements-lock.txt"], runner=runner, sleeper=sleeper
            )

        self.assertEqual(returncode, 1)
        self.assertEqual(runner.call_count, 1)
        sleeper.assert_not_called()

    def test_retries_a_transient_network_failure_until_success(self) -> None:
        """Retry a recognized network failure and report later success."""
        runner = Mock(
            side_effect=[
                audit_result(
                    1, stderr="requests.exceptions.ConnectionError: connection reset by peer\n"
                ),
                audit_result(0, stdout="No known vulnerabilities found\n"),
            ]
        )
        sleeper = Mock()

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            returncode = run_pip_audit(
                ["-r", "requirements-lock.txt"], runner=runner, sleeper=sleeper
            )

        self.assertEqual(returncode, 0)
        self.assertEqual(runner.call_count, 2)
        sleeper.assert_called_once_with(5)

    def test_stops_after_the_bounded_number_of_network_attempts(self) -> None:
        """Stop after the configured retry budget is exhausted."""
        runner = Mock(
            return_value=audit_result(1, stderr="ConnectionResetError: connection reset by peer\n")
        )
        sleeper = Mock()

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            returncode = run_pip_audit(
                ["-r", "requirements-lock.txt"], runner=runner, sleeper=sleeper
            )

        self.assertEqual(returncode, 1)
        self.assertEqual(runner.call_count, MAX_ATTEMPTS)
        self.assertEqual([call.args[0] for call in sleeper.call_args_list], [5, 15])


if __name__ == "__main__":
    unittest.main()
