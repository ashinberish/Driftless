import { Card, EmptyState, PageHeader } from "@driftless/ui";
import { Hammer } from "lucide-react";

export function ComingSoonPage({ title, sprint }: { title: string; sprint: string }) {
  return (
    <>
      <PageHeader title={title} />
      <Card>
        <EmptyState
          icon={<Hammer />}
          title="Not built yet"
          description={`This screen is scheduled for sprint ${sprint} in the execution plan.`}
        />
      </Card>
    </>
  );
}
