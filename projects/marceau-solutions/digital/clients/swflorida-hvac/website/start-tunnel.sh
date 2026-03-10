#!/bin/bash
# Start SW Florida Comfort HVAC website with ngrok tunnel

echo "🚀 Starting SW Florida Comfort HVAC Website Tunnel"
echo "=================================================="
echo ""

# Check if port 3002 is already in use
if lsof -Pi :3002 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 3002 is already in use"
    echo "   Existing server:"
    lsof -Pi :3002 -sTCP:LISTEN
    echo ""
    read -p "Kill existing server and continue? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill $(lsof -t -i:3002)
        echo "✓ Killed existing server"
        sleep 1
    else
        echo "Exiting..."
        exit 1
    fi
fi

# Start the web server in background
echo "1️⃣  Starting web server on port 3002..."
cd /Users/williammarceaujr./swflorida-comfort-hvac
python3 serve.py > /tmp/swflorida-server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Check if server started successfully
if ! ps -p $SERVER_PID > /dev/null; then
    echo "❌ Failed to start web server"
    cat /tmp/swflorida-server.log
    exit 1
fi

echo "✓ Web server running (PID: $SERVER_PID)"
echo "  Local URL: http://localhost:3002"
echo ""

# Start ngrok tunnel
echo "2️⃣  Starting ngrok tunnel..."
echo "  Domain: www.swfloridacomfort.com"
echo ""

ngrok start hvac

# If ngrok exits, kill the web server
echo ""
echo "Shutting down..."
kill $SERVER_PID
echo "✓ Web server stopped"
