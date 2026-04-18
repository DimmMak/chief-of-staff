# CHANGELOG — Chief of Staff

---

## [2026-04-18] — v0.2.0 — First DISPATCH command (.chief watchlist)

**Trigger:** User asked "can I ask my personal assistant to pull this for me?" after seeing a manual bash-pipeline watchlist view. Chief was read-only until now — this version turns her into a dispatcher for the most common recurring query.

### Shipped
- `scripts/watchlist_view.py` — standalone renderer, reusable
- `.chief watchlist` command wired in SKILL.md
- Reads waypoint-capital/watchlist.md, calls price-desk + fundamentals-desk, joins, analyzes

### Output sections (all one command)
1. Header (timestamp + ticker count)
2. Full table (price, post, day%, P/E fwd, P/S, rev growth, FCF, net cash, margin, target, upside, recommendation)
3. Sorted by upside-to-consensus-target
4. Standouts (top 4 by composite score: strong_buy + upside + low P/E + margin + growth)
5. Red flags (negative upside, negative margin, P/E>100, heavy debt, P/S>50, negative growth)
6. Next moves (suggested follow-up commands)

### Architecture note
This is Chief's first command that RUNS a script instead of reading state. Still never executes trades or side effects — she only queries and presents. Attention buffer + dispatch layer, cleanly separated.

---

## [2026-04-17] — v0.1.0 — Initial ship

**Trigger:** User said "I have so many roles and tools I'm getting confused" — the earn-your-features bar fired for the attention layer.

### Shipped

**The 5-level filter gradient (architectural invariant):**
- Level 1 RANK (autonomous)
- Level 2 BATCH (autonomous)
- Level 3 SUMMARIZE (autonomous)
- Level 4 SUPPRESS (user-explicit only)
- Level 5 DELETE (FORBIDDEN)

**11 commands:**
- `.chief` (quick P0+P1)
- `.chief morning` (proactive day plan)
- `.chief eod` (end-of-day ritual)
- `.chief check` (full sweep)
- `.chief status` (cross-skill dashboard)
- `.chief audit` (show demoted items)
- `.chief tune` (edit preferences)
- `.chief feedback` (rate briefing)
- `.chief review` (weekly calibration)
- `.chief miss` (correction — "you missed this")
- `.chief remind` (one-off reminder)

**Data architecture:**
- `data/preferences.md` — user-written rules (plain markdown, reversible)
- `data/feedback-log.jsonl` — briefing ratings
- `data/calibration.json` — learned thresholds
- `data/audit-log.md` — every decision with reasoning
- `data/inbox/` — push-mode escalations from other skills

**Integrations:**
- Reads royal-rumble predictions.json / strategy-meetings.json / comparisons.json
- Reads waypoint-capital trades, CONSTRAINTS, TRACK-RECORD
- Pairs with Mewtwo (opposite direction — outbound router)
- Never executes side-effects (suggests only)

### Posture

Starts with LOW filter / HIGH throughput. Over-reports for ~4 weeks. Earns filtering rights through explicit feedback + passive signal.

### Next

Real-world use will reveal calibration gaps. First weekly review: 2026-04-24.
