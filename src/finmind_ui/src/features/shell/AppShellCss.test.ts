import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";

const styles = readFileSync("src/styles.css", "utf8");

const historySection = styles.match(/\.historySection\s*\{[^}]+\}/)?.[0] ?? "";
assert.match(historySection, /flex:\s*1 1 auto;/);
assert.match(historySection, /grid-template-rows:\s*max-content minmax\(0,\s*1fr\);/);
assert.match(historySection, /overflow-x:\s*hidden;/);
assert.match(historySection, /overflow-y:\s*auto;/);
assert.doesNotMatch(historySection, /overflow:\s*auto;/);

const historyGroup = styles.match(/\.historyGroup\s*\{[^}]+\}/)?.[0] ?? "";
assert.match(historyGroup, /align-content:\s*start;/);
assert.match(historyGroup, /overflow-x:\s*hidden;/);

const historyActions = styles.match(/\.historyActions\s*\{[^}]+\}/)?.[0] ?? "";
assert.match(historyActions, /top:\s*0;/);
assert.match(historyActions, /bottom:\s*0;/);
assert.doesNotMatch(historyActions, /transform:/);

const historyMenu = styles.match(/\.historyMenu\s*\{[^}]+\}/)?.[0] ?? "";
assert.match(historyMenu, /position:\s*fixed;/);
assert.match(historyMenu, /z-index:\s*80;/);
assert.match(historyMenu, /width:\s*min\(150px,\s*calc\(100vw - 24px\)\);/);

const historyMenuItem = styles.match(/\.historyMenuItem\s*\{[^}]+\}/)?.[0] ?? "";
assert.match(historyMenuItem, /min-height:\s*30px;/);
assert.match(historyMenuItem, /font-size:\s*12px;/);
