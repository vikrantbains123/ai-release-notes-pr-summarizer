"""Release Identity: the release name, version/tag, RC branch, and commit
SHA that together identify a specific release (FR-011, FR-012, FR-019).

release_name/version/rc_branch are explicit user inputs; commit_sha is
always auto-resolved from the Time Window's end reference/commit, never
user-supplied.
"""
from dataclasses import dataclass
from typing import Optional


class ReleaseIdentityError(Exception):
    """Raised when a Release Identity is missing a required field."""


@dataclass
class ReleaseIdentity:
    release_name: str
    version: str
    commit_sha: str
    rc_branch: Optional[str] = None

    @property
    def matching_key(self) -> str:
        """The sole identity/matching key for FR-012's immutability check --
        two identities with the same version are the same release,
        regardless of rc_branch/commit_sha.
        """
        return self.version


def build_release_identity(
    release_name: str,
    version: str,
    commit_sha: str,
    rc_branch: Optional[str] = None,
) -> ReleaseIdentity:
    if not version:
        raise ReleaseIdentityError("version is required")
    if not release_name:
        raise ReleaseIdentityError("release_name is required")
    if not commit_sha:
        raise ReleaseIdentityError("commit_sha is required")
    return ReleaseIdentity(
        release_name=release_name,
        version=version,
        commit_sha=commit_sha,
        rc_branch=rc_branch,
    )
