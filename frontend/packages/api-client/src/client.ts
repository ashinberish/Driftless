import type {
  ApiErrorBody,
  CatalogSummary,
  Connection,
  ConnectionCreate,
  ConnectionSpec,
  ConnectionTestResult,
  ConnectorInfo,
  Page,
} from "./types";

/** Error thrown for non-2xx responses; carries the API's stable error code. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly details: Record<string, unknown> = {},
    readonly requestId: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface ClientOptions {
  baseUrl?: string;
  fetch?: typeof fetch;
  headers?: () => Record<string, string>;
}

export function createApiClient({ baseUrl = "/api/v1", fetch: fetchImpl = fetch, headers }: ClientOptions = {}) {
  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const res = await fetchImpl(`${baseUrl}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...headers?.(),
        ...init.headers,
      },
    });
    if (!res.ok) {
      const body = (await res.json().catch(() => null)) as ApiErrorBody | null;
      throw new ApiError(
        res.status,
        body?.error.code ?? "http_error",
        body?.error.message ?? res.statusText,
        body?.error.details ?? {},
        body?.request_id ?? res.headers.get("X-Request-ID"),
      );
    }
    return (res.status === 204 ? undefined : await res.json()) as T;
  }

  return {
    connectors: {
      list: () => request<ConnectorInfo[]>("/connectors"),
    },
    connections: {
      list: () => request<Page<Connection>>("/connections"),
      get: (id: string) => request<Connection>(`/connections/${encodeURIComponent(id)}`),
      create: (body: ConnectionCreate) =>
        request<Connection>("/connections", { method: "POST", body: JSON.stringify(body) }),
      remove: (id: string) =>
        request<void>(`/connections/${encodeURIComponent(id)}`, { method: "DELETE" }),
      /** Pre-flight checks for settings that are not saved yet. */
      testSpec: (body: ConnectionSpec) =>
        request<ConnectionTestResult>("/connections/test", {
          method: "POST",
          body: JSON.stringify(body),
        }),
      test: (id: string) =>
        request<ConnectionTestResult>(`/connections/${encodeURIComponent(id)}/test`, {
          method: "POST",
        }),
      discover: (id: string, schemas?: string[]) => {
        const query = schemas?.length
          ? "?" + new URLSearchParams(schemas.map((s) => ["schemas", s])).toString()
          : "";
        return request<CatalogSummary>(
          `/connections/${encodeURIComponent(id)}/discover${query}`,
          { method: "POST" },
        );
      },
    },
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
