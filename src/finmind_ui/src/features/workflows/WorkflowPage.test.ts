import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";

const source = readFileSync("src/features/workflows/WorkflowPage.tsx", "utf8");

assert.match(source, /className="workflowDialog"/);
assert.match(source, /role="dialog"/);
assert.match(source, /selected\.id !== "gold-technical-analysis"/);
assert.doesNotMatch(source, /className="workflowGrid"/);
assert.doesNotMatch(source, /<ArrowLeft/);
