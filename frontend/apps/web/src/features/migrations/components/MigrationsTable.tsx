import { DataTable, EngineBadge, ProgressBar, type Column } from "@driftless/ui";
import { ArrowRight } from "lucide-react";

import { RISK_META, type MigrationSummary } from "../model";
import { MigrationStatusBadge } from "./MigrationStatusBadge";

const columns: Column<MigrationSummary>[] = [
  {
    id: "name",
    header: "Migration",
    cell: (m) => (
      <div>
        <div className="font-semibold text-ink">{m.name}</div>
        <div className="text-[12px] text-muted">
          {m.id} · {m.sizeLabel}
        </div>
      </div>
    ),
  },
  { id: "team", header: "Team", cell: (m) => m.team },
  {
    id: "engines",
    header: "Source → Target",
    cell: (m) => (
      <span className="inline-flex items-center gap-2">
        <EngineBadge engine={m.sourceEngine} />
        <ArrowRight className="size-3.5 text-muted" aria-hidden />
        <EngineBadge engine={m.targetEngine} />
      </span>
    ),
  },
  { id: "wave", header: "Wave", cell: (m) => m.wave },
  { id: "status", header: "Status", cell: (m) => <MigrationStatusBadge status={m.status} /> },
  {
    id: "progress",
    header: "Progress",
    className: "w-40",
    cell: (m) => (
      <ProgressBar
        value={m.progress}
        label={`${m.name} progress`}
        tone={m.status === "live" ? "success" : m.status === "needs_attention" ? "danger" : "progress"}
      />
    ),
  },
  { id: "window", header: "Go-live window", cell: (m) => m.goLiveWindow ?? "—" },
  {
    id: "risk",
    header: "Risk",
    cell: (m) => (
      <span className={`font-medium ${RISK_META[m.risk].className}`}>● {RISK_META[m.risk].label}</span>
    ),
  },
  {
    id: "owner",
    header: "Owner",
    cell: (m) => (
      <span className="grid size-7 place-items-center rounded-full bg-[#e4e4e7] text-[10.5px] font-semibold text-ink-2">
        {m.ownerInitials}
      </span>
    ),
  },
];

export function MigrationsTable({ rows }: { rows: MigrationSummary[] }) {
  return (
    <DataTable
      columns={columns}
      rows={rows}
      rowKey={(m) => m.id}
      empty="No migrations match this filter"
    />
  );
}
