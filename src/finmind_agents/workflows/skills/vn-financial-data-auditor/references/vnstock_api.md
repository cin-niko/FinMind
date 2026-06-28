# vnstock API Reference For FinMind VN Data Collection

Use vnstock before web scraping for VN workflow data collection.

Primary data families:

- Quote/history: price, volume, and VNINDEX comparison data.
- Finance: income statement, balance sheet, cash flow, and ratios.
- Company: overview, market cap, issue shares, news, events, shareholders, and
  capital history where available.
- Listing: symbol and industry reference data.

Provider rules:

- Prefer VCI for broad quote, finance, company, and listing coverage.
- Use KBS where capital history or shareholder data is unavailable through VCI.
- Keep provider source identity in every normalized field group.
- Do not expose raw provider payloads in user-facing output.

Normalization reminders:

- Price units may vary by vnstock interface. Normalize final user-facing values
  with explicit units.
- Financial statement values must include clear units such as `b_vnd`, `vnd`, or
  `percent`.
- Ratio tables may be report-oriented with metric rows and period columns.
- News/events require publication timestamps and source references.

Failure handling:

- Provider API changes must produce a provider warning, not fabricated data.
- Missing API keys, rate limits, unsupported symbols, and stale data must mark
  affected claim categories unavailable.
