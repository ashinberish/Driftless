import { cn } from "../lib/cn";

export type ProgressTone = "progress" | "success" | "danger";

const FILL: Record<ProgressTone, string> = {
  progress: "bg-accent",
  success: "bg-success",
  danger: "bg-danger",
};

export interface ProgressBarProps {
  /** 0-100; values outside the range are clamped. */
  value: number;
  tone?: ProgressTone;
  label?: string;
  className?: string;
}

export function ProgressBar({ value, tone = "progress", label, className }: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, value));
  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(pct)}
      aria-label={label}
      className={cn("h-1.5 w-full overflow-hidden rounded-full bg-line-soft", className)}
    >
      <div className={cn("h-full rounded-full", FILL[tone])} style={{ width: `${pct}%` }} />
    </div>
  );
}
