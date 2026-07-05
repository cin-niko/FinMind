import assert from "node:assert/strict";

import { parseSseFrame, parseSseFrames } from "./client";

const buffered = "event: run.stage\ndata: {\"kind\":\"run.stage\"}\n\nevent: answer.delta\ndata: {\"kind\":\"answer.delta\"}\n";
const split = parseSseFrames(buffered);

assert.deepEqual(split.frames, ["event: run.stage\ndata: {\"kind\":\"run.stage\"}"]);
assert.equal(split.remainder, "event: answer.delta\ndata: {\"kind\":\"answer.delta\"}\n");

assert.deepEqual(
  parseSseFrame(
    "event: run.completed\ndata: {\"event_id\":\"evt_0004\",\"run_id\":\"run_1\",\"sequence\":4,\"kind\":\"run.completed\",\"created_at\":\"2026-07-04T00:00:00+00:00\",\"payload\":{\"status\":\"success\",\"run\":{\"id\":\"run_1\"}}}"
  ),
  {
    event_id: "evt_0004",
    run_id: "run_1",
    sequence: 4,
    kind: "run.completed",
    created_at: "2026-07-04T00:00:00+00:00",
    payload: {
      status: "success",
      run: { id: "run_1" }
    }
  }
);
