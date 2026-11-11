import { Check, Copy, TriangleAlert, X } from "lucide-react";
import { useState } from "react";

import { cn } from "../lib/cn";
import { Button } from "./button";

export type CheckItemStatus = "ok" | "warning" | "failed";

export interface CheckItem {
  name: string;
  status: CheckItemStatus;
  detail?: string | null;
  fixScript?: string | null;
}

const ICON = {
  ok: { Icon: Check, className: "text-success" },
  warning: { Icon: TriangleAlert, className: "text-warning" },
  failed: { Icon: X, className: "text-danger" },
} as const;

export interface CheckListProps {
  items: CheckItem[];
  className?: string;
}

/** Pre-flight results: one line per check, with a copyable fix when we have one. */
export function CheckList({ items, className }: CheckListProps) {
  return (
    <ul className={cn("divide-y divide-line-soft", className)} aria-label="Connection checks">
      {items.map((item) => (
        <CheckRow key={item.name} item={item} />
      ))}
    </ul>
  );
}

function CheckRow({ item }: { item: CheckItem }) {
  const [copied, setCopied] = useState(false);
  const { Icon, className } = ICON[item.status];
  return (
    <li className="flex items-start gap-3 py-2.5" data-status={item.status}>
      <span
        className={cn("mt-0.5 grid size-6 shrink-0 place-items-center rounded-full border border-line", className)}
      >
        <Icon className="size-3.5" strokeWidth={2.6} aria-label={item.status} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="text-[13.5px] font-semibold text-ink">{item.name}</div>
        {item.detail ? <div className="text-[12.5px] break-words text-muted">{item.detail}</div> : null}
      </div>
      {item.fixScript ? (
        <Button
          size="sm"
          onClick={() => {
            void navigator.clipboard?.writeText(item.fixScript ?? "");
            setCopied(true);
          }}
        >
          <Copy /> {copied ? "Copied" : "Copy fix"}
        </Button>
      ) : null}
    </li>
  );
}
