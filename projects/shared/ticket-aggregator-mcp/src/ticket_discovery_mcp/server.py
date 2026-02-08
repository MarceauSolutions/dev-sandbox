#!/usr/bin/env python3
"""
Ticket Discovery MCP Server

An MCP server that helps AI agents discover, compare, and find the best ticket prices
across multiple platforms. Uses official public APIs only - no automated purchasing.

Supported Platforms:
- Ticketmaster Discovery API (primary + some resale)
- SeatGeek API (aggregator with good price data)
- Eventbrite API (primarily smaller/local events)
"""

import os
import json
import httpx
from datetime import datetime, timedelta
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("ticket-discovery")

# API Configuration
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY", "")
SEATGEEK_CLIENT_ID = os.getenv("SEATGEEK_CLIENT_ID", "")
SEATGEEK_CLIENT_SECRET = os.getenv("SEATGEEK_CLIENT_SECRET", "")

# Affiliate IDs for monetization
SEATGEEK_AID = os.getenv("SEATGEEK_AFFILIATE_ID", "")
STUBHUB_AID = os.getenv("STUBHUB_AFFILIATE_ID", "")

# Base URLs
TICKETMASTER_BASE = "https://app.ticketmaster.com/discovery/v2"
SEATGEEK_BASE = "https://api.seatgeek.com/2"


async def search_ticketmaster(
    keyword: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    size: int = 20
) -> list[dict]:
    """Search Ticketmaster Discovery API for events."""
    if not TICKETMASTER_API_KEY:
        return []

    params = {
        "apikey": TICKETMASTER_API_KEY,
        "keyword": keyword,
        "size": size,
        "sort": "date,asc"
    }

    if city:
        params["city"] = city
    if state:
        params["stateCode"] = state
    if start_date:
        params["startDateTime"] = f"{start_date}T00:00:00Z"
    if end_date:
        params["endDateTime"] = f"{end_date}T23:59:59Z"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{TICKETMASTER_BASE}/events.json",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            events = []
            for event in data.get("_embedded", {}).get("events", []):
                venue = event.get("_embedded", {}).get("venues", [{}])[0]
                price_range = event.get("priceRanges", [{}])[0] if event.get("priceRanges") else {}

                events.append({
                    "source": "ticketmaster",
                    "id": event.get("id"),
                    "name": event.get("name"),
                    "date": event.get("dates", {}).get("start", {}).get("localDate"),
                    "time": event.get("dates", {}).get("start", {}).get("localTime"),
                    "venue": venue.get("name"),
                    "city": venue.get("city", {}).get("name"),
                    "state": venue.get("state", {}).get("stateCode"),
                    "min_price": price_range.get("min"),
                    "max_price": price_range.get("max"),
                    "currency": price_range.get("currency", "USD"),
                    "url": event.get("url"),
                    "image": event.get("images", [{}])[0].get("url") if event.get("images") else None
                })

            return events
        except Exception as e:
            return [{"error": f"Ticketmaster API error: {str(e)}"}]


