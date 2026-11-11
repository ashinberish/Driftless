import type { NavGroup } from "@driftless/ui";
import {
  Activity,
  CreditCard,
  Database,
  FileText,
  Globe,
  House,
  List,
  Lock,
  Server,
  Settings,
  ShieldCheck,
} from "lucide-react";

/** Sidebar is configuration, not markup: add a feature by adding an entry here + a route. */
export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Workspace · Data Platform",
    items: [
      { id: "overview", label: "Overview", href: "/", icon: <House /> },
      { id: "migrations", label: "Migrations", href: "/migrations", icon: <Database />, count: 24 },
      { id: "approvals", label: "Approvals", href: "/approvals", icon: <ShieldCheck />, count: 2, attention: true },
      { id: "runs", label: "Live runs", href: "/runs", icon: <Activity />, count: 5 },
      { id: "reports", label: "Reports", href: "/reports", icon: <FileText /> },
    ],
  },
  {
    label: "Infrastructure",
    items: [
      { id: "connections", label: "Connections", href: "/connections", icon: <Server /> },
      { id: "regions", label: "Regions", href: "/regions", icon: <Globe /> },
    ],
  },
  {
    label: "Governance",
    items: [
      { id: "audit", label: "Audit log", href: "/audit", icon: <List /> },
      { id: "policies", label: "Policies", href: "/policies", icon: <Lock /> },
    ],
  },
  {
    label: "Organization",
    items: [
      { id: "settings", label: "Settings & access", href: "/settings", icon: <Settings /> },
      { id: "billing", label: "Usage & billing", href: "/billing", icon: <CreditCard /> },
    ],
  },
];
