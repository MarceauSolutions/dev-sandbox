#!/usr/bin/env python3
"""
health-check.py — Check all PT business and infrastructure services.

Usage:
    python scripts/health-check.py
    python scripts/health-check.py --verbose
"""

import argparse
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


CHECKS = [
    {
        "name": "FitAI API (Swagger Docs)",
        "url": "https://fitai.marceausolutions.com/docs",
        "expect_status": 200,
    },
    {
        "name": "PDF API (Templates Endpoint)",
        "url": "https://fitai.marceausolutions.com/api/pdf/templates",
        "expect_status": 200,
    },
    {
        "name": "n8n Dashboard",
        "url": "http://34.193.98.97:5678/healthz",
        "expect_status": 200,
    },
    {
        "name": "n8n HTTPS (via domain)",
        "url": "https://n8n.marceausolutions.com/healthz",
        "expect_status": 200,
    },
    {
        "name": "Mem0 API",
        "url": "http://34.193.98.97:5020/health",
        "expect_status": 200,
    },
    {
        "name": "Python Bridge API",
        "url": "http://34.193.98.97:5010/health",
        "expect_status": 200,
    },
    {
        "name": "Website (marceausolutions.com)",
        "url": "https://marceausolutions.com",
        "expect_status": 200,
    },
    {
        "name": "Coaching Page",
        "url": "https://marceausolutions.com/coaching.html",
        "expect_status": 200,
    },
]


def check_url(url: str, timeout: int = 10) -> tuple:
    """Check a URL and return (status_code, response_time_ms, error_msg)."""
    start = time.time()
    try:
        req = Request(url, headers={"User-Agent": "MarceauHealthCheck/1.0"})
        resp = urlopen(req, timeout=timeout)
        elapsed = (time.time() - start) * 1000
        return resp.status, elapsed, None
    except HTTPError as e:
        elapsed = (time.time() - start) * 1000
        return e.code, elapsed, str(e)
    except URLError as e:
        elapsed = (time.time() - start) * 1000
        return 0, elapsed, str(e.reason)
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return 0, elapsed, str(e)


def main():
    parser = argparse.ArgumentParser(description="PT Business Health Check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    print("=" * 60)
    print("  Marceau Solutions — Service Health Check")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    passed = 0
    failed = 0
    results = []

    for check in CHECKS:
        name = check["name"]
        url = check["url"]
        expected = check["expect_status"]

        status, ms, err = check_url(url)
        ok = status == expected

        if ok:
            symbol = "PASS"
            passed += 1
        else:
            symbol = "FAIL"
            failed += 1

        results.append((name, symbol, status, ms, err))

        # Print result
        status_str = f"{status}" if status else "---"
        line = f"  [{symbol}] {name:<35} {status_str:>3}  {ms:>7.0f}ms"
        if not ok and err:
            line += f"  ({err[:50]})"
        print(line)

    print()
    print("-" * 60)
    print(f"  Results: {passed} passed, {failed} failed, {len(CHECKS)} total")
    print("-" * 60)

    if failed > 0:
        print("\n  Failed services:")
        for name, symbol, status, ms, err in results:
            if symbol == "FAIL":
                print(f"    - {name}: {err or f'Expected 200, got {status}'}")
        print()
        sys.exit(1)
    else:
        print("\n  All services healthy!")
        sys.exit(0)


if __name__ == "__main__":
    main()
