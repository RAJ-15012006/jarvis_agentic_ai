#!/bin/bash
# jarvis_autostart.sh
# Starts Jarvis backend server and opens the frontend in Chrome.
# This script is called by the macOS LaunchAgent on every login.

# ── Configuration ────────────────────────────────────────────────────────────
JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$JARVIS_DIR/.venv/bin/python"
BACKEND_DIR="$JARVIS_DIR/backend"
LOG_FILE="$HOME/Library/Logs/jarvis_autostart.log"
JARVIS_URL="http://localhost:8000"

# ── Logging ───────────────────────────────────────────────────────────────────
exec >> "$LOG_FILE" 2>&1
echo ""
echo "============================================================"
echo "  JARVIS AutoStart — $(date)"
echo "============================================================"

# ── Prevent concurrent runs ──────────────────────────────────────────────────
# Check if another instance of this script is already running
# We search for "jarvis_autostart.sh" and exclude the current process ID ($$)
OTHER_PIDS=$(pgrep -f "jarvis_autostart.sh" | grep -v "^$$\$")
if [ -n "$OTHER_PIDS" ]; then
    echo "[*] Another instance of jarvis_autostart.sh is already running (PIDs: $OTHER_PIDS). Exiting."
    exit 0
fi

# ── Wait for network (max 30s) ────────────────────────────────────────────────
echo "[*] Waiting for network..."
for i in {1..15}; do
    if ping -c 1 -W 1 8.8.8.8 &>/dev/null; then
        echo "[✓] Network available."
        break
    fi
    sleep 2
done

# ── Kill any existing Jarvis process ─────────────────────────────────────────
echo "[*] Stopping any existing Jarvis instance..."
pkill -fi "uvicorn.*main:socket_app" 2>/dev/null || true
pkill -fi "python.*main.py" 2>/dev/null || true
sleep 1

# ── Start Jarvis backend ──────────────────────────────────────────────────────
echo "[*] Starting JARVIS backend..."
cd "$BACKEND_DIR" || exit 1
"$VENV_PYTHON" main.py &
BACKEND_PID=$!
echo "[✓] Backend PID: $BACKEND_PID"

# ── Wait for backend to be ready (max 20s) ────────────────────────────────────
echo "[*] Waiting for backend to be ready..."
for i in {1..20}; do
    if curl -s "$JARVIS_URL/api" | grep -q "JARVIS"; then
        echo "[✓] Backend is ready!"
        break
    fi
    sleep 1
done

# ── Open Jarvis UI in Google Chrome ──────────────────────────────────────────
echo "[*] Opening JARVIS in Google Chrome..."
sleep 1
open -a "Google Chrome" "$JARVIS_URL"

echo "[✓] JARVIS is live at $JARVIS_URL"
echo ""
