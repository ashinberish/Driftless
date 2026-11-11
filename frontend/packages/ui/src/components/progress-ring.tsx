import type { ReactNode } from "react";

import { cn } from "../lib/cn";

export interface ProgressRingProps {
  /** 0-100; clamped. */
  value: number;
  size?: number;
  stroke?: number;
  label: string;
  /** Centre content; defaults to the percentage. */
  children?: ReactNode;
  tone?: "progress" | "success" | "warning" | "danger";
  className?: string;
}

const TONE = {
  progress: "stroke-accent",
  success: "stroke-success",
  warning: "stroke-warning",
  danger: "stroke-danger",
} as const;

/** Circular progress for headline numbers (readiness, copy progress). Solid colours only. */
export function ProgressRing({
  value,
  size = 140,
  stroke = 12,
  label,
  children,
  tone = "progress",
  className,
}: ProgressRingProps) {
  const pct = Math.min(100, Math.max(0, value));
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(pct)}
      className={cn("relative shrink-0", className)}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" strokeWidth={stroke} className="stroke-line-soft" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - pct / 100)}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          className={TONE[tone]}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        {children ?? <span className="text-2xl font-bold tracking-tight">{Math.round(pct)}%</span>}
      </div>
    </div>
  );
}
