import type { StatusTone } from "@driftless/ui";

export type MigrationStatus =
  | "draft"
  | "assessing"
  | "scheduled"
  | "copying"
  | "verifying"
  | "awaiting_approval"
  | "needs_attention"
  | "live";

export type Risk = "low" | "medium" | "high";

export interface MigrationSummary {
  id: string;
  name: string;
  team: string;
  sourceEngine: string;
  targetEngine: string;
  wave: number;
  status: MigrationStatus;
  progress: number;
  goLiveWindow: string | null;
  risk: Risk;
  ownerInitials: string;
  sizeLabel: string;
}

/** One place that decides how a status looks — every screen reuses it. */
export const STATUS_META: Record<MigrationStatus, { label: string; tone: StatusTone }> = {
  draft: { label: "Draft", tone: "neutral" },
  assessing: { label: "Assessing", tone: "neutral" },
  scheduled: { label: "Scheduled", tone: "neutral" },
  copying: { label: "Copying", tone: "progress" },
  verifying: { label: "Verifying", tone: "info" },
  awaiting_approval: { label: "Awaiting approval", tone: "warning" },
  needs_attention: { label: "Needs attention", tone: "danger" },
  live: { label: "Live", tone: "success" },
};

export const RISK_META: Record<Risk, { label: string; className: string }> = {
  low: { label: "Low", className: "text-success" },
  medium: { label: "Medium", className: "text-warning" },
  high: { label: "High", className: "text-danger" },
};

export type MigrationFilter = "all" | "running" | "attention" | "scheduled" | "live" | "draft";

const RUNNING: MigrationStatus[] = ["copying", "verifying", "assessing"];

export function matchesFilter(m: MigrationSummary, filter: MigrationFilter): boolean {
  switch (filter) {
    case "all":
      return true;
    case "running":
      return RUNNING.includes(m.status);
    case "attention":
      return m.status === "needs_attention" || m.status === "awaiting_approval";
    case "scheduled":
      return m.status === "scheduled";
    case "live":
      return m.status === "live";
    case "draft":
      return m.status === "draft";
  }
}
