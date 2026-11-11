import { Check } from "lucide-react";

import { cn } from "../lib/cn";

export interface Step {
  id: string;
  label: string;
  hint?: string;
}

export interface StepperProps {
  steps: Step[];
  /** id of the current step; earlier steps render as done. */
  current: string;
  className?: string;
}

export function Stepper({ steps, current, className }: StepperProps) {
  const currentIndex = Math.max(
    0,
    steps.findIndex((s) => s.id === current),
  );
  return (
    <ol
      className={cn("flex items-center gap-1 rounded-card border border-line bg-surface p-1.5", className)}
    >
      {steps.map((step, i) => {
        const state = i < currentIndex ? "done" : i === currentIndex ? "current" : "todo";
        return (
          <li
            key={step.id}
            aria-current={state === "current" ? "step" : undefined}
            data-state={state}
            className={cn(
              "flex flex-1 items-center gap-2.5 rounded-md px-3 py-2 text-[13.5px] font-medium",
              state === "current" ? "bg-subtle text-ink" : "text-muted",
              state === "done" && "text-ink-2",
            )}
          >
            <span
              className={cn(
                "grid size-6 shrink-0 place-items-center rounded-full border text-xs",
                state === "current" && "border-ink bg-ink text-white",
                state === "done" && "border-line bg-surface text-success",
                state === "todo" && "border-line",
              )}
            >
              {state === "done" ? <Check className="size-3.5" strokeWidth={2.6} /> : i + 1}
            </span>
            <span className="min-w-0 leading-tight">
              {step.label}
              {step.hint ? (
                <span className="block text-[11.5px] font-normal text-muted">{step.hint}</span>
              ) : null}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
