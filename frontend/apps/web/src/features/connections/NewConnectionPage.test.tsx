import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { page, renderRoute } from "@/test/render";

import { NewConnectionPage } from "./NewConnectionPage";

const api = vi.hoisted(() => ({
  connectors: { list: vi.fn() },
  connections: { testSpec: vi.fn(), create: vi.fn() },
}));
vi.mock("@/shared/api", () => ({ api }));

const routes = [
  page("/connections/new", <NewConnectionPage />),
  page("/connections/:id", <h1>Detail page</h1>),
];

async function fillForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/^Name/), "billing-prod");
  await user.type(screen.getByLabelText(/^Host/), "db.internal");
  await user.type(screen.getByRole("textbox", { name: /^Database/ }), "billing");
  await user.type(screen.getByLabelText(/^Username/), "ro");
  await user.type(screen.getByLabelText(/^Password reference/), "env:BILLING_PW");
}

describe("NewConnectionPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.connectors.list.mockResolvedValue([
      { engine: "mysql", display_name: "MySQL", default_port: 3306, capabilities: {} },
      { engine: "postgres", display_name: "PostgreSQL", default_port: 5432, capabilities: {} },
    ]);
  });

  it("shows validation errors instead of calling the API", async () => {
    const user = userEvent.setup();
    renderRoute(routes, "/connections/new");
    await user.click(screen.getByRole("button", { name: /Save connection/ }));
    expect(screen.getByText("Host is required")).toBeInTheDocument();
    expect(api.connections.create).not.toHaveBeenCalled();
  });

  it("tests unsaved settings and shows the checks", async () => {
    api.connections.testSpec.mockResolvedValue({
      ok: true,
      checks: [
        { name: "Reachable", status: "ok", detail: "PostgreSQL 17 · 3 ms" },
        { name: "Change tracking", status: "warning", fix_script: "ALTER SYSTEM ..." },
      ],
    });
    const user = userEvent.setup();
    renderRoute(routes, "/connections/new");
    await fillForm(user);
    await user.click(screen.getByRole("button", { name: /Test connection/ }));

    expect(await screen.findByText("PostgreSQL 17 · 3 ms")).toBeInTheDocument();
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(api.connections.testSpec).toHaveBeenCalledWith(
      expect.objectContaining({ engine: "postgres", port: 5432, secret_ref: "env:BILLING_PW" }),
    );
  });

  it("switching engine updates a default port", async () => {
    const user = userEvent.setup();
    renderRoute(routes, "/connections/new");
    await user.click(await screen.findByRole("radio", { name: /MySQL/ }));
    expect(screen.getByLabelText(/^Port/)).toHaveValue("3306");
  });

  it("saves and opens the new connection", async () => {
    api.connections.create.mockResolvedValue({ id: "conn_123" });
    const user = userEvent.setup();
    const { router } = renderRoute(routes, "/connections/new");
    await fillForm(user);
    await user.click(screen.getByRole("button", { name: /Save connection/ }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/connections/conn_123"));
    expect(api.connections.create).toHaveBeenCalledWith(
      expect.objectContaining({ name: "billing-prod", host: "db.internal" }),
    );
  });
});
