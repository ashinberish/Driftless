import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { page, renderRoute } from "@/test/render";

import { MigrationCheckPage } from "./MigrationCheckPage";
import { NewMigrationPage } from "./NewMigrationPage";

const api = vi.hoisted(() => ({
  connectors: { list: vi.fn() },
  connections: { list: vi.fn() },
  migrations: {
    get: vi.fn(),
    create: vi.fn(),
    assess: vi.fn(),
    latestAssessment: vi.fn(),
    reportUrl: (id: string) => `/api/v1/migrations/${id}/assessments/latest/report.md`,
  },
}));
vi.mock("@/shared/api", () => ({ api }));

const migration = {
  id: "mig_1",
  name: "shop to pg17",
  source_connection_id: "conn_1",
  source_engine: "postgres",
  target_engine: "postgres",
  target_connection_id: null,
  status: "needs_attention",
  created_at: "2026-12-14T09:00:00Z",
  updated_at: "2026-12-14T09:00:00Z",
};

function run(overrides: Record<string, unknown> = {}) {
  return {
    id: "asmt_1",
    migration_id: "mig_1",
    created_at: "2026-12-14T09:01:00Z",
    assessment: {
      source_engine: "postgres",
      source_version: "16.15",
      target_engine: "postgres",
      tables: 4,
      columns: 10,
      total_rows: 440_000,
      total_bytes: 27_000_000,
      score: 41,
      level: "moderate",
      readiness_pct: 60,
      effort_days_min: 4,
      effort_days_max: 7,
      ready: false,
      findings: [
        {
          rule_id: "no-primary-key",
          severity: "blocking",
          category: "keys",
          title: "2 tables don't have a unique key",
          detail: "Without one we can't copy them in parallel.",
          recommendation: "Let Driftless add a hidden key column.",
          objects: ["sales.order_items", "public.audit_raw"],
          affected_columns: 4,
          auto_fixable: true,
        },
        {
          rule_id: "case-insensitive-text",
          severity: "info",
          category: "behaviour",
          title: "1 column ignores upper/lowercase today",
          detail: "We'll keep today's behaviour.",
          objects: [],
          affected_columns: 0,
          auto_fixable: false,
        },
      ],
      ...overrides,
    },
  };
}

describe("MigrationCheckPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.migrations.get.mockResolvedValue(migration);
  });

  it("leads with blocking items and keeps Continue disabled", async () => {
    api.migrations.latestAssessment.mockResolvedValue(run());
    renderRoute([page("/migrations/:migrationId/check", <MigrationCheckPage />)], "/migrations/mig_1/check");

    expect(await screen.findByRole("heading", { name: "1 thing to sort out first" })).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "Converts without review" })).toHaveAttribute("aria-valuenow", "60");
    expect(screen.getByText("Fix available")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Continue to settings/ })).toBeDisabled();
    expect(screen.getByRole("link", { name: /Download report/ })).toHaveAttribute(
      "href",
      "/api/v1/migrations/mig_1/assessments/latest/report.md",
    );
  });

  it("shows the friendly headline when nothing blocks", async () => {
    api.migrations.latestAssessment.mockResolvedValue(
      run({ ready: true, level: "low", readiness_pct: 100, findings: [] }),
    );
    renderRoute([page("/migrations/:migrationId/check", <MigrationCheckPage />)], "/migrations/mig_1/check");
    expect(await screen.findByText("Good news — this one looks very doable")).toBeInTheDocument();
    expect(screen.getByText(/everything converts cleanly/)).toBeInTheDocument();
  });

  it("offers to run the first check when none exists", async () => {
    const { ApiError } = await import("@driftless/api-client");
    api.migrations.latestAssessment.mockRejectedValue(new ApiError(404, "not_found", "not assessed"));
    api.migrations.assess.mockResolvedValue(run());
    const user = userEvent.setup();
    renderRoute([page("/migrations/:migrationId/check", <MigrationCheckPage />)], "/migrations/mig_1/check");
    await user.click(await screen.findByRole("button", { name: /Run check/ }));
    expect(await screen.findByText("2 tables don't have a unique key")).toBeInTheDocument();
  });
});

describe("NewMigrationPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.connectors.list.mockResolvedValue([
      { engine: "postgres", display_name: "PostgreSQL", default_port: 5432, capabilities: { write: true } },
      { engine: "mysql", display_name: "MySQL", default_port: 3306, capabilities: { write: false } },
    ]);
    api.connections.list.mockResolvedValue({
      total: 1,
      items: [{ id: "conn_1", name: "shop", engine: "postgres", host: "db", port: 5432, database: "shop" }],
    });
  });

  it("requires a name and a source", async () => {
    const user = userEvent.setup();
    renderRoute([page("/migrations/new", <NewMigrationPage />)], "/migrations/new");
    await user.click(await screen.findByRole("button", { name: /Continue — check my database/ }));
    expect(screen.getByText("Give the migration a name")).toBeInTheDocument();
    expect(api.migrations.create).not.toHaveBeenCalled();
  });

  it("creates the draft, assesses it and opens Check", async () => {
    api.migrations.create.mockResolvedValue(migration);
    api.migrations.assess.mockResolvedValue(run());
    const user = userEvent.setup();
    const { router } = renderRoute(
      [page("/migrations/new", <NewMigrationPage />), page("/migrations/:id/check", <h1>check</h1>)],
      "/migrations/new",
    );
    await user.type(await screen.findByLabelText(/^Migration name/), "shop to pg17");
    await user.selectOptions(screen.getByLabelText(/^Source connection/), "conn_1");
    expect(screen.getByRole("radio", { name: /MySQL/ })).toHaveTextContent("Source only for now");
    await user.click(screen.getByRole("button", { name: /Continue — check my database/ }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/migrations/mig_1/check"));
    expect(api.migrations.create).toHaveBeenCalledWith({
      name: "shop to pg17",
      source_connection_id: "conn_1",
      target_engine: "postgres",
      target_connection_id: null,
    });
    expect(api.migrations.assess).toHaveBeenCalledWith("mig_1");
  });
});
