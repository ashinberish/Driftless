import { describe, expect, it } from "vitest";

import { MOCK_MIGRATIONS } from "./mock-data";
import { matchesFilter, STATUS_META, type MigrationStatus } from "./model";

describe("migration filters", () => {
  it("'all' includes everything", () => {
    expect(MOCK_MIGRATIONS.filter((m) => matchesFilter(m, "all"))).toHaveLength(
      MOCK_MIGRATIONS.length,
    );
  });

  it("'attention' covers approvals and failures", () => {
    const names = MOCK_MIGRATIONS.filter((m) => matchesFilter(m, "attention")).map((m) => m.name);
    expect(names).toEqual(["billing-db", "inventory"]);
  });

  it("every status has display metadata", () => {
    const statuses: MigrationStatus[] = MOCK_MIGRATIONS.map((m) => m.status);
    for (const s of statuses) expect(STATUS_META[s].label).toBeTruthy();
  });
});
