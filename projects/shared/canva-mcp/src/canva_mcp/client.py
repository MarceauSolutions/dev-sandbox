"""
Canva Connect API Client.

Wraps the Canva REST API with:
- Automatic token refresh
- Rate limiting (10 req/10s for exports, 20 req/10s for elements)
- Async job polling for exports
- Error handling with retries
"""

import time
import httpx
from typing import Any
from dataclasses import dataclass
from enum import Enum

from .auth import CanvaAuth

CANVA_API_BASE = "https://api.canva.com/rest/v1"


class DesignType(str, Enum):
    """Supported Canva design types."""
    PRESENTATION = "presentation"
    DOC = "doc"
    WHITEBOARD = "whiteboard"
    INSTAGRAM_POST = "instagram_post"
    INSTAGRAM_STORY = "instagram_story"
    FACEBOOK_POST = "facebook_post"
    YOUTUBE_THUMBNAIL = "youtube_thumbnail"
    POSTER = "poster"
    FLYER = "flyer"
    BUSINESS_CARD = "business_card"
    LOGO = "logo"
    A4_DOCUMENT = "a4_document"
    US_LETTER = "us_letter"


class ExportFormat(str, Enum):
    """Supported export formats."""
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    GIF = "gif"
    MP4 = "mp4"
    PPTX = "pptx"


class ExportQuality(str, Enum):
    """Export quality options."""
    REGULAR = "regular"
    HIGH = "high"


