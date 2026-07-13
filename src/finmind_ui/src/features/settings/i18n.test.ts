import { strict as assert } from "node:assert";
import { resolveLanguageSelection } from "./language.ts";
import { translate, workflowStepTitle } from "./catalog.ts";

assert.equal(resolveLanguageSelection("auto", ["vi-VN", "en-US"]), "vi");
assert.equal(resolveLanguageSelection("auto", ["fr-FR", "en-US"]), "en");
assert.equal(resolveLanguageSelection("auto", ["fr-FR"]), "en");
assert.equal(resolveLanguageSelection("vi", ["en-US"]), "vi");

assert.equal(translate("vi", "working"), "Đang xử lý");
assert.equal(translate("vi", "completedSteps", { count: 3 }), "Đã hoàn tất 3 bước");
assert.equal(workflowStepTitle("vi", "collect_data", "VN_STOCK"), "Thu thập dữ liệu cổ phiếu VN");
assert.equal(workflowStepTitle("en", "vn-technical-analysis"), "Analyze technical momentum");
assert.equal(workflowStepTitle("vi", "future-stage"), "Future Stage");
