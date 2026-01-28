"""
ABC Trainerize API Client

Async HTTP client for the ABC Trainerize personal training platform API.
Implements OAuth 2.0 authentication, rate limiting, and comprehensive
methods for client management, training programs, nutrition, messaging,
scheduling, analytics, and habits.

Since the official Trainerize developer API documentation is password-protected,
endpoint paths follow REST conventions inferred from their Zapier integration
and standard fitness platform API patterns.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class TrainerizeAPIError(Exception):
    """Custom exception for Trainerize API errors.

    Attributes:
        status_code: HTTP status code from the API response.
        message: Human-readable error message.
        response_body: Raw response body if available.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        return " ".join(parts)


class TrainerizeClient:
    """Async client for the ABC Trainerize API.

    Handles OAuth 2.0 authentication (client credentials flow), automatic
    token refresh, rate limiting, and provides typed methods for every
    supported API operation.

    Environment Variables:
        TRAINERIZE_API_URL: Base URL for the API (default: https://api.trainerize.com)
        TRAINERIZE_CLIENT_ID: OAuth 2.0 client ID
        TRAINERIZE_CLIENT_SECRET: OAuth 2.0 client secret

    Usage:
        async with TrainerizeClient() as client:
            clients = await client.list_clients(tag="VIP")
    """

    DEFAULT_BASE_URL = "https://api.trainerize.com"
    TOKEN_ENDPOINT = "/oauth/token"
    API_PREFIX = "/api/v1"

    # Rate limiting: max 60 requests per minute
    RATE_LIMIT_MAX_REQUESTS = 60
    RATE_LIMIT_WINDOW_SECONDS = 60

    def __init__(
        self,
        base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """Initialize the Trainerize API client.

        Args:
            base_url: API base URL. Falls back to TRAINERIZE_API_URL env var.
            client_id: OAuth client ID. Falls back to TRAINERIZE_CLIENT_ID env var.
            client_secret: OAuth client secret. Falls back to TRAINERIZE_CLIENT_SECRET env var.
        """
        self.base_url = (
            base_url
            or os.getenv("TRAINERIZE_API_URL", self.DEFAULT_BASE_URL)
        ).rstrip("/")
        self.client_id = client_id or os.getenv("TRAINERIZE_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("TRAINERIZE_CLIENT_SECRET", "")

        if not self.client_id or not self.client_secret:
            logger.warning(
                "Trainerize client_id or client_secret not configured. "
                "Set TRAINERIZE_CLIENT_ID and TRAINERIZE_CLIENT_SECRET environment variables."
            )

        # OAuth token state
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._refresh_token: Optional[str] = None

        # Rate limiting state
        self._request_timestamps: List[float] = []

        # HTTP client
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "TrainerizeClient":
        """Enter async context manager."""
        self._http_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(30.0),
            headers={"User-Agent": "TrainerizeMCP/1.0.0"},
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager and close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get the HTTP client, raising if not initialized."""
        if self._http_client is None:
            raise TrainerizeAPIError(
                "HTTP client not initialized. Use 'async with TrainerizeClient() as client:'"
            )
        return self._http_client

    # ─────────────────────────────────────────────
    # Authentication
    # ─────────────────────────────────────────────

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid access token, refreshing if necessary.

        Implements OAuth 2.0 client credentials flow. If a refresh token is
        available and the access token is expired, it will attempt a refresh
        before falling back to a fresh client credentials grant.
        """
        if self._access_token and time.time() < self._token_expires_at - 30:
            return  # Token still valid (with 30s buffer)

        if self._refresh_token:
            try:
                await self._refresh_access_token()
                return
            except TrainerizeAPIError:
                logger.warning("Token refresh failed, falling back to client credentials grant.")

        await self._request_access_token()

    async def _request_access_token(self) -> None:
        """Request a new access token using client credentials grant.

        Raises:
            TrainerizeAPIError: If token request fails.
        """
        client = self._get_client()
        logger.info("Requesting new access token via client credentials grant.")

        try:
            response = await client.post(
                self.TOKEN_ENDPOINT,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as e:
            raise TrainerizeAPIError(f"Failed to request access token: {e}")

        if response.status_code != 200:
            raise TrainerizeAPIError(
                "Failed to obtain access token",
                status_code=response.status_code,
                response_body=response.text,
            )

        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600)
        self._refresh_token = data.get("refresh_token")
        logger.info("Successfully obtained access token.")

    async def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token.

        Raises:
            TrainerizeAPIError: If refresh fails.
        """
        client = self._get_client()
        logger.info("Refreshing access token.")

        try:
            response = await client.post(
                self.TOKEN_ENDPOINT,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as e:
            raise TrainerizeAPIError(f"Failed to refresh access token: {e}")

        if response.status_code != 200:
            self._refresh_token = None
            raise TrainerizeAPIError(
                "Token refresh failed",
                status_code=response.status_code,
                response_body=response.text,
            )

        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600)
        self._refresh_token = data.get("refresh_token", self._refresh_token)
        logger.info("Successfully refreshed access token.")

    # ─────────────────────────────────────────────
    # Rate Limiting
    # ─────────────────────────────────────────────

    async def _wait_for_rate_limit(self) -> None:
        """Enforce rate limiting by waiting if necessary.

        Uses a sliding window approach to ensure we don't exceed
        RATE_LIMIT_MAX_REQUESTS within RATE_LIMIT_WINDOW_SECONDS.
        """
        now = time.time()
        window_start = now - self.RATE_LIMIT_WINDOW_SECONDS

        # Prune old timestamps
        self._request_timestamps = [
            ts for ts in self._request_timestamps if ts > window_start
        ]

        if len(self._request_timestamps) >= self.RATE_LIMIT_MAX_REQUESTS:
            oldest_in_window = self._request_timestamps[0]
            wait_time = oldest_in_window + self.RATE_LIMIT_WINDOW_SECONDS - now + 0.1
            if wait_time > 0:
                logger.info("Rate limit reached, waiting %.1f seconds.", wait_time)
                await asyncio.sleep(wait_time)

        self._request_timestamps.append(time.time())

    # ─────────────────────────────────────────────
    # Core Request Methods
    # ─────────────────────────────────────────────

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH).
            path: API path (relative to API_PREFIX).
            params: Query parameters.
            json_body: JSON request body.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            TrainerizeAPIError: On HTTP or API errors.
        """
        await self._ensure_authenticated()
        await self._wait_for_rate_limit()

        client = self._get_client()
        url = f"{self.API_PREFIX}{path}"

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }

        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
                headers=headers,
            )
        except httpx.HTTPError as e:
            raise TrainerizeAPIError(f"HTTP request failed: {e}")

        # Handle 401 with one retry (token may have expired)
        if response.status_code == 401:
            logger.info("Received 401, attempting token refresh and retry.")
            self._access_token = None
            await self._ensure_authenticated()
            headers["Authorization"] = f"Bearer {self._access_token}"
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_body,
                    headers=headers,
                )
            except httpx.HTTPError as e:
                raise TrainerizeAPIError(f"HTTP request failed after token refresh: {e}")

        if response.status_code >= 400:
            raise TrainerizeAPIError(
                f"API error on {method} {url}",
                status_code=response.status_code,
                response_body=response.text,
            )

        # Handle empty responses (e.g., 204 No Content)
        if response.status_code == 204 or not response.content:
            return {"success": True}

        return response.json()

    async def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated GET request."""
        return await self._request("GET", path, params=params)

    async def _post(
        self, path: str, json_body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated POST request."""
        return await self._request("POST", path, json_body=json_body)

    async def _put(
        self, path: str, json_body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated PUT request."""
        return await self._request("PUT", path, json_body=json_body)

    async def _patch(
        self, path: str, json_body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated PATCH request."""
        return await self._request("PATCH", path, json_body=json_body)

    async def _delete(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated DELETE request."""
        return await self._request("DELETE", path, params=params)

    # ─────────────────────────────────────────────
    # Client Management
    # ─────────────────────────────────────────────

    async def list_clients(
        self,
        tag: Optional[str] = None,
        status: Optional[str] = None,
        compliance_level: Optional[str] = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Dict[str, Any]:
        """List all clients with optional filters.

        Args:
            tag: Filter by client tag (e.g., "VIP", "weight-loss").
            status: Filter by status ("active", "inactive", "pending").
            compliance_level: Filter by compliance ("high", "medium", "low").
            page: Page number for pagination.
            per_page: Number of results per page.

        Returns:
            Dictionary containing client list and pagination metadata.
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if tag:
            params["tag"] = tag
        if status:
            params["status"] = status
        if compliance_level:
            params["compliance_level"] = compliance_level

        logger.info("Listing clients with filters: %s", params)
        return await self._get("/clients", params=params)

    async def get_client(self, client_id: str) -> Dict[str, Any]:
        """Get full client profile including programs, compliance, and progress.

        Args:
            client_id: Unique client identifier.

        Returns:
            Dictionary with complete client profile data.
        """
        logger.info("Getting client profile: %s", client_id)
        return await self._get(f"/clients/{client_id}")

    async def create_client(
        self,
        name: str,
        email: str,
        phone: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new client.

        Args:
            name: Client's full name.
            email: Client's email address.
            phone: Client's phone number (optional).
            tags: List of tags to assign (optional).
            notes: Initial notes about the client (optional).

        Returns:
            Dictionary with the newly created client data.
        """
        body: Dict[str, Any] = {"name": name, "email": email}
        if phone:
            body["phone"] = phone
        if tags:
            body["tags"] = tags
        if notes:
            body["notes"] = notes

        logger.info("Creating client: %s (%s)", name, email)
        return await self._post("/clients", json_body=body)

    async def update_client(
        self,
        client_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing client's information.

        Args:
            client_id: Unique client identifier.
            name: Updated name (optional).
            email: Updated email (optional).
            phone: Updated phone (optional).
            tags: Updated tags list (replaces existing, optional).
            notes: Updated notes (optional).
            status: Updated status ("active", "inactive", optional).

        Returns:
            Dictionary with updated client data.
        """
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if email is not None:
            body["email"] = email
        if phone is not None:
            body["phone"] = phone
        if tags is not None:
            body["tags"] = tags
        if notes is not None:
            body["notes"] = notes
        if status is not None:
            body["status"] = status

        logger.info("Updating client %s with fields: %s", client_id, list(body.keys()))
        return await self._put(f"/clients/{client_id}", json_body=body)

    async def get_client_progress(
        self,
        client_id: str,
        period: str = "week",
    ) -> Dict[str, Any]:
        """Get a client's progress report for a given period.

        Includes workout compliance, nutrition compliance, and body measurements.

        Args:
            client_id: Unique client identifier.
            period: Report period ("week", "month", "quarter").

        Returns:
            Dictionary with progress report data.
        """
        logger.info("Getting progress report for client %s (%s)", client_id, period)
        return await self._get(
            f"/clients/{client_id}/progress",
            params={"period": period},
        )

    async def tag_clients(
        self,
        client_ids: List[str],
        tags: List[str],
        action: str = "add",
    ) -> Dict[str, Any]:
        """Add or remove tags from one or more clients.

        Args:
            client_ids: List of client IDs to update.
            tags: List of tags to add or remove.
            action: Either "add" or "remove".

        Returns:
            Dictionary with result summary.
        """
        logger.info("%s tags %s for %d clients", action.capitalize(), tags, len(client_ids))
        return await self._post(
            "/clients/tags",
            json_body={
                "client_ids": client_ids,
                "tags": tags,
                "action": action,
            },
        )

    # ─────────────────────────────────────────────
    # Training Programs
    # ─────────────────────────────────────────────

    async def list_programs(
        self,
        page: int = 1,
        per_page: int = 25,
    ) -> Dict[str, Any]:
        """List available training programs.

        Args:
            page: Page number for pagination.
            per_page: Number of results per page.

        Returns:
            Dictionary containing program list and pagination info.
        """
        logger.info("Listing training programs.")
        return await self._get(
            "/programs",
            params={"page": page, "per_page": per_page},
        )

    async def create_program(
        self,
        name: str,
        description: Optional[str] = None,
        phases: Optional[List[Dict[str, Any]]] = None,
        duration_weeks: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new training program.

        Args:
            name: Program name.
            description: Program description (optional).
            phases: List of phase objects, each with name, duration, and workouts (optional).
            duration_weeks: Total duration in weeks (optional).

        Returns:
            Dictionary with the created program data.
        """
        body: Dict[str, Any] = {"name": name}
        if description:
            body["description"] = description
        if phases:
            body["phases"] = phases
        if duration_weeks:
            body["duration_weeks"] = duration_weeks

        logger.info("Creating training program: %s", name)
        return await self._post("/programs", json_body=body)

    async def assign_program(
        self,
        client_id: str,
        program_id: str,
        start_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assign a training program to a client.

        Args:
            client_id: Unique client identifier.
            program_id: Unique program identifier.
            start_date: Start date in ISO format (optional, defaults to today).

        Returns:
            Dictionary with assignment confirmation.
        """
        body: Dict[str, Any] = {"program_id": program_id}
        if start_date:
            body["start_date"] = start_date

        logger.info("Assigning program %s to client %s", program_id, client_id)
        return await self._post(f"/clients/{client_id}/programs", json_body=body)

    async def list_workouts(
        self,
        page: int = 1,
        per_page: int = 25,
    ) -> Dict[str, Any]:
        """List available workout templates.

        Args:
            page: Page number for pagination.
            per_page: Number of results per page.

        Returns:
            Dictionary containing workout template list.
        """
        logger.info("Listing workout templates.")
        return await self._get(
            "/workouts",
            params={"page": page, "per_page": per_page},
        )

    async def create_workout(
        self,
        name: str,
        exercises: List[Dict[str, Any]],
        description: Optional[str] = None,
        workout_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new workout template.

        Args:
            name: Workout name.
            exercises: List of exercise objects with name, sets, reps, rest_seconds, etc.
            description: Workout description (optional).
            workout_type: Type of workout ("strength", "cardio", "hiit", "flexibility", optional).

        Returns:
            Dictionary with the created workout data.
        """
        body: Dict[str, Any] = {"name": name, "exercises": exercises}
        if description:
            body["description"] = description
        if workout_type:
            body["workout_type"] = workout_type

        logger.info("Creating workout template: %s (%d exercises)", name, len(exercises))
        return await self._post("/workouts", json_body=body)

    async def log_workout(
        self,
        client_id: str,
        workout_id: str,
        completed_at: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        notes: Optional[str] = None,
        exercises: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Log a completed workout for a client.

        Args:
            client_id: Unique client identifier.
            workout_id: Unique workout template identifier.
            completed_at: Completion timestamp in ISO format (optional).
            duration_minutes: Workout duration in minutes (optional).
            notes: Client or trainer notes about the session (optional).
            exercises: Actual exercises performed with sets/reps/weight (optional).

        Returns:
            Dictionary with the logged workout record.
        """
        body: Dict[str, Any] = {"workout_id": workout_id}
        if completed_at:
            body["completed_at"] = completed_at
        if duration_minutes:
            body["duration_minutes"] = duration_minutes
        if notes:
            body["notes"] = notes
        if exercises:
            body["exercises"] = exercises

        logger.info("Logging workout %s for client %s", workout_id, client_id)
        return await self._post(f"/clients/{client_id}/workouts", json_body=body)

    async def send_wod(
        self,
        group_id: str,
        workout_id: str,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send Workout of the Day (WOD) to a group.

        Args:
            group_id: Unique group identifier.
            workout_id: Workout template ID to send as WOD.
            message: Optional message to accompany the WOD.

        Returns:
            Dictionary with send confirmation.
        """
        body: Dict[str, Any] = {"workout_id": workout_id}
        if message:
            body["message"] = message

        logger.info("Sending WOD %s to group %s", workout_id, group_id)
        return await self._post(f"/groups/{group_id}/wod", json_body=body)

    # ─────────────────────────────────────────────
    # Nutrition
    # ─────────────────────────────────────────────

    async def get_nutrition_log(
        self,
        client_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a client's nutrition log including meals, macros, and calories.

        Args:
            client_id: Unique client identifier.
            start_date: Start date filter in ISO format (optional).
            end_date: End date filter in ISO format (optional).

        Returns:
            Dictionary with nutrition log entries.
        """
        params: Dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        logger.info("Getting nutrition log for client %s", client_id)
        return await self._get(f"/clients/{client_id}/nutrition", params=params)

    async def create_meal_plan(
        self,
        client_id: str,
        name: str,
        meals: List[Dict[str, Any]],
        daily_calories: Optional[int] = None,
        daily_protein_g: Optional[int] = None,
        daily_carbs_g: Optional[int] = None,
        daily_fat_g: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a meal plan for a client.

        Args:
            client_id: Unique client identifier.
            name: Meal plan name (e.g., "Week 1 - Cutting Phase").
            meals: List of meal objects with name, foods, calories, macros.
            daily_calories: Target daily calorie intake (optional).
            daily_protein_g: Target daily protein in grams (optional).
            daily_carbs_g: Target daily carbs in grams (optional).
            daily_fat_g: Target daily fat in grams (optional).

        Returns:
            Dictionary with the created meal plan data.
        """
        body: Dict[str, Any] = {"name": name, "meals": meals}
        if daily_calories is not None:
            body["daily_calories"] = daily_calories
        if daily_protein_g is not None:
            body["daily_protein_g"] = daily_protein_g
        if daily_carbs_g is not None:
            body["daily_carbs_g"] = daily_carbs_g
        if daily_fat_g is not None:
            body["daily_fat_g"] = daily_fat_g

        logger.info("Creating meal plan '%s' for client %s", name, client_id)
        return await self._post(f"/clients/{client_id}/meal-plans", json_body=body)

    async def get_nutrition_compliance(
        self,
        client_id: str,
        period: str = "week",
    ) -> Dict[str, Any]:
        """Get nutrition compliance stats for a client.

        Args:
            client_id: Unique client identifier.
            period: Compliance period ("week", "month").

        Returns:
            Dictionary with compliance percentage, streak, and details.
        """
        logger.info("Getting nutrition compliance for client %s (%s)", client_id, period)
        return await self._get(
            f"/clients/{client_id}/nutrition/compliance",
            params={"period": period},
        )

    # ─────────────────────────────────────────────
    # Communication
    # ─────────────────────────────────────────────

    async def send_message(
        self,
        client_id: str,
        text: str,
        message_type: str = "text",
        attachment_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message to a client.

        Args:
            client_id: Unique client identifier.
            text: Message text content.
            message_type: Type of message ("text", "voice", "image").
            attachment_url: URL to attachment for voice/image messages (optional).

        Returns:
            Dictionary with the sent message data.
        """
        body: Dict[str, Any] = {"text": text, "type": message_type}
        if attachment_url:
            body["attachment_url"] = attachment_url

        logger.info("Sending %s message to client %s", message_type, client_id)
        return await self._post(f"/clients/{client_id}/messages", json_body=body)

    async def send_group_message(
        self,
        group_id: str,
        text: str,
        message_type: str = "text",
        attachment_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message to a group.

        Args:
            group_id: Unique group identifier.
            text: Message text content.
            message_type: Type of message ("text", "voice", "image").
            attachment_url: URL to attachment (optional).

        Returns:
            Dictionary with the sent group message data.
        """
        body: Dict[str, Any] = {"text": text, "type": message_type}
        if attachment_url:
            body["attachment_url"] = attachment_url

        logger.info("Sending group message to group %s", group_id)
        return await self._post(f"/groups/{group_id}/messages", json_body=body)

    async def list_messages(
        self,
        client_id: str,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        """Get message history with a client.

        Args:
            client_id: Unique client identifier.
            page: Page number for pagination.
            per_page: Number of messages per page.

        Returns:
            Dictionary containing messages and pagination info.
        """
        logger.info("Listing messages for client %s", client_id)
        return await self._get(
            f"/clients/{client_id}/messages",
            params={"page": page, "per_page": per_page},
        )

    # ─────────────────────────────────────────────
    # Scheduling
    # ─────────────────────────────────────────────

    async def list_appointments(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        client_id: Optional[str] = None,
        appointment_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Dict[str, Any]:
        """List upcoming appointments and classes.

        Args:
            start_date: Filter by start date in ISO format (optional).
            end_date: Filter by end date in ISO format (optional).
            client_id: Filter by specific client (optional).
            appointment_type: Filter by type ("session", "class", "consultation", optional).
            page: Page number for pagination.
            per_page: Number of results per page.

        Returns:
            Dictionary containing appointments list.
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if client_id:
            params["client_id"] = client_id
        if appointment_type:
            params["type"] = appointment_type

        logger.info("Listing appointments with filters: %s", params)
        return await self._get("/appointments", params=params)

    async def create_appointment(
        self,
        client_id: str,
        start_time: str,
        end_time: str,
        appointment_type: str = "session",
        title: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Schedule a new appointment.

        Args:
            client_id: Unique client identifier.
            start_time: Start time in ISO format.
            end_time: End time in ISO format.
            appointment_type: Type ("session", "class", "consultation").
            title: Appointment title (optional).
            location: Location or meeting link (optional).
            notes: Appointment notes (optional).

        Returns:
            Dictionary with created appointment data.
        """
        body: Dict[str, Any] = {
            "client_id": client_id,
            "start_time": start_time,
            "end_time": end_time,
            "type": appointment_type,
        }
        if title:
            body["title"] = title
        if location:
            body["location"] = location
        if notes:
            body["notes"] = notes

        logger.info("Creating %s appointment for client %s", appointment_type, client_id)
        return await self._post("/appointments", json_body=body)

    async def get_availability(
        self,
        date: str,
        duration_minutes: int = 60,
    ) -> Dict[str, Any]:
        """Check trainer availability for a given date.

        Args:
            date: Date to check in ISO format (YYYY-MM-DD).
            duration_minutes: Desired appointment duration in minutes.

        Returns:
            Dictionary with available time slots.
        """
        logger.info("Checking availability for %s (%d min slots)", date, duration_minutes)
        return await self._get(
            "/availability",
            params={"date": date, "duration_minutes": duration_minutes},
        )

    # ─────────────────────────────────────────────
    # Analytics & Reporting
    # ─────────────────────────────────────────────

    async def get_compliance_report(
        self,
        period: str = "week",
    ) -> Dict[str, Any]:
        """Get compliance statistics across all clients.

        Includes workout completion rates, nutrition adherence, and overall
        engagement metrics.

        Args:
            period: Report period ("week", "month", "quarter").

        Returns:
            Dictionary with aggregated compliance data.
        """
        logger.info("Getting compliance report for period: %s", period)
        return await self._get(
            "/analytics/compliance",
            params={"period": period},
        )

    async def get_client_metrics(
        self,
        client_id: str,
        metric_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get client body metrics such as weight, body fat, and measurements.

        Args:
            client_id: Unique client identifier.
            metric_types: List of metric types to include
                         (e.g., ["weight", "body_fat", "chest", "waist"]).
            start_date: Start date filter in ISO format (optional).
            end_date: End date filter in ISO format (optional).

        Returns:
            Dictionary with metric data and trends.
        """
        params: Dict[str, Any] = {}
        if metric_types:
            params["types"] = ",".join(metric_types)
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        logger.info("Getting metrics for client %s", client_id)
        return await self._get(f"/clients/{client_id}/metrics", params=params)

    async def get_business_stats(
        self,
        period: str = "month",
    ) -> Dict[str, Any]:
        """Get business overview including active clients, revenue, and retention.

        Args:
            period: Report period ("week", "month", "quarter", "year").

        Returns:
            Dictionary with business statistics.
        """
        logger.info("Getting business stats for period: %s", period)
        return await self._get(
            "/analytics/business",
            params={"period": period},
        )

    # ─────────────────────────────────────────────
    # Habits
    # ─────────────────────────────────────────────

    async def assign_habit(
        self,
        client_id: str,
        name: str,
        description: Optional[str] = None,
        frequency: str = "daily",
        target_count: int = 1,
    ) -> Dict[str, Any]:
        """Assign a habit to a client.

        Args:
            client_id: Unique client identifier.
            name: Habit name (e.g., "Drink 8 glasses of water").
            description: Detailed description of the habit (optional).
            frequency: How often ("daily", "weekly").
            target_count: Number of times per frequency period.

        Returns:
            Dictionary with the assigned habit data.
        """
        body: Dict[str, Any] = {
            "name": name,
            "frequency": frequency,
            "target_count": target_count,
        }
        if description:
            body["description"] = description

        logger.info("Assigning habit '%s' to client %s", name, client_id)
        return await self._post(f"/clients/{client_id}/habits", json_body=body)

    async def get_habit_progress(
        self,
        client_id: str,
        habit_id: Optional[str] = None,
        period: str = "week",
    ) -> Dict[str, Any]:
        """Get a client's habit progress including streaks and completion rates.

        Args:
            client_id: Unique client identifier.
            habit_id: Specific habit ID to check (optional, returns all if omitted).
            period: Progress period ("week", "month").

        Returns:
            Dictionary with habit progress and streak data.
        """
        params: Dict[str, Any] = {"period": period}
        if habit_id:
            params["habit_id"] = habit_id

        logger.info("Getting habit progress for client %s", client_id)
        return await self._get(f"/clients/{client_id}/habits/progress", params=params)