@dataclass
class RateLimiter:
    """Simple rate limiter for API calls."""
    max_requests: int
    window_seconds: int
    _requests: list = None

    def __post_init__(self):
        self._requests = []

    def wait_if_needed(self):
        """Wait if we've exceeded the rate limit."""
        now = time.time()
        # Remove old requests outside the window
        self._requests = [t for t in self._requests if now - t < self.window_seconds]

        if len(self._requests) >= self.max_requests:
            # Wait until oldest request expires
            sleep_time = self.window_seconds - (now - self._requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            self._requests = self._requests[1:]

        self._requests.append(time.time())


class CanvaClient:
    """Canva Connect API client with automatic token refresh and rate limiting."""

    def __init__(self, auth: CanvaAuth):
        self.auth = auth
        self._client = httpx.Client(timeout=60.0)

        # Rate limiters per endpoint type
        self._export_limiter = RateLimiter(max_requests=10, window_seconds=10)
        self._element_limiter = RateLimiter(max_requests=20, window_seconds=10)
        self._general_limiter = RateLimiter(max_requests=100, window_seconds=60)

    def _headers(self) -> dict:
        """Get headers with valid access token."""
        token = self.auth.get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        limiter: RateLimiter | None = None,
        **kwargs
    ) -> dict:
        """Make an API request with rate limiting and error handling."""
        limiter = limiter or self._general_limiter
        limiter.wait_if_needed()

        url = f"{CANVA_API_BASE}{endpoint}"
        response = self._client.request(
            method,
            url,
            headers=self._headers(),
            **kwargs
        )

        if response.status_code == 429:
            # Rate limited - wait and retry
            retry_after = int(response.headers.get("Retry-After", 10))
            time.sleep(retry_after)
            return self._request(method, endpoint, limiter, **kwargs)

        response.raise_for_status()

        if response.content:
            return response.json()
        return {}

    # ========== User Profile ==========

    def get_user_profile(self) -> dict:
        """Get current user's profile information."""
        return self._request("GET", "/users/me")

    # ========== Designs ==========

    def list_designs(
        self,
        query: str | None = None,
        continuation: str | None = None,
        ownership: str = "owned"
    ) -> dict:
        """List user's designs with optional search."""
        params = {"ownership": ownership}
        if query:
            params["query"] = query
        if continuation:
            params["continuation"] = continuation

        return self._request("GET", "/designs", params=params)

    def get_design(self, design_id: str) -> dict:
        """Get a specific design by ID."""
        return self._request("GET", f"/designs/{design_id}")

    def create_design(
        self,
        design_type: DesignType | str,
        title: str | None = None,
        asset_id: str | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> dict:
        """
        Create a new design.

        Args:
            design_type: Type of design (e.g., "instagram_post")
            title: Optional title for the design
            asset_id: Optional asset to use as background
            width: Custom width (for some design types)
            height: Custom height (for some design types)
        """
        data = {"design_type": str(design_type)}

        if title:
            data["title"] = title
        if asset_id:
            data["asset_id"] = asset_id
        if width and height:
            data["width"] = width
            data["height"] = height

        return self._request("POST", "/designs", json=data)

    def delete_design(self, design_id: str) -> dict:
        """Delete a design."""
        return self._request("DELETE", f"/designs/{design_id}")

    # ========== Assets ==========

    def upload_asset(
        self,
        file_path: str | None = None,
        file_url: str | None = None,
        name: str | None = None,
    ) -> dict:
        """
        Upload an asset (image, video, audio) to Canva.

        Args:
            file_path: Local file path to upload
            file_url: URL of file to import
            name: Optional name for the asset
        """
        if file_url:
            data = {"url": file_url}
            if name:
                data["name"] = name
            return self._request("POST", "/assets/upload", json=data)

        if file_path:
            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {}
                if name:
                    data["name"] = name

                # For file uploads, use multipart form
                token = self.auth.get_valid_token()
                response = self._client.post(
                    f"{CANVA_API_BASE}/assets/upload",
                    headers={"Authorization": f"Bearer {token}"},
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                return response.json()

        raise ValueError("Either file_path or file_url must be provided")

    def list_assets(
        self,
        folder_id: str | None = None,
        continuation: str | None = None,
    ) -> dict:
        """List assets in user's media library."""
        params = {}
        if folder_id:
            params["folder_id"] = folder_id
        if continuation:
            params["continuation"] = continuation

        return self._request("GET", "/assets", params=params)

    def get_asset(self, asset_id: str) -> dict:
        """Get a specific asset by ID."""
        return self._request("GET", f"/assets/{asset_id}")

    def delete_asset(self, asset_id: str) -> dict:
        """Delete an asset."""
        return self._request("DELETE", f"/assets/{asset_id}")

    # ========== Folders ==========

    def list_folders(
        self,
        parent_folder_id: str | None = None,
        continuation: str | None = None,
    ) -> dict:
        """List folders."""
        params = {}
        if parent_folder_id:
            params["parent_folder_id"] = parent_folder_id
        if continuation:
            params["continuation"] = continuation

        return self._request("GET", "/folders", params=params)

    def create_folder(self, name: str, parent_folder_id: str | None = None) -> dict:
        """Create a new folder."""
        data = {"name": name}
        if parent_folder_id:
            data["parent_folder_id"] = parent_folder_id

        return self._request("POST", "/folders", json=data)

    def get_folder(self, folder_id: str) -> dict:
        """Get a specific folder by ID."""
        return self._request("GET", f"/folders/{folder_id}")

    def delete_folder(self, folder_id: str) -> dict:
        """Delete a folder."""
        return self._request("DELETE", f"/folders/{folder_id}")

    # ========== Brand Templates ==========

    def list_brand_templates(
        self,
        query: str | None = None,
        continuation: str | None = None,
    ) -> dict:
        """List brand templates available to the user."""
        params = {}
        if query:
            params["query"] = query
        if continuation:
            params["continuation"] = continuation

        return self._request("GET", "/brand-templates", params=params)

    def get_brand_template(self, template_id: str) -> dict:
        """Get a specific brand template."""
        return self._request("GET", f"/brand-templates/{template_id}")

    def get_template_dataset(self, template_id: str) -> dict:
        """Get the autofill dataset schema for a template."""
        return self._request("GET", f"/brand-templates/{template_id}/dataset")

    # ========== Autofill ==========

    def create_autofill_job(
        self,
        template_id: str,
        data: dict,
        title: str | None = None,
    ) -> dict:
        """
        Create an autofill job to generate designs from template.

        Args:
            template_id: Brand template ID
            data: Dictionary mapping template fields to values
            title: Optional title for generated design
        """
        payload = {
            "brand_template_id": template_id,
            "data": data,
        }
        if title:
            payload["title"] = title

        return self._request("POST", "/autofills", json=payload)

    def get_autofill_job(self, job_id: str) -> dict:
        """Get the status of an autofill job."""
        return self._request("GET", f"/autofills/{job_id}")

    def wait_for_autofill(
        self,
        job_id: str,
        timeout: int = 120,
        poll_interval: int = 2,
    ) -> dict:
        """
        Wait for an autofill job to complete.

        Returns the completed job data including the generated design ID.
        """
        start = time.time()
        while time.time() - start < timeout:
            job = self.get_autofill_job(job_id)
            status = job.get("job", {}).get("status")

            if status == "success":
                return job
            elif status == "failed":
                error = job.get("job", {}).get("error", {})
                raise ValueError(f"Autofill failed: {error.get('message', 'Unknown error')}")

            time.sleep(poll_interval)

        raise TimeoutError(f"Autofill job {job_id} timed out after {timeout}s")

    # ========== Exports ==========

    def create_export_job(
        self,
        design_id: str,
        format: ExportFormat | str = ExportFormat.PDF,
        quality: ExportQuality | str = ExportQuality.REGULAR,
        pages: list[int] | None = None,
    ) -> dict:
        """
        Create an export job for a design.

        Args:
            design_id: Design to export
            format: Export format (pdf, png, jpg, etc.)
            quality: Export quality (regular, high)
            pages: Optional list of page indices to export (0-indexed)
        """
        data = {
            "design_id": design_id,
            "format": str(format),
            "quality": str(quality),
        }
        if pages:
            data["pages"] = pages

        return self._request(
            "POST",
            "/exports",
            json=data,
            limiter=self._export_limiter
        )

    def get_export_job(self, job_id: str) -> dict:
        """Get the status of an export job."""
        return self._request(
            "GET",
            f"/exports/{job_id}",
            limiter=self._export_limiter
        )

    def wait_for_export(
        self,
        job_id: str,
        timeout: int = 120,
        poll_interval: int = 2,
    ) -> dict:
        """
        Wait for an export job to complete.

        Returns the completed job data including download URLs.
        """
        start = time.time()
        while time.time() - start < timeout:
            job = self.get_export_job(job_id)
            status = job.get("job", {}).get("status")

            if status == "success":
                return job
            elif status == "failed":
                error = job.get("job", {}).get("error", {})
                raise ValueError(f"Export failed: {error.get('message', 'Unknown error')}")

            time.sleep(poll_interval)

        raise TimeoutError(f"Export job {job_id} timed out after {timeout}s")

    def export_design(
        self,
        design_id: str,
        format: ExportFormat | str = ExportFormat.PDF,
        quality: ExportQuality | str = ExportQuality.REGULAR,
        pages: list[int] | None = None,
        timeout: int = 120,
    ) -> dict:
        """
        Export a design and wait for completion.

        Convenience method that creates export job and waits for it.
        Returns job data with download URLs.
        """
        job = self.create_export_job(design_id, format, quality, pages)
        job_id = job.get("job", {}).get("id")
        if not job_id:
            raise ValueError("Failed to create export job")

        return self.wait_for_export(job_id, timeout)

    def download_export(self, export_url: str, output_path: str) -> str:
        """
        Download an exported file.

        Args:
            export_url: URL from export job result
            output_path: Local path to save the file

        Returns:
            The output path
        """
        response = self._client.get(export_url)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        return output_path

    # ========== Comments ==========

    def list_comments(
        self,
        design_id: str,
        continuation: str | None = None,
    ) -> dict:
        """List comments on a design."""
        params = {}
        if continuation:
            params["continuation"] = continuation

        return self._request("GET", f"/designs/{design_id}/comments", params=params)

    def create_comment(
        self,
        design_id: str,
        message: str,
        thread_id: str | None = None,
    ) -> dict:
        """Add a comment to a design."""
        data = {"message": message}
        if thread_id:
            data["thread_id"] = thread_id

        return self._request("POST", f"/designs/{design_id}/comments", json=data)

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
