import { strict as assert } from "node:assert";
import { MARKET_INSTRUMENTS, getInstrumentBySymbol } from "./marketData";

assert.ok(MARKET_INSTRUMENTS.some((instrument) => instrument.market === "VN_STOCK"));
assert.ok(MARKET_INSTRUMENTS.some((instrument) => instrument.market === "GOLD"));
assert.equal(
  MARKET_INSTRUMENTS.some((instrument) => instrument.summary.toLowerCase().includes("recommend")),
  false
);

const vcb = getInstrumentBySymbol("VCB");
assert.equal(vcb?.symbol, "VCB");
assert.ok(vcb?.priceSeries.length);
