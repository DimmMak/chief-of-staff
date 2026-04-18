#!/usr/bin/env bash
# chief-of-staff — install/sync script
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL_DIR="$HOME/.claude/skills/chief-of-staff"
STALE_ZIP="$HOME/.claude/skills/chief-of-staff.skill"

echo "📦 chief-of-staff install/sync"
echo "   source: $REPO_DIR"
echo "   target: $INSTALL_DIR"

[ -f "$STALE_ZIP" ] && { echo "🗑️  removing stale $STALE_ZIP"; rm "$STALE_ZIP"; }

if [ "${1:-}" = "--clean" ]; then
  echo "🧹 clean install"
  rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
cp "$REPO_DIR/SKILL.md" "$INSTALL_DIR/"
cp -R "$REPO_DIR/data" "$INSTALL_DIR/" 2>/dev/null || true
cp -R "$REPO_DIR/scripts" "$INSTALL_DIR/"

VERSION=$(grep -m1 "^version:" "$INSTALL_DIR/SKILL.md" | awk '{print $2}')
echo "✅ installed chief-of-staff v$VERSION — restart Claude Code to reload"
