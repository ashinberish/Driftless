import { StatusBadge } from "@driftless/ui";

import { STATUS_META, type MigrationStatus } from "../model";

export function MigrationStatusBadge({ status }: { status: MigrationStatus }) {
  const meta = STATUS_META[status];
  return <StatusBadge tone={meta.tone}>{meta.label}</StatusBadge>;
}
