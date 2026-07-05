# Deprecated UI

These components are not rendered by the app and are kept here for future reuse
once richer market-data coverage lands. They were superseded by the chat-based
workflow surface (`features/chat/ArtifactPanel.tsx`, `features/chat/ChatPage.tsx`).

- `market/` — the market data-platform tab (`MarketPage`) and its seeded
  instrument data (`marketData`). Includes `GOLD` scope, which is roadmap-only
  per `AGENTS.md` hard rule 5; do not re-activate without a spec scope change.
- `results/ResultView.tsx` — the standalone workflow result renderer. Result
  rendering now lives in the chat surface; this is preserved as a reference
  layout for a future dedicated results page.

Nothing in `src/` outside this folder imports these files. Keep them out of the
active build graph until a spec re-introduces them.
