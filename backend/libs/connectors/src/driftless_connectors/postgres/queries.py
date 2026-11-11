"""Catalog queries for PostgreSQL. ``%(schemas)s`` is NULL for "all user schemas"."""

from typing import Final

_USER_SCHEMAS = """
    n.nspname NOT IN ('pg_catalog', 'information_schema')
    AND n.nspname NOT LIKE 'pg_toast%%'
    AND (%(schemas)s::text[] IS NULL OR n.nspname = ANY(%(schemas)s::text[]))
"""

WAL_LEVEL: Final = "SHOW wal_level"
SERVER_VERSION: Final = "SHOW server_version"

VISIBLE_TABLES: Final = """
SELECT count(*) FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
  AND table_schema NOT IN ('pg_catalog', 'information_schema')
"""

COLUMNS = f"""
SELECT n.nspname, c.relname, a.attname,
       format_type(a.atttypid, a.atttypmod),
       a.attnotnull,
       pg_get_expr(d.adbin, d.adrelid),
       a.attidentity <> ''
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid AND c.relkind IN ('r', 'p')
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
WHERE a.attnum > 0 AND NOT a.attisdropped AND {_USER_SCHEMAS}
ORDER BY n.nspname, c.relname, a.attnum
"""  # noqa: S608 - static fragment, parameters are bound

PRIMARY_KEYS = f"""
SELECT n.nspname, c.relname, con.conname,
       array_agg(a.attname ORDER BY k.ord)
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
CROSS JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS k(attnum, ord)
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum
WHERE con.contype = 'p' AND {_USER_SCHEMAS}
GROUP BY n.nspname, c.relname, con.conname
"""  # noqa: S608

FOREIGN_KEYS = f"""
SELECT n.nspname, c.relname, con.conname,
       array_agg(a.attname ORDER BY k.ord),
       rn.nspname, rc.relname,
       array_agg(ra.attname ORDER BY k.ord)
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_class rc ON rc.oid = con.confrelid
JOIN pg_namespace rn ON rn.oid = rc.relnamespace
CROSS JOIN LATERAL unnest(con.conkey, con.confkey) WITH ORDINALITY AS k(attnum, refnum, ord)
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum
JOIN pg_attribute ra ON ra.attrelid = rc.oid AND ra.attnum = k.refnum
WHERE con.contype = 'f' AND {_USER_SCHEMAS}
GROUP BY n.nspname, c.relname, con.conname, rn.nspname, rc.relname
"""  # noqa: S608

TABLE_STATS = f"""
SELECT n.nspname, c.relname,
       GREATEST(c.reltuples, 0)::bigint,
       pg_total_relation_size(c.oid)
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'p') AND {_USER_SCHEMAS}
"""  # noqa: S608
