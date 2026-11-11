import { ChevronsUpDown, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "../../lib/cn";

export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon?: ReactNode;
  count?: number;
  /** Highlight the count (e.g. pending approvals). */
  attention?: boolean;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

export type RenderLink = (props: {
  item: NavItem;
  className: string;
  children: ReactNode;
}) => ReactNode;

const defaultRenderLink: RenderLink = ({ item, className, children }) => (
  <a href={item.href} className={className}>
    {children}
  </a>
);

export interface SidebarProps {
  org: { name: string; plan: string };
  user: { name: string; role: string; initials: string };
  groups: NavGroup[];
  activeId?: string;
  footer?: ReactNode;
  renderLink?: RenderLink;
}

export function Sidebar({
  org,
  user,
  groups,
  activeId,
  footer,
  renderLink = defaultRenderLink,
}: SidebarProps) {
  return (
    <aside className="flex w-[248px] shrink-0 flex-col border-r border-line bg-sidebar">
      <button
        type="button"
        className="mx-3 mt-3 mb-1 flex items-center gap-2.5 rounded-control border border-line bg-surface p-2 text-left"
      >
        <span className="grid size-7 place-items-center rounded-[7px] bg-ink text-xs font-bold text-white">
          {org.name.slice(0, 1)}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[13.5px] font-semibold text-ink">{org.name}</span>
          <span className="block truncate text-[11.5px] text-muted">{org.plan}</span>
        </span>
        <ChevronsUpDown className="size-4 text-muted" aria-hidden />
      </button>

      <nav aria-label="Main" className="flex-1 overflow-y-auto px-3 py-1.5">
        {groups.map((group) => (
          <div key={group.label}>
            <div className="mx-2.5 mt-4 mb-1 text-[10.5px] font-medium uppercase tracking-wider text-faint">
              {group.label}
            </div>
            {group.items.map((item) => {
              const active = item.id === activeId;
              return (
                <div key={item.id}>
                  {renderLink({
                    item,
                    className: cn(
                      "mb-px flex items-center gap-2.5 rounded-[7px] px-2.5 py-1.5 text-[13.5px] text-ink-2",
                      "[&_svg]:size-[17px] [&_svg]:text-muted hover:bg-hover hover:text-ink",
                      active && "bg-selected font-medium text-ink [&_svg]:text-ink",
                    ),
                    children: (
                      <>
                        {item.icon}
                        <span className="flex-1 truncate">{item.label}</span>
                        {item.count !== undefined ? (
                          <span
                            className={cn(
                              "rounded-md px-1.5 text-[11px] font-medium",
                              item.attention ? "bg-warning-soft text-amber-800" : "text-muted",
                            )}
                          >
                            {item.count}
                          </span>
                        ) : null}
                      </>
                    ),
                  })}
                </div>
              );
            })}
          </div>
        ))}
      </nav>

      {footer ?? (
        <div className="mx-3 mb-2.5 flex items-center gap-2 rounded-control border border-line px-3 py-2 text-[11.5px] text-muted">
          <ShieldCheck className="size-4" aria-hidden /> SOC 2 Type II · ISO 27001 · GDPR
        </div>
      )}
      <div className="flex items-center gap-2.5 border-t border-line px-4 py-3.5">
        <span className="grid size-8 place-items-center rounded-full bg-[#e4e4e7] text-xs font-semibold text-ink-2">
          {user.initials}
        </span>
        <span className="min-w-0">
          <span className="block truncate text-[13px] font-semibold text-ink">{user.name}</span>
          <span className="block truncate text-[11.5px] text-muted">{user.role}</span>
        </span>
      </div>
    </aside>
  );
}
