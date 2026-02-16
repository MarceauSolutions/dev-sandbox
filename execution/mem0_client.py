#!/usr/bin/env python3
"""
Mem0 Client Library - Simple Python client for Mem0 API.

This library provides a clean interface for adding, searching, and managing
memories across all three agents (Claude Code, Clawdbot, Ralph).

Usage:
    from execution.mem0_client import Mem0Client

    # Initialize client
    client = Mem0Client(agent_id="claude-code")

    # Add a memory
    client.add("User prefers concise responses without emojis")

    # Search memories
    results = client.search("preferences")

    # List all memories
    all_memories = client.list_all()

    # Add with metadata
    client.add(
        "User is working on fitness-influencer project",
        metadata={"category": "context", "project": "fitness-influencer"}
    )

Author: William Marceau Jr.
Created: 2026-02-15
"""

from typing import Any, Dict, List, Optional

import requests


class Mem0ClientError(Exception):
    """Base exception for Mem0 client errors."""
    pass


class Mem0Client:
    """
    Simple client for Mem0 API.

    Provides methods for adding, searching, listing, updating, and deleting
    memories for a specific agent.

    Args:
        agent_id: Agent identifier (claude-code, clawdbot, ralph)
        base_url: API base URL (default: http://localhost:5020)
        timeout: Request timeout in seconds (default: 10)

    Example:
        client = Mem0Client("claude-code")
        client.add("User prefers terse responses")
        results = client.search("preferences")
    """

    def __init__(
        self,
        agent_id: str,
        base_url: str = "http://localhost:5020",
        timeout: int = 10
    ):
        """Initialize the Mem0 client."""
        self.agent_id = agent_id
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            json: JSON body for POST/PUT requests
            params: Query parameters for GET requests

        Returns:
            Response JSON as dict

        Raises:
            Mem0ClientError: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                json=json,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Mem0ClientError(f"API request failed: {e}")

    def health(self) -> Dict[str, Any]:
        """
        Check API health.

        Returns:
            Health status dict

        Example:
            status = client.health()
            print(status["status"])  # "healthy"
        """
        return self._request("GET", "/health")

    def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a memory.

        Args:
            content: Memory content/text
            metadata: Optional metadata dict

        Returns:
            API response with memory ID and confirmation

        Example:
            result = client.add(
                "User prefers concise responses",
                metadata={"category": "preference", "priority": "high"}
            )
        """
        payload = {
            "agent_id": self.agent_id,
            "content": content,
            "metadata": metadata or {}
        }
        return self._request("POST", "/memory", json=payload)

    def search(
        self,
        query: str,
        limit: int = 10,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories by query.

        Args:
            query: Search query string
            limit: Max results to return (default: 10)
            agent_id: Override default agent_id for cross-agent search

        Returns:
            List of matching memories

        Example:
            results = client.search("preferences", limit=5)
            for memory in results:
                print(memory["content"])
        """
        params = {
            "q": query,
            "agent_id": agent_id or self.agent_id,
            "limit": limit
        }
        response = self._request("GET", "/memory/search", params=params)
        return response.get("results", [])

    def list_all(
        self,
        limit: int = 100,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all memories for agent.

        Args:
            limit: Max results to return (default: 100)
            agent_id: Override default agent_id

        Returns:
            List of all memories

        Example:
            all_memories = client.list_all()
            print(f"Found {len(all_memories)} memories")
        """
        params = {
            "agent_id": agent_id or self.agent_id,
            "limit": limit
        }
        response = self._request("GET", "/memory/all", params=params)
        return response.get("results", [])

    def update(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update a memory.

        Args:
            memory_id: Memory ID to update
            content: New content
            metadata: New metadata

        Returns:
            Update confirmation

        Example:
            client.update("abc123", "Updated preference", {"priority": "medium"})
        """
        payload = {
            "content": content,
            "metadata": metadata or {}
        }
        return self._request("PUT", f"/memory/{memory_id}", json=payload)

    def delete(self, memory_id: str) -> Dict[str, Any]:
        """
        Delete a memory.

        Args:
            memory_id: Memory ID to delete

        Returns:
            Deletion confirmation

        Example:
            client.delete("abc123")
        """
        return self._request("DELETE", f"/memory/{memory_id}")

    def search_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories by metadata category.

        Args:
            category: Metadata category to filter by
            limit: Max results

        Returns:
            Matching memories

        Example:
            prefs = client.search_by_category("preference")
        """
        # First get all memories, then filter by metadata
        all_memories = self.list_all(limit=limit)
        return [
            m for m in all_memories
            if m.get("metadata", {}).get("category") == category
        ]

    def count(self, agent_id: Optional[str] = None) -> int:
        """
        Get total memory count for agent.

        Args:
            agent_id: Override default agent_id

        Returns:
            Total number of memories

        Example:
            count = client.count()
            print(f"Agent has {count} memories")
        """
        response = self._request(
            "GET",
            "/memory/all",
            params={"agent_id": agent_id or self.agent_id, "limit": 1}
        )
        return response.get("count", 0)


# Convenience functions for common operations
def add_memory(content: str, agent_id: str = "claude-code", metadata: Dict = None):
    """
    Quick add memory function.

    Args:
        content: Memory content
        agent_id: Agent identifier (default: claude-code)
        metadata: Optional metadata

    Returns:
        API response

    Example:
        add_memory("User prefers terse responses", metadata={"category": "preference"})
    """
    client = Mem0Client(agent_id)
    return client.add(content, metadata)


def search_memory(query: str, agent_id: str = "claude-code", limit: int = 10):
    """
    Quick search function.

    Args:
        query: Search query
        agent_id: Agent identifier (default: claude-code)
        limit: Max results

    Returns:
        List of matching memories

    Example:
        results = search_memory("preferences")
    """
    client = Mem0Client(agent_id)
    return client.search(query, limit)


def list_memories(agent_id: str = "claude-code", limit: int = 100):
    """
    Quick list function.

    Args:
        agent_id: Agent identifier (default: claude-code)
        limit: Max results

    Returns:
        List of all memories

    Example:
        all_memories = list_memories("clawdbot")
    """
    client = Mem0Client(agent_id)
    return client.list_all(limit)


# Example usage
if __name__ == "__main__":
    import sys

    # Check if API is running
    try:
        client = Mem0Client("test-agent")
        health = client.health()
        print(f"API Status: {health['status']}")
    except Mem0ClientError as e:
        print(f"ERROR: {e}")
        print("\nIs the Mem0 API running?")
        print("Start it with: python -m execution.mem0_api")
        sys.exit(1)

    # Demo operations
    print("\n=== Mem0 Client Demo ===\n")

    # Add a memory
    print("1. Adding memory...")
    result = client.add(
        "This is a test memory from the client library",
        metadata={"category": "test", "source": "demo"}
    )
    print(f"   Added: {result.get('status')}")

    # Search
    print("\n2. Searching for 'test'...")
    results = client.search("test", limit=5)
    print(f"   Found {len(results)} results")

    # List all
    print("\n3. Listing all memories...")
    all_memories = client.list_all()
    print(f"   Total memories: {len(all_memories)}")

    # Count
    print("\n4. Counting memories...")
    count = client.count()
    print(f"   Count: {count}")

    print("\n=== Demo Complete ===\n")
