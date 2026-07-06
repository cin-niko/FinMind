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

const completedWithArtifact = parseSseFrame(
  'event: run.completed\ndata: {"event_id":"evt_0005","run_id":"run_1","sequence":5,"kind":"run.completed","created_at":"2026-07-04T00:00:00+00:00","payload":{"status":"success","run":{"id":"run_1","output":{"artifacts":[{"artifact_id":"art_1","artifact_type":"chart","chart_intent":"price_trend","title":"DXG price chart","status":"ready","inputs":{},"spec":{"supported_views":["line","candlestick"],"default_view":"line","x_axis":{"field":"date","type":"time"},"series":[],"candles":[]},"downloads":[{"format":"svg","url":"/api/artifacts/art_1/download?format=svg","filename":"dxg.svg","mime_type":"image/svg+xml"}],"source_refs":["cite_1"]}]}}}}'
);
assert.ok(completedWithArtifact);
const completedPayload = completedWithArtifact.payload as {
  run: { output: { artifacts: unknown[] } };
};

assert.deepEqual(
  completedPayload.run.output.artifacts[0],
  {
    artifact_id: "art_1",
    artifact_type: "chart",
    chart_intent: "price_trend",
    title: "DXG price chart",
    status: "ready",
    inputs: {},
    spec: {
      supported_views: ["line", "candlestick"],
      default_view: "line",
      x_axis: { field: "date", type: "time" },
      series: [],
      candles: []
    },
    downloads: [
      {
        format: "svg",
        url: "/api/artifacts/art_1/download?format=svg",
        filename: "dxg.svg",
        mime_type: "image/svg+xml"
      }
    ],
    source_refs: ["cite_1"]
  }
);
