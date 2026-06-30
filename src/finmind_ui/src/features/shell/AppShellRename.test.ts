import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";

const source = readFileSync("src/features/shell/AppShell.tsx", "utf8");

assert.match(source, /onBlur=\{commitRename\}/);
assert.match(source, /event\.currentTarget\.blur\(\)/);
assert.doesNotMatch(source, /aria-label="Save name"/);
assert.doesNotMatch(source, /aria-label="Cancel rename"/);
