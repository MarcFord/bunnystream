#!/usr/bin/env python3
"""
Version management script for bunnystream.

This script helps automate version bumping and tagging for releases.
"""
import argparse
import re
import subprocess
import sys


def run_command(cmd, check=True, capture_output=True):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check, capture_output=capture_output, text=True)
    if result.stdout:
        print(result.stdout.strip())
    return result


def get_current_version():
    """Get the current version from git tags."""
    try:
        result = run_command(["git", "describe", "--tags", "--abbrev=0"])
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("No existing tags found, starting from v0.1.0")
        return "v0.1.0"


def parse_version(version_str):
    """Parse version string into components."""
    # Remove 'v' prefix if present
    version_str = version_str.lstrip("v")

    # Parse semantic version
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$", version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")

    major, minor, patch, prerelease = match.groups()
    return int(major), int(minor), int(patch), prerelease


def bump_version(current_version, bump_type):
    """Bump version based on type (major, minor, patch)."""
    major, minor, patch, _ = parse_version(current_version)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"v{major}.{minor}.{patch}"


def check_working_directory():
    """Check if working directory is clean."""
    result = run_command(["git", "status", "--porcelain"], check=False)
    if result.stdout.strip():
        print("Warning: You have uncommitted changes:")
        print(result.stdout)
        response = input("Continue anyway? (y/N): ")
        if response.lower() != "y":
            sys.exit(1)


def create_tag(version, message=None):
    """Create and push a git tag."""
    if message is None:
        message = f"Release {version}"

    print(f"Creating tag {version} with message: {message}")
    run_command(["git", "tag", "-a", version, "-m", message])

    print(f"Pushing tag {version} to origin...")
    run_command(["git", "push", "origin", version])


def main():
    parser = argparse.ArgumentParser(description="Bump version and create release tag")
    parser.add_argument(
        "bump_type", choices=["major", "minor", "patch"], help="Type of version bump"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )
    parser.add_argument("--message", help="Custom tag message (default: 'Release {version}')")
    parser.add_argument("--force", action="store_true", help="Skip working directory check")

    args = parser.parse_args()

    # Check if we're in a git repository
    try:
        run_command(["git", "rev-parse", "--git-dir"], capture_output=True)
    except subprocess.CalledProcessError:
        print("Error: Not in a git repository")
        sys.exit(1)

    # Check working directory
    if not args.force:
        check_working_directory()

    # Get current version and calculate new version
    current_version = get_current_version()
    new_version = bump_version(current_version, args.bump_type)

    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")

    if args.dry_run:
        print("Dry run - no changes made")
        return

    # Confirm the action
    response = input(f"Create and push tag {new_version}? (y/N): ")
    if response.lower() != "y":
        print("Cancelled")
        return

    # Create and push the tag
    create_tag(new_version, args.message)

    print(f"✅ Successfully created and pushed tag {new_version}")
    print("🚀 GitHub Actions will now build and publish the package to PyPI")


if __name__ == "__main__":
    main()
