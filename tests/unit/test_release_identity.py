import pytest

from ai_release_notes.release_identity import ReleaseIdentityError, build_release_identity


def test_same_version_is_the_same_release_regardless_of_other_fields():
    identity_a = build_release_identity(
        release_name="v1.3.0",
        version="v1.3.0",
        commit_sha="abc123",
        rc_branch="release/1.3",
    )
    identity_b = build_release_identity(
        release_name="Version 1.3.0 (different name)",
        version="v1.3.0",
        commit_sha="def456",
        rc_branch=None,
    )

    assert identity_a.matching_key == identity_b.matching_key == "v1.3.0"


def test_different_version_is_a_different_release():
    identity_a = build_release_identity(release_name="a", version="v1.3.0", commit_sha="abc123")
    identity_b = build_release_identity(release_name="b", version="v1.4.0", commit_sha="abc123")

    assert identity_a.matching_key != identity_b.matching_key


def test_rc_branch_is_optional():
    identity = build_release_identity(release_name="v1.3.0", version="v1.3.0", commit_sha="abc123")

    assert identity.rc_branch is None


def test_missing_version_raises():
    with pytest.raises(ReleaseIdentityError):
        build_release_identity(release_name="v1.3.0", version="", commit_sha="abc123")


def test_missing_release_name_raises():
    with pytest.raises(ReleaseIdentityError):
        build_release_identity(release_name="", version="v1.3.0", commit_sha="abc123")


def test_missing_commit_sha_raises():
    with pytest.raises(ReleaseIdentityError):
        build_release_identity(release_name="v1.3.0", version="v1.3.0", commit_sha="")
