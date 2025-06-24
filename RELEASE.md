# Release and Version Management

This document explains the automated version management and release process for the bunnystream package.

## 🚀 Quick Release (Recommended)

The easiest way to create a release is using the interactive shell script:

```bash
./release.sh
```

This script will:
1. Check your git status
2. Run tests and linting
3. Ask you what type of release (patch/minor/major)
4. Calculate the new version automatically
5. Create and push the git tag
6. Trigger GitHub Actions to build and publish to PyPI

## 📋 Release Options

### Option 1: Interactive Shell Script (Easiest)

```bash
./release.sh
```

- **Pros**: Simple, interactive, runs all checks
- **Cons**: Requires manual interaction

### Option 2: Makefile Commands

```bash
make release-patch   # For bug fixes (x.y.Z)
make release-minor   # For new features (x.Y.0)  
make release-major   # For breaking changes (X.0.0)
```

- **Pros**: Simple one-command release
- **Cons**: Less validation than shell script

### Option 3: Python Script

```bash
python scripts/bump_version.py patch
python scripts/bump_version.py minor
python scripts/bump_version.py major
```

Options:
- `--dry-run`: Show what would happen without making changes
- `--force`: Skip working directory check
- `--message "Custom message"`: Use custom tag message

### Option 4: GitHub Actions Workflow (Manual Trigger)

1. Go to GitHub Actions tab in your repository
2. Select "Create Release" workflow
3. Click "Run workflow"
4. Choose version bump type and add release notes
5. The workflow will create the tag and release automatically

### Option 5: Manual Process

```bash
# Get current version
CURRENT=$(git describe --tags --abbrev=0)
echo "Current version: $CURRENT"

# Create new tag (replace with your version)
NEW_VERSION="v1.2.3"
git tag -a "$NEW_VERSION" -m "Release $NEW_VERSION"
git push origin "$NEW_VERSION"
```

## 🔄 How It Works

### Version Strategy

We use **semantic versioning** (semver):
- **MAJOR** (X.y.z): Breaking changes
- **MINOR** (x.Y.z): New features, backward compatible
- **PATCH** (x.y.Z): Bug fixes, backward compatible

### Automated Process

1. **Version Detection**: Uses `setuptools_scm` to automatically determine version from git tags
2. **Tag Creation**: Creates annotated git tags (e.g., `v1.2.3`)
3. **GitHub Actions**: Automatically triggered on tag push
4. **CI/CD Pipeline**:
   - Runs tests on multiple Python versions (3.9-3.12)
   - Runs code quality checks (pylint, black, mypy, etc.)
   - Builds source distribution and wheel
   - Publishes to PyPI using trusted publishing
   - Creates GitHub release with changelog

### GitHub Actions Workflows

- **`test.yml`**: Runs on every push/PR
- **`publish.yml`**: Runs on tag creation, publishes to PyPI
- **`release.yml`**: Creates GitHub releases
- **`code-quality.yml`**: Code quality checks
- **`automated-release.yml`**: Manual workflow for creating releases

## 🛠 Development Commands

```bash
# Install development dependencies
make install-dev

# Run tests
make test

# Run all quality checks
make lint

# Build package locally
make build

# Clean build artifacts
make clean

# Run pre-release checks
make pre-release
```

## 🔐 PyPI Publishing

The package is configured to use PyPI's **trusted publishing**, which is more secure than API tokens:

1. No need to store API tokens as secrets
2. GitHub Actions authenticates directly with PyPI
3. Automatic publishing on tag creation

### First-Time Setup (if needed)

If you need to configure trusted publishing on PyPI:

1. Go to your PyPI project settings
2. Add a trusted publisher for GitHub Actions
3. Repository: `MarcFord/bunnystream`
4. Workflow: `publish.yml`
5. Environment: `pypi` (optional)

## 📊 Release Checklist

Before creating a release:

- [ ] All tests pass (`make test`)
- [ ] Code quality checks pass (`make lint`)
- [ ] Update CHANGELOG.md with new features/fixes
- [ ] Commit all changes
- [ ] Choose appropriate version bump (patch/minor/major)
- [ ] Run release script or command
- [ ] Verify GitHub Actions complete successfully
- [ ] Check that package appears on PyPI

## 🐛 Troubleshooting

### "Tests failed"
Fix failing tests before releasing. Run `make test` to see details.

### "Linting issues"
Fix code quality issues with:
```bash
uv run black src/ tests/          # Format code
uv run isort src/ tests/          # Sort imports
```

### "Tag already exists"
Delete the tag and try again:
```bash
git tag -d v1.2.3
git push origin :refs/tags/v1.2.3
```

### "PyPI upload failed"
Check GitHub Actions logs for details. Common issues:
- Version already exists on PyPI
- PyPI trusted publishing not configured
- Package build errors

## 📝 Examples

### Creating a patch release (bug fixes)
```bash
./release.sh
# Choose option 1 (patch)
# v1.2.3 → v1.2.4
```

### Creating a minor release (new features)
```bash
make release-minor
# v1.2.3 → v1.3.0
```

### Creating a major release (breaking changes)
```bash
python scripts/bump_version.py major --message "Breaking changes in API"
# v1.2.3 → v2.0.0
```
