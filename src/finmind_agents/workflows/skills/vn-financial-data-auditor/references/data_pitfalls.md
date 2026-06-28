# VN Data Pitfalls

VN equity workflows must check these issues before analysis:

1. Share count changes over time can distort EPS, BVPS, PE, and PB.
2. Units can be inconsistent across providers and API surfaces.
3. Net profit must distinguish profit before tax, after tax, and parent-company
   shareholder profit.
4. Search or web sources can surface stale financial periods.
5. Split-adjusted prices and unadjusted per-share metrics can create invalid
   cross-year valuation multiples.
6. Market cap should prefer provider overview data and current issue shares over
   stale manual calculations.
7. Ratio tables can be stale or incomplete for some symbols.

Quality gate implications:

- If share-count or split consistency fails, block valuation-sensitive claims.
- If ratio periods do not cover the expected analysis years, mark ratio-derived
  claims as warning or unavailable.
- If source documents/news are missing, block news and catalyst claims.
- If a metric fails unit sanity checks, do not pass it to analysis as a clean
  evidence field.
