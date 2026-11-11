"""``driftless-api-migrate`` — apply metadata-DB migrations.

Runs as a Helm pre-install/pre-upgrade Job in production and via ``make db-upgrade``
locally. The API itself never migrates on startup (multiple replicas would race).
"""

from __future__ import annotations

import argparse
import logging

from alembic import command
from alembic.config import Config

from driftless_api.settings import get_settings

SCRIPT_LOCATION = "driftless_api:migrations"


def alembic_config(database_url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", SCRIPT_LOCATION)
    # ConfigParser interpolation: escape '%' in passwords.
    cfg.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return cfg


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    up = sub.add_parser("upgrade", help="upgrade to a revision (default: head)")
    up.add_argument("revision", nargs="?", default="head")
    down = sub.add_parser("downgrade", help="downgrade to a revision")
    down.add_argument("revision")
    sub.add_parser("current", help="show the current revision")
    rev = sub.add_parser("revision", help="autogenerate a new revision (developers)")
    rev.add_argument("-m", "--message", required=True)
    args = parser.parse_args(argv)

    # Alembic logs through stdlib logging; show progress in container logs.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    url = get_settings().database_url
    if not url:
        parser.error("DRIFTLESS_DATABASE_URL is not set")
    cfg = alembic_config(url)
    match args.cmd:
        case "upgrade":
            command.upgrade(cfg, args.revision)
        case "downgrade":
            command.downgrade(cfg, args.revision)
        case "current":
            command.current(cfg, verbose=True)
        case "revision":
            command.revision(cfg, message=args.message, autogenerate=True)
        case _:  # pragma: no cover - argparse enforces choices
            parser.error(f"unknown command {args.cmd}")
