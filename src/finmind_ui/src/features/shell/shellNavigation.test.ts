import { strict as assert } from "node:assert";
import { HISTORY_SECTIONS, PRIMARY_NAV_ITEMS } from "./shellNavigation";

assert.deepEqual(
  PRIMARY_NAV_ITEMS.map((item) => item.label),
  ["New Chat", "Workflows"]
);

assert.equal(
  PRIMARY_NAV_ITEMS.some((item) => item.label === "Market"),
  false,
  "Market nav stays hidden until a bounded feature spec makes it active"
);

assert.deepEqual(
  HISTORY_SECTIONS.map((section) => section.label),
  ["Chat", "Workflow Runs"]
);

assert.equal(PRIMARY_NAV_ITEMS.every((item) => item.iconName.length > 0), true);
