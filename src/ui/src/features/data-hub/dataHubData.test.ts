import { strict as assert } from "node:assert";
import { DATA_HUB_INSTRUMENTS, getInstrumentBySymbol } from "./dataHubData";

assert.ok(DATA_HUB_INSTRUMENTS.some((instrument) => instrument.market === "VN_STOCK"));
assert.ok(DATA_HUB_INSTRUMENTS.some((instrument) => instrument.market === "GOLD"));
assert.equal(
  DATA_HUB_INSTRUMENTS.some((instrument) => instrument.summary.toLowerCase().includes("recommend")),
  false
);

const vcb = getInstrumentBySymbol("VCB");
assert.equal(vcb?.symbol, "VCB");
assert.ok(vcb?.priceSeries.length);
