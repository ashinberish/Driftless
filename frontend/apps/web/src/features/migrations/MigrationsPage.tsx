import { Button, Card, PageHeader, SegmentedTabs } from "@driftless/ui";
import { Download, Plus } from "lucide-react";
import { useMemo, useState } from "react";

import { MigrationsTable } from "./components/MigrationsTable";
import { MOCK_MIGRATIONS } from "./mock-data";
import { matchesFilter, type MigrationFilter } from "./model";

const FILTERS: { id: MigrationFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "running", label: "Running" },
  { id: "attention", label: "Needs attention" },
  { id: "scheduled", label: "Scheduled" },
  { id: "live", label: "Live" },
  { id: "draft", label: "Draft" },
];

export function MigrationsPage() {
  const [filter, setFilter] = useState<MigrationFilter>("all");
  const migrations = MOCK_MIGRATIONS;

  const tabs = useMemo(
    () =>
      FILTERS.map((f) => ({
        ...f,
        count: migrations.filter((m) => matchesFilter(m, f.id)).length,
      })),
    [migrations],
  );
  const rows = migrations.filter((m) => matchesFilter(m, filter));

  return (
    <>
      <PageHeader
        title="Migrations"
        description="FY26 Data platform modernization · 3 waves"
        actions={
          <>
            <Button>
              <Download /> Export CSV
            </Button>
            <Button variant="primary">
              <Plus /> New migration
            </Button>
          </>
        }
      />
      <Card className="p-0">
        <div className="border-b border-line p-4">
          <SegmentedTabs
            aria-label="Filter migrations"
            tabs={tabs}
            value={filter}
            onChange={(id) => setFilter(id as MigrationFilter)}
          />
        </div>
        <MigrationsTable rows={rows} />
      </Card>
    </>
  );
}
