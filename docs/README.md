# Documentation

This directory contains the project documentation source files.

## Structure

The documentation is built using Sphinx and follows standard Python documentation practices:

```
docs/
├── README.md          # This file
├── conf.py           # Sphinx configuration (when created)
├── index.rst         # Main documentation index
├── api/              # API reference documentation
├── tutorials/        # User tutorials and guides
├── development/      # Development and contribution guides
└── _build/           # Built documentation (generated, not in git)
```

## Building Documentation

To build the documentation locally:

```bash
# Install documentation dependencies
pip install -e .[docs]

# Build HTML documentation
sphinx-build -b html docs docs/_build/html

# Or use the tox environment (when configured)
tox run -e docs
```

## Writing Documentation

### Guidelines:
- Use reStructuredText (.rst) for main documentation files
- Follow Sphinx conventions for cross-references
- Include docstrings in source code for API documentation
- Write clear, concise explanations with examples
- Update documentation when adding new features

### API Documentation:
API documentation is automatically generated from docstrings in the source code. Ensure all public functions, classes, and modules have proper docstrings following Google or NumPy style.

## Documentation Dependencies

Documentation dependencies are defined in `pyproject.toml` under `[project.optional-dependencies.docs]`.
