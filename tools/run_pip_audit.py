"""Execute pip-audit with bounded retries for transient network failures."""

from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Callable, Sequence

MAX_ATTEMPTS = 3
RETRY_DELAYS_SECONDS = (5, 15)
TRANSIENT_NETWORK_MARKERS = (
    "connection aborted",
    "connection refused",
    "connection reset",
    "connectionerror",
    "connectionreseterror",
    "connecttimeout",
    "maxretryerror",
    "name or service not known",
    "network is unreachable",
    "protocolerror",
    "readtimeout",
    "remotedisconnected",
    "sslerror",
    "temporary failure in name resolution",
)


def is_transient_network_failure(output: str) -> bool:
    """Return whether pip-audit output represents a retryable network failure."""
    normalized_output = output.lower()
    return any(marker in normalized_output for marker in TRANSIENT_NETWORK_MARKERS)


def run_pip_audit(
    arguments: Sequence[str],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    sleeper: Callable[[float], None] = time.sleep,
) -> int:
    """Run pip-audit, retrying only failures identified as transient network errors."""
    command = [sys.executable, "-m", "pip_audit", *arguments]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = runner(command, capture_output=True, check=False, text=True)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)

        if result.returncode == 0:
            return 0

        output = f"{result.stdout}\n{result.stderr}"
        if not is_transient_network_failure(output):
            return result.returncode

        if attempt == MAX_ATTEMPTS:
            print(
                "pip-audit continuou indisponivel apos 3 falhas transitórias de rede.",
                file=sys.stderr,
            )
            return result.returncode

        retry_delay = RETRY_DELAYS_SECONDS[attempt - 1]
        print(
            "pip-audit encontrou uma falha transitória de rede "
            f"(tentativa {attempt}/{MAX_ATTEMPTS}); nova tentativa em {retry_delay}s.",
            file=sys.stderr,
        )
        sleeper(retry_delay)

    raise AssertionError("unreachable")


def main() -> int:
    """Forward command-line arguments to pip-audit."""
    if len(sys.argv) == 1:
        print("uso: run_pip_audit.py <argumentos do pip-audit>", file=sys.stderr)
        return 2
    return run_pip_audit(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
