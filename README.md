# 📋 Chief of Staff

> The attention layer for Blue Hill Capital. Every other skill reports through her.

---

## What she does

```
YOU → Chief of Staff → (filters + ranks) → YOU
        │
        ▲─ reads state from all skills
        ▲─ receives escalations via inbox
        ▼─ briefs you on what matters
```

**She protects attention, not information.** Ranks P0-P3. Never deletes.

---

## The inviolable rule

> "I can demote. I cannot delete. I can deprioritize. I cannot disappear.
> I can compress. I cannot erase. Noise today is signal tomorrow."

Every item lives in `data/audit-log.md`. Nothing vanishes.

---

## Commands

```
.chief              → quick P0+P1 status
.chief morning      → proactive day plan
.chief eod          → end-of-day ritual + prompts .cash-out
.chief check        → full sweep
.chief status       → cross-skill dashboard
.chief audit        → show what I demoted
.chief tune         → edit preferences
.chief feedback     → rate last briefing
.chief review       → weekly calibration ritual
.chief miss [item]  → "you missed this, learn"
.chief remind       → one-off reminder
```

---

## Install

```bash
./scripts/install.sh
```

Syncs Desktop → `~/.claude/skills/chief-of-staff/`. Restart Claude Code.

---

## Architecture

She sits between you and the skill fleet as **the inbound filter.** Pairs with **Mewtwo** (the outbound router). Different directions, same layer.

```
              YOU
               │
     ┌─────────┴─────────┐
     ▼                   ▼
   MEWTWO            CHIEF OF STAFF
 (outbound)           (inbound)
     │                   ▲
     ▼                   │
   SKILLS ──────────────┘
```

🃏⚔️