async def search_seatgeek(
    keyword: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    size: int = 20
) -> list[dict]:
    """Search SeatGeek API for events."""
    if not SEATGEEK_CLIENT_ID:
        return []

    params = {
        "client_id": SEATGEEK_CLIENT_ID,
        "q": keyword,
        "per_page": size,
        "sort": "datetime_local.asc"
    }

    if SEATGEEK_CLIENT_SECRET:
        params["client_secret"] = SEATGEEK_CLIENT_SECRET

    # Build location filter
    if city and state:
        params["venue.city"] = city
        params["venue.state"] = state
    elif state:
        params["venue.state"] = state

    if start_date:
        params["datetime_local.gte"] = f"{start_date}T00:00:00"
    if end_date:
        params["datetime_local.lte"] = f"{end_date}T23:59:59"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{SEATGEEK_BASE}/events",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            events = []
            for event in data.get("events", []):
                venue = event.get("venue", {})
                stats = event.get("stats", {})

                # Build affiliate URL if we have an ID
                url = event.get("url", "")
                if SEATGEEK_AID and url:
                    url = f"{url}?aid={SEATGEEK_AID}"

                events.append({
                    "source": "seatgeek",
                    "id": str(event.get("id")),
                    "name": event.get("title"),
                    "date": event.get("datetime_local", "")[:10] if event.get("datetime_local") else None,
                    "time": event.get("datetime_local", "")[11:16] if event.get("datetime_local") else None,
                    "venue": venue.get("name"),
                    "city": venue.get("city"),
                    "state": venue.get("state"),
                    "min_price": stats.get("lowest_price"),
                    "max_price": stats.get("highest_price"),
                    "avg_price": stats.get("average_price"),
                    "listing_count": stats.get("listing_count"),
                    "currency": "USD",
                    "url": url,
                    "score": event.get("score"),  # SeatGeek popularity score
                    "image": event.get("performers", [{}])[0].get("image") if event.get("performers") else None
                })

            return events
        except Exception as e:
            return [{"error": f"SeatGeek API error: {str(e)}"}]


@mcp.tool()
async def search_events(
    query: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = 10
) -> str:
    """
    Search for events across multiple ticket platforms.

    Args:
        query: Artist name, event name, or keywords to search for
        city: Filter by city name (e.g., "Miami", "New York")
        state: Filter by state code (e.g., "FL", "NY", "CA")
        start_date: Filter events on or after this date (YYYY-MM-DD format)
        end_date: Filter events on or before this date (YYYY-MM-DD format)
        max_results: Maximum number of results per platform (default: 10)

    Returns:
        JSON list of events from all platforms, sorted by date
    """
    # Search both platforms in parallel
    import asyncio

    ticketmaster_task = search_ticketmaster(query, city, state, start_date, end_date, max_results)
    seatgeek_task = search_seatgeek(query, city, state, start_date, end_date, max_results)

    results = await asyncio.gather(ticketmaster_task, seatgeek_task)

    all_events = []
    for result in results:
        if isinstance(result, list):
            all_events.extend([e for e in result if "error" not in e])

    # Sort by date
    all_events.sort(key=lambda x: x.get("date") or "9999-99-99")

    # Add summary
    summary = {
        "total_events": len(all_events),
        "platforms_searched": ["ticketmaster", "seatgeek"],
        "query": query,
        "filters": {
            "city": city,
            "state": state,
            "start_date": start_date,
            "end_date": end_date
        }
    }

    return json.dumps({
        "summary": summary,
        "events": all_events[:max_results * 2]  # Cap total results
    }, indent=2)


@mcp.tool()
async def compare_prices(
    event_name: str,
    date: str,
    city: Optional[str] = None,
    state: Optional[str] = None
) -> str:
    """
    Compare ticket prices across platforms for a specific event.

    Args:
        event_name: Name of the event or artist
        date: Date of the event (YYYY-MM-DD format)
        city: City where the event is located
        state: State code where the event is located (e.g., "FL", "CA")

    Returns:
        Price comparison across platforms with recommendations
    """
    import asyncio

    # Search with tight date range to find specific event
    end_date = date  # Same day

    ticketmaster_task = search_ticketmaster(event_name, city, state, date, end_date, 5)
    seatgeek_task = search_seatgeek(event_name, city, state, date, end_date, 5)

    results = await asyncio.gather(ticketmaster_task, seatgeek_task)

    comparisons = []

    for result in results:
        if isinstance(result, list):
            for event in result:
                if "error" not in event and event.get("min_price"):
                    comparisons.append({
                        "platform": event.get("source"),
                        "event_name": event.get("name"),
                        "venue": event.get("venue"),
                        "date": event.get("date"),
                        "min_price": event.get("min_price"),
                        "max_price": event.get("max_price"),
                        "avg_price": event.get("avg_price"),
                        "listing_count": event.get("listing_count"),
                        "url": event.get("url")
                    })

    # Sort by minimum price
    comparisons.sort(key=lambda x: x.get("min_price") or float("inf"))

    # Generate recommendation
    recommendation = None
    if comparisons:
        best = comparisons[0]
        recommendation = {
            "best_price_platform": best["platform"],
            "best_min_price": best["min_price"],
            "best_url": best["url"],
            "savings_vs_highest": None
        }

        if len(comparisons) > 1:
            highest_min = max(c.get("min_price", 0) for c in comparisons if c.get("min_price"))
            if highest_min and best["min_price"]:
                recommendation["savings_vs_highest"] = round(highest_min - best["min_price"], 2)

    return json.dumps({
        "event_query": event_name,
        "date": date,
        "location": f"{city}, {state}" if city and state else state or city or "Any",
        "platforms_compared": len(set(c["platform"] for c in comparisons)),
        "recommendation": recommendation,
        "price_comparison": comparisons
    }, indent=2)


