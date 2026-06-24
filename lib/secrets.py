"""
ff-secrets integration client.

Resolves an opaque secret reference (e.g. ffsec:hootsuite.slack) to its value,
without the caller knowing which secret backend sits behind it.
"""

import subprocess
import logging


class SecretsClient:
    """Resolves secret references through the ff-secrets CLI."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def resolve(self, ref: str) -> str:
        """
        Resolve a secret reference to its value.

        Args:
            ref: An opaque secret reference (e.g. ffsec:hootsuite.slack)

        Returns:
            The secret value as a string

        Raises:
            RuntimeError: If resolution fails or yields an empty value
        """
        try:
            result = subprocess.run(
                ["ff-secrets", "inject"],
                input=ref,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout while resolving secret via ff-secrets")
        except FileNotFoundError:
            raise RuntimeError("ff-secrets not found in PATH")

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise RuntimeError(f"Failed to resolve secret via ff-secrets: {error_msg}")

        secret = result.stdout.strip()
        if not secret:
            raise RuntimeError("Resolved empty secret via ff-secrets")
        return secret
