import { useState } from "react";
import { DATA_HUB_INSTRUMENTS } from "./dataHubData";

export function DataHubPage() {
  const [selectedSymbol, setSelectedSymbol] = useState(DATA_HUB_INSTRUMENTS[0]?.symbol ?? "");
  const selected =
    DATA_HUB_INSTRUMENTS.find((instrument) => instrument.symbol === selectedSymbol) ??
    DATA_HUB_INSTRUMENTS[0];

  if (!selected) {
    return <div className="stateBox">No market data available.</div>;
  }

  const maxValue = Math.max(...selected.priceSeries.map((point) => point.value));
  const minValue = Math.min(...selected.priceSeries.map((point) => point.value));

  return (
    <section className="dataHubPage" aria-label="Market">
      <div className="hubSummary">
        {DATA_HUB_INSTRUMENTS.map((instrument) => (
          <button
            className={instrument.symbol === selected.symbol ? "hubCard active" : "hubCard"}
            key={instrument.symbol}
            onClick={() => setSelectedSymbol(instrument.symbol)}
            type="button"
          >
            <span>{instrument.symbol}</span>
            <strong>{instrument.lastPrice}</strong>
            <small className={instrument.changePercent >= 0 ? "up" : "down"}>
              {instrument.changePercent >= 0 ? "+" : ""}
              {instrument.changePercent}%
            </small>
          </button>
        ))}
      </div>
      <div className="hubGrid">
        <section className="panel selectedInstrument">
          <div className="panelHeader">
            <div>
              <h2>{selected.name}</h2>
              <span className="meta">
                {selected.market} · freshness {selected.freshness} · volume {selected.volume}
              </span>
            </div>
            <span className="badge">Real demo data</span>
          </div>
          <p className="dataSummary">{selected.summary}</p>
          <div className="sparkChart" aria-label={`${selected.symbol} price series`}>
            {selected.priceSeries.map((point) => {
              const range = Math.max(maxValue - minValue, 1);
              const height = 24 + ((point.value - minValue) / range) * 86;
              return (
                <span
                  key={point.time}
                  style={{ height: `${height}px` }}
                  title={`${point.time}: ${point.value}`}
                />
              );
            })}
          </div>
        </section>
        <section className="panel">
          <h2>News / Sources</h2>
          <div className="sourceFeed">
            {selected.news.map((item) => (
              <article key={item.id}>
                <h3>{item.title}</h3>
                <span className="meta">
                  {item.source} · {item.timestamp}
                </span>
              </article>
            ))}
          </div>
        </section>
        <section className="panel marketTable">
          <h2>Watchlist</h2>
          <table>
            <thead>
              <tr>
                <th>Instrument</th>
                <th>Market</th>
                <th>Last</th>
                <th>Change</th>
                <th>Freshness</th>
              </tr>
            </thead>
            <tbody>
              {DATA_HUB_INSTRUMENTS.map((instrument) => (
                <tr key={instrument.symbol}>
                  <td>{instrument.symbol}</td>
                  <td>{instrument.market}</td>
                  <td>{instrument.lastPrice}</td>
                  <td className={instrument.changePercent >= 0 ? "up" : "down"}>
                    {instrument.changePercent >= 0 ? "+" : ""}
                    {instrument.changePercent}%
                  </td>
                  <td>{instrument.freshness}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </section>
  );
}
