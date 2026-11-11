"""Driftless connectors.

``sdk`` holds the contracts every connector implements; each sub-package
(``postgres``, ``mysql``, ...) is one engine.
"""

from driftless_connectors.sdk import (
    Capabilities,
    ConnectionConfig,
    Connector,
    TypeMapper,
    registry,
)

# Importing the built-in engines registers them with ``registry``.
from driftless_connectors import mysql, postgres  # isort: skip

__all__ = [
    "Capabilities",
    "ConnectionConfig",
    "Connector",
    "TypeMapper",
    "mysql",
    "postgres",
    "registry",
]
