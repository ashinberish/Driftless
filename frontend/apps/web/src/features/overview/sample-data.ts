import type { MigrationStatus } from "@/features/migrations/model";

/** Program-level dashboard data. Sample only — real program metrics arrive with runs (S4+). */
export interface SampleMigration {
  id: string;
  name: string;
  team: string;
  sourceEngine: string;
  targetEngine: string;
  wave: number;
  status: MigrationStatus;
  progress: number;
  goLiveWindow: string | null;
  risk: "low" | "medium" | "high";
  ownerInitials: string;
  sizeLabel: string;
}

export const SAMPLE_MIGRATIONS: SampleMigration[] = [
  { id: "DM-1042", name: "billing-db", team: "Finance", sourceEngine: "sqlserver", targetEngine: "postgres", wave: 2, status: "awaiting_approval", progress: 100, goLiveWindow: "Nov 14 · 02:00", risk: "medium", ownerInitials: "MR", sizeLabel: "1.8 TB" },
  { id: "DM-1038", name: "orders-core", team: "Commerce", sourceEngine: "mysql", targetEngine: "postgres", wave: 1, status: "copying", progress: 64, goLiveWindow: "Nov 28 · 02:00", risk: "low", ownerInitials: "JT", sizeLabel: "3.1 TB" },
  { id: "DM-1031", name: "crm-legacy", team: "Sales Ops", sourceEngine: "oracle", targetEngine: "postgres", wave: 1, status: "verifying", progress: 92, goLiveWindow: "Nov 21 · 01:00", risk: "high", ownerInitials: "AK", sizeLabel: "2.4 TB" },
  { id: "DM-1029", name: "inventory", team: "Supply chain", sourceEngine: "mysql", targetEngine: "mysql", wave: 1, status: "needs_attention", progress: 41, goLiveWindow: null, risk: "low", ownerInitials: "DS", sizeLabel: "640 GB" },
  { id: "DM-1045", name: "gl-reporting", team: "Finance", sourceEngine: "sqlserver", targetEngine: "postgres", wave: 2, status: "scheduled", progress: 0, goLiveWindow: "Dec 5 · 02:00", risk: "medium", ownerInitials: "MR", sizeLabel: "920 GB" },
  { id: "DM-1047", name: "payroll-ext", team: "Finance", sourceEngine: "oracle", targetEngine: "postgres", wave: 2, status: "assessing", progress: 12, goLiveWindow: "Dec 12 · 01:00", risk: "high", ownerInitials: "LP", sizeLabel: "210 GB" },
  { id: "DM-1021", name: "catalog-search", team: "Commerce", sourceEngine: "postgres", targetEngine: "postgres", wave: 1, status: "live", progress: 100, goLiveWindow: "Oct 24 · done", risk: "low", ownerInitials: "JT", sizeLabel: "380 GB" },
  { id: "DM-1050", name: "hr-analytics", team: "People", sourceEngine: "postgres", targetEngine: "postgres", wave: 3, status: "draft", progress: 0, goLiveWindow: null, risk: "low", ownerInitials: "MR", sizeLabel: "95 GB" },
];
