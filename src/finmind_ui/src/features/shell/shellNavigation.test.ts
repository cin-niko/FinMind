import { strict as assert } from "node:assert";
import { PRIMARY_NAV_ITEMS } from "./shellNavigation";

assert.deepEqual(
  PRIMARY_NAV_ITEMS.map((item) => item.label),
  ["New Chat"]
);

assert.equal(
  PRIMARY_NAV_ITEMS.some((item) => item.label === "Market"),
  false,
  "Market nav stays hidden until a bounded feature spec makes it active"
);

assert.equal(PRIMARY_NAV_ITEMS.every((item) => item.iconName.length > 0), true);
