#!/usr/bin/env python3
"""
sensei — daily drill selector.

Picks today's drill weighted by the user's weakest skill-tree branch.
Never repeats the last 3 drills.

Usage:
  python3 drill.py              → today's drill
  python3 drill.py complete ID  → mark a drill completed (awards XP)
"""
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
LIBRARY = DATA_DIR / "drill-library.json"
TREE = DATA_DIR / "skill-tree.json"
COMPLETED = DATA_DIR / "completed-drills.jsonl"


def load_library():
    return json.loads(LIBRARY.read_text())


def load_tree():
    return json.loads(TREE.read_text())


def save_tree(tree):
    TREE.write_text(json.dumps(tree, indent=2))


def recently_done_ids(n=3):
    """Return set of last N drill IDs completed."""
    if not COMPLETED.exists():
        return set()
    lines = COMPLETED.read_text().strip().split("\n")[-n:]
    ids = set()
    for line in lines:
        try:
            ids.add(json.loads(line).get("drill_id"))
        except Exception:
            pass
    return ids


def weakest_branch(tree):
    """Return the branch with lowest XP (tie-break: least drills done)."""
    branches = tree["branches"]
    return min(branches.keys(), key=lambda b: (branches[b]["xp"], branches[b]["drills_completed"]))


def pick_drill():
    library = load_library()
    tree = load_tree()
    skip_ids = recently_done_ids(3)
    weak = weakest_branch(tree)

    candidates = [d for d in library["drills"]
                  if d["branch"] == weak and d["id"] not in skip_ids]

    # Fallback: if weakest branch has no eligible drills, pick from any branch
    if not candidates:
        candidates = [d for d in library["drills"] if d["id"] not in skip_ids]

    if not candidates:
        # Everything's been done recently — re-open the pool
        candidates = library["drills"]

    return random.choice(candidates), weak


def show_drill():
    drill, weak = pick_drill()
    tree = load_tree()
    cur_xp = tree["branches"][drill["branch"]]["xp"]
    cur_level = tree["branches"][drill["branch"]]["level"]

    print()
    print("🥋 SENSEI — TODAY'S DRILL")
    print("━" * 60)
    print(f"  Weakest branch today: {drill['branch']}  (level {cur_level}, {cur_xp} XP)")
    print()
    print(f"  📝 [{drill['id']}] {drill['title']}  (level {drill['level']}, {drill['timebox_min']} min)")
    print()
    print(f"     {drill['prompt']}")
    print()
    print("━" * 60)
    print(f"When done, run:  .chief drill complete {drill['id']}")
    print()


def mark_complete(drill_id):
    library = load_library()
    drill = next((d for d in library["drills"] if d["id"] == drill_id), None)
    if not drill:
        print(f"❌ Unknown drill id: {drill_id}")
        sys.exit(1)

    tree = load_tree()
    branch = drill["branch"]
    xp_gain = tree["xp_per_drill_level"].get(str(drill["level"]), 10)

    tree["branches"][branch]["xp"] += xp_gain
    tree["branches"][branch]["drills_completed"] += 1

    # Level up check
    thresholds = tree["level_thresholds"]
    new_xp = tree["branches"][branch]["xp"]
    new_level = 1
    for i, t in enumerate(thresholds, start=1):
        if new_xp >= t:
            new_level = i
    tree["branches"][branch]["level"] = new_level
    save_tree(tree)

    # Log
    COMPLETED.parent.mkdir(parents=True, exist_ok=True)
    with COMPLETED.open("a") as f:
        f.write(json.dumps({
            "drill_id": drill_id,
            "branch": branch,
            "level": drill["level"],
            "xp_gained": xp_gain,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }) + "\n")

    print(f"✅ Drill {drill_id} completed. +{xp_gain} XP in {branch}")
    print(f"   New total: {new_xp} XP, level {new_level}")


def main():
    args = sys.argv[1:]
    if args and args[0] == "complete":
        if len(args) < 2:
            print("Usage: drill.py complete DRILL_ID")
            sys.exit(1)
        mark_complete(args[1])
    else:
        show_drill()


if __name__ == "__main__":
    main()
