export type MarketScope = "VN_STOCK" | "GOLD";

export type MarketInstrument = {
  symbol: string;
  name: string;
  market: MarketScope;
  lastPrice: string;
  changePercent: number;
  volume: string;
  freshness: string;
  summary: string;
  priceSeries: Array<{ time: string; value: number }>;
  news: Array<{ id: string; title: string; source: string; timestamp: string }>;
};

export const MARKET_INSTRUMENTS: MarketInstrument[] = [
  {
    symbol: "VCB",
    name: "Vietcombank",
    market: "VN_STOCK",
    lastPrice: "86.4",
    changePercent: 1.2,
    volume: "2.1M",
    freshness: "12m",
    summary: "Banking watchlist record with latest seeded/demo price and source metadata.",
    priceSeries: [
      { time: "2026-06-12", value: 84.7 },
      { time: "2026-06-13", value: 85.1 },
      { time: "2026-06-16", value: 85.4 },
      { time: "2026-06-17", value: 85.8 },
      { time: "2026-06-18", value: 86.4 }
    ],
    news: [
      {
        id: "vcb-news-1",
        title: "Banking liquidity improves in latest session",
        source: "Demo Market Feed",
        timestamp: "2026-06-18 09:20"
      },
      {
        id: "vcb-news-2",
        title: "Foreign flow turns positive across large-cap banks",
        source: "Demo Source Wire",
        timestamp: "2026-06-18 08:40"
      }
    ]
  },
  {
    symbol: "FPT",
    name: "FPT Corporation",
    market: "VN_STOCK",
    lastPrice: "117.0",
    changePercent: 0.6,
    volume: "3.8M",
    freshness: "14m",
    summary: "Technology watchlist record with seeded/demo price, volume, and source metadata.",
    priceSeries: [
      { time: "2026-06-12", value: 114.8 },
      { time: "2026-06-13", value: 115.6 },
      { time: "2026-06-16", value: 116.2 },
      { time: "2026-06-17", value: 116.3 },
      { time: "2026-06-18", value: 117.0 }
    ],
    news: [
      {
        id: "fpt-news-1",
        title: "Technology sector turnover remains above five-day average",
        source: "Demo Market Feed",
        timestamp: "2026-06-18 09:05"
      }
    ]
  },
  {
    symbol: "HPG",
    name: "Hoa Phat Group",
    market: "VN_STOCK",
    lastPrice: "28.7",
    changePercent: -0.4,
    volume: "8.9M",
    freshness: "18m",
    summary: "Materials watchlist record with seeded/demo price, volume, and source metadata.",
    priceSeries: [
      { time: "2026-06-12", value: 29.3 },
      { time: "2026-06-13", value: 29.1 },
      { time: "2026-06-16", value: 28.9 },
      { time: "2026-06-17", value: 28.8 },
      { time: "2026-06-18", value: 28.7 }
    ],
    news: [
      {
        id: "hpg-news-1",
        title: "Steel names trade mixed as volume rotates",
        source: "Demo Source Wire",
        timestamp: "2026-06-18 08:55"
      }
    ]
  },
  {
    symbol: "SJC",
    name: "SJC Gold",
    market: "GOLD",
    lastPrice: "75.2M",
    changePercent: 0,
    volume: "Demo",
    freshness: "2h",
    summary: "Gold watchlist record with seeded/demo price and freshness metadata.",
    priceSeries: [
      { time: "2026-06-12", value: 74.6 },
      { time: "2026-06-13", value: 74.8 },
      { time: "2026-06-16", value: 75.0 },
      { time: "2026-06-17", value: 75.2 },
      { time: "2026-06-18", value: 75.2 }
    ],
    news: [
      {
        id: "sjc-news-1",
        title: "Gold spread remains elevated before policy update",
        source: "Demo Gold Feed",
        timestamp: "2026-06-18 08:10"
      },
      {
        id: "sjc-news-2",
        title: "Domestic gold quotes hold steady after morning adjustment",
        source: "Demo Source Wire",
        timestamp: "2026-06-18 07:45"
      }
    ]
  }
];

export function getInstrumentBySymbol(symbol: string): MarketInstrument | undefined {
  return MARKET_INSTRUMENTS.find((instrument) => instrument.symbol === symbol);
}
