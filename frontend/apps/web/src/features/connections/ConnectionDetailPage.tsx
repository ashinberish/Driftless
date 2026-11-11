import type { TableSummary } from "@driftless/api-client";
import {
  Button,
  Card,
  CardHeader,
  CheckList,
  DataTable,
  EmptyState,
  EngineBadge,
  PageHeader,
  StatusBadge,
  type Column,
} from "@driftless/ui";
import { Database, Loader2, PlugZap, ScanSearch, Trash2, TriangleAlert } from "lucide-react";
import { useNavigate, useParams } from "react-router";

import { formatBytes, formatCount } from "@/shared/format";

import { useConnection, useDeleteConnection, useDiscover, useTestConnection } from "./api";
import { toCheckItems } from "./connection-form";

const tableColumns: Column<TableSummary>[] = [
  { id: "name", header: "Table", cell: (t) => <span className="font-mono text-[12.5px]">{t.name}</span> },
  { id: "columns", header: "Columns", align: "right", cell: (t) => t.columns },
  { id: "rows", header: "Rows (est.)", align: "right", cell: (t) => formatCount(t.rows) },
  { id: "size", header: "Size", align: "right", cell: (t) => formatBytes(t.size_bytes) },
  {
    id: "pk",
    header: "Unique key",
    cell: (t) =>
      t.has_primary_key ? (
        <StatusBadge tone="success">Primary key</StatusBadge>
      ) : (
        <StatusBadge tone="warning">Missing</StatusBadge>
      ),
  },
];

function Detail({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 border-b border-line-soft py-2.5 text-[13px] last:border-b-0">
      <span className="text-muted">{label}</span>
      <span className="truncate text-right text-ink">{value}</span>
    </div>
  );
}

export function ConnectionDetailPage() {
  const { connectionId = "" } = useParams();
  const navigate = useNavigate();
  const connection = useConnection(connectionId);
  const test = useTestConnection(connectionId);
  const discover = useDiscover(connectionId);
  const remove = useDeleteConnection();

  if (connection.isPending) return <p className="text-muted">Loading…</p>;
  if (connection.isError) {
    return (
      <Card>
        <EmptyState icon={<TriangleAlert />} title="Connection not found" description={connection.error.message} />
      </Card>
    );
  }
  const c = connection.data;
  const catalog = discover.data;
  const missingKeys = catalog?.tables.filter((t) => !t.has_primary_key).length ?? 0;

  return (
    <>
      <PageHeader
        title={c.name}
        description={
          <span className="inline-flex items-center gap-2">
            <EngineBadge engine={c.engine} showLabel /> · <span className="font-mono text-[12.5px]">{`${c.host}:${c.port}/${c.database}`}</span>
          </span>
        }
        actions={
          <>
            <Button
              variant="danger"
              onClick={() => {
                if (window.confirm(`Delete connection “${c.name}”?`)) {
                  remove.mutate(c.id, { onSuccess: () => navigate("/connections") });
                }
              }}
            >
              <Trash2 /> Delete
            </Button>
            <Button onClick={() => test.mutate()} disabled={test.isPending}>
              {test.isPending ? <Loader2 className="animate-spin" /> : <PlugZap />} Test
            </Button>
            <Button variant="primary" onClick={() => discover.mutate(undefined)} disabled={discover.isPending}>
              {discover.isPending ? <Loader2 className="animate-spin" /> : <ScanSearch />} Discover tables
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card className="p-0">
          <div className="p-5 pb-0">
            <CardHeader
              title="Catalog"
              description={
                catalog
                  ? `${catalog.total_tables} tables · ${formatCount(catalog.total_rows)} rows · ${formatBytes(catalog.total_bytes)}`
                  : "Read table names, sizes and keys. No row data is read."
              }
              actions={missingKeys ? <StatusBadge tone="warning">{missingKeys} without a unique key</StatusBadge> : null}
            />
          </div>
          {catalog ? (
            <DataTable columns={tableColumns} rows={catalog.tables} rowKey={(t) => t.name} empty="No tables found" />
          ) : discover.isError ? (
            <EmptyState icon={<TriangleAlert />} title="Discovery failed" description={discover.error.message} />
          ) : (
            <EmptyState icon={<Database />} title="Not discovered yet" description="Run Discover tables to see what's inside." />
          )}
        </Card>

        <div className="flex flex-col gap-5">
          <Card>
            <CardHeader title="Checks" />
            {test.data ? (
              <CheckList items={toCheckItems(test.data.checks)} />
            ) : test.isError ? (
              <p role="alert" className="text-[13px] text-danger">{test.error.message}</p>
            ) : (
              <p className="text-[13px] text-muted">Run Test to check this connection now.</p>
            )}
          </Card>
          <Card>
            <CardHeader title="Details" />
            <Detail label="Username" value={c.username} />
            <Detail label="Password reference" value={<span className="font-mono text-[12px]">{c.secret_ref}</span>} />
            <Detail label="TLS" value={c.ssl_mode} />
            <Detail label="Added" value={new Date(c.created_at).toLocaleString()} />
            <Detail label="ID" value={<span className="font-mono text-[12px]">{c.id}</span>} />
          </Card>
        </div>
      </div>
    </>
  );
}
