#!/bin/bash
# install_autostart.sh
# One-click installer: sets up JARVIS to auto-start on every macOS login.
# Run this ONCE: bash install_autostart.sh

set -e

JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.raj.jarvis.plist"
PLIST_SRC="$JARVIS_DIR/$PLIST_NAME"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_DEST="$LAUNCH_AGENTS_DIR/$PLIST_NAME"
AUTOSTART_SCRIPT="$JARVIS_DIR/jarvis_autostart.sh"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║          JARVIS Auto-Start Installer                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Make scripts executable ──────────────────────────────────────────
echo "[1/5] Making scripts executable..."
chmod +x "$AUTOSTART_SCRIPT"
echo "      ✓ jarvis_autostart.sh is now executable"

# ── Step 2: Create LaunchAgents directory if needed ───────────────────────────
echo "[2/5] Checking ~/Library/LaunchAgents directory..."
mkdir -p "$LAUNCH_AGENTS_DIR"
echo "      ✓ Directory ready"

# ── Step 3: Unload existing agent if present ─────────────────────────────────
echo "[3/5] Removing any existing JARVIS LaunchAgent..."
if launchctl list | grep -q "com.raj.jarvis" 2>/dev/null; then
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    echo "      ✓ Old agent unloaded"
else
    echo "      ✓ No existing agent found"
fi

# ── Step 4: Copy plist to LaunchAgents ───────────────────────────────────────
echo "[4/5] Installing LaunchAgent plist..."
cp "$PLIST_SRC" "$PLIST_DEST"
# Fix permissions — plist must be owned by user, not group-writable
chmod 644 "$PLIST_DEST"
echo "      ✓ Plist installed at $PLIST_DEST"

# ── Step 5: Load the LaunchAgent ─────────────────────────────────────────────
echo "[5/5] Loading JARVIS LaunchAgent..."
launchctl load "$PLIST_DEST"
echo "      ✓ Agent loaded successfully"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅  JARVIS will now auto-start on every login!         ║"
echo "║                                                          ║"
echo "║  To DISABLE auto-start, run:                            ║"
echo "║    bash uninstall_autostart.sh                          ║"
echo "║                                                          ║"
echo "║  Logs:                                                   ║"
echo "║    ~/Library/Logs/jarvis_autostart.log                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Optional: run Jarvis right now ───────────────────────────────────────────
read -p "  Start JARVIS right now? [Y/n]: " answer
answer="${answer:-Y}"
if [[ "$answer" =~ ^[Yy]$ ]]; then
    echo ""
    echo "  Starting JARVIS..."
    bash "$AUTOSTART_SCRIPT" &
    sleep 3
    echo "  ✓ JARVIS is starting. Opening Chrome..."
fi
