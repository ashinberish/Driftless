import type { Assessment } from "@driftless/api-client";
import {
  Button,
  Card,
  CardHeader,
  EmptyState,
  EngineBadge,
  ProgressRing,
  Stepper,
} from "@driftless/ui";
import { ArrowLeft, ArrowRight, Download, Loader2, RefreshCw, ScanSearch, TriangleAlert } from "lucide-react";
import { useNavigate, useParams } from "react-router";

import { api } from "@/shared/api";
import { formatBytes, formatCount } from "@/shared/format";

import { useLatestAssessment, useMigration, useRunAssessment } from "./api";
import { FindingCard } from "./components/FindingCard";
import { LEVEL_COPY, WIZARD_STEPS } from "./model";

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 border-b border-line-soft py-2.5 text-[13px] last:border-b-0">
      <span className="text-muted">{label}</span>
      <span className="text-right font-semibold text-ink">{value}</span>
    </div>
  );
}

function ringTone(a: Assessment) {
  if (!a.ready) return "danger" as const;
  return a.readiness_pct >= 80 ? ("success" as const) : ("warning" as const);
}

export function MigrationCheckPage() {
  const { migrationId = "" } = useParams();
  const navigate = useNavigate();
  const migration = useMigration(migrationId);
  const latest = useLatestAssessment(migrationId);
  const rerun = useRunAssessment(migrationId);

  if (migration.isPending || latest.isPending) return <p className="text-muted">Loading…</p>;
  if (migration.isError) {
    return (
      <Card>
        <EmptyState icon={<TriangleAlert />} title="Migration not found" description={migration.error.message} />
      </Card>
    );
  }

  const m = migration.data;
  const run = latest.data ?? null;
  const rerunButton = (
    <Button onClick={() => rerun.mutate()} disabled={rerun.isPending}>
      {rerun.isPending ? <Loader2 className="animate-spin" /> : <RefreshCw />} {run ? "Check again" : "Run check"}
    </Button>
  );

  if (!run) {
    return (
      <>
        <Stepper steps={WIZARD_STEPS} current="check" className="mb-6" />
        <Card>
          <EmptyState
            icon={<ScanSearch />}
            title="Not checked yet"
            description="We'll read the source catalog and tell you what converts automatically."
            action={rerunButton}
          />
        </Card>
      </>
    );
  }

  const a = run.assessment;
  const blocking = a.findings.filter((f) => f.severity === "blocking");
  const headsUps = a.findings.filter((f) => f.severity !== "blocking");
  const checkedAt = new Date(run.created_at).toLocaleString();

  return (
    <>
      <Stepper steps={WIZARD_STEPS} current="check" className="mb-6" />
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="flex min-w-0 flex-col gap-5">
          <Card className="flex items-center gap-7 p-7">
            <ProgressRing value={a.readiness_pct} label="Converts without review" tone={ringTone(a)}>
              <div>
                <div className="text-[30px] font-bold tracking-tight">{a.readiness_pct}%</div>
                <div className="text-[12px] text-muted">automatic</div>
              </div>
            </ProgressRing>
            <div className="min-w-0">
              <div className="text-[11px] font-medium uppercase tracking-wider text-muted">Check complete · {checkedAt}</div>
              <h1 className="mt-1 text-[22px] font-semibold tracking-tight">
                {a.ready ? LEVEL_COPY[a.level] : `${blocking.length} ${blocking.length === 1 ? "thing" : "things"} to sort out before we start`}
              </h1>
              <p className="mt-1.5 text-sm text-muted">
                We looked at {formatCount(a.tables)} tables, {formatCount(a.columns)} columns and{" "}
                {formatBytes(a.total_bytes)} of data. Expect{" "}
                <span className="font-semibold text-ink">
                  {a.effort_days_min}–{a.effort_days_max} days
                </span>{" "}
                of work.
              </p>
              <div className="mt-3 flex items-center gap-2 text-[13px] text-ink-2">
                <EngineBadge engine={m.source_engine} showLabel version={a.source_version ?? undefined} />
                <ArrowRight className="size-3.5 text-muted" aria-hidden />
                <EngineBadge engine={m.target_engine} showLabel />
              </div>
            </div>
          </Card>

          {blocking.length > 0 ? (
            <section aria-labelledby="blocking-heading" className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h2 id="blocking-heading" className="text-base font-semibold">
                  {blocking.length} {blocking.length === 1 ? "thing" : "things"} to sort out first
                </h2>
                <span className="text-[12.5px] text-muted">Fix these, then check again</span>
              </div>
              {blocking.map((f) => (
                <FindingCard key={`${f.rule_id}-${f.title}`} finding={f} />
              ))}
            </section>
          ) : null}

          <section aria-labelledby="headsup-heading" className="flex flex-col gap-3">
            <h2 id="headsup-heading" className="text-base font-semibold">
              Heads-ups <span className="font-normal text-muted">· {headsUps.length}</span>
            </h2>
            {headsUps.length ? (
              headsUps.map((f) => <FindingCard key={`${f.rule_id}-${f.title}`} finding={f} />)
            ) : (
              <Card className="p-4 text-[13px] text-muted">Nothing to review — everything converts cleanly.</Card>
            )}
          </section>
        </div>

        <div className="flex flex-col gap-5">
          <Card>
            <CardHeader title="What we found" />
            <Stat label="Tables" value={formatCount(a.tables)} />
            <Stat label="Columns" value={formatCount(a.columns)} />
            <Stat label="Rows (est.)" value={formatCount(a.total_rows)} />
            <Stat label="Data" value={formatBytes(a.total_bytes)} />
            <Stat label="Complexity" value={`${a.score}/100 · ${a.level}`} />
            <Stat label="Effort" value={`${a.effort_days_min}–${a.effort_days_max} engineer-days`} />
          </Card>
          <Card>
            <CardHeader title="Share the report" description="A plain-English summary for your manager or change board." />
            <a
              href={api.migrations.reportUrl(m.id)}
              download
              className="inline-flex h-[34px] items-center gap-2 rounded-control border border-line px-3.5 text-[13.5px] font-medium hover:bg-hover"
            >
              <Download className="size-4" /> Download report (.md)
            </a>
          </Card>
        </div>
      </div>

      <div className="mt-6 flex items-center gap-2 border-t border-line pt-5">
        <Button variant="ghost" onClick={() => navigate("/migrations")}>
          <ArrowLeft /> All migrations
        </Button>
        <span className="flex-1" />
        {rerunButton}
        <Button variant="primary" disabled title="The Settings step arrives in Sprint 3">
          Continue to settings <ArrowRight />
        </Button>
      </div>
      <p className="mt-2 text-right text-[12px] text-muted">
        {a.ready ? "Settings (type choices) arrive in Sprint 3." : "Resolve the items above, then check again."}
      </p>
    </>
  );
}
