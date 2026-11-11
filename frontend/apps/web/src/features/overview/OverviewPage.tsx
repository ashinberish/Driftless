import { Button, Card, CardHeader, EngineBadge, PageHeader, ProgressBar } from "@driftless/ui";
import { ArrowRight, Download, Flag, Plus } from "lucide-react";
import { Link, useNavigate } from "react-router";

import { MigrationStatusBadge } from "@/features/migrations/components/MigrationStatusBadge";
import { SAMPLE_MIGRATIONS } from "./sample-data";

export function OverviewPage() {
  const navigate = useNavigate();
  const active = SAMPLE_MIGRATIONS.filter((m) => m.status !== "live" && m.status !== "draft");
  return (
    <>
      <PageHeader
        eyebrow="Data Platform workspace · sample data"
        title="Good afternoon, Maya"
        description={`${active.length} migrations in flight · 18.4 TB moved this month`}
        actions={
          <>
            <Button>
              <Download /> Export program report
            </Button>
            <Button variant="primary" size="lg" onClick={() => navigate("/migrations/new")}>
              <Plus /> New migration
            </Button>
          </>
        }
      />

      <Card className="mb-6 flex items-center gap-4">
        <span className="grid size-10 place-items-center rounded-full border border-line text-warning">
          <Flag className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="text-[11px] font-medium uppercase tracking-wider text-warning">Needs you</div>
          <div className="font-semibold text-ink">billing-db is ready to go live</div>
          <div className="text-[13px] text-muted">
            All 4.21 B rows match. One approval left from Finance Apps.
          </div>
        </div>
        <Button variant="primary">
          Review &amp; go live <ArrowRight />
        </Button>
      </Card>

      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold">Your migrations</h2>
        <Link to="/migrations" className="text-[13px] font-medium text-accent">
          View all →
        </Link>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {SAMPLE_MIGRATIONS.slice(0, 6).map((m) => (
          <Card key={m.id}>
            <CardHeader title={m.name} actions={<MigrationStatusBadge status={m.status} />} />
            <div className="mb-4 flex items-center gap-2">
              <EngineBadge engine={m.sourceEngine} showLabel />
              <ArrowRight className="size-3.5 text-muted" aria-hidden />
              <EngineBadge engine={m.targetEngine} showLabel />
            </div>
            <ProgressBar value={m.progress} label={`${m.name} progress`} />
            <div className="mt-3 flex justify-between text-[12.5px] text-muted">
              <span>{m.progress}% complete</span>
              <span>{m.team}</span>
            </div>
          </Card>
        ))}
      </div>
    </>
  );
}
