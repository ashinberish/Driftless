import type { Finding } from "@driftless/api-client";
import { Card, StatusBadge } from "@driftless/ui";
import { ChevronRight, Sparkles } from "lucide-react";

import { SEVERITY_TONE } from "../model";

const MAX_SHOWN = 50;

/** One finding with plain-language detail, a recommendation and the affected objects. */
export function FindingCard({ finding }: { finding: Finding }) {
  const objects = finding.objects ?? [];
  return (
    <Card className="p-4" data-rule={finding.rule_id}>
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-ink">{finding.title}</h3>
            {finding.auto_fixable ? (
              <StatusBadge tone="info">
                <Sparkles className="size-3" aria-hidden /> Fix available
              </StatusBadge>
            ) : null}
          </div>
          <p className="mt-1 text-[13px] text-muted">{finding.detail}</p>
          {finding.recommendation ? (
            <p className="mt-2 text-[13px] text-ink-2">
              <span className="font-semibold">Recommended:</span> {finding.recommendation}
            </p>
          ) : null}
          {objects.length > 0 ? (
            <details className="group mt-2">
              <summary className="inline-flex cursor-pointer list-none items-center gap-1 text-[12.5px] font-medium text-accent">
                <ChevronRight className="size-3.5 transition-transform group-open:rotate-90" aria-hidden />
                {objects.length} affected {objects.length === 1 ? "object" : "objects"}
              </summary>
              <ul className="mt-2 flex flex-wrap gap-1.5">
                {objects.slice(0, MAX_SHOWN).map((o) => (
                  <li key={o} className="rounded-md bg-subtle px-2 py-0.5 font-mono text-[11.5px] text-ink-2">
                    {o}
                  </li>
                ))}
                {objects.length > MAX_SHOWN ? (
                  <li className="px-2 py-0.5 text-[11.5px] text-muted">and {objects.length - MAX_SHOWN} more</li>
                ) : null}
              </ul>
            </details>
          ) : null}
        </div>
        <StatusBadge tone={SEVERITY_TONE[finding.severity]} className="capitalize">
          {finding.severity}
        </StatusBadge>
      </div>
    </Card>
  );
}
