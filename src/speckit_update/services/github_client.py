"""GitHub Releases API client.

This module provides access to the GitHub Releases API for fetching
SpecKit release metadata and downloading release tarballs.
"""

import os
import time
from typing import Any

import httpx

from speckit_update.exceptions import NetworkError
from speckit_update.models import Release

# GitHub API constants
GITHUB_API_BASE = "https://api.github.com"
SPECKIT_REPO = "github/spec-kit"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # Exponential backoff


class GitHubClient:
    """Client for GitHub Releases API.

    Handles authentication via GITHUB_TOKEN or GITHUB_PAT environment
    variables and implements rate limit handling with exponential backoff.
    """

    def __init__(
        self,
        *,
        repo: str = SPECKIT_REPO,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the GitHub client.

        Args:
            repo: Repository in 'owner/repo' format.
            timeout: Request timeout in seconds.
        """
        self.repo = repo
        self.timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def _auth_token(self) -> str | None:
        """Get authentication token from environment."""
        return os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PAT")

    @property
    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        return headers

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=GITHUB_API_BASE,
                headers=self._headers,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make a request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Request URL (relative to base).
            **kwargs: Additional arguments for httpx.

        Returns:
            Response object.

        Raises:
            NetworkError: If all retries fail or rate limit exceeded.
        """
        client = self._get_client()
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = client.request(method, url, **kwargs)

                # Check for rate limiting
                if response.status_code == 403:
                    remaining = response.headers.get("X-RateLimit-Remaining", "0")
                    if remaining == "0":
                        reset_time = response.headers.get("X-RateLimit-Reset", "")
                        raise NetworkError(
                            f"GitHub API rate limit exceeded. "
                            f"Resets at: {reset_time}. "
                            f"Set GITHUB_TOKEN or GITHUB_PAT for higher limits."
                        )

                # Check for other errors
                if response.status_code == 404:
                    raise NetworkError(f"GitHub resource not found: {url}")

                response.raise_for_status()
                return response

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
            except httpx.HTTPStatusError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1 and e.response.status_code >= 500:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
                raise NetworkError(f"GitHub API error: {e}") from e
            except httpx.RequestError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue

        raise NetworkError(
            f"GitHub API request failed after {MAX_RETRIES} retries: {last_error}"
        )

    def get_latest_release(self) -> Release:
        """Fetch the latest SpecKit release.

        Returns:
            Release metadata for the latest version.

        Raises:
            NetworkError: If the API request fails.
        """
        url = f"/repos/{self.repo}/releases/latest"
        response = self._request_with_retry("GET", url)
        data = response.json()
        return Release.from_github_response(data)

    def get_release(self, version: str) -> Release:
        """Fetch a specific SpecKit release by version tag.

        Args:
            version: Version tag (e.g., 'v0.0.79').

        Returns:
            Release metadata for the specified version.

        Raises:
            NetworkError: If the API request fails or version not found.
        """
        url = f"/repos/{self.repo}/releases/tags/{version}"
        response = self._request_with_retry("GET", url)
        data = response.json()
        return Release.from_github_response(data)

    def list_releases(self, *, per_page: int = 30) -> list[Release]:
        """List available releases.

        Args:
            per_page: Number of releases to fetch (max 100).

        Returns:
            List of Release objects.

        Raises:
            NetworkError: If the API request fails.
        """
        url = f"/repos/{self.repo}/releases"
        response = self._request_with_retry("GET", url, params={"per_page": per_page})
        data = response.json()
        return [Release.from_github_response(r) for r in data]

    def download_tarball(self, url: str) -> bytes:
        """Download a release tarball.

        Args:
            url: The tarball URL from Release.tarball_url.

        Returns:
            Raw tarball content as bytes.

        Raises:
            NetworkError: If the download fails.
        """
        # Use a fresh client for downloads (may need different timeout)
        with httpx.Client(
            headers=self._headers,
            timeout=60.0,  # Longer timeout for downloads
            follow_redirects=True,
        ) as client:
            try:
                response = client.get(url)
                response.raise_for_status()
                return response.content
            except httpx.RequestError as e:
                raise NetworkError(f"Failed to download tarball: {e}") from e
            except httpx.HTTPStatusError as e:
                raise NetworkError(f"Download failed: {e}") from e

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "GitHubClient":
        """Enter context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Exit context manager."""
        self.close()
