import type { Migration } from "@driftless/api-client";
import { DataTable, EngineBadge, type Column } from "@driftless/ui";
import { ArrowRight } from "lucide-react";

import { MigrationStatusBadge } from "./MigrationStatusBadge";

const columns: Column<Migration>[] = [
  {
    id: "name",
    header: "Migration",
    cell: (m) => (
      <div>
        <div className="font-semibold text-ink">{m.name}</div>
        <div className="font-mono text-[11.5px] text-muted">{m.id}</div>
      </div>
    ),
  },
  {
    id: "engines",
    header: "Source → Target",
    cell: (m) => (
      <span className="inline-flex items-center gap-2">
        <EngineBadge engine={m.source_engine} showLabel />
        <ArrowRight className="size-3.5 text-muted" aria-hidden />
        <EngineBadge engine={m.target_engine} showLabel />
      </span>
    ),
  },
  { id: "status", header: "Status", cell: (m) => <MigrationStatusBadge status={m.status} /> },
  {
    id: "updated",
    header: "Last activity",
    cell: (m) => new Date(m.updated_at).toLocaleString(),
  },
];

export function MigrationsTable({ rows, onOpen }: { rows: Migration[]; onOpen: (m: Migration) => void }) {
  return (
    <DataTable
      columns={columns}
      rows={rows}
      rowKey={(m) => m.id}
      onRowClick={onOpen}
      empty="No migrations match this filter"
    />
  );
}
