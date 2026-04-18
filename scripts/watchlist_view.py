#!/usr/bin/env python3
"""
chief-of-staff → watchlist view

Combined price + fundamentals + analysis table for the Blue Hill Capital watchlist.

Flow:
  1. Read tickers from blue-hill-capital/watchlist.md
  2. Call price-desk + fundamentals-desk
  3. Join data by ticker
  4. Render: header → full table → upside-sorted list → standouts → red flags

Usage:
  python3 watchlist_view.py
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
PRICE_SCRIPT = HOME / ".claude/skills/price-desk/scripts/price.py"
FUND_SCRIPT = HOME / ".claude/skills/fundamentals-desk/scripts/fundamentals.py"
WATCHLIST_MD = HOME / "Desktop/CLAUDE CODE/blue-hill-capital/watchlist.md"

D = "$"  # dollar sign (avoid f-string escape headaches)


def run_script(script_path, arg):
    """Run a python script and return stdout."""
    result = subprocess.run(
        ["python3", str(script_path), arg],
        capture_output=True,
        text=True,
    )
    return result.stdout


def extract_json(raw):
    """Find the first [ and parse from there (skip any header prints)."""
    try:
        start = raw.index("[")
        return json.loads(raw[start:])
    except (ValueError, json.JSONDecodeError):
        return []


def render():
    # --- Pull data ---
    prices_raw = run_script(PRICE_SCRIPT, "watchlist")
    funds_raw = run_script(FUND_SCRIPT, "watchlist")

    prices = extract_json(prices_raw)
    funds = extract_json(funds_raw)

    if not prices or not funds:
        print("❌ Could not pull watchlist. Verify:")
        print(f"   • {WATCHLIST_MD} exists")
        print(f"   • {PRICE_SCRIPT} works")
        print(f"   • {FUND_SCRIPT} works")
        sys.exit(1)

    pmap = {p["ticker"]: p for p in prices}
    fmap = {f["ticker"]: f for f in funds}

    # --- Build combined records ---
    rows = []
    for ticker in pmap:
        p = pmap[ticker]
        f = fmap.get(ticker, {})
        if p.get("status") != "OK" or f.get("status") != "OK":
            continue

        price = p["price"]
        post = p.get("post_market_price")
        chg = p.get("change_pct", 0)

        pe_fwd = f["valuation"].get("forward_pe")
        ps = f["valuation"].get("price_to_sales")
        rg = f["revenue"].get("revenue_growth_yoy")
        fcf = f["cashflow"].get("free_cashflow")
        cash = f["balance_sheet"].get("total_cash") or 0
        debt = f["balance_sheet"].get("total_debt") or 0
        net_cash_b = (cash - debt) / 1e9
        margin = f["margins"].get("profit_margin")
        tgt = f["analyst"].get("price_target_mean")
        rec = f["analyst"].get("recommendation_key", "—")
        upside = ((tgt - price) / price * 100) if tgt else None

        rows.append({
            "ticker": ticker,
            "price": price,
            "post": post,
            "chg": chg,
            "pe_fwd": pe_fwd,
            "ps": ps,
            "rg": rg,
            "fcf": fcf,
            "net_cash_b": net_cash_b,
            "margin": margin,
            "tgt": tgt,
            "rec": rec,
            "upside": upside,
        })

    # --- Header ---
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print()
    print("📊 BLUE HILL CAPITAL — WATCHLIST VIEW")
    print(f"    Pulled: {now} · {len(rows)} names · price-desk + fundamentals-desk")
    print("=" * 120)

    # --- Full table ---
    print(f'{"TICKER":<6} {"PRICE":>9} {"POST":>9} {"Day%":>7} {"P/E fwd":>8} {"P/S":>6} {"Rev Grw":>9} {"FCF":>9} {"Net Cash":>11} {"Margin":>7} {"Target":>8} {"Upside":>8} {"Rec":>12}')
    print("=" * 120)

    for r in rows:
        price_s = f"{D}{r['price']:.2f}"
        post_s = f"{D}{r['post']:.2f}" if r["post"] else "—"
        chg_s = f"{r['chg']:+.2f}%"
        pe_s = f"{r['pe_fwd']:.1f}" if r["pe_fwd"] else "—"
        ps_s = f"{r['ps']:.1f}" if r["ps"] else "—"
        rg_s = f"{r['rg']*100:+.1f}%" if r["rg"] is not None else "—"
        fcf_s = f"{D}{r['fcf']/1e9:.1f}B" if r["fcf"] else "—"
        net_s = f"{D}{r['net_cash_b']:+.1f}B"
        m_s = f"{r['margin']*100:.1f}%" if r["margin"] is not None else "—"
        tgt_s = f"{D}{r['tgt']:.0f}" if r["tgt"] else "—"
        up_s = f"{r['upside']:+.1f}%" if r["upside"] is not None else "—"
        print(f'{r["ticker"]:<6} {price_s:>9} {post_s:>9} {chg_s:>7} {pe_s:>8} {ps_s:>6} {rg_s:>9} {fcf_s:>9} {net_s:>11} {m_s:>7} {tgt_s:>8} {up_s:>8} {r["rec"]:>12}')

    print("=" * 120)
    print()

    # --- Sorted by upside ---
    sorted_rows = sorted(
        [r for r in rows if r["upside"] is not None],
        key=lambda r: r["upside"],
        reverse=True,
    )
    print("🔥 SORTED BY UPSIDE TO CONSENSUS TARGET")
    print("-" * 60)
    for i, r in enumerate(sorted_rows, 1):
        star = "⭐" if r["rec"] == "strong_buy" else "  "
        print(f"  #{i:<3} {r['ticker']:<6} {r['upside']:+6.1f}%  {star} {r['rec']}")
    print()

    # --- Standouts ---
    standouts = []
    for r in rows:
        if r["upside"] is None or r["pe_fwd"] is None:
            continue
        score = 0
        if r["rec"] == "strong_buy":
            score += 2
        if r["upside"] > 20:
            score += 2
        if r["pe_fwd"] < 25:
            score += 1
        if r["margin"] is not None and r["margin"] > 0.25:
            score += 1
        if r["rg"] is not None and r["rg"] > 0.15:
            score += 1
        r["_score"] = score

    standouts = sorted(
        [r for r in rows if r.get("_score", 0) >= 5],
        key=lambda r: -r["_score"],
    )[:4]

    if standouts:
        print("🎯 STANDOUTS — names where fundamentals + consensus + upside align")
        print("-" * 60)
        medals = ["🥇", "🥈", "🥉", "🏅"]
        for i, r in enumerate(standouts):
            medal = medals[i] if i < len(medals) else "   "
            print(f"  {medal} {r['ticker']}  (price {D}{r['price']:.2f})")
            notes = []
            if r["upside"] is not None and r["upside"] > 15:
                notes.append(f"{r['upside']:+.1f}% upside")
            if r["pe_fwd"] is not None and r["pe_fwd"] < 25:
                notes.append(f"fwd P/E {r['pe_fwd']:.1f}x")
            if r["rg"] is not None and r["rg"] > 0.3:
                notes.append(f"+{r['rg']*100:.0f}% rev growth")
            if r["margin"] is not None and r["margin"] > 0.3:
                notes.append(f"{r['margin']*100:.0f}% margin")
            if r["rec"] == "strong_buy":
                notes.append("strong_buy consensus")
            print(f"      → {' · '.join(notes)}")
        print()

    # --- Red flags ---
    flags = []
    for r in rows:
        reasons = []
        if r["upside"] is not None and r["upside"] < 0:
            reasons.append(f"ABOVE consensus target ({r['upside']:+.1f}%)")
        if r["margin"] is not None and r["margin"] < 0:
            reasons.append(f"NEGATIVE margin ({r['margin']*100:+.1f}%)")
        if r["pe_fwd"] is not None and r["pe_fwd"] > 100:
            reasons.append(f"P/E > 100 ({r['pe_fwd']:.0f}x)")
        if r["net_cash_b"] < -50:
            reasons.append(f"heavy net debt ({D}{r['net_cash_b']:.0f}B)")
        if r["ps"] is not None and r["ps"] > 50:
            reasons.append(f"P/S > 50 ({r['ps']:.0f})")
        if r["rg"] is not None and r["rg"] < 0:
            reasons.append(f"negative revenue growth ({r['rg']*100:+.1f}%)")
        if reasons:
            flags.append((r["ticker"], reasons))

    if flags:
        print("🚨 RED FLAGS")
        print("-" * 60)
        for ticker, reasons in flags:
            print(f"  ⚠️  {ticker:<6} {' · '.join(reasons)}")
        print()

    # --- Action prompt ---
    print("━" * 60)
    print("Next moves:")
    print("  .rumble TICKER          — deep-dive any standout")
    print("  .compare A vs B         — head-to-head any two")
    print("  .chief watchlist        — refresh this view anytime")
    print("━" * 60)


if __name__ == "__main__":
    render()
