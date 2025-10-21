# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions for continuous integration and continuous deployment (CI/CD). The pipeline automatically runs tests and code quality checks on every push and pull request.

## Workflow: CI (`ci.yml`)

### Trigger Events

The CI workflow runs on:
- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop` branches

### Jobs

#### 1. Test Suite (`test`)

Runs the complete test suite across multiple Python versions.

**Python Versions Tested:**
- Python 3.10
- Python 3.11
- Python 3.12

**Steps:**
1. ✅ Checkout code
2. ✅ Set up Python environment with caching
3. ✅ Install dependencies from `requirements.txt`
4. ✅ Run pytest with coverage reporting
5. ✅ Upload coverage to Codecov (Python 3.12 only)
6. ✅ Test demo scripts run without errors

**Coverage:**
- Generates XML and terminal coverage reports
- Tracks coverage for the `backend/` directory
- Uploads to Codecov for visualization

#### 2. Code Quality (`lint`)

Checks code formatting and style.

**Tools:**
- **black**: Code formatter
- **isort**: Import sorter
- **flake8**: Style guide enforcement

**Checks:**
- ⚠️ Code formatting (non-blocking)
- ⚠️ Import sorting (non-blocking)
- ❌ Syntax errors and undefined names (blocking)
- ⚠️ Code complexity and line length (non-blocking)

#### 3. Security Check (`security`)

Scans for security vulnerabilities.

**Tools:**
- **safety**: Dependency vulnerability scanner
- **bandit**: Python security linter

**Checks:**
- ⚠️ Known vulnerabilities in dependencies (non-blocking)
- ⚠️ Security issues in code (non-blocking)

#### 4. Build Status (`build-status`)

Final status check that depends on all other jobs.

**Behavior:**
- ✅ Passes if all tests pass
- ❌ Fails if any tests fail
- ⚠️ Non-blocking checks don't affect final status

## Pull Request Protection

### Recommended Branch Protection Rules

For the `main` branch, set up the following rules in GitHub:

1. **Require pull request reviews before merging**
   - Require at least 1 approval

2. **Require status checks to pass before merging**
   - Required checks:
     - `Test Suite (3.10)`
     - `Test Suite (3.11)`
     - `Test Suite (3.12)`
     - `Build Status`

3. **Require branches to be up to date before merging**
   - Ensures tests run on latest code

4. **Include administrators**
   - Apply rules to administrators as well

### Setting up Branch Protection

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Branches**
3. Click **Add rule** under "Branch protection rules"
4. Enter branch name pattern: `main`
5. Enable the options above
6. Click **Create** or **Save changes**

## Local Development

### Running Tests Locally

Before pushing, run tests locally to catch issues early:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=backend --cov-report=term
```

### Code Quality Checks

Install and run linting tools locally:

```bash
# Install tools
pip install black flake8 isort safety bandit

# Format code
black backend/ tests/

# Sort imports
isort backend/ tests/

# Lint code
flake8 backend/ tests/ --max-line-length=127

# Check security
safety check
bandit -r backend/
```

### Pre-commit Hook (Optional)

Create a pre-commit hook to run tests automatically:

```bash
# Create .git/hooks/pre-commit file
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Running tests before commit..."
python -m pytest tests/ -v
if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi
echo "Tests passed! Proceeding with commit."
EOF

chmod +x .git/hooks/pre-commit
```

## Workflow Status

### Viewing Workflow Runs

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. View all workflow runs and their status

### Understanding Status Badges

The README includes status badges:

- [![CI](https://img.shields.io/badge/CI-passing-brightgreen)]() **Passing** - All tests pass
- [![CI](https://img.shields.io/badge/CI-failing-red)]() **Failing** - Some tests fail
- [![CI](https://img.shields.io/badge/CI-pending-yellow)]() **Pending** - Tests running

## Troubleshooting

### Common Issues

**1. Tests pass locally but fail in CI**

Possible causes:
- Different Python version
- Missing dependencies
- Environment-specific code

Solution:
```bash
# Test with specific Python version locally
python3.10 -m pytest tests/ -v
```

**2. Import errors in CI**

Possible causes:
- Incorrect PYTHONPATH
- Missing `__init__.py` files

Solution: Ensure all package directories have `__init__.py`

**3. Coverage upload fails**

This is non-blocking and won't fail the build. Usually caused by:
- Network issues
- Codecov API limits

Solution: Check Codecov status or ignore if tests pass

### Re-running Failed Workflows

1. Go to **Actions** tab
2. Click on the failed workflow run
3. Click **Re-run jobs** → **Re-run all jobs**

## Future Enhancements

### Potential Additions

1. **Deployment Pipeline**
   - Auto-deploy to staging on `develop` push
   - Auto-deploy to production on `main` push
   - Deploy to Heroku/AWS/Azure

2. **Performance Testing**
   - Add performance benchmarks
   - Track performance over time
   - Alert on regressions

3. **Documentation Generation**
   - Auto-generate API docs
   - Deploy docs to GitHub Pages

4. **Release Automation**
   - Automatic version bumping
   - CHANGELOG generation
   - GitHub release creation

5. **Integration Tests**
   - Database integration tests
   - API endpoint tests
   - Frontend E2E tests

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [black Documentation](https://black.readthedocs.io/)
- [flake8 Documentation](https://flake8.pycqa.org/)

## Support

If you encounter issues with the CI/CD pipeline:

1. Check the workflow run logs in the Actions tab
2. Review this documentation
3. Check for similar issues in the repository's Issues tab
4. Create a new issue with:
   - Workflow run link
   - Error message
   - Steps to reproduce
