import { createBrowserRouter, RouterProvider, type RouteObject } from "react-router";

import { ConnectionDetailPage } from "@/features/connections/ConnectionDetailPage";
import { ConnectionsPage } from "@/features/connections/ConnectionsPage";
import { NewConnectionPage } from "@/features/connections/NewConnectionPage";
import { MigrationsPage } from "@/features/migrations/MigrationsPage";
import { OverviewPage } from "@/features/overview/OverviewPage";
import { ComingSoonPage } from "@/shared/ComingSoonPage";

import { AppLayout, type RouteHandle } from "./layout";

const comingSoon = (path: string, nav: string, crumbs: string[], sprint: string): RouteObject => ({
  path,
  element: <ComingSoonPage title={crumbs.at(-1) ?? ""} sprint={sprint} />,
  handle: { nav, crumbs } satisfies RouteHandle,
});

export const routes: RouteObject[] = [
  {
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <OverviewPage />,
        handle: { nav: "overview", crumbs: ["Data Platform", "Overview"] } satisfies RouteHandle,
      },
      {
        path: "migrations",
        element: <MigrationsPage />,
        handle: { nav: "migrations", crumbs: ["Data Platform", "Migrations"] } satisfies RouteHandle,
      },
      {
        path: "connections",
        element: <ConnectionsPage />,
        handle: { nav: "connections", crumbs: ["Infrastructure", "Connections"] } satisfies RouteHandle,
      },
      {
        path: "connections/new",
        element: <NewConnectionPage />,
        handle: {
          nav: "connections",
          crumbs: ["Infrastructure", "Connections", "New"],
        } satisfies RouteHandle,
      },
      {
        path: "connections/:connectionId",
        element: <ConnectionDetailPage />,
        handle: {
          nav: "connections",
          crumbs: ["Infrastructure", "Connections", "Details"],
        } satisfies RouteHandle,
      },
      comingSoon("approvals", "approvals", ["Data Platform", "Approvals"], "S10"),
      comingSoon("runs", "runs", ["Data Platform", "Live runs"], "S4"),
      comingSoon("reports", "reports", ["Data Platform", "Reports"], "S5"),
      comingSoon("regions", "regions", ["Infrastructure", "Regions"], "S12"),
      comingSoon("audit", "audit", ["Governance", "Audit log"], "S11"),
      comingSoon("policies", "policies", ["Governance", "Policies"], "S10"),
      comingSoon("settings", "settings", ["Organization", "Settings & access"], "S10"),
      comingSoon("billing", "billing", ["Organization", "Usage & billing"], "S15"),
    ],
  },
];

const router = createBrowserRouter(routes);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
