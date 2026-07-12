# Notes: Pattern Detection + Citation Content (work-in-progress, paused)

> Tạm lưu kết quả brainstorm/decision. Chưa implement. Quay lại sau.
> Created: 2026-07-07. Context: refine UIUX citation/artifact flow → dẫn tới
> thiết kế citation content + deterministic pattern detection cho technical skill.

## 1. Citation content (right panel show content, không chỉ id/date)

### Hiện trạng
- `build_citations(records)` (`src/finmind_agents/workflows/citations.py`) tạo Citation
  chỉ 5 trường: `citation_id, source_id, dataset_id, label, timestamp` (label = `{source_id} {date}`).
- `run.output.citations` (JSONB bảng `runs.data`) chỉ persist 5 trường đó. **Record payload
  và SourceDocument KHÔNG persist** — chỉ `collection` (metadata) + `citations` + `artifacts` + `grounding`.
- Records là ephemeral (chỉ truyền vào agent context rồi bỏ).
- Hiện CHƯA có citation từ `SourceDocument` (news/document) — không có `SourceDocument(...)`
  nào trong agents; `news` provider là stub.

### Quyết định
- Citation content trong panel = **chính payload đã deliver cho skill** (cái LLM thấy), không phải raw record.
- Persist `content` vào `run.output.citations[i].content` (cùng JSONB) + mirror vào streaming
  `citation` event → live inspect + history reinspect đều hoạt động.
- `content` là discriminated union theo `view` (canonical, deterministic, không raw provider schema):
  - `price_summary` = year-end summary (`year_end_prices`) — đúng fundamental skill thấy
  - `indicator_table` = full indicator dict — đúng technical skill thấy
  - `fundamental_row` = full fundamental payload/kỳ
  - `company_profile` = full profile
  - `document` = title/published_at/url/excerpt/sentiment (giữ sẵn schema, news chưa bật)
- Price là loại duy nhất cần tóm lược (full ~90KB/750 bar → ~0.4KB); 3 loại kia vốn nhỏ, lưu gần nguyên.
- Một run ~4–6 citations → thêm ~2–5KB JSONB, không đáng kể.

### Open
- Citation content gắn payload-delivered-per-citation hay canonical-per-dataset? (đề xuất delivered-per-citation).
- Price: giữ year-end summary (đúng model thấy) hay thêm recent bars cho panel? (đề xuất giữ + chart artifact đảm nhận raw).

## 2. Pattern detection cho technical skill (deterministic, không vision)

### Vì sao raw price series không đưa vào LLM
- Technical: indicator tính deterministic bởi `compute_indicators`; LLM chỉ diễn giải. SKILL.md cấm
  "compute indicators from raw data" + "never fabricate/simulate price data". Raw 750 bar → LLM tự tính = hallucination risk.
- Fundamental: raw series là nhiễu; dùng year-end summary (~3 bar). Nguyên tắc chung: compute deterministic, LLM interpret.

### Vì sao KHÔNG dùng gen-ảnh → vision LLM
- Ta đã có số; chart là hình vẽ của số → vision là proxy lossy. Hallucination + non-deterministic,
  grounding/citation vỡ (perception không có nguồn canonical), cost/latency. Chart artifact đã render cho USER xem.
- Vision chỉ hợp lý khi không có structured data (screenshot/filing ảnh) — Phase khác.

### Quyết định
- Port pattern detection + scoring thành **deterministic Python trong `compute_indicators`**
  (không LLM-reasoned, không vision). LLM chỉ interpret pre-computed `patterns`.
- Scope: **cả detection (`pattern_detection.md`) + scoring (`pattern_scoring.md`)**.
- PROFILE mode reachable: **để sau** (002-workflow chỉ input market+symbol → luôn default ACTIVE;
  PROFILE cần 003-chatflow hoặc thêm input `mode`/`question`).

### Reference sources (đã có sẵn trong skill folder canonical)
- `src/finmind_agents/workflows/skills/vn-technical-analysis/references/pattern_detection.md`
  (rules: swing, double top/bottom, channel, candlestick, divergence, verdict table, honesty rule).
- `src/finmind_agents/workflows/skills/vn-technical-analysis/references/pattern_scoring.md`
  (Python daily: 8 setup heuristic + setup()/status + pattern_family + archetype + helpers pct/slope/clamp).
- Bản `equity-research-vn/.../references/` là working copy untracked, hơi khác — dùng bản canonical trong `src/`.

### Slope: "percent-slope" = cách `pattern_scoring` đã làm
- `slope(values)` = regression coefficient (đơn vị giá) — chỉ dùng cho **dấu (hướng)**.
- Mọi độ lớn dùng `pct(a,b) = (a/b-1)*100`.
- Legacy `pattern_detection` channel dùng absolute `>100 đ` (weekly) → khi port sang daily thay bằng `pct()`.

