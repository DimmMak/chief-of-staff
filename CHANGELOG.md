# CHANGELOG — Chief of Staff

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
