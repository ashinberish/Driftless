import type { Connection } from "@driftless/api-client";
import {
  Button,
  Card,
  DataTable,
  EmptyState,
  EngineBadge,
  PageHeader,
  type Column,
} from "@driftless/ui";
import { Lock, Plus, Server, TriangleAlert } from "lucide-react";

import { useConnections } from "./api";

const columns: Column<Connection>[] = [
  { id: "name", header: "Name", cell: (c) => <span className="font-semibold text-ink">{c.name}</span> },
  { id: "engine", header: "Engine", cell: (c) => <EngineBadge engine={c.engine} showLabel /> },
  { id: "host", header: "Host", cell: (c) => <span className="font-mono text-[12px]">{`${c.host}:${c.port}/${c.database}`}</span> },
  {
    id: "secret",
    header: "Credentials",
    cell: (c) => (
      <span className="inline-flex items-center gap-1.5 text-ink-2">
        <Lock className="size-3.5 text-success" aria-hidden /> {c.secret_ref}
      </span>
    ),
  },
  { id: "ssl", header: "TLS", cell: (c) => c.ssl_mode },
];

export function ConnectionsPage() {
  const { data, isPending, isError, error } = useConnections();

  return (
    <>
      <PageHeader
        title="Connections"
        description="Databases Driftless can reach. Credentials stay in your secrets backend."
        actions={
          <Button variant="primary">
            <Plus /> New connection
          </Button>
        }
      />
      <Card className="p-0">
        {isPending ? (
          <div className="p-10 text-center text-muted">Loading connections…</div>
        ) : isError ? (
          <EmptyState
            icon={<TriangleAlert />}
            title="Couldn't load connections"
            description={error instanceof Error ? error.message : "Is the API running? (make api)"}
          />
        ) : data.items.length === 0 ? (
          <EmptyState
            icon={<Server />}
            title="No connections yet"
            description="Add a source and a target database to start your first migration."
            action={
              <Button variant="primary">
                <Plus /> New connection
              </Button>
            }
          />
        ) : (
          <DataTable columns={columns} rows={data.items} rowKey={(c) => c.id} />
        )}
      </Card>
    </>
  );
}
