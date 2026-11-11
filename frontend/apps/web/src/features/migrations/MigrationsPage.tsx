import { Button, Card, EmptyState, PageHeader, SegmentedTabs } from "@driftless/ui";
import { Database, Plus, TriangleAlert } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router";

import { useMigrations } from "./api";
import { MigrationsTable } from "./components/MigrationsTable";
import { matchesFilter, type MigrationFilter } from "./model";

const FILTERS: { id: MigrationFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "attention", label: "Needs attention" },
  { id: "ready", label: "Ready" },
  { id: "draft", label: "Draft" },
];

export function MigrationsPage() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<MigrationFilter>("all");
  const { data, isPending, isError, error } = useMigrations();
  const migrations = useMemo(() => data?.items ?? [], [data]);

  const tabs = useMemo(
    () => FILTERS.map((f) => ({ ...f, count: migrations.filter((m) => matchesFilter(m, f.id)).length })),
    [migrations],
  );
  const newMigration = (
    <Button variant="primary" onClick={() => navigate("/migrations/new")}>
      <Plus /> New migration
    </Button>
  );

  return (
    <>
      <PageHeader
        title="Migrations"
        description="Every database move, from first check to go-live."
        actions={newMigration}
      />
      <Card className="p-0">
        {isPending ? (
          <div className="p-10 text-center text-muted">Loading migrations…</div>
        ) : isError ? (
          <EmptyState icon={<TriangleAlert />} title="Couldn't load migrations" description={error.message} />
        ) : migrations.length === 0 ? (
          <EmptyState
            icon={<Database />}
            title="No migrations yet"
            description="Pick a source database and a target engine — we'll check it in seconds."
            action={newMigration}
          />
        ) : (
          <>
            <div className="border-b border-line p-4">
              <SegmentedTabs
                aria-label="Filter migrations"
                tabs={tabs}
                value={filter}
                onChange={(id) => setFilter(id as MigrationFilter)}
              />
            </div>
            <MigrationsTable
              rows={migrations.filter((m) => matchesFilter(m, filter))}
              onOpen={(m) => navigate(`/migrations/${m.id}/check`)}
            />
          </>
        )}
      </Card>
    </>
  );
}
