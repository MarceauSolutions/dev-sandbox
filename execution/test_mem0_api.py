#!/usr/bin/env python3
"""
Test script for Mem0 API.

This script validates the Mem0 API is running correctly and all endpoints work.
Can be run locally or on EC2 after deployment.

Usage:
    # Test local instance
    python execution/test_mem0_api.py

    # Test EC2 instance (from local machine)
    ssh ec2 'cd dev-sandbox && python3 -m execution.test_mem0_api'

Author: William Marceau Jr.
Created: 2026-02-15
"""

import json
import sys
import time
from typing import Dict, Any

import requests


API_BASE_URL = "http://localhost:5020"


def print_test(test_name: str):
    """Print test header."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print('='*60)


def print_result(success: bool, message: str, data: Any = None):
    """Print test result."""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {message}")
    if data:
        print(f"Response: {json.dumps(data, indent=2)}")


def test_health_check() -> bool:
    """Test health check endpoint."""
    print_test("Health Check")

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        data = response.json()

        if response.status_code == 200 and data.get("status") == "healthy":
            print_result(True, "Health check passed", data)
            return True
        else:
            print_result(False, f"Health check failed: {data}")
            return False
    except Exception as e:
        print_result(False, f"Health check failed: {e}")
        return False


def test_add_memory() -> tuple[bool, str]:
    """Test adding a memory."""
    print_test("Add Memory")

    try:
        payload = {
            "agent_id": "test-agent",
            "content": "This is a test memory for validation purposes.",
            "metadata": {
                "category": "test",
                "priority": "high",
                "tags": ["test", "validation"]
            }
        }

        response = requests.post(
            f"{API_BASE_URL}/memory",
            json=payload,
            timeout=10
        )
        data = response.json()

        if response.status_code == 200 and data.get("status") == "success":
            print_result(True, "Memory added successfully", data)
            # Extract memory ID if available
            memory_id = None
            if "result" in data and isinstance(data["result"], dict):
                memory_id = data["result"].get("id")
            return True, memory_id
        else:
            print_result(False, f"Failed to add memory: {data}")
            return False, None
    except Exception as e:
        print_result(False, f"Failed to add memory: {e}")
        return False, None


def test_search_memory(query: str = "test") -> bool:
    """Test searching memories."""
    print_test("Search Memory")

    try:
        params = {
            "q": query,
            "agent_id": "test-agent",
            "limit": 10
        }

        response = requests.get(
            f"{API_BASE_URL}/memory/search",
            params=params,
            timeout=10
        )
        data = response.json()

        if response.status_code == 200 and data.get("status") == "success":
            print_result(
                True,
                f"Search returned {data.get('count', 0)} results",
                data
            )
            return True
        else:
            print_result(False, f"Search failed: {data}")
            return False
    except Exception as e:
        print_result(False, f"Search failed: {e}")
        return False


def test_list_all_memories() -> bool:
    """Test listing all memories."""
    print_test("List All Memories")

    try:
        params = {
            "agent_id": "test-agent",
            "limit": 100
        }

        response = requests.get(
            f"{API_BASE_URL}/memory/all",
            params=params,
            timeout=10
        )
        data = response.json()

        if response.status_code == 200 and data.get("status") == "success":
            print_result(
                True,
                f"Found {data.get('count', 0)} total memories",
                data
            )
            return True
        else:
            print_result(False, f"List failed: {data}")
            return False
    except Exception as e:
        print_result(False, f"List failed: {e}")
        return False


def test_delete_memory(memory_id: str) -> bool:
    """Test deleting a memory."""
    print_test("Delete Memory")

    if not memory_id:
        print_result(False, "No memory ID provided, skipping delete test")
        return False

    try:
        response = requests.delete(
            f"{API_BASE_URL}/memory/{memory_id}",
            timeout=10
        )
        data = response.json()

        if response.status_code == 200 and data.get("status") == "success":
            print_result(True, f"Memory {memory_id} deleted successfully", data)
            return True
        else:
            print_result(False, f"Delete failed: {data}")
            return False
    except Exception as e:
        print_result(False, f"Delete failed: {e}")
        return False


def run_all_tests():
    """Run all tests in sequence."""
    print(f"\n{'#'*60}")
    print("# Mem0 API Test Suite")
    print(f"# Target: {API_BASE_URL}")
    print(f"# Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    results = []
    memory_id = None

    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))

    # Test 2: Add Memory
    success, memory_id = test_add_memory()
    results.append(("Add Memory", success))

    # Test 3: Search Memory
    results.append(("Search Memory", test_search_memory()))

    # Test 4: List All Memories
    results.append(("List All Memories", test_list_all_memories()))

    # Test 5: Delete Memory (if we got an ID)
    if memory_id:
        results.append(("Delete Memory", test_delete_memory(memory_id)))

    # Print Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print('='*60)

    return passed == total


def main():
    """Main entry point."""
    # Check if API is reachable
    try:
        requests.get(f"{API_BASE_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"\n✗ ERROR: Cannot connect to {API_BASE_URL}")
        print("Is the Mem0 API running?")
        print("\nStart it with:")
        print("  python -m execution.mem0_api")
        print("\nOr check the service:")
        print("  sudo systemctl status mem0-api")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)

    # Run tests
    success = run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
