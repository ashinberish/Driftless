import { describe, expect, it } from "vitest";

import { matchesFilter, STATUS_META, type MigrationStatus } from "./model";

const rows: { status: "draft" | "ready" | "needs_attention" }[] = [
  { status: "draft" },
  { status: "ready" },
  { status: "needs_attention" },
  { status: "ready" },
];

describe("migration filters", () => {
  it("'all' includes everything", () => {
    expect(rows.filter((m) => matchesFilter(m, "all"))).toHaveLength(4);
  });

  it.each([
    ["attention", 1],
    ["ready", 2],
    ["draft", 1],
  ] as const)("'%s' matches %i", (filter, count) => {
    expect(rows.filter((m) => matchesFilter(m, filter))).toHaveLength(count);
  });

  it("every status has display metadata", () => {
    const statuses = Object.keys(STATUS_META) as MigrationStatus[];
    expect(statuses).toContain("needs_attention");
    for (const s of statuses) expect(STATUS_META[s].label).toBeTruthy();
  });
});
