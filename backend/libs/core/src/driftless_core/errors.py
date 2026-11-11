"""Error hierarchy.

Every error carries a stable machine-readable ``code`` so the API, CLI and UI can map
it to a message and HTTP status without string matching.
"""

from __future__ import annotations

from typing import Any


class DriftlessError(Exception):
    code: str = "driftless_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


class ConfigurationError(DriftlessError):
    code = "configuration_error"


class NotFoundError(DriftlessError):
    code = "not_found"


class ConflictError(DriftlessError):
    code = "conflict"


class ConnectorError(DriftlessError):
    code = "connector_error"


class ConnectionFailedError(ConnectorError):
    code = "connection_failed"


class UnsupportedFeatureError(ConnectorError):
    """The engine (or engine pair) cannot represent the requested object or type."""

    code = "unsupported_feature"


class ValidationMismatchError(DriftlessError):
    """Source and target data differ."""

    code = "validation_mismatch"
