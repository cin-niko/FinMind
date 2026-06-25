#!/usr/bin/env node
// Discovers and runs every `*.test.ts` script under `src/`.
// The existing UI tests are top-level scripts using `node:assert`, so this
// runner just imports each file in turn under the `tsx` loader.
import { readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

function findTests(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    if (entry === "node_modules" || entry === "dist") {
      continue;
    }
    const full = join(dir, entry);
    const info = statSync(full);
    if (info.isDirectory()) {
      out.push(...findTests(full));
    } else if (entry.endsWith(".test.ts") || entry.endsWith(".test.tsx")) {
      out.push(full);
    }
  }
  return out;
}

const root = resolve(process.cwd(), "src");
const tests = findTests(root).sort();
let failures = 0;
for (const file of tests) {
  try {
    await import(pathToFileURL(file).href);
    console.log(`PASS ${file}`);
  } catch (error) {
    failures += 1;
    console.error(`FAIL ${file}`);
    console.error(error);
  }
}
console.log(`\n${tests.length - failures}/${tests.length} test files passed`);
if (failures > 0) {
  process.exit(1);
}
