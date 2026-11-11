"""Driftless control-plane API.

Layout: ``platform/`` holds cross-cutting HTTP concerns (errors, middleware);
``modules/<feature>/`` holds one vertical slice each (router -> service -> repository).
"""

__version__ = "0.1.0"
