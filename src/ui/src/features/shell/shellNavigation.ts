import type { LucideIcon } from "lucide-react";
import { MessageSquarePlus, Workflow } from "lucide-react";

export type PrimaryView = "chat" | "market" | "workflows" | "admin";

export type PrimaryNavItem = {
  view: PrimaryView;
  label: string;
  iconName: string;
  Icon: LucideIcon;
};

export const PRIMARY_NAV_ITEMS: PrimaryNavItem[] = [
  { view: "chat", label: "New Chat", iconName: "MessageSquarePlus", Icon: MessageSquarePlus },
  { view: "workflows", label: "Workflows", iconName: "Workflow", Icon: Workflow }
];

export const HISTORY_SECTIONS = [
  { id: "chat", label: "Chat" },
  { id: "workflowRuns", label: "Workflow Runs" }
] as const;
