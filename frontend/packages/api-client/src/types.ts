/**
 * API contracts, derived from the backend's OpenAPI document.
 *
 * Do not hand-edit shapes here: change the FastAPI schema, then run `make api-types`
 * (regenerates openapi.json and src/generated/schema.ts). CI fails if they drift.
 */
import type { components } from "./generated/schema";

type Schemas = components["schemas"];

export type Capabilities = Schemas["Capabilities"];
export type ConnectorInfo = Schemas["ConnectorInfo"];
export type SslMode = Schemas["SslMode"];
export type Connection = Schemas["Connection"];
export type ConnectionCreate = Schemas["ConnectionCreate"];
export type ConnectionSpec = Schemas["ConnectionSpec"];
export type ConnectionCheck = Schemas["ConnectionCheck"];
export type CheckStatus = Schemas["CheckStatus"];
export type ConnectionTestResult = Schemas["ConnectionTestResult"];
export type CatalogSummary = Schemas["CatalogSummary"];
export type TableSummary = Schemas["TableSummary"];

export interface Page<T> {
  items: T[];
  total: number;
}

/** Error envelope produced by the API's error handler (not part of OpenAPI yet). */
export interface ApiErrorBody {
  error: { code: string; message: string; details: Record<string, unknown> };
  request_id: string | null;
}
