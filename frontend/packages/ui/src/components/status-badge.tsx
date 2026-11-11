import type { HTMLAttributes } from "react";

import { cn } from "../lib/cn";

export type StatusTone = "neutral" | "success" | "warning" | "danger" | "info" | "progress";

const DOT: Record<StatusTone, string> = {
  neutral: "bg-faint",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
  info: "bg-info",
  progress: "bg-accent",
};

export interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: StatusTone;
}

/** Neutral outlined badge with a colored status dot — color carries meaning, not decoration. */
export function StatusBadge({ tone = "neutral", className, children, ...props }: StatusBadgeProps) {
  return (
    <span
      data-tone={tone}
      className={cn(
        "inline-flex h-[22px] items-center gap-1.5 whitespace-nowrap rounded-md border border-line bg-surface px-2 text-xs font-medium text-ink-2",
        className,
      )}
      {...props}
    >
      <span aria-hidden className={cn("size-1.5 rounded-full", DOT[tone])} />
      {children}
    </span>
  );
}
