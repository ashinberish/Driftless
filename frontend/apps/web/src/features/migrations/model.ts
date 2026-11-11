import type { Migration, Severity } from "@driftless/api-client";
import type { StatusTone } from "@driftless/ui";

/**
 * Every status a migration can show. The first three come from the API today; the rest
 * arrive with copy, CDC and cutover (S4–S8) and are already styled so screens agree.
 */
export type MigrationStatus =
  | Migration["status"]
  | "assessing"
  | "scheduled"
  | "copying"
  | "verifying"
  | "awaiting_approval"
  | "live";

/** One place that decides how a status looks — every screen reuses it. */
export const STATUS_META: Record<MigrationStatus, { label: string; tone: StatusTone }> = {
  draft: { label: "Draft", tone: "neutral" },
  ready: { label: "Ready", tone: "success" },
  needs_attention: { label: "Needs attention", tone: "danger" },
  assessing: { label: "Assessing", tone: "neutral" },
  scheduled: { label: "Scheduled", tone: "neutral" },
  copying: { label: "Copying", tone: "progress" },
  verifying: { label: "Verifying", tone: "info" },
  awaiting_approval: { label: "Awaiting approval", tone: "warning" },
  live: { label: "Live", tone: "success" },
};

export const SEVERITY_TONE: Record<Severity, StatusTone> = {
  blocking: "danger",
  warning: "warning",
  info: "info",
};

export type MigrationFilter = "all" | "attention" | "ready" | "draft";

export function matchesFilter(m: Pick<Migration, "status">, filter: MigrationFilter): boolean {
  switch (filter) {
    case "all":
      return true;
    case "attention":
      return m.status === "needs_attention";
    case "ready":
      return m.status === "ready";
    case "draft":
      return m.status === "draft";
  }
}

/** Headline for the Check screen, by complexity level. */
export const LEVEL_COPY = {
  low: "Good news — this one looks very doable",
  moderate: "Doable, with some work up front",
  high: "This one needs careful planning",
} as const;

/** The six steps of the migration journey (v5 design). */
export const WIZARD_STEPS = [
  { id: "connect", label: "Connect", hint: "Source & target" },
  { id: "check", label: "Check", hint: "What we found" },
  { id: "settings", label: "Settings", hint: "Quick choices" },
  { id: "launch", label: "Launch", hint: "How & when" },
  { id: "copy", label: "Copy", hint: "Live progress" },
  { id: "golive", label: "Go live", hint: "Switch over" },
];
