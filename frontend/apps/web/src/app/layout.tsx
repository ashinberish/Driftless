import { AppShell, Button, type RenderLink } from "@driftless/ui";
import { Globe, Sparkles } from "lucide-react";
import { Link, Outlet, useMatches } from "react-router";

import { NAV_GROUPS } from "./navigation";

export interface RouteHandle {
  nav: string;
  crumbs: string[];
}

const renderLink: RenderLink = ({ item, className, children }) => (
  <Link to={item.href} className={className}>
    {children}
  </Link>
);

function useRouteHandle(): RouteHandle {
  const matches = useMatches();
  const handle = [...matches].reverse().find((m) => m.handle)?.handle as RouteHandle | undefined;
  return handle ?? { nav: "", crumbs: ["Driftless"] };
}

export function AppLayout() {
  const { nav, crumbs } = useRouteHandle();
  return (
    <AppShell
      sidebar={{
        org: { name: "Halden Group", plan: "Enterprise · EU tenant" },
        user: { name: "Maya Rivera", role: "Migration Admin", initials: "MR" },
        groups: NAV_GROUPS,
        activeId: nav,
        renderLink,
      }}
      topbar={{
        breadcrumbs: crumbs,
        context: (
          <>
            <Button size="md">
              <span className="size-2 rounded-full bg-danger" aria-hidden /> Production
            </Button>
            <Button size="md">
              <Globe /> eu-central-1
            </Button>
          </>
        ),
        actions: (
          <Button size="sm">
            <Sparkles /> Ask Driftless
          </Button>
        ),
      }}
    >
      <Outlet />
    </AppShell>
  );
}
