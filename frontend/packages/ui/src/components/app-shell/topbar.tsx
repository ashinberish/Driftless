import { Bell, CircleHelp, Search } from "lucide-react";
import { Fragment, type ReactNode } from "react";

export interface TopbarProps {
  breadcrumbs: string[];
  /** Left of the search box: environment / region switchers, etc. */
  context?: ReactNode;
  actions?: ReactNode;
}

export function Topbar({ breadcrumbs, context, actions }: TopbarProps) {
  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-line bg-surface px-8">
      <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-2 text-[13.5px] text-muted">
        {breadcrumbs.map((crumb, i) => {
          const last = i === breadcrumbs.length - 1;
          return (
            <Fragment key={`${crumb}-${i}`}>
              {i > 0 ? <span className="text-faint">/</span> : null}
              <span className={last ? "truncate font-semibold text-ink" : "truncate"} aria-current={last ? "page" : undefined}>
                {crumb}
              </span>
            </Fragment>
          );
        })}
      </nav>
      <div className="ml-auto flex items-center gap-2">
        {context}
        <button
          type="button"
          className="flex h-[34px] w-64 items-center gap-2 rounded-control border border-line bg-surface px-3 text-muted"
        >
          <Search className="size-4" aria-hidden />
          <span className="flex-1 text-left">Search…</span>
          <kbd className="rounded-md border border-line px-1.5 text-[11px]">⌘K</kbd>
        </button>
        {actions}
        <button type="button" aria-label="Help" className="grid size-[34px] place-items-center rounded-control text-muted hover:bg-hover">
          <CircleHelp className="size-[18px]" />
        </button>
        <button type="button" aria-label="Notifications" className="grid size-[34px] place-items-center rounded-control text-muted hover:bg-hover">
          <Bell className="size-[18px]" />
        </button>
      </div>
    </header>
  );
}
