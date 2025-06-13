# Linting Guide - Preventing CI Failures

## 🚨 Problem
We've experienced embarrassing CI failures due to linting errors that weren't caught locally before pushing to GitHub.

## ✅ Solution
Use the comprehensive linting check script before every push.

## 🔧 How to Check for Linting Issues

### Quick Check (Recommended before every push)
```bash
python tools/check_all_linting.py
```

This script checks:
- ✅ Source code (`src/`) linting
- ✅ Test code (`tests/`) linting
- ✅ Entire project linting
- ✅ Code formatting
- ✅ All pre-commit hooks

### Auto-Fix Most Issues
```bash
# Fix linting errors automatically
python -m ruff check . --fix --unsafe-fixes

# Fix formatting
python -m ruff format .

# Then verify everything is clean
python tools/check_all_linting.py
```

### Manual Pre-commit Check
```bash
# Run pre-commit on all files
pre-commit run --all-files
```

## 🎯 Workflow

**Before every commit/push:**

1. **Check**: `python tools/check_all_linting.py`
2. **Fix** (if needed): `python -m ruff check . --fix --unsafe-fixes && python -m ruff format .`
3. **Verify**: `python tools/check_all_linting.py`
4. **Commit & Push**: Only when all checks pass ✅

## 🔍 What Gets Checked

- **F841**: Unused variables
- **SIM117**: Nested `with` statements
- **SIM105**: `try-except-pass` patterns
- **B007**: Unused loop variables
- **UP038**: Old-style `isinstance` calls
- **E402**: Import order issues
- **Formatting**: Code style consistency

## 🚀 Pro Tips

1. **Install pre-commit hooks**: They run automatically on commit
   ```bash
   pip install pre-commit
   pre-commit install
   ```

2. **IDE Integration**: Configure your editor to run ruff on save

3. **Make it a habit**: Always run the check script before pushing

## 🎉 Result
No more embarrassing CI failures! The world won't see our linting mistakes anymore.
