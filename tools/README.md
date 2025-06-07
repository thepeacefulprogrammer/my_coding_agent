# Development Tools

This directory contains utility scripts and tools for development workflow.

## Purpose

Tools in this directory are meant for:
- Development setup and configuration
- Project maintenance scripts  
- Build automation helpers
- Development workflow utilities

## Guidelines

### What belongs here:
- ✅ Development setup scripts
- ✅ Code generation tools
- ✅ Project validation scripts
- ✅ Build/release automation
- ✅ Development debugging utilities

### What does NOT belong here:
- ❌ Application source code (belongs in `src/`)
- ❌ Tests (belongs in `tests/`)
- ❌ Examples (belongs in `examples/`)
- ❌ User-facing scripts (should be in `src/` as proper modules)

## Running Tools

Tools should be run from the project root:

```bash
# From project root
python tools/script_name.py
```

## Contributing Tools

When adding new tools:
1. Add a descriptive docstring explaining the tool's purpose
2. Include usage instructions in the docstring or as comments
3. Follow the project's coding standards
4. Update this README if adding new categories of tools 