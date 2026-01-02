"""GitHub release data model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Release:
    """GitHub release metadata.

    Represents information about a SpecKit release fetched from
    the GitHub Releases API.
    """

    tag_name: str
    """Version tag (e.g., 'v0.0.79')."""

    name: str
    """Release title."""

    published_at: datetime
    """Publication timestamp."""

    tarball_url: str
    """URL to download release tarball."""

    body: str = ""
    """Release notes markdown."""

    @classmethod
    def from_github_response(cls, data: dict[str, object]) -> "Release":
        """Create from GitHub API response.

        Args:
            data: Raw JSON response from GitHub Releases API.

        Returns:
            Release instance with parsed data.
        """
        tag_name = str(data.get("tag_name", ""))
        name = str(data.get("name", ""))
        published_at_str = str(data.get("published_at", ""))
        tarball_url = str(data.get("tarball_url", ""))
        body = str(data.get("body", ""))

        # Parse ISO 8601 datetime from GitHub
        # GitHub format: "2024-01-15T10:30:00Z"
        published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))

        return cls(
            tag_name=tag_name,
            name=name,
            published_at=published_at,
            tarball_url=tarball_url,
            body=body,
        )
