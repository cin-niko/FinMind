import type { LucideIcon } from "lucide-react";
import { MessageSquarePlus } from "lucide-react";

export type PrimaryView = "chat";

export type PrimaryNavItem = {
  view: PrimaryView;
  label: string;
  iconName: string;
  Icon: LucideIcon;
};

export const PRIMARY_NAV_ITEMS: PrimaryNavItem[] = [
  { view: "chat", label: "New Chat", iconName: "MessageSquarePlus", Icon: MessageSquarePlus }
];
