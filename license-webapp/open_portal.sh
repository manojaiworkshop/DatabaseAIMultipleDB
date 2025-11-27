#!/bin/bash

# Simple Portal Launcher - Just opens the HTML file directly in browser
# No server required!

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🚀 Opening PGAIView License Portal..."
echo ""
echo "⚠️  NOTE: Make sure the License Server is running!"
echo "   Start it with: python3 ../license_server.py"
echo ""

# Open in default browser
if command -v xdg-open &> /dev/null; then
    xdg-open "$SCRIPT_DIR/index.html"
    echo "✓ Opened in default browser"
elif command -v open &> /dev/null; then
    open "$SCRIPT_DIR/index.html"
    echo "✓ Opened in default browser"
elif command -v firefox &> /dev/null; then
    firefox "$SCRIPT_DIR/index.html" &
    echo "✓ Opened in Firefox"
elif command -v google-chrome &> /dev/null; then
    google-chrome "$SCRIPT_DIR/index.html" &
    echo "✓ Opened in Chrome"
else
    echo "❌ Could not find a browser"
    echo "Please manually open: $SCRIPT_DIR/index.html"
fi

echo ""
echo "🔧 Configure License Server URL in Settings (⚙️) if needed"
echo "   Default: http://localhost:5000"
