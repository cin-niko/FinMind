import type { LucideIcon } from "lucide-react";
import { BarChart3, DatabaseZap, MessageSquarePlus, Workflow } from "lucide-react";

export type PrimaryView = "chat" | "market" | "workflows" | "admin";

export type PrimaryNavItem = {
  view: PrimaryView;
  label: string;
  iconName: string;
  Icon: LucideIcon;
};

export const PRIMARY_NAV_ITEMS: PrimaryNavItem[] = [
  { view: "chat", label: "New Chat", iconName: "MessageSquarePlus", Icon: MessageSquarePlus },
  { view: "market", label: "Market", iconName: "BarChart3", Icon: BarChart3 },
  { view: "workflows", label: "Workflows", iconName: "Workflow", Icon: Workflow },
  { view: "admin", label: "Admin", iconName: "DatabaseZap", Icon: DatabaseZap }
];

export const HISTORY_SECTIONS = [
  { id: "chat", label: "Chat" },
  { id: "workflowRuns", label: "Workflow Runs" }
] as const;
