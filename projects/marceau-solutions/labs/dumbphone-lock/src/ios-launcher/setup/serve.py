#!/usr/bin/env python3
"""
One-tap profile installer for DumbPhone.
Hosts the .mobileconfig on your local network so your iPhone can install it.
"""
import http.server
import socket
import os
import sys

PORT = 8888
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class ProfileHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        if self.path.endswith('.mobileconfig'):
            self.send_header('Content-Type', 'application/x-apple-aspen-config')
        super().end_headers()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()

if __name__ == '__main__':
    ip = get_local_ip()
    url = f"http://{ip}:{PORT}/profile.mobileconfig"

    print(f"\n{'='*50}")
    print(f"  DUMB PHONE PROFILE INSTALLER")
    print(f"{'='*50}")
    print(f"\n  On your iPhone, open Safari and go to:\n")
    print(f"  {url}")
    print(f"\n  Then: Settings > General > VPN & Device Management")
    print(f"  > Install the 'Dumb Phone Mode' profile")
    print(f"\n  Press Ctrl+C to stop the server")
    print(f"{'='*50}\n")

    with http.server.HTTPServer(('', PORT), ProfileHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
