"""Exception hierarchy for SpecKit Update.

Exit codes match the PowerShell implementation for seamless migration:
- 0: Success
- 1: General error (SpecKitError)
- 2: Prerequisites not met (PrerequisiteError)
- 3: Network/API error (NetworkError)
- 4: Git error (GitError)
- 5: User cancelled (UserCancelledError)
- 6: Rollback occurred (RollbackError)
"""


class SpecKitError(Exception):
    """Base exception for all SpecKit errors.

    Attributes:
        exit_code: The exit code to return when this error occurs.
        message: Human-readable error message.
    """

    exit_code: int = 1

    def __init__(self, message: str) -> None:
        """Initialize with error message.

        Args:
            message: Human-readable error description.
        """
        super().__init__(message)
        self.message = message


class PrerequisiteError(SpecKitError):
    """Prerequisites not met (e.g., Git missing, not in SpecKit project).

    Exit code: 2
    """

    exit_code = 2


class NetworkError(SpecKitError):
    """Network or API error (e.g., GitHub API unreachable, rate limited).

    Exit code: 3
    """

    exit_code = 3


class GitError(SpecKitError):
    """Git-related error (e.g., uncommitted changes, merge conflicts).

    Exit code: 4
    """

    exit_code = 4


class UserCancelledError(SpecKitError):
    """User cancelled the operation.

    Exit code: 5
    """

    exit_code = 5


class RollbackError(SpecKitError):
    """Automatic rollback occurred due to update failure.

    Exit code: 6
    """

    exit_code = 6


class ManifestError(SpecKitError):
    """Error reading or writing manifest file.

    Exit code: 1 (general error)
    """

    exit_code = 1


class HashError(SpecKitError):
    """Error calculating or validating file hash.

    Exit code: 1 (general error)
    """

    exit_code = 1


class MergeError(SpecKitError):
    """Error during 3-way merge operation.

    Exit code: 1 (general error)
    """

    exit_code = 1
