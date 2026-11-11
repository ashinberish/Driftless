"""``driftless-api-openapi`` — print the OpenAPI document (used to generate the
frontend's typed client, and checked in CI so the two never drift)."""

from __future__ import annotations

import json
import sys

from driftless_api.main import create_app
from driftless_api.settings import ApiSettings


def main() -> None:
    app = create_app(ApiSettings(log_level="ERROR"))
    json.dump(app.openapi(), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
