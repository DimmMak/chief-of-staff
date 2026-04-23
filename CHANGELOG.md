# CHANGELOG — Chief of Staff

## v0.5.0 — 2026-04-23

**Phase 4 of filings-desk + .chief rhythm build.** Adds research-cadence
infrastructure: 5 new commands that read from the full desk stack.

### Added
- `scripts/rhythm.py` — single orchestrator with 5 subcommands
  - `today` — daily briefing: SPY+VIX (price-desk), portfolio (book),
    insider activity on watchlist (filings-desk), earnings-of-week
    (earnings-desk). Proves end-to-end cross-skill integration.
  - `week --force-mode {monday|friday}` — auto-detects day; Monday surfaces
    top 3 backlog + earnings of week + insider clusters; Friday auto-runs
    `.accuracy review 7d` and prompts for reflection.
  - `month` — monthly factor review: `.accuracy cohort` + `.accuracy legends`
    + `git log --since=30 days ago` across all fund repos.
  - `backlog {add|list|close|groom}` — append-only hypothesis queue at
    `data/backlog.jsonl`. Dedupes by ID (last write wins). `groom` flags
    items untouched >14 days for review/kill.
  - `reflect [text]` — no-arg prompts + surfaces this week's rumbles from
    predictions.json. With text, appends to `data/reflections.jsonl`.
- `data/backlog.jsonl` — append-only hypothesis queue (gitignored)
- `data/rhythm-log.jsonl` — every command invocation logged (gitignored)
- `data/reflections.jsonl` — explicit + auto reflections (gitignored)
- `.gitignore` (new) — excludes user-data files; keeps repo lean

### Changed
- Frontmatter: capabilities.writes + capabilities.calls + composable_with
  expanded to declare new dependencies (filings-desk, earnings-desk,
  accuracy-tracker, book, macro-desk)

### Ship gate (PASSED)
- All 5 commands return non-error output on a fresh install
- `.chief today` reads from filings-desk + earnings-desk + price-desk:
  - SPY $711.21 (+0.60%), VIX 18.92 (-2.92%)
  - Watchlist insider activity: NVDA $-208M / AMD $-64M / PLTR $-435M
  - Earnings this week: TSLA today, MSFT/META/GOOG in 7d
- backlog cycle verified: add → list → close (dedup-by-ID fix) → groom
  (seeded 20-day-old item correctly flagged as stale)
- `.chief month` actually pulls cohort + legends from accuracy-tracker

---

## v0.4.0 — 2026-04-18

**World-Class Overhaul shipped.** Part of the fleet-wide upgrade to tree+plugin+unix architecture.

- 🌳 **Tree:** `domain:` field added to frontmatter (fund)
- 🎮 **Plugin:** `capabilities:` block declares reads / writes / calls / cannot
- 🐧 **Unix:** `unix_contract:` block declares data_format / schema_version / stdin_support / stdout_format / composable_with
- 🛡️ Schema v0.3 validation required at install (via `future-proof/scripts/validate-skill.py`)
- 🔗 Install converted to symlink pattern (kills drift between Desktop source and live install)
- 🏷️ Tagged at `v-2026-04-18-world-class` for rollback

See `memory/project_world_class_architecture.md` for the full model.

---


---

## [2026-04-18] — v0.2.0 — First DISPATCH command (.chief watchlist)

**Trigger:** User asked "can I ask my personal assistant to pull this for me?" after seeing a manual bash-pipeline watchlist view. Chief was read-only until now — this version turns her into a dispatcher for the most common recurring query.

### Shipped
- `scripts/watchlist_view.py` — standalone renderer, reusable
- `.chief watchlist` command wired in SKILL.md
- Reads blue-hill-capital/watchlist.md, calls price-desk + fundamentals-desk, joins, analyzes

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
- Reads blue-hill-capital trades, CONSTRAINTS, TRACK-RECORD
- Pairs with Mewtwo (opposite direction — outbound router)
- Never executes side-effects (suggests only)

### Posture

Starts with LOW filter / HIGH throughput. Over-reports for ~4 weeks. Earns filtering rights through explicit feedback + passive signal.

### Next

Real-world use will reveal calibration gaps. First weekly review: 2026-04-24.
