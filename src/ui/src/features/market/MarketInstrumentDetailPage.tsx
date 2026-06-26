import { InstrumentChartPanel } from "../charts/InstrumentChartPanel";

type Props = {
  instrumentId: string;
  onBack: () => void;
};

export function MarketInstrumentDetailPage({ instrumentId, onBack }: Props) {
  return (
    <section className="marketPage instrumentDetailPage">
      <div className="detailPageHeader">
        <div>
          <h2>{instrumentId.replace("vn_stock:", "")}</h2>
          <span className="meta">Instrument detail</span>
        </div>
        <button className="textButton compactAction" onClick={onBack} type="button">
          Back to Market
        </button>
      </div>
      <InstrumentChartPanel instrumentId={instrumentId} />
    </section>
  );
}
