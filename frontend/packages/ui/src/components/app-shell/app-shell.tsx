import type { ReactNode } from "react";

import { Sidebar, type SidebarProps } from "./sidebar";
import { Topbar, type TopbarProps } from "./topbar";

export interface AppShellProps {
  sidebar: SidebarProps;
  topbar: TopbarProps;
  children: ReactNode;
}

/** Enterprise app frame: org switcher + grouped nav on the left, breadcrumbs bar on top. */
export function AppShell({ sidebar, topbar, children }: AppShellProps) {
  return (
    <div className="flex h-screen min-h-0 bg-canvas">
      <Sidebar {...sidebar} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar {...topbar} />
        <main className="flex-1 overflow-y-auto px-8 py-7">{children}</main>
      </div>
    </div>
  );
}
