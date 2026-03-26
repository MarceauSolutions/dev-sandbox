#!/usr/bin/env python3
"""
Simple HTTP server for SW Florida Comfort HVAC website
Serves on port 3002 for ngrok tunnel to www.swfloridacomfort.com
"""

import http.server
import socketserver
import os

PORT = 3002
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers if needed
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

if __name__ == "__main__":
    os.chdir(DIRECTORY)

    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"✓ Serving SW Florida Comfort HVAC website at http://localhost:{PORT}")
        print(f"✓ Directory: {DIRECTORY}")
        print(f"✓ Ngrok will tunnel this to: www.swfloridacomfort.com")
        print(f"\nPress Ctrl+C to stop")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped")
