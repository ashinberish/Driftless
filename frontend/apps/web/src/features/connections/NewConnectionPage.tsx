import { ApiError } from "@driftless/api-client";
import { Button, Card, CardHeader, CheckList, PageHeader, StatusBadge } from "@driftless/ui";
import { Loader2, PlugZap, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";

import { useConnectors, useCreateConnection, useTestSpec } from "./api";
import { ConnectionForm } from "./components/ConnectionForm";
import {
  emptyForm,
  toCheckItems,
  toCreate,
  toSpec,
  validate,
  type ConnectionFormValues,
  type FormErrors,
} from "./connection-form";

export function NewConnectionPage() {
  const navigate = useNavigate();
  const connectors = useConnectors();
  const testSpec = useTestSpec();
  const create = useCreateConnection();
  const [values, setValues] = useState<ConnectionFormValues>(() => emptyForm());
  const [errors, setErrors] = useState<FormErrors>({});

  const onChange = (next: ConnectionFormValues) => {
    setValues(next);
    testSpec.reset(); // results describe the previous settings
    if (Object.keys(errors).length) setErrors(validate(next));
  };

  const runTest = () => {
    const found = validate(values, { requireName: false });
    setErrors(found);
    if (Object.keys(found).length === 0) testSpec.mutate(toSpec(values));
  };

  const save = () => {
    const found = validate(values);
    setErrors(found);
    if (Object.keys(found).length > 0) return;
    create.mutate(toCreate(values), {
      onSuccess: (conn) => navigate(`/connections/${conn.id}`),
    });
  };

  const result = testSpec.data;
  const saveError = create.error instanceof ApiError ? create.error.message : null;

  return (
    <>
      <PageHeader
        title="New connection"
        description="Driftless only needs read access to a source database."
      />
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
        <Card>
          <ConnectionForm values={values} onChange={onChange} errors={errors} engines={connectors.data ?? []} />
          {saveError ? (
            <p role="alert" className="mt-5 rounded-control border border-line bg-subtle px-3 py-2 text-[13px] text-danger">
              {saveError}
            </p>
          ) : null}
          <div className="mt-6 flex items-center gap-2 border-t border-line-soft pt-5">
            <Button onClick={runTest} disabled={testSpec.isPending}>
              {testSpec.isPending ? <Loader2 className="animate-spin" /> : <PlugZap />} Test connection
            </Button>
            <span className="flex-1" />
            <Button variant="ghost" onClick={() => navigate("/connections")}>
              Cancel
            </Button>
            <Button variant="primary" onClick={save} disabled={create.isPending}>
              {create.isPending ? <Loader2 className="animate-spin" /> : null} Save connection
            </Button>
          </div>
        </Card>

        <div className="flex flex-col gap-5">
          <Card>
            <CardHeader
              title="Checks"
              actions={
                result ? (
                  <StatusBadge tone={result.ok ? "success" : "danger"}>{result.ok ? "Ready" : "Needs attention"}</StatusBadge>
                ) : null
              }
            />
            {result ? (
              <CheckList items={toCheckItems(result.checks)} />
            ) : testSpec.isError ? (
              <p role="alert" className="text-[13px] text-danger">
                {testSpec.error instanceof Error ? testSpec.error.message : "Test failed"}
              </p>
            ) : (
              <p className="text-[13px] text-muted">
                Run a test to check reachability, permissions and whether change tracking is on.
              </p>
            )}
          </Card>
          <Card>
            <div className="flex gap-3">
              <ShieldCheck className="mt-0.5 size-5 shrink-0 text-success" aria-hidden />
              <div>
                <h3 className="text-sm font-semibold">Passwords never reach Driftless</h3>
                <p className="mt-1 text-[13px] text-muted">
                  You give a reference to your secrets manager. It is resolved only when a connection opens,
                  inside your network, and never stored or logged.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
