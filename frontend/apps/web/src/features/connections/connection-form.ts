import type { ConnectionCheck, ConnectionCreate, ConnectionSpec, SslMode } from "@driftless/api-client";
import type { CheckItem } from "@driftless/ui";

export interface ConnectionFormValues {
  name: string;
  engine: string;
  host: string;
  port: string;
  database: string;
  username: string;
  secretRef: string;
  sslMode: SslMode;
}

export type FormErrors = Partial<Record<keyof ConnectionFormValues, string>>;

export const DEFAULT_PORTS: Record<string, number> = {
  postgres: 5432,
  mysql: 3306,
  sqlserver: 1433,
  oracle: 1521,
};

export function emptyForm(engine = "postgres"): ConnectionFormValues {
  return {
    name: "",
    engine,
    host: "",
    port: String(DEFAULT_PORTS[engine] ?? ""),
    database: "",
    username: "",
    secretRef: "",
    sslMode: "prefer",
  };
}

const SECRET_REF = /^[a-z][a-z0-9+-]*:\S.*$/;

/** Mirrors the API's validation so users see problems before submitting. */
export function validate(values: ConnectionFormValues, { requireName = true } = {}): FormErrors {
  const errors: FormErrors = {};
  if (requireName && !values.name.trim()) errors.name = "Give the connection a name";
  if (!values.host.trim()) errors.host = "Host is required";
  const port = Number(values.port);
  if (!Number.isInteger(port) || port < 1 || port > 65535) errors.port = "Port must be 1–65535";
  if (!values.database.trim()) errors.database = "Database is required";
  if (!values.username.trim()) errors.username = "Username is required";
  if (!values.secretRef.trim()) {
    errors.secretRef = "Point to where the password is stored, e.g. vault:db/billing-ro";
  } else if (!SECRET_REF.test(values.secretRef.trim())) {
    errors.secretRef = "Use a reference like vault:path or env:VAR — never the password itself";
  }
  return errors;
}

export function toSpec(values: ConnectionFormValues): ConnectionSpec {
  return {
    engine: values.engine,
    host: values.host.trim(),
    port: Number(values.port),
    database: values.database.trim(),
    username: values.username.trim(),
    secret_ref: values.secretRef.trim(),
    ssl_mode: values.sslMode,
  };
}

export function toCreate(values: ConnectionFormValues): ConnectionCreate {
  return { ...toSpec(values), name: values.name.trim() };
}

const SCHEME_ENGINE: Record<string, string> = {
  postgres: "postgres",
  postgresql: "postgres",
  mysql: "mysql",
  sqlserver: "sqlserver",
  mssql: "sqlserver",
  oracle: "oracle",
};

/**
 * Fill the form from a pasted URL like ``postgresql://user@host:5432/db?sslmode=require``.
 * Any password in the URL is deliberately ignored — credentials go through secret refs.
 */
export function parseConnectionString(
  raw: string,
): { values: Partial<ConnectionFormValues>; droppedPassword: boolean } | null {
  let url: URL;
  try {
    url = new URL(raw.trim());
  } catch {
    return null;
  }
  const engine = SCHEME_ENGINE[url.protocol.replace(/:$/, "")];
  if (!engine) return null;
  const values: Partial<ConnectionFormValues> = {
    engine,
    host: decodeURIComponent(url.hostname),
    port: url.port || String(DEFAULT_PORTS[engine] ?? ""),
    database: decodeURIComponent(url.pathname.replace(/^\//, "")),
    username: decodeURIComponent(url.username),
  };
  const ssl = url.searchParams.get("sslmode");
  if (ssl === "disable" || ssl === "prefer" || ssl === "require" || ssl === "verify-full") {
    values.sslMode = ssl;
  }
  return { values, droppedPassword: url.password !== "" };
}

export function toCheckItems(checks: ConnectionCheck[]): CheckItem[] {
  return checks.map((c) => ({
    name: c.name,
    status: c.status,
    detail: c.detail ?? null,
    fixScript: c.fix_script ?? null,
  }));
}
