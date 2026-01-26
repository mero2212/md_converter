"""Tests for profile system."""

import pytest
from pathlib import Path

from converter.errors import ProfileError
from converter.profiles import Profile, get_profile, list_profiles, register_profile


def test_list_profiles():
    """Test listing available profiles."""
    profiles = list_profiles()
    assert isinstance(profiles, list)
    assert len(profiles) > 0
    assert "angebot" in profiles
    assert "bericht" in profiles
    assert "analyse" in profiles
    assert "script" in profiles


def test_get_profile_existing():
    """Test getting an existing profile."""
    profile = get_profile("bericht")
    assert profile is not None
    assert profile.name == "bericht"
    assert profile.display_name == "Bericht"
    assert isinstance(profile.pandoc_args, list)


def test_get_profile_nonexistent():
    """Test getting a non-existent profile."""
    with pytest.raises(ProfileError, match="not found"):
        get_profile("nonexistent")


def test_profile_attributes():
    """Test profile attributes."""
    profile = get_profile("bericht")
    assert hasattr(profile, "name")
    assert hasattr(profile, "display_name")
    assert hasattr(profile, "description")
    assert hasattr(profile, "default_template")
    assert hasattr(profile, "pandoc_args")
    assert hasattr(profile, "output_naming")
    assert hasattr(profile, "toc")
    assert hasattr(profile, "number_sections")


def test_profile_get_template_path():
    """Test profile template path resolution."""
    profile = Profile(
        name="test",
        default_template="templates/test.docx",
    )

    # With non-existent template, should return None or unresolved path
    result = profile.get_template_path()
    # Template doesn't exist, so result may be None or unresolved Path
    assert result is None or isinstance(result, Path)


def test_register_custom_profile():
    """Test registering a custom profile."""
    custom_profile = Profile(
        name="custom",
        default_template=None,
        pandoc_args=["--toc"],
    )

    register_profile(custom_profile)
    assert get_profile("custom").name == "custom"

    # Cleanup: remove custom profile (if needed for other tests)
    # Note: This modifies global state, so be careful in real tests


def test_register_profile_invalid_name():
    """Test registering profile with invalid name."""
    with pytest.raises(ProfileError, match="cannot be empty"):
        register_profile(Profile(name=""))
