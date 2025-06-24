#!/bin/bash
# Simple release script for bunnystream

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml not found. Run this script from the project root."
    exit 1
fi

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    print_warning "You have uncommitted changes:"
    git status --short
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get current version
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
print_status "Current version: $CURRENT_VERSION"

# Ask for version bump type
echo "What type of release?"
echo "1) Patch (bug fixes)"
echo "2) Minor (new features)"
echo "3) Major (breaking changes)"
read -p "Enter choice (1-3): " -n 1 -r
echo

case $REPLY in
    1)
        BUMP_TYPE="patch"
        ;;
    2)
        BUMP_TYPE="minor"
        ;;
    3)
        BUMP_TYPE="major"
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Calculate new version
VERSION_NUM=${CURRENT_VERSION#v}
IFS='.' read -ra VERSION_PARTS <<< "$VERSION_NUM"
MAJOR=${VERSION_PARTS[0]:-0}
MINOR=${VERSION_PARTS[1]:-0}
PATCH=${VERSION_PARTS[2]:-0}

case $BUMP_TYPE in
    "major")
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    "minor")
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    "patch")
        PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="v${MAJOR}.${MINOR}.${PATCH}"
print_status "New version will be: $NEW_VERSION"

# Run tests
print_status "Running tests..."
if ! uv run pytest --cov=src/bunnystream --cov-report=term-missing; then
    print_error "Tests failed! Fix them before releasing."
    exit 1
fi

# Run linting
print_status "Running code quality checks..."
if ! uv run pylint src/bunnystream/ --output-format=text; then
    print_warning "Linting issues found, but continuing..."
fi

# Final confirmation
read -p "Create and push tag $NEW_VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Cancelled"
    exit 1
fi

# Create and push tag
print_status "Creating tag $NEW_VERSION..."
git tag -a "$NEW_VERSION" -m "Release $NEW_VERSION"

print_status "Pushing tag to origin..."
git push origin "$NEW_VERSION"

print_status "🚀 Release $NEW_VERSION created successfully!"
print_status "GitHub Actions will now build and publish to PyPI."
print_status "Monitor the progress at: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
