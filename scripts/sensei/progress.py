#!/usr/bin/env python3
"""
sensei — skill-tree progress viewer.

Shows XP per branch with a visual bar chart.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
TREE = DATA_DIR / "skill-tree.json"


def bar(pct, width=20):
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def main():
    tree = json.loads(TREE.read_text())
    branches = tree["branches"]
    max_xp = max((b["xp"] for b in branches.values()), default=1) or 1

    print()
    print("🥋 SENSEI — SKILL TREE PROGRESS")
    print("━" * 70)
    print(f"  Started: {tree.get('started_at', '—')}")
    print()

    # Sort by XP descending (strongest at top)
    sorted_branches = sorted(branches.items(), key=lambda x: -x[1]["xp"])

    for name, b in sorted_branches:
        pct = (b["xp"] / max_xp * 100) if max_xp else 0
        branch_label = name.replace("_", " ").ljust(22)
        print(f"  {branch_label}  {bar(pct)}  L{b['level']}  {b['xp']} XP  ({b['drills_completed']} drills)")

    print()
    print("━" * 70)
    # Find weakest
    weakest = min(branches.items(), key=lambda x: (x[1]["xp"], x[1]["drills_completed"]))
    print(f"  🎯 Focus branch today: {weakest[0].replace('_', ' ')} (L{weakest[1]['level']})")
    print(f"  💡 Run .chief drill to get a drill targeting this branch")
    print()


if __name__ == "__main__":
    main()
