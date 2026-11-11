/**
 * API contracts. Hand-written to mirror the FastAPI schemas for now;
 * replaced by types generated from /api/v1/openapi.json in S1 (`pnpm gen:api`).
 */

export type SslMode = "disable" | "prefer" | "require" | "verify-full";

export interface Capabilities {
  read: boolean;
  write: boolean;
  cdc: boolean;
  parallel_read: boolean;
  native_checksum: boolean;
}

export interface ConnectorInfo {
  engine: string;
  display_name: string;
  default_port: number;
  capabilities: Capabilities;
}

export interface Connection {
  id: string;
  name: string;
  engine: string;
  host: string;
  port: number;
  database: string;
  username: string;
  secret_ref: string;
  ssl_mode: SslMode;
  created_at: string;
}

export interface ConnectionCreate {
  name: string;
  engine: string;
  host: string;
  port: number;
  database: string;
  username: string;
  secret_ref: string;
  ssl_mode?: SslMode;
}

export interface Page<T> {
  items: T[];
  total: number;
}

export interface ApiErrorBody {
  error: { code: string; message: string; details: Record<string, unknown> };
  request_id: string | null;
}
