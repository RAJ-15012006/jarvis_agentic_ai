#!/bin/bash
# uninstall_autostart.sh
# Removes the JARVIS LaunchAgent so it no longer auto-starts on login.

PLIST_NAME="com.raj.jarvis.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo ""
echo "Uninstalling JARVIS AutoStart..."

if launchctl list | grep -q "com.raj.jarvis" 2>/dev/null; then
    launchctl unload "$PLIST_DEST" 2>/dev/null && echo "  ✓ Agent unloaded"
fi

if [ -f "$PLIST_DEST" ]; then
    rm "$PLIST_DEST"
    echo "  ✓ Plist removed"
fi

# Kill any running Jarvis process
pkill -f "uvicorn.*main:socket_app" 2>/dev/null && echo "  ✓ Stopped Jarvis backend" || true

echo ""
echo "  JARVIS auto-start has been DISABLED."
echo "  You can still start it manually with: bash jarvis_autostart.sh"
echo ""
