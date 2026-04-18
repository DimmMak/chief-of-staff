#!/usr/bin/env python3
"""
sensei — morning standup: reads recent work, identifies patterns, assigns drill.
"""
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

HOME = Path.home()
GAP_LOG = HOME / "Desktop/CLAUDE CODE/waypoint-capital/GAP-LOG.md"
DRILL_SCRIPT = Path(__file__).parent / "drill.py"


def recent_commits_count():
    """Count commits across Waypoint repos in last 24h."""
    repos = [
        "waypoint-capital", "royal-rumble", "price-desk",
        "fundamentals-desk", "technicals-desk", "accuracy-tracker",
        "journalist", "chief-of-staff",
    ]
    count = 0
    for r in repos:
        path = HOME / f"Desktop/CLAUDE CODE/{r}"
        if not path.exists():
            continue
        try:
            result = subprocess.run(
                ["git", "-C", str(path), "log", "--since=24 hours ago", "--oneline"],
                capture_output=True, text=True, timeout=5,
            )
            count += len([l for l in result.stdout.strip().split("\n") if l])
        except Exception:
            pass
    return count


def gaps_today():
    if not GAP_LOG.exists():
        return 0
    today = datetime.now().strftime("%Y-%m-%d")
    text = GAP_LOG.read_text()
    # Count bullets under today's section
    if f"## {today}" not in text:
        return 0
    section = text.split(f"## {today}")[1].split("## 2026")[0]
    return section.count("- **")


def main():
    commits = recent_commits_count()
    gaps = gaps_today()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print()
    print("🥋 SENSEI — MORNING STANDUP")
    print("━" * 60)
    print(f"  {now}")
    print()

    print("📊 Yesterday/Today at a glance:")
    print(f"   Commits across fund repos (24h):  {commits}")
    print(f"   Gaps caught today (GAP-LOG):      {gaps}")
    print()

    if commits >= 10:
        print("  🟢 STRENGTH: High ship rate. You're in flow.")
    elif commits >= 3:
        print("  🟢 STRENGTH: Steady output. Sustainable pace.")
    else:
        print("  🟡 OBSERVATION: Low commit count. Rest day? Or stuck?")

    if gaps >= 5:
        print("  🟡 WATCH:     Many gaps caught — good hunting, but verify all were real.")
    elif gaps >= 1:
        print("  🟢 HEALTHY:   Catching gaps without overreporting.")
    else:
        print("  🟡 WATCH:     No gaps logged. Either you're not prodding or the system is humming.")
    print()

    print("━" * 60)
    print("🎯 TODAY'S DRILL: (running drill.py)")
    print()

    # Chain: run drill.py for today's assignment
    try:
        result = subprocess.run(["python3", str(DRILL_SCRIPT)], capture_output=True, text=True, timeout=5)
        # Strip the duplicate header from drill.py output
        output = result.stdout
        # Drop the first header lines if present
        print(output)
    except Exception as e:
        print(f"  (could not load drill: {e})")

    print("━" * 60)


if __name__ == "__main__":
    main()
