import { cn } from "../lib/cn";

export interface SegmentedTab {
  id: string;
  label: string;
  count?: number;
}

export interface SegmentedTabsProps {
  tabs: SegmentedTab[];
  value: string;
  onChange: (id: string) => void;
  className?: string;
  "aria-label"?: string;
}

/** Filled segmented control — the active tab is a white pill, no underline. */
export function SegmentedTabs({ tabs, value, onChange, className, ...aria }: SegmentedTabsProps) {
  return (
    <div
      role="tablist"
      aria-label={aria["aria-label"]}
      className={cn("inline-flex gap-0.5 rounded-xl bg-subtle p-[3px]", className)}
    >
      {tabs.map((tab) => {
        const active = tab.id === value;
        return (
          <button
            key={tab.id}
            role="tab"
            type="button"
            aria-selected={active}
            onClick={() => onChange(tab.id)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-[9px] px-3 py-1.5 text-[13.5px] font-semibold transition-colors",
              active ? "bg-surface text-ink ring-1 ring-line" : "text-muted hover:text-ink",
            )}
          >
            {tab.label}
            {tab.count !== undefined ? (
              <span className="text-[11.5px] font-medium text-muted">{tab.count}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
