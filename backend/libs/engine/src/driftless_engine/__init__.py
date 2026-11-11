"""Driftless migration engine.

Pure, connector-agnostic logic organised by migration stage:

* ``assess``   - inspect a catalog and produce findings
* ``convert``  - translate a canonical schema to a target engine's DDL
* ``copy``     - plan chunked, resumable bulk copies
* ``validate`` - compare source and target using normalized checksums
"""

__version__ = "0.1.0"