### Tách setup vs pattern: KHÔNG tách — gộp 1 list `patterns` có `kind`
- Lý do: 1 record/1 skill/2 mode cùng consume; tránh contradiction double_bottom (2 reference định nghĩa
  khác nhau); ACTIVE/PROFILE là policy của SKILL không phải shape dữ liệu.
- `kind` ∈ `structural` (double top/bottom, channel, divergence) | `candlestick` (1–3 nến) | `setup` (8 bullish, có score 0–100).
- double_bottom: **một entry** kind=`setup`, gộp structural breakout-status + score + levels.
- `pattern_family` + `archetype` là aggregate → field riêng cấp record, không phải entry.

### Schema `vn_indicators.payload` (mới)
```
{
  ...indicators hiện có (latest_close, sma/ema, rsi14, macd, bollinger, atr, volume, trend, drawdown, sr, dates)...,
  swings: [{index, date, price, type}],
  patterns: [
    { kind: "structural",  name: "double_top",    status: "potential"|"confirmed"|"failed",
      evidence: {high1, high2, neckline, retracement_pct} },
    { kind: "structural",  name: "descending_channel", status: "confirmed",
      evidence: {high_start, high_end, low_start, low_end, slope_pct} },
    { kind: "structural",  name: "bullish_rsi_divergence", status: "potential",
      evidence: {low1, low2, rsi1, rsi2} },
    { kind: "candlestick", name: "hammer",        status: "confirmed", evidence: {date, body_pct} },
    { kind: "setup",       name: "double_bottom", score: 55, status: "potential"|"forming"|"near_confirmation"|"not_clean"|"noisy",
      confirmation_price, watch_zone:{low,high}, distance_to_confirmation_pct, reader_note,
      evidence: {first_low, second_low, neckline, separation} },
    { kind: "setup",       name: "bull_flag",     score: 72, status: "forming", ... }
  ],
  pattern_family: "pullback_continuation" | "accumulation_breakout" | "trend_following" | "defensive_caution" | "reversal_or_recovery" | "mixed",
  archetype: { primary: "...", reader_note: "..." }
}
```

### SKILL.md policy đi kèm
- ACTIVE: dùng kind=structural + candlestick cho verdict; setup chỉ tham khảo.
- PROFILE: dùng kind=setup + pattern_family + archetype; không verdict.
- Cấm claim pattern không có trong `patterns`; "potential" phải hedge; honesty ("no divergence → nói không có").
- Đổi từ "Identify chart patterns" → "Interpret pre-computed `patterns`".

## 3. Plan triển khai (khi quay lại)
1. Spec/SKILL trước (rule 1): `specs/002-workflow/{data-model,plan}.md` + `contracts/api-contract.md`
   thêm `swings`, `patterns` (gộp, có `kind`), `pattern_family`, `archetype` + honesty rule;
   SKILL.md đổi "Identify" → "Interpret pre-computed" + policy trên.
2. Port code vào `src/finmind_agents/workflows/indicators.py`:
   - detection: `_swings`, `_double_top/_bottom`, `_channel` (pct-magnitude + slope-sign),
     `_candlestick_patterns`, `_rsi_series` + `_divergence`.
   - scoring: port `pattern_scoring.md` (8 `detect_*` + `setup()` + `status_from_score` + `reader_note`
     + `scan_setups` + `pattern_family` + `estimate_archetype`).
   - gộp vào 1 list `patterns` theo `kind`.
3. Thêm fields vào return `compute_indicators`.
4. pytest positive/negative mỗi detector + scoring + gộp `kind` (file mới `tests/test_pattern_detection.py`).
5. `uv run pytest`.

## 4. Đã làm xong (trước khi đổi ý) — UI citation/artifact flow
- Đã implement (commit-ready, chưa commit): consume citation/artifact events live; panel jump-to-selected;
  inline chip = ordinal number; order panel = appearance order (fix completed-branch wiring); tests pass.
- Files đã đổi: `src/finmind_ui/src/{App.tsx, components/Markdown.tsx, features/chat/{ArtifactPanel.tsx,ChatPage.tsx,ChatPage.test.tsx,mockChat.ts}}`, `styles.css`.
- Build (`npm run build`) + 11 UI test pass.

## 5. Open / chưa chốt
- Citation content: delivered-per-citation vs canonical-per-dataset (đề xuất delivered).
- Price citation content: year-end only hay +recent bars.
- PROFILE reachable trong 002 (cần input mode/question) — để sau.
- Có nên thêm deterministic pattern feature cho các thị trường khác hay chỉ VN trước.
