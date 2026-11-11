import { describe, expect, it, vi } from "vitest";

import { ApiError, createApiClient } from "./client";

function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}) {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

describe("createApiClient", () => {
  it("calls the versioned base URL and parses JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { items: [], total: 0 }));
    const api = createApiClient({ fetch: fetchMock });
    await expect(api.connections.list()).resolves.toEqual({ items: [], total: 0 });
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/connections", expect.any(Object));
  });

  it("sends JSON bodies with the right content type", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(201, { id: "conn_1" }));
    const api = createApiClient({ fetch: fetchMock });
    await api.connections.create({
      name: "billing",
      engine: "postgres",
      host: "db",
      port: 5432,
      database: "billing",
      username: "ro",
      secret_ref: "vault:db/billing",
    });
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.method).toBe("POST");
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
  });

  it("raises ApiError with the server's error code", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(409, {
        error: { code: "conflict", message: "exists", details: {} },
        request_id: "req_1",
      }),
    );
    const api = createApiClient({ fetch: fetchMock });
    const error = await api.connections.get("x").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 409, code: "conflict", requestId: "req_1" });
  });

  it("handles 204 No Content", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    const api = createApiClient({ fetch: fetchMock });
    await expect(api.connections.remove("conn_1")).resolves.toBeUndefined();
  });
});
