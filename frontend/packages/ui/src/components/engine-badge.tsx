import { cn } from "../lib/cn";

const ENGINES: Record<string, { label: string; short: string; color: string }> = {
  postgres: { label: "PostgreSQL", short: "PG", color: "bg-engine-postgres" },
  mysql: { label: "MySQL", short: "MY", color: "bg-engine-mysql" },
  sqlserver: { label: "SQL Server", short: "MS", color: "bg-engine-sqlserver" },
  oracle: { label: "Oracle", short: "OR", color: "bg-engine-oracle" },
};

export interface EngineBadgeProps {
  engine: string;
  /** Show the engine name (and optional version) next to the mark. */
  showLabel?: boolean;
  version?: string;
  size?: "sm" | "md";
  className?: string;
}

export function EngineBadge({ engine, showLabel, version, size = "sm", className }: EngineBadgeProps) {
  const meta = ENGINES[engine] ?? { label: engine, short: engine.slice(0, 2).toUpperCase(), color: "bg-faint" };
  return (
    <span className={cn("inline-flex items-center gap-1.5", className)}>
      <span
        aria-hidden={showLabel ? true : undefined}
        title={meta.label}
        className={cn(
          "grid place-items-center font-bold text-white",
          meta.color,
          size === "sm" ? "size-6 rounded-[7px] text-[9px]" : "size-8 rounded-[9px] text-[11px]",
        )}
      >
        {meta.short}
      </span>
      {showLabel ? (
        <span className="text-[13px] text-ink-2">
          {meta.label}
          {version ? ` ${version}` : ""}
        </span>
      ) : (
        <span className="sr-only">{meta.label}</span>
      )}
    </span>
  );
}
