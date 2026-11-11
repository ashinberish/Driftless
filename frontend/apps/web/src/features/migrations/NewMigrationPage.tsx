import { ApiError } from "@driftless/api-client";
import {
  Button,
  Card,
  CardHeader,
  EmptyState,
  EngineBadge,
  Field,
  Input,
  PageHeader,
  Select,
  Stepper,
  TileGroup,
} from "@driftless/ui";
import { ArrowRight, Loader2, Server } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router";

import { useConnections, useConnectors } from "@/features/connections/api";

import { useCreateAndAssess } from "./api";
import { WIZARD_STEPS } from "./model";

interface Draft {
  name: string;
  sourceId: string;
  targetEngine: string;
  targetId: string;
}

export function NewMigrationPage() {
  const navigate = useNavigate();
  const connections = useConnections();
  const connectors = useConnectors();
  const createAndAssess = useCreateAndAssess();
  const [draft, setDraft] = useState<Draft>({ name: "", sourceId: "", targetEngine: "postgres", targetId: "" });
  const [errors, setErrors] = useState<Partial<Record<keyof Draft, string>>>({});

  const all = useMemo(() => connections.data?.items ?? [], [connections.data]);
  const source = all.find((c) => c.id === draft.sourceId);
  const targetChoices = all.filter((c) => c.engine === draft.targetEngine && c.id !== draft.sourceId);

  const submit = () => {
    const found: typeof errors = {};
    if (!draft.name.trim()) found.name = "Give the migration a name";
    if (!draft.sourceId) found.sourceId = "Choose the database to move";
    setErrors(found);
    if (Object.keys(found).length) return;
    createAndAssess.mutate(
      {
        name: draft.name.trim(),
        source_connection_id: draft.sourceId,
        target_engine: draft.targetEngine,
        target_connection_id: draft.targetId || null,
      },
      { onSuccess: ({ migration }) => navigate(`/migrations/${migration.id}/check`) },
    );
  };

  const failure = createAndAssess.error instanceof ApiError ? createAndAssess.error.message : null;

  return (
    <>
      <Stepper steps={WIZARD_STEPS} current="connect" className="mb-6" />
      <PageHeader
        title="Where's your data now, and where should it go?"
        description="Pick a saved source connection and the engine you're moving to. Checking takes seconds and changes nothing."
      />

      {connections.isSuccess && all.length === 0 ? (
        <Card>
          <EmptyState
            icon={<Server />}
            title="Add a source connection first"
            description="Driftless needs read access to the database you want to move."
            action={
              <Button variant="primary" onClick={() => navigate("/connections/new")}>
                New connection
              </Button>
            }
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <Card>
            <CardHeader title="From" description="The database you're moving" />
            <div className="flex flex-col gap-5">
              <Field label="Migration name" required error={errors.name}>
                {(p) => (
                  <Input
                    {...p}
                    value={draft.name}
                    placeholder="billing-db to PostgreSQL 17"
                    onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                  />
                )}
              </Field>
              <Field
                label="Source connection"
                required
                error={errors.sourceId}
                hint={
                  <>
                    Not listed? <Link to="/connections/new" className="font-medium text-accent">Add a connection</Link>
                  </>
                }
              >
                {(p) => (
                  <Select {...p} value={draft.sourceId} onChange={(e) => setDraft({ ...draft, sourceId: e.target.value })}>
                    <option value="">Choose a connection…</option>
                    {all.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} — {c.engine} · {c.host}/{c.database}
                      </option>
                    ))}
                  </Select>
                )}
              </Field>
              {source ? (
                <div className="flex items-center gap-2 rounded-control bg-subtle px-3 py-2 text-[13px]">
                  <EngineBadge engine={source.engine} showLabel />
                  <span className="font-mono text-[12px] text-muted">{`${source.host}:${source.port}/${source.database}`}</span>
                </div>
              ) : null}
            </div>
          </Card>

          <Card>
            <CardHeader title="To" description="The engine you're moving to" />
            <div className="flex flex-col gap-5">
              <TileGroup
                aria-label="Target engine"
                columns={2}
                value={draft.targetEngine}
                onChange={(targetEngine) => setDraft({ ...draft, targetEngine, targetId: "" })}
                options={(connectors.data ?? []).map((c) => ({
                  value: c.engine,
                  label: c.display_name,
                  icon: <EngineBadge engine={c.engine} />,
                  description: c.capabilities.write ? "Supported target" : "Source only for now",
                }))}
              />
              <Field
                label="Target connection"
                hint="Optional now — you can choose or create the target database later."
              >
                {(p) => (
                  <Select {...p} value={draft.targetId} onChange={(e) => setDraft({ ...draft, targetId: e.target.value })}>
                    <option value="">Decide later</option>
                    {targetChoices.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} · {c.host}/{c.database}
                      </option>
                    ))}
                  </Select>
                )}
              </Field>
            </div>
          </Card>
        </div>
      )}

      {failure ? (
        <p role="alert" className="mt-5 rounded-control border border-line bg-surface px-3 py-2 text-[13px] text-danger">
          {failure}
        </p>
      ) : null}

      <div className="mt-6 flex items-center gap-2 border-t border-line pt-5">
        <Button variant="ghost" onClick={() => navigate("/migrations")}>
          Cancel
        </Button>
        <span className="flex-1" />
        <Button variant="primary" onClick={submit} disabled={createAndAssess.isPending || all.length === 0}>
          {createAndAssess.isPending ? (
            <>
              <Loader2 className="animate-spin" /> Checking your database…
            </>
          ) : (
            <>
              Continue — check my database <ArrowRight />
            </>
          )}
        </Button>
      </div>
    </>
  );
}
