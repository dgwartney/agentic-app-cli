# Publishing Guide

This document provides instructions for publishing `agentic-api-cli` to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at [https://pypi.org/account/register/](https://pypi.org/account/register/)
2. **TestPyPI Account** (recommended for testing): [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/)
3. **API Token**: Generate an API token from your PyPI account settings

## Setup

### Configure PyPI Credentials

Create or update `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TEST-API-TOKEN-HERE
```

**Security Note**: Alternatively, use environment variables or keyring for token storage.

## Pre-Publishing Checklist

Before publishing, ensure:

- [ ] Version number is updated in `pyproject.toml`
- [ ] `CHANGELOG.md` is updated with release notes
- [ ] All tests pass: `uv run pytest`
- [ ] Type checking passes: `uv run mypy agentic_api_cli`
- [ ] Linting passes: `uv run ruff check agentic_api_cli`
- [ ] Package builds successfully: `uv build`
- [ ] README.md is accurate and complete
- [ ] LICENSE file is present and correct
- [ ] Author information is updated in `pyproject.toml`
- [ ] GitHub repository URLs are updated in `pyproject.toml`

## Building the Package

Build both source distribution and wheel:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build package
uv build
```

This creates:
- `dist/agentic_api_cli-X.Y.Z.tar.gz` (source distribution)
- `dist/agentic_api_cli-X.Y.Z-py3-none-any.whl` (wheel)

## Testing the Build

### Install Locally

Test the built package locally:

```bash
# Create a test virtual environment
uv venv test-env
source test-env/bin/activate

# Install from wheel
uv pip install dist/agentic_api_cli-0.1.0-py3-none-any.whl

# Test the command
agentic-api-cli

# Clean up
deactivate
rm -rf test-env
```

### Publish to TestPyPI

Test the publishing process on TestPyPI first:

```bash
# Install twine (if not already installed)
uv pip install twine

# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

### Install from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentic-api-cli
```

Note: `--extra-index-url` is needed because dependencies are on PyPI, not TestPyPI.

## Publishing to PyPI

Once testing is complete, publish to PyPI:

```bash
# Upload to PyPI
twine upload dist/*
```

Or use `uv` with publish support:

```bash
uv publish
```

## Post-Publishing

After publishing:

1. **Create Git Tag**: Tag the release in git
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

2. **Create GitHub Release**: Create a release on GitHub with release notes from CHANGELOG.md

3. **Verify Installation**: Test installation from PyPI
   ```bash
   pip install agentic-api-cli
   agentic-api-cli
   ```

4. **Update Documentation**: Ensure all documentation references the correct version

## Version Bumping

For subsequent releases, update the version:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with new changes
3. Update version in `agentic_api_cli/__init__.py` (if manually set)
4. Commit changes
5. Follow publishing process

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (X.0.0): Incompatible API changes
- **MINOR** (0.X.0): New functionality, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

## Automation (Optional)

Consider automating releases with GitHub Actions:

1. Create `.github/workflows/publish.yml`
2. Configure to trigger on tag push
3. Automatically build and publish to PyPI

Example workflow:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv build
      - run: uv publish
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
```

## Troubleshooting

### Build Issues

```bash
# Verify package structure
tar -tzf dist/agentic_api_cli-X.Y.Z.tar.gz

# Check wheel contents
unzip -l dist/agentic_api_cli-X.Y.Z-py3-none-any.whl
```

### Upload Issues

- **403 Forbidden**: Check API token and permissions
- **400 Bad Request**: Version may already exist (PyPI doesn't allow overwrites)
- **File already exists**: You cannot re-upload the same version

### Installation Issues

```bash
# Clear pip cache
pip cache purge

# Install with verbose output
pip install -v agentic-api-cli
```

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Twine Documentation](https://twine.readthedocs.io/)
