import { strict as assert } from "node:assert";
import { renderToStaticMarkup } from "react-dom/server";
import { MarketChart } from "./MarketChart";

const chartArtifact = {
  artifact_id: "art_chart_1",
  artifact_type: "chart",
  chart_intent: "price_trend",
  title: "DXG price chart",
  status: "ready",
  inputs: { dataset_id: "vn_prices", record_key: "VCB-prices" },
  spec: {
    supported_views: ["line", "candlestick"],
    default_view: "line",
    x_axis: { field: "date", type: "time" },
    series: [
      {
        name: "Close",
        type: "line",
        data: [{ date: "2026-06-18", value: 58200 }]
      }
    ],
    candles: [
      {
        date: "2026-06-18",
        open: 58200,
        high: 58200,
        low: 58200,
        close: 58200,
        volume: 4920000
      }
    ]
  },
  downloads: [
    {
      format: "svg",
      url: "/api/artifacts/art_1/download?format=svg",
      filename: "dxg-price-series.svg",
      mime_type: "image/svg+xml"
    }
  ],
  source_refs: ["citation_vn_prices_DXG-prices"]
};

const markup = renderToStaticMarkup(
  <MarketChart artifact={chartArtifact as never} />
);

assert.match(markup, /DXG price chart/);
assert.match(markup, /Line/);
assert.match(markup, /Candlestick/);
assert.match(markup, /Download SVG/);
assert.doesNotMatch(markup, /Data table/);
assert.doesNotMatch(markup, /Chart unavailable/);
