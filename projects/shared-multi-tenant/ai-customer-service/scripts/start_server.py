#!/usr/bin/env python3
"""Start the Voice AI server with proper health checks and safeguards.

This script:
1. Checks if server is already running
2. Kills stale processes if needed
3. Starts uvicorn server
4. Verifies ngrok tunnel is active
5. Makes health check before allowing calls

Usage:
    python scripts/start_server.py [--restart]
"""

import os
import sys
import time
import subprocess
import requests
import signal
import json

# Configuration
SERVER_PORT = 8000
NGROK_API = "http://localhost:4040/api/tunnels"
HEALTH_ENDPOINT = "/health"
MAX_RETRIES = 3
RETRY_DELAY = 2


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def kill_process_on_port(port: int) -> bool:
    """Kill process using a specific port."""
    try:
        result = subprocess.run(
            f"lsof -ti:{port} | xargs kill -9 2>/dev/null",
            shell=True,
            capture_output=True
        )
        time.sleep(1)
        return not is_port_in_use(port)
    except Exception as e:
        print(f"Warning: Could not kill process on port {port}: {e}")
        return False


def check_server_health(base_url: str) -> dict:
    """Check server health endpoint."""
    try:
        response = requests.get(f"{base_url}{HEALTH_ENDPOINT}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def get_ngrok_url() -> str:
    """Get the public ngrok URL."""
    try:
        response = requests.get(NGROK_API, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("tunnels"):
                for tunnel in data["tunnels"]:
                    if tunnel.get("proto") == "https":
                        return tunnel["public_url"]
                return data["tunnels"][0]["public_url"]
    except requests.RequestException:
        pass
    return None


def start_uvicorn() -> subprocess.Popen:
    """Start uvicorn server."""
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    process = subprocess.Popen(
        ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", str(SERVER_PORT)],
        stdout=open("/tmp/server.log", "w"),
        stderr=subprocess.STDOUT,
        preexec_fn=os.setpgrp
    )
    return process


def start_ngrok() -> subprocess.Popen:
    """Start ngrok tunnel with pooling enabled."""
    # Kill any existing ngrok
    subprocess.run("pkill -f ngrok 2>/dev/null", shell=True)
    time.sleep(2)

    process = subprocess.Popen(
        ["ngrok", "http", str(SERVER_PORT), "--pooling-enabled"],
        stdout=open("/tmp/ngrok.log", "w"),
        stderr=subprocess.STDOUT,
        preexec_fn=os.setpgrp
    )
    return process


def verify_system(ngrok_url: str) -> dict:
    """Verify entire system is working."""
    health = check_server_health(ngrok_url)
    if not health:
        return {"status": "error", "message": "Health check failed via ngrok"}

    return {
        "status": "healthy",
        "local_url": f"http://localhost:{SERVER_PORT}",
        "public_url": ngrok_url,
        "twilio_configured": health.get("twilio_configured", False),
        "anthropic_configured": health.get("anthropic_configured", False)
    }


def main(restart: bool = False):
    """Main startup routine."""
    print("🚀 Voice AI Server Startup\n")

    # Step 1: Check if server is already running
    print("1️⃣ Checking existing processes...")

    if is_port_in_use(SERVER_PORT):
        if restart:
            print(f"   Port {SERVER_PORT} in use, killing existing process...")
            if not kill_process_on_port(SERVER_PORT):
                print(f"   ❌ Failed to kill process on port {SERVER_PORT}")
                sys.exit(1)
        else:
            # Check if it's healthy
            health = check_server_health(f"http://localhost:{SERVER_PORT}")
            if health:
                print(f"   ✅ Server already running and healthy")
            else:
                print(f"   ⚠️ Server on port {SERVER_PORT} not responding, use --restart to restart")
                sys.exit(1)
    else:
        print(f"   Starting uvicorn on port {SERVER_PORT}...")
        start_uvicorn()
        time.sleep(3)

        # Verify startup
        for attempt in range(MAX_RETRIES):
            if check_server_health(f"http://localhost:{SERVER_PORT}"):
                print("   ✅ Uvicorn started successfully")
                break
            print(f"   Waiting for server... (attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
        else:
            print("   ❌ Server failed to start")
            print("   Check /tmp/server.log for errors")
            sys.exit(1)

    # Step 2: Check ngrok
    print("\n2️⃣ Checking ngrok tunnel...")

    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("   Starting ngrok tunnel...")
        start_ngrok()
        time.sleep(5)

        for attempt in range(MAX_RETRIES):
            ngrok_url = get_ngrok_url()
            if ngrok_url:
                break
            print(f"   Waiting for ngrok... (attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)

        if not ngrok_url:
            print("   ❌ Failed to start ngrok tunnel")
            print("   Check /tmp/ngrok.log for errors")
            sys.exit(1)

    print(f"   ✅ ngrok URL: {ngrok_url}")

    # Step 3: Full system verification
    print("\n3️⃣ Verifying system...")

    result = verify_system(ngrok_url)
    if result["status"] != "healthy":
        print(f"   ❌ {result['message']}")
        sys.exit(1)

    print("   ✅ System healthy and ready!")

    # Summary
    print("\n" + "=" * 50)
    print("✅ VOICE AI SERVER READY")
    print("=" * 50)
    print(f"   Local:  http://localhost:{SERVER_PORT}")
    print(f"   Public: {ngrok_url}")
    print(f"   Twilio: {'✅' if result['twilio_configured'] else '❌'}")
    print(f"   Claude: {'✅' if result['anthropic_configured'] else '❌'}")
    print("\n   To make outreach calls:")
    print("   python scripts/outreach_call.py <phone> --person Name --business Company")
    print("\n   Logs: tail -f /tmp/server.log")


if __name__ == "__main__":
    restart = "--restart" in sys.argv
    main(restart=restart)
