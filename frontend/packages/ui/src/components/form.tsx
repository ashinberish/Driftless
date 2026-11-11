import { ChevronDown } from "lucide-react";
import {
  forwardRef,
  useId,
  type InputHTMLAttributes,
  type ReactElement,
  type ReactNode,
  type SelectHTMLAttributes,
} from "react";

import { cn } from "../lib/cn";

const control =
  "h-[38px] w-full rounded-control border border-line bg-surface px-3 text-[13.5px] text-ink " +
  "placeholder:text-faint focus:border-ink-2 focus:outline-none focus:ring-2 focus:ring-accent/15 " +
  "disabled:cursor-not-allowed disabled:bg-subtle aria-[invalid=true]:border-danger";

export interface FieldProps {
  label: ReactNode;
  hint?: ReactNode;
  error?: string;
  required?: boolean;
  className?: string;
  /** Receives the generated id + aria props so label, hint and error stay linked. */
  children: (control: {
    id: string;
    "aria-invalid": boolean;
    "aria-describedby"?: string;
  }) => ReactElement;
}

/** Label + control + hint/error, wired for screen readers. */
export function Field({ label, hint, error, required, className, children }: FieldProps) {
  const id = useId();
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined;
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label htmlFor={id} className="text-[12.5px] font-semibold text-ink-2">
        {label}
        {required ? <span className="text-danger"> *</span> : null}
      </label>
      {children({ id, "aria-invalid": Boolean(error), "aria-describedby": describedBy })}
      {error ? (
        <p id={`${id}-error`} role="alert" className="text-[12px] text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-[12px] text-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  leading?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, leading, ...props }, ref) =>
    leading ? (
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted [&_svg]:size-4">
          {leading}
        </span>
        <input ref={ref} className={cn(control, "pl-9", className)} {...props} />
      </div>
    ) : (
      <input ref={ref} className={cn(control, className)} {...props} />
    ),
);
Input.displayName = "Input";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <div className="relative">
      <select ref={ref} className={cn(control, "appearance-none pr-9", className)} {...props}>
        {children}
      </select>
      <ChevronDown
        aria-hidden
        className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-muted"
      />
    </div>
  ),
);
Select.displayName = "Select";