@mcp.tool()
async def get_event_details(
    event_id: str,
    platform: str = "ticketmaster"
) -> str:
    """
    Get detailed information about a specific event.

    Args:
        event_id: The event ID from a previous search
        platform: Which platform the event is from ("ticketmaster" or "seatgeek")

    Returns:
        Detailed event information including venue, pricing, and purchase link
    """
    if platform == "ticketmaster":
        if not TICKETMASTER_API_KEY:
            return json.dumps({"error": "Ticketmaster API key not configured"})

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{TICKETMASTER_BASE}/events/{event_id}.json",
                    params={"apikey": TICKETMASTER_API_KEY},
                    timeout=10.0
                )
                response.raise_for_status()
                event = response.json()

                venue = event.get("_embedded", {}).get("venues", [{}])[0]
                price_ranges = event.get("priceRanges", [])

                return json.dumps({
                    "platform": "ticketmaster",
                    "id": event.get("id"),
                    "name": event.get("name"),
                    "description": event.get("info") or event.get("pleaseNote"),
                    "date": event.get("dates", {}).get("start", {}).get("localDate"),
                    "time": event.get("dates", {}).get("start", {}).get("localTime"),
                    "timezone": event.get("dates", {}).get("timezone"),
                    "venue": {
                        "name": venue.get("name"),
                        "address": venue.get("address", {}).get("line1"),
                        "city": venue.get("city", {}).get("name"),
                        "state": venue.get("state", {}).get("stateCode"),
                        "postal_code": venue.get("postalCode"),
                        "country": venue.get("country", {}).get("name")
                    },
                    "price_ranges": [
                        {
                            "type": pr.get("type"),
                            "min": pr.get("min"),
                            "max": pr.get("max"),
                            "currency": pr.get("currency")
                        }
                        for pr in price_ranges
                    ],
                    "sale_status": event.get("dates", {}).get("status", {}).get("code"),
                    "url": event.get("url"),
                    "seatmap": event.get("seatmap", {}).get("staticUrl"),
                    "age_restriction": event.get("ageRestrictions", {}).get("legalAgeEnforced")
                }, indent=2)
            except Exception as e:
                return json.dumps({"error": f"Failed to get event details: {str(e)}"})

    elif platform == "seatgeek":
        if not SEATGEEK_CLIENT_ID:
            return json.dumps({"error": "SeatGeek API credentials not configured"})

        async with httpx.AsyncClient() as client:
            try:
                params = {"client_id": SEATGEEK_CLIENT_ID}
                if SEATGEEK_CLIENT_SECRET:
                    params["client_secret"] = SEATGEEK_CLIENT_SECRET

                response = await client.get(
                    f"{SEATGEEK_BASE}/events/{event_id}",
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                event = response.json()

                venue = event.get("venue", {})
                stats = event.get("stats", {})

                url = event.get("url", "")
                if SEATGEEK_AID and url:
                    url = f"{url}?aid={SEATGEEK_AID}"

                return json.dumps({
                    "platform": "seatgeek",
                    "id": event.get("id"),
                    "name": event.get("title"),
                    "short_title": event.get("short_title"),
                    "date": event.get("datetime_local"),
                    "venue": {
                        "name": venue.get("name"),
                        "address": venue.get("address"),
                        "city": venue.get("city"),
                        "state": venue.get("state"),
                        "postal_code": venue.get("postal_code"),
                        "country": venue.get("country"),
                        "capacity": venue.get("capacity")
                    },
                    "pricing": {
                        "lowest_price": stats.get("lowest_price"),
                        "highest_price": stats.get("highest_price"),
                        "average_price": stats.get("average_price"),
                        "median_price": stats.get("median_price"),
                        "listing_count": stats.get("listing_count")
                    },
                    "popularity_score": event.get("score"),
                    "url": url,
                    "performers": [
                        {"name": p.get("name"), "type": p.get("type")}
                        for p in event.get("performers", [])
                    ]
                }, indent=2)
            except Exception as e:
                return json.dumps({"error": f"Failed to get event details: {str(e)}"})

    else:
        return json.dumps({"error": f"Unknown platform: {platform}"})


@mcp.tool()
async def get_upcoming_events(
    artist: str,
    state: Optional[str] = None,
    days_ahead: int = 90
) -> str:
    """
    Find upcoming events for an artist within a time window.

    Args:
        artist: Artist or performer name
        state: Limit to a specific state (e.g., "FL", "CA", "NY")
        days_ahead: How many days ahead to search (default: 90)

    Returns:
        List of upcoming events for the artist
    """
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    return await search_events(
        query=artist,
        state=state,
        start_date=start_date,
        end_date=end_date,
        max_results=20
    )


@mcp.tool()
async def find_cheap_tickets(
    event_name: str,
    max_price: float,
    state: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """
    Find tickets under a specific price point.

    Args:
        event_name: Artist name or event to search for
        max_price: Maximum ticket price in USD
        state: Limit to a specific state (e.g., "FL", "CA")
        start_date: Start of date range (YYYY-MM-DD)
        end_date: End of date range (YYYY-MM-DD)

    Returns:
        Events with tickets available under the specified price
    """
    import asyncio

    # Default to next 90 days if no dates specified
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    if not end_date:
        end_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")

    ticketmaster_task = search_ticketmaster(event_name, None, state, start_date, end_date, 25)
    seatgeek_task = search_seatgeek(event_name, None, state, start_date, end_date, 25)

    results = await asyncio.gather(ticketmaster_task, seatgeek_task)

    cheap_events = []
    for result in results:
        if isinstance(result, list):
            for event in result:
                if "error" not in event:
                    min_price = event.get("min_price")
                    if min_price and min_price <= max_price:
                        cheap_events.append(event)

    # Sort by price (cheapest first)
    cheap_events.sort(key=lambda x: x.get("min_price") or float("inf"))

    return json.dumps({
        "query": event_name,
        "max_price_filter": max_price,
        "events_found": len(cheap_events),
        "events": cheap_events
    }, indent=2)


@mcp.tool()
async def check_api_status() -> str:
    """
    Check which ticket APIs are configured and available.

    Returns:
        Status of each configured API
    """
    status = {
        "ticketmaster": {
            "configured": bool(TICKETMASTER_API_KEY),
            "api_key_set": "Yes" if TICKETMASTER_API_KEY else "No - Set TICKETMASTER_API_KEY env var"
        },
        "seatgeek": {
            "configured": bool(SEATGEEK_CLIENT_ID),
            "client_id_set": "Yes" if SEATGEEK_CLIENT_ID else "No - Set SEATGEEK_CLIENT_ID env var",
            "client_secret_set": "Yes" if SEATGEEK_CLIENT_SECRET else "No (optional)"
        },
        "affiliate_ids": {
            "seatgeek_aid": "Configured" if SEATGEEK_AID else "Not set",
            "stubhub_aid": "Configured" if STUBHUB_AID else "Not set"
        },
        "instructions": {
            "ticketmaster": "Get free API key at https://developer.ticketmaster.com/",
            "seatgeek": "Get free client ID at https://seatgeek.com/account/develop"
        }
    }

    return json.dumps(status, indent=2)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
