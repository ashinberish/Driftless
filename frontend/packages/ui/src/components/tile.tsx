import type { ReactNode } from "react";

import { cn } from "../lib/cn";

export interface TileOption {
  value: string;
  label: ReactNode;
  icon?: ReactNode;
  description?: ReactNode;
  disabled?: boolean;
}

export interface TileGroupProps {
  options: TileOption[];
  value: string | null;
  onChange: (value: string) => void;
  "aria-label": string;
  columns?: 2 | 3 | 4;
  className?: string;
}

const COLS = { 2: "grid-cols-2", 3: "grid-cols-3", 4: "grid-cols-4" } as const;

/** Single-choice cards (engine pickers, strategy choices). Keyboard: arrow keys move. */
export function TileGroup({ options, value, onChange, columns = 4, className, ...aria }: TileGroupProps) {
  const enabled = options.filter((o) => !o.disabled);
  const move = (delta: number) => {
    const index = enabled.findIndex((o) => o.value === value);
    const next = enabled[(index + delta + enabled.length) % enabled.length];
    if (next) onChange(next.value);
  };
  return (
    <div
      role="radiogroup"
      aria-label={aria["aria-label"]}
      className={cn("grid gap-2.5", COLS[columns], className)}
      onKeyDown={(e) => {
        if (e.key === "ArrowRight" || e.key === "ArrowDown") {
          e.preventDefault();
          move(1);
        } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
          e.preventDefault();
          move(-1);
        }
      }}
    >
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            disabled={option.disabled}
            tabIndex={selected || (value === null && option === enabled[0]) ? 0 : -1}
            onClick={() => onChange(option.value)}
            className={cn(
              "flex items-center gap-2.5 rounded-control border bg-surface p-3 text-left text-[13px] font-semibold transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/30",
              "disabled:cursor-not-allowed disabled:opacity-50",
              selected ? "border-ink" : "border-line hover:border-faint",
            )}
          >
            {option.icon}
            <span className="min-w-0">
              <span className="block truncate">{option.label}</span>
              {option.description ? (
                <span className="block text-[12px] font-normal text-muted">{option.description}</span>
              ) : null}
            </span>
          </button>
        );
      })}
    </div>
  );
}
