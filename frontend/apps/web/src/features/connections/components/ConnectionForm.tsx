import type { ConnectorInfo } from "@driftless/api-client";
import { EngineBadge, Field, Input, Select, TileGroup } from "@driftless/ui";
import { KeyRound, Link2 } from "lucide-react";
import { useState } from "react";

import {
  DEFAULT_PORTS,
  parseConnectionString,
  type ConnectionFormValues,
  type FormErrors,
} from "../connection-form";

export interface ConnectionFormProps {
  values: ConnectionFormValues;
  onChange: (values: ConnectionFormValues) => void;
  errors: FormErrors;
  engines: ConnectorInfo[];
  /** Hide the name field when the form is embedded in a larger flow. */
  showName?: boolean;
}

/** Reusable connection form — used by "New connection" now and the migration wizard later. */
export function ConnectionForm({ values, onChange, errors, engines, showName = true }: ConnectionFormProps) {
  const [pasteNote, setPasteNote] = useState<string | null>(null);
  const set = <K extends keyof ConnectionFormValues>(key: K, value: ConnectionFormValues[K]) =>
    onChange({ ...values, [key]: value });

  const changeEngine = (engine: string) => {
    const wasDefaultPort = values.port === String(DEFAULT_PORTS[values.engine] ?? "");
    onChange({
      ...values,
      engine,
      port: wasDefaultPort ? String(DEFAULT_PORTS[engine] ?? values.port) : values.port,
    });
  };

  return (
    <div className="flex flex-col gap-5">
      {showName ? (
        <Field label="Name" required error={errors.name} hint="How this database appears across Driftless">
          {(p) => (
            <Input {...p} value={values.name} placeholder="billing-prod" onChange={(e) => set("name", e.target.value)} />
          )}
        </Field>
      ) : null}

      <div className="flex flex-col gap-1.5">
        <span className="text-[12.5px] font-semibold text-ink-2">Engine</span>
        <TileGroup
          aria-label="Database engine"
          value={values.engine}
          onChange={changeEngine}
          options={engines.map((e) => ({
            value: e.engine,
            label: e.display_name,
            icon: <EngineBadge engine={e.engine} />,
          }))}
        />
      </div>

      <Field
        label="Connection string"
        hint={pasteNote ?? "Optional — paste a URL to fill in the fields below"}
      >
        {(p) => (
          <Input
            {...p}
            leading={<Link2 />}
            className="font-mono text-[12.5px]"
            placeholder="postgresql://user@host:5432/database"
            onPaste={(e) => {
              const parsed = parseConnectionString(e.clipboardData.getData("text"));
              if (!parsed) return;
              e.preventDefault();
              onChange({ ...values, ...parsed.values });
              setPasteNote(
                parsed.droppedPassword
                  ? "Filled in from the URL. The password was ignored — use a secret reference instead."
                  : "Filled in from the URL.",
              );
            }}
          />
        )}
      </Field>

      <div className="grid grid-cols-[1fr_120px] gap-4">
        <Field label="Host" required error={errors.host}>
          {(p) => <Input {...p} value={values.host} placeholder="db.internal" onChange={(e) => set("host", e.target.value)} />}
        </Field>
        <Field label="Port" required error={errors.port}>
          {(p) => <Input {...p} inputMode="numeric" value={values.port} onChange={(e) => set("port", e.target.value)} />}
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Database" required error={errors.database}>
          {(p) => <Input {...p} value={values.database} onChange={(e) => set("database", e.target.value)} />}
        </Field>
        <Field label="Username" required error={errors.username}>
          {(p) => <Input {...p} autoComplete="off" value={values.username} onChange={(e) => set("username", e.target.value)} />}
        </Field>
      </div>

      <div className="grid grid-cols-[1fr_180px] gap-4">
        <Field
          label="Password reference"
          required
          error={errors.secretRef}
          hint="Where the password lives, e.g. vault:db/billing-ro or env:BILLING_PW"
        >
          {(p) => (
            <Input
              {...p}
              leading={<KeyRound />}
              className="font-mono text-[12.5px]"
              autoComplete="off"
              spellCheck={false}
              value={values.secretRef}
              placeholder="vault:db/billing-ro"
              onChange={(e) => set("secretRef", e.target.value)}
            />
          )}
        </Field>
        <Field label="TLS">
          {(p) => (
            <Select {...p} value={values.sslMode} onChange={(e) => set("sslMode", e.target.value as ConnectionFormValues["sslMode"])}>
              <option value="verify-full">Verify (recommended)</option>
              <option value="require">Require</option>
              <option value="prefer">Prefer</option>
              <option value="disable">Disable</option>
            </Select>
          )}
        </Field>
      </div>
    </div>
  );
}
