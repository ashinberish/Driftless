"""Secret references.

Driftless never stores database passwords. A connection holds a *reference* such as
``vault:db/billing-ro`` or ``env:BILLING_DB_PASSWORD``; the reference is resolved at the
moment a connection is opened, by whichever component runs the work (API for
pre-flight checks, agents for data movement).

Resolvers are pluggable per scheme so customers can add their own backend
(AWS Secrets Manager, Azure Key Vault, CyberArk...) without touching callers.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from pydantic import SecretStr

from driftless_core.errors import ConfigurationError, DriftlessError

_REF_RE = re.compile(r"^(?P<scheme>[a-z][a-z0-9+-]*):(?P<path>\S.*)$")


class SecretNotFoundError(DriftlessError):
    code = "secret_not_found"


@dataclass(frozen=True, slots=True)
class SecretRef:
    scheme: str
    path: str

    @classmethod
    def parse(cls, reference: str) -> SecretRef:
        match = _REF_RE.match(reference.strip())
        if match is None:
            raise ValueError(f"not a secret reference: expected 'scheme:path', got {reference!r}")
        return cls(scheme=match["scheme"], path=match["path"])

    def __str__(self) -> str:
        return f"{self.scheme}:{self.path}"


@runtime_checkable
class SecretResolver(Protocol):
    scheme: str

    async def resolve(self, path: str) -> SecretStr: ...


class EnvSecretResolver:
    """``env:NAME`` — reads an environment variable. Intended for local dev and CI."""

    scheme = "env"

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = environ if environ is not None else os.environ

    async def resolve(self, path: str) -> SecretStr:
        try:
            return SecretStr(self._environ[path])
        except KeyError:
            raise SecretNotFoundError(
                f"environment variable {path!r} is not set", details={"reference": f"env:{path}"}
            ) from None


class SecretResolverRegistry:
    def __init__(self, resolvers: list[SecretResolver] | None = None) -> None:
        self._resolvers: dict[str, SecretResolver] = {}
        for resolver in resolvers or []:
            self.register(resolver)

    def register(self, resolver: SecretResolver) -> None:
        self._resolvers[resolver.scheme] = resolver

    @property
    def schemes(self) -> list[str]:
        return sorted(self._resolvers)

    def supports(self, reference: str) -> bool:
        try:
            return SecretRef.parse(reference).scheme in self._resolvers
        except ValueError:
            return False

    async def resolve(self, reference: str) -> SecretStr:
        ref = SecretRef.parse(reference)
        resolver = self._resolvers.get(ref.scheme)
        if resolver is None:
            raise ConfigurationError(
                f"no secret backend configured for scheme {ref.scheme!r}",
                details={"reference": str(ref), "available": self.schemes},
            )
        return await resolver.resolve(ref.path)
