"""Connector registry.

Built-in connectors register with ``@registry.register``; external packages expose a
``driftless.connectors`` entry point and are picked up by :meth:`load_plugins`.
"""

from __future__ import annotations

from importlib.metadata import entry_points

from driftless_connectors.sdk.base import Connector
from driftless_connectors.sdk.models import ConnectionConfig
from driftless_core.errors import NotFoundError

ENTRY_POINT_GROUP = "driftless.connectors"


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, type[Connector]] = {}

    def register[C: type[Connector]](self, cls: C) -> C:
        """Class decorator: ``@registry.register``."""
        existing = self._connectors.get(cls.engine)
        if existing is not None and existing is not cls:
            raise ValueError(f"engine {cls.engine!r} is already registered by {existing!r}")
        self._connectors[cls.engine] = cls
        return cls

    def get(self, engine: str) -> type[Connector]:
        try:
            return self._connectors[engine]
        except KeyError:
            raise NotFoundError(
                f"no connector for engine {engine!r}",
                details={"engine": engine, "available": self.engines()},
            ) from None

    def create(self, config: ConnectionConfig) -> Connector:
        return self.get(config.engine)(config)

    def engines(self) -> list[str]:
        return sorted(self._connectors)

    def all(self) -> list[type[Connector]]:
        return [self._connectors[e] for e in self.engines()]

    def load_plugins(self) -> None:
        for ep in entry_points(group=ENTRY_POINT_GROUP):
            cls = ep.load()
            if not (isinstance(cls, type) and issubclass(cls, Connector)):
                raise TypeError(f"entry point {ep.name!r} is not a Connector subclass")
            self.register(cls)


registry = ConnectorRegistry()
