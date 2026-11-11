"""Temporal worker.

``workflows/`` must stay deterministic (no I/O, no clocks, no randomness); all side
effects live in ``activities/``, which call into ``driftless_engine`` and connectors.
"""
