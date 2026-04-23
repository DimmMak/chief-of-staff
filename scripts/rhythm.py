#!/usr/bin/env python3
"""
chief-of-staff → rhythm.py

Research cadence orchestrator for Blue Hill Capital. Five subcommands:

  .chief today     daily checklist (markets/portfolio/insider/earnings)
  .chief week      Monday plan + Friday reflect (auto-detect day)
  .chief month     monthly factor review (cohort + legends + commits)
  .chief backlog   hypothesis queue (add/list/close/groom)
  .chief reflect   explicit reflection prompt + write

Cross-skill calls (gracefully degrade if a desk is down):
  - macro-desk          → SPY/VIX snapshot
  - price-desk          → portfolio mark-to-market
  - filings-desk        → insider activity on watchlist
  - earnings-desk       → next-7d earnings on positions
  - accuracy-tracker    → review/cohort/legends
  - book                → open positions / pnl

Storage:
  data/backlog.jsonl       append-only hypothesis queue (open/closed/groomed)
  data/rhythm-log.jsonl    every command invocation logged
  data/reflections.jsonl   week/month/explicit reflections

Usage:
  python3 rhythm.py today
  python3 rhythm.py week
  python3 rhythm.py month
  python3 rhythm.py backlog add "TSLA insider cluster worth rumbling"
  python3 rhythm.py backlog list
  python3 rhythm.py backlog close <id> "outcome text"
  python3 rhythm.py backlog groom
  python3 rhythm.py reflect
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


HOME = Path.home()
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

BACKLOG_FILE = DATA_DIR / "backlog.jsonl"
RHYTHM_LOG_FILE = DATA_DIR / "rhythm-log.jsonl"
REFLECTIONS_FILE = DATA_DIR / "reflections.jsonl"

# Cross-skill script paths (resolved against installed symlinks)
PRICE_SCRIPT = HOME / ".claude/skills/price-desk/scripts/price.py"
MACRO_SCRIPT = HOME / ".claude/skills/macro-desk/scripts/macro.py"
FILINGS_SCRIPT = HOME / ".claude/skills/filings-desk/scripts/filings.py"
EARNINGS_SCRIPT = HOME / ".claude/skills/earnings-desk/scripts/earnings.py"
ACCURACY_SCRIPT = HOME / ".claude/skills/accuracy-tracker/scripts/accuracy.py"
BOOK_SCRIPT = HOME / ".claude/skills/book/scripts/book.py"
DRIFT_GUARD_SCRIPT = HOME / ".claude/skills/drift-guard/scripts/heartbeat.py"
DRIFT_GUARD_LOG = HOME / "Desktop/CLAUDE CODE/drift-guard/data/heartbeat-log.jsonl"

WATCHLIST_MD = HOME / "Desktop/CLAUDE CODE/blue-hill-capital/watchlist.md"
PREDICTIONS_JSON = HOME / "Desktop/CLAUDE CODE/royal-rumble/data/predictions.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(event_type: str, detail: Dict[str, Any]) -> None:
    try:
        rec = {"ts": now_iso(), "event": event_type, **detail}
        with RHYTHM_LOG_FILE.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass  # logging never breaks a command


def run_cmd(script: Path, args: List[str], timeout: int = 60) -> Optional[str]:
    """Run a python script. Return stdout on success, None on error."""
    if not script.exists():
        return None
    try:
        result = subprocess.run(
            ["python3", str(script), *args],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
    except Exception:
        return None
    return None


def parse_first_json(text: str) -> Optional[dict]:
    """Find the first { and parse the JSON object starting there."""
    if not text:
        return None
    try:
        i = text.index("{")
        # Scan to matching brace using a simple decoder loop
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(text[i:])
        return obj
    except Exception:
        return None


def read_watchlist() -> List[str]:
    """Parse tickers from watchlist.md (table column 1)."""
    if not WATCHLIST_MD.exists():
        return []
    tickers: List[str] = []
    table_started = False
    for line in WATCHLIST_MD.read_text().splitlines():
        line = line.strip()
        if line.startswith("| Ticker |"):
            table_started = True
            continue
        if not table_started:
            continue
        if line.startswith("|---"):
            continue
        if not line.startswith("|"):
            if tickers:
                break  # first table ended
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0] and cells[0].isupper() and cells[0].isalnum():
            tickers.append(cells[0])
    return tickers


# ---------------------------------------------------------------------------
# .chief today
# ---------------------------------------------------------------------------

def cmd_today(args) -> int:
    today = datetime.now()
    print(f"\n📅 BLUE HILL CAPITAL — DAILY BRIEFING · {today:%Y-%m-%d %a %H:%M}")
    print("=" * 72)

    # --- Markets snapshot (price-desk on SPY + VIX proxy) ---
    print("\n🌐 MARKETS")
    print("-" * 72)
    spy_raw = run_cmd(PRICE_SCRIPT, ["SPY"], timeout=30)
    spy = parse_first_json(spy_raw) if spy_raw else None
    if spy and spy.get("status") == "OK":
        print(f"  SPY: ${spy['price']:.2f}  ({spy.get('change_pct', 0):+.2f}% today)")
    else:
        print("  SPY: price-desk unavailable")
    vix_raw = run_cmd(PRICE_SCRIPT, ["^VIX"], timeout=30)
    vix = parse_first_json(vix_raw) if vix_raw else None
    if vix and vix.get("status") == "OK":
        print(f"  VIX: {vix['price']:.2f}  ({vix.get('change_pct', 0):+.2f}% today)")
    else:
        print("  VIX: not available (try macro-desk)")

    # --- Portfolio (book) ---
    print("\n💼 PORTFOLIO")
    print("-" * 72)
    book_raw = run_cmd(BOOK_SCRIPT, ["list"], timeout=20)
    if book_raw:
        # Just echo a trimmed view
        lines = book_raw.strip().split("\n")
        for line in lines[:15]:
            print(f"  {line}")
        if len(lines) > 15:
            print(f"  ... +{len(lines) - 15} more lines")
    else:
        print("  No open positions logged in .book")

    # --- Insider activity in watchlist (filings-desk) ---
    print("\n🕵️  INSIDER ACTIVITY (watchlist · last 90d via filings-desk)")
    print("-" * 72)
    watchlist = read_watchlist()
    if not watchlist:
        print("  (watchlist.md empty or missing)")
    else:
        # Limit to first 5 to keep daily briefing snappy
        for ticker in watchlist[:5]:
            f_raw = run_cmd(FILINGS_SCRIPT, [ticker, "--no-log"], timeout=120)
            f = parse_first_json(f_raw) if f_raw else None
            if not f or f.get("status") == "ERROR":
                print(f"  {ticker:<5}  filings-desk error")
                continue
            ins = f.get("insider_transactions", {})
            net = ins.get("insider_net_buying_90d_usd")
            cnt = ins.get("insider_txn_count_90d") or 0
            cluster = ins.get("exec_cluster_buy_flag")
            net_str = f"${net/1e6:+.1f}M" if net is not None else "—"
            cluster_flag = " 🟢 EXEC CLUSTER BUY" if cluster else ""
            print(f"  {ticker:<5}  net 90d: {net_str:<12} txns: {cnt:<4}{cluster_flag}")
        if len(watchlist) > 5:
            print(f"  ... ({len(watchlist) - 5} more in watchlist; run with --all to see)")

    # --- Earnings within 7 days for watchlist (earnings-desk) ---
    print("\n📊 EARNINGS THIS WEEK (watchlist · via earnings-desk)")
    print("-" * 72)
    flagged = 0
    for ticker in watchlist[:8]:
        e_raw = run_cmd(EARNINGS_SCRIPT, [ticker, "--no-log"], timeout=60)
        e = parse_first_json(e_raw) if e_raw else None
        if not e:
            continue
        ne = e.get("next_earnings", {}) or {}
        days = ne.get("days_out")
        status = ne.get("event_status") or "UNKNOWN"
        if days is None:
            continue
        if days <= 7 and status in ("UPCOMING", "TODAY_OR_IMMINENT"):
            print(f"  {ticker:<5}  in {days}d  status={status}  EPS est: {ne.get('eps_estimate')}")
            flagged += 1
    if flagged == 0:
        print("  (none in next 7d for watchlist sample)")

    # --- Drift-guard heartbeat (latest fleet-health status) ---
    print("\n🩺 FLEET HEALTH (drift-guard latest)")
    print("-" * 72)
    drift_status = "never run"
    drift_alarms = {"red": 0, "orange": 0, "yellow": 0}
    if DRIFT_GUARD_LOG.exists():
        try:
            lines = DRIFT_GUARD_LOG.read_text().strip().split("\n")
            if lines and lines[-1]:
                latest = json.loads(lines[-1])
                sev = latest.get("severity", {}) or {}
                drift_alarms = {"red": sev.get("red", 0), "orange": sev.get("orange", 0), "yellow": sev.get("yellow", 0)}
                clean = latest.get("clean", False)
                ran_at = (latest.get("run_at") or "")[:16]
                flag = "🟩 CLEAN" if clean else ("🟥 RED" if drift_alarms["red"] else ("🟧 ORANGE" if drift_alarms["orange"] else "🟨 YELLOW"))
                drift_status = f"{flag}  ·  last run {ran_at}  ·  red={drift_alarms['red']} orange={drift_alarms['orange']} yellow={drift_alarms['yellow']}"
        except Exception:
            drift_status = "log unreadable — try `.drift-guard` manually"
    print(f"  {drift_status}")
    if drift_alarms["red"] > 0:
        print(f"  🚨 RED alarms present — run `.drift-guard` for details BEFORE trusting downstream analysis")

    print("\n" + "=" * 72)
    print("Next moves: `.chief backlog list`  ·  `.rumble TICKER`  ·  `.chief week`")

    log_event("today", {
        "watchlist_size": len(watchlist),
        "earnings_flagged": flagged,
        "drift_red": drift_alarms["red"],
        "drift_orange": drift_alarms["orange"],
    })
    return 0


# ---------------------------------------------------------------------------
# .chief week
# ---------------------------------------------------------------------------

def cmd_week(args) -> int:
    today = datetime.now()
    is_friday = today.weekday() == 4
    is_monday = today.weekday() == 0
    forced = args.force_mode if hasattr(args, "force_mode") else None
    mode = forced or ("friday" if is_friday else "monday")

    print(f"\n📅 BLUE HILL CAPITAL — WEEKLY · {today:%Y-%m-%d %a} · mode={mode}")
    print("=" * 72)

    if mode == "monday":
        print("\n🎯 MONDAY PLAN — top backlog + earnings of week + insider clusters")
        print("-" * 72)

        # Top 3 backlog by recency
        items = read_backlog(open_only=True)
        items.sort(key=lambda x: x.get("priority", "P2"))
        print(f"\n  📋 TOP 3 BACKLOG ({len(items)} open total)")
        for it in items[:3]:
            age = days_since(it.get("created_at"))
            print(f"    [{it['id'][:8]}] ({it.get('priority','P2')}, {age}d old) {it['title']}")
        if not items:
            print("    (backlog empty — `.chief backlog add \"...\"`)")

        # Earnings this week from watchlist
        print("\n  📊 EARNINGS THIS WEEK (watchlist sample)")
        watchlist = read_watchlist()
        flagged = 0
        for ticker in watchlist[:8]:
            e_raw = run_cmd(EARNINGS_SCRIPT, [ticker, "--no-log"], timeout=60)
            e = parse_first_json(e_raw) if e_raw else None
            if not e:
                continue
            ne = e.get("next_earnings", {}) or {}
            days = ne.get("days_out")
            if days is not None and days <= 7:
                status = ne.get("event_status") or "UNKNOWN"
                print(f"    {ticker:<5}  in {days}d  status={status}")
                flagged += 1
        if flagged == 0:
            print("    (none in next 7d)")

        # Insider clusters
        print("\n  🕵️  INSIDER CLUSTERS (watchlist sample)")
        clusters = 0
        for ticker in watchlist[:8]:
            f_raw = run_cmd(FILINGS_SCRIPT, [ticker, "--no-log"], timeout=120)
            f = parse_first_json(f_raw) if f_raw else None
            if not f:
                continue
            if f.get("insider_transactions", {}).get("exec_cluster_buy_flag"):
                print(f"    {ticker:<5}  🟢 EXEC CLUSTER BUY (last 90d)")
                clusters += 1
        if clusters == 0:
            print("    (no exec-cluster buys this week)")

    else:  # friday
        print("\n🪞 FRIDAY REFLECT — auto-runs .accuracy review 7d")
        print("-" * 72)
        acc_raw = run_cmd(ACCURACY_SCRIPT, ["review", "7d"], timeout=60)
        if acc_raw:
            for line in acc_raw.strip().split("\n")[:30]:
                print(f"  {line}")
        else:
            print("  (.accuracy review 7d unavailable)")

        # Prompt for reflection
        print("\n  📝 What's one thing the week taught you?")
        print('    Run: python3 rhythm.py reflect "your one-liner"')

    log_event("week", {"mode": mode})
    print("\n" + "=" * 72)
    return 0


# ---------------------------------------------------------------------------
# .chief month
# ---------------------------------------------------------------------------

def cmd_month(args) -> int:
    today = datetime.now()
    print(f"\n📅 BLUE HILL CAPITAL — MONTHLY FACTOR REVIEW · {today:%Y-%m}")
    print("=" * 72)

    # Cohort (rumble_version groupings)
    print("\n🏛️ ACCURACY COHORTS (.accuracy cohort)")
    print("-" * 72)
    cohort_raw = run_cmd(ACCURACY_SCRIPT, ["cohort"], timeout=60)
    if cohort_raw:
        for line in cohort_raw.strip().split("\n")[:25]:
            print(f"  {line}")
    else:
        print("  (.accuracy cohort unavailable)")

    # Legends attribution
    print("\n🎭 PER-LEGEND ATTRIBUTION (.accuracy legends)")
    print("-" * 72)
    leg_raw = run_cmd(ACCURACY_SCRIPT, ["legends"], timeout=60)
    if leg_raw:
        for line in leg_raw.strip().split("\n")[:25]:
            print(f"  {line}")
    else:
        print("  (.accuracy legends unavailable)")

    # Recent commits across fund repos (past 30 days)
    print("\n🚀 SHIPPED THIS MONTH (last 30 days, fund repos)")
    print("-" * 72)
    repos = ["royal-rumble", "accuracy-tracker", "earnings-desk", "filings-desk",
             "fundamentals-desk", "price-desk", "technicals-desk", "options-desk",
             "macro-desk", "chief-of-staff", "book"]
    base = HOME / "Desktop/CLAUDE CODE"
    for repo in repos:
        repo_path = base / repo
        if not (repo_path / ".git").exists():
            continue
        try:
            out = subprocess.check_output(
                ["git", "-C", str(repo_path), "log", "--since=30 days ago",
                 "--pretty=%h %s"],
                text=True, timeout=15,
            ).strip()
            if out:
                lines = out.split("\n")
                print(f"  {repo}:")
                for line in lines[:5]:
                    print(f"    {line}")
                if len(lines) > 5:
                    print(f"    ... +{len(lines) - 5} more commits")
        except Exception:
            continue

    log_event("month", {})
    print("\n" + "=" * 72)
    return 0


# ---------------------------------------------------------------------------
# .chief backlog
# ---------------------------------------------------------------------------

def read_backlog(open_only: bool = False) -> List[Dict[str, Any]]:
    """Read all backlog records.

    The file is append-only, so a single hypothesis can have multiple records
    (open then closed). Dedupe by ID, keeping the LAST record for each ID
    (which reflects current status). If `open_only`, filter to status=="open".
    """
    if not BACKLOG_FILE.exists():
        return []
    by_id: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for line in BACKLOG_FILE.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        rid = rec.get("id")
        if not rid:
            continue
        if rid not in by_id:
            order.append(rid)
        by_id[rid] = rec
    items = [by_id[i] for i in order]
    if open_only:
        items = [i for i in items if i.get("status") == "open"]
    return items


def write_backlog_record(rec: Dict[str, Any]) -> None:
    with BACKLOG_FILE.open("a") as f:
        f.write(json.dumps(rec) + "\n")


def days_since(iso_ts: Optional[str]) -> int:
    if not iso_ts:
        return 0
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return delta.days
    except Exception:
        return 0


def cmd_backlog_add(title: str, priority: str = "P2") -> int:
    item = {
        "id": uuid.uuid4().hex[:12],
        "title": title,
        "priority": priority,
        "status": "open",
        "created_at": now_iso(),
    }
    write_backlog_record(item)
    print(f"✅ Added [{item['id'][:8]}] ({priority}) {title}")
    log_event("backlog_add", {"id": item["id"], "title": title})
    return 0


def cmd_backlog_list() -> int:
    items = read_backlog(open_only=True)
    print(f"\n📋 BACKLOG — {len(items)} open hypotheses")
    print("-" * 72)
    if not items:
        print("  (empty — `.chief backlog add \"...\"`)")
        return 0
    items.sort(key=lambda x: (x.get("priority", "P2"), x.get("created_at", "")))
    for it in items:
        age = days_since(it.get("created_at"))
        flag = " ⏳" if age > 14 else ""
        print(f"  [{it['id'][:8]}] ({it.get('priority','P2')}, {age}d){flag} {it['title']}")
    print()
    return 0


def cmd_backlog_close(item_id: str, outcome: str) -> int:
    items = read_backlog()
    matched = None
    for it in items:
        if it.get("status") == "open" and it["id"].startswith(item_id):
            matched = it
            break
    if not matched:
        print(f"❌ No open backlog item matching '{item_id}'")
        return 1
    closed = {
        "id": matched["id"],
        "title": matched["title"],
        "priority": matched.get("priority", "P2"),
        "status": "closed",
        "created_at": matched.get("created_at"),
        "closed_at": now_iso(),
        "outcome": outcome,
    }
    write_backlog_record(closed)
    print(f"✅ Closed [{matched['id'][:8]}] — outcome: {outcome}")
    log_event("backlog_close", {"id": matched["id"], "outcome": outcome})
    return 0


def cmd_backlog_groom() -> int:
    items = read_backlog(open_only=True)
    stale = [i for i in items if days_since(i.get("created_at")) > 14]
    print(f"\n🧹 BACKLOG GROOM — {len(stale)} item(s) untouched >14 days")
    print("-" * 72)
    if not stale:
        print("  (nothing stale)")
        return 0
    for it in stale:
        age = days_since(it.get("created_at"))
        print(f"  [{it['id'][:8]}] ({age}d old) {it['title']}")
        print("    → Decision: rumble it, kill it, or re-prioritize?")
    log_event("backlog_groom", {"stale_count": len(stale)})
    return 0


def cmd_backlog(args) -> int:
    sub = args.backlog_subcommand
    if sub == "add":
        return cmd_backlog_add(args.title, priority=args.priority)
    if sub == "list":
        return cmd_backlog_list()
    if sub == "close":
        return cmd_backlog_close(args.id, args.outcome)
    if sub == "groom":
        return cmd_backlog_groom()
    print("Usage: .chief backlog {add|list|close|groom}")
    return 1


# ---------------------------------------------------------------------------
# .chief reflect
# ---------------------------------------------------------------------------

def cmd_reflect(args) -> int:
    text = args.text or ""
    today = datetime.now()
    if not text:
        print("\n🪞 REFLECTION PROMPT")
        print("-" * 72)
        print("  • What worked this week?")
        print("  • What didn't?")
        print("  • What do I change next week?")
        print()
        print('  Run: python3 rhythm.py reflect "your one-liner"')

        # Also surface week's rumbles for context
        rumbles_this_week = []
        if PREDICTIONS_JSON.exists():
            try:
                d = json.loads(PREDICTIONS_JSON.read_text())
                cutoff = today - timedelta(days=7)
                for r in d.get("rumbles", []):
                    ts = r.get("timestamp") or r.get("rumbled_at") or r.get("created_at")
                    if not ts:
                        continue
                    try:
                        rt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        if rt.replace(tzinfo=None) >= cutoff:
                            rumbles_this_week.append(r)
                    except Exception:
                        continue
            except Exception:
                pass
        if rumbles_this_week:
            print("\n  📊 Rumbles this week (predictions.json):")
            for r in rumbles_this_week[:10]:
                t = r.get("ticker", "?")
                v = r.get("verdict") or r.get("recommendation") or "—"
                print(f"    {t:<6} → {v}")
        return 0

    rec = {
        "ts": now_iso(),
        "kind": "explicit",
        "text": text,
    }
    with REFLECTIONS_FILE.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"✅ Reflection logged ({len(text)} chars).")
    log_event("reflect", {"chars": len(text)})
    return 0


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(prog="rhythm",
                                     description="chief-of-staff research-cadence orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("today", help="Daily checklist")

    week_p = sub.add_parser("week", help="Weekly plan/reflect")
    week_p.add_argument("--force-mode", choices=["monday", "friday"], default=None)

    sub.add_parser("month", help="Monthly factor review")

    backlog_p = sub.add_parser("backlog", help="Hypothesis queue")
    backlog_sub = backlog_p.add_subparsers(dest="backlog_subcommand", required=True)
    add_p = backlog_sub.add_parser("add")
    add_p.add_argument("title")
    add_p.add_argument("--priority", default="P2", choices=["P0", "P1", "P2", "P3"])
    backlog_sub.add_parser("list")
    close_p = backlog_sub.add_parser("close")
    close_p.add_argument("id")
    close_p.add_argument("outcome")
    backlog_sub.add_parser("groom")

    reflect_p = sub.add_parser("reflect", help="Reflection prompt or write")
    reflect_p.add_argument("text", nargs="?", default=None)

    args = parser.parse_args()

    handlers = {
        "today":    cmd_today,
        "week":     cmd_week,
        "month":    cmd_month,
        "backlog":  cmd_backlog,
        "reflect":  cmd_reflect,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
