# Contributing to My Coding Agent 🚀

Thank you for your interest in contributing to **My Coding Agent**! This document provides guidelines and best practices to ensure a smooth contribution process.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Documentation Standards](#documentation-standards)
- [Testing Requirements](#testing-requirements)
- [Submitting Changes](#submitting-changes)
- [Performance Guidelines](#performance-guidelines)
- [Security Considerations](#security-considerations)

## 🤝 Code of Conduct

This project follows a strict code of conduct. Please be respectful, inclusive, and collaborative in all interactions.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment (recommended)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/my_coding_agent.git
   cd my_coding_agent
   ```

## 🔧 Development Setup

### Quick Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Complete development setup
make setup-dev
```

### Manual Setup

```bash
# Install in development mode with all dependencies
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
pre-commit install

# Run initial checks
make check-all
```

## 📝 Coding Standards

### Python Code Style

We use **Ruff** for linting and formatting (replaces Black, isort, flake8):

```bash
# Format code
make format

# Check code style
make lint
```

### Type Hints

**ALL** public functions, methods, and classes must include type hints:

```python
def process_file(file_path: Path, encoding: str = "utf-8") -> dict[str, Any]:
    """Process a file and return metadata.
    
    Args:
        file_path: Path to the file to process.
        encoding: Text encoding to use.
        
    Returns:
        Dictionary containing file metadata.
        
    Raises:
        FileNotFoundError: If the file doesn't exist.
        UnicodeDecodeError: If encoding fails.
    """
    # Implementation here
    pass
```

### Docstring Standards

We use **Google-style docstrings** for all public APIs:

```python
def calculate_complexity(code: str, language: str) -> ComplexityResult:
    """Calculate code complexity metrics.
    
    This function analyzes the provided code and returns various
    complexity metrics including cyclomatic complexity, cognitive
    complexity, and maintainability index.
    
    Args:
        code: The source code to analyze.
        language: Programming language of the code (e.g., "python", "javascript").
        
    Returns:
        ComplexityResult object containing all calculated metrics.
        
    Raises:
        UnsupportedLanguageError: If the language is not supported.
        ParseError: If the code cannot be parsed.
        
    Example:
        >>> result = calculate_complexity("def hello(): print('hi')", "python")
        >>> print(result.cyclomatic_complexity)
        1
        
    Note:
        Large code files may take significant time to process.
        Consider using async version for UI applications.
    """
```

### Error Handling

- Use specific exception types
- Always include helpful error messages
- Log errors appropriately
- Handle edge cases gracefully

```python
class CodeViewerError(Exception):
    """Base exception for code viewer errors."""
    pass

class FileLoadError(CodeViewerError):
    """Raised when a file cannot be loaded."""
    
    def __init__(self, file_path: Path, reason: str) -> None:
        super().__init__(f"Could not load {file_path}: {reason}")
        self.file_path = file_path
        self.reason = reason
```

## 📚 Documentation Standards

### Docstring Requirements

- **All public functions, classes, and methods** must have docstrings
- Include `Args`, `Returns`, `Raises`, and `Example` sections
- Use proper type annotations in docstrings
- Provide working code examples

### API Documentation

- Auto-generated from docstrings using Sphinx
- Examples must be testable with doctest
- Include performance notes for complex operations

### README Updates

Update relevant README sections when:
- Adding new features
- Changing installation requirements
- Modifying usage patterns

## 🧪 Testing Requirements

### Test Coverage

- **Minimum 90% test coverage** for new code
- All public APIs must have tests
- Include both unit and integration tests

### Test Types

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run performance benchmarks
make performance

# Run security checks
make security
```

### Writing Tests

```python
def test_code_viewer_load_file(sample_code_files: dict[str, Path], qapp: QApplication) -> None:
    """Test loading a file in the code viewer.
    
    Args:
        sample_code_files: Fixture providing sample files.
        qapp: QApplication fixture for GUI testing.
    """
    viewer = CodeViewer()
    python_file = sample_code_files["python"]
    
    # Test successful loading
    result = viewer.load_file(python_file)
    assert result is True
    assert viewer.current_file == python_file
    
    # Test file content is properly loaded
    content = viewer.get_content()
    assert "fibonacci" in content
    assert "Calculator" in content
```

### Performance Tests

```python
def test_large_file_performance(benchmark: Callable, benchmark_large_file: Path) -> None:
    """Benchmark loading large files.
    
    Args:
        benchmark: Pytest benchmark fixture.
        benchmark_large_file: Large file fixture.
    """
    def load_file() -> None:
        viewer = CodeViewer()
        viewer.load_file(benchmark_large_file)
    
    # Should complete within 500ms for 1000-line file
    result = benchmark(load_file)
    assert result < 0.5  # seconds
```

## 🔄 Submitting Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `perf/description` - Performance improvements

### Commit Messages

Follow conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(gui): add syntax highlighting for TypeScript`
- `fix(agent): handle API timeout errors gracefully`
- `docs(api): update CodeViewer docstrings`
- `perf(viewer): optimize large file loading`

### Pull Request Process

1. **Before submitting:**
   ```bash
   make check-all  # Run all checks
   ```

2. **PR Requirements:**
   - Clear description of changes
   - Link to related issues
   - Screenshots for UI changes
   - Performance impact notes
   - Breaking change documentation

3. **Review Process:**
   - All checks must pass
   - At least one code review required
   - Documentation review for API changes
   - Performance review for optimization PRs

## ⚡ Performance Guidelines

### Code Performance

- Profile code changes affecting UI responsiveness
- Large file operations must be asynchronous
- Memory usage should be reasonable (< 100MB for typical files)

### Benchmark Requirements

```python
@pytest.mark.benchmark(group="file_loading")
def test_file_loading_performance(benchmark: Callable) -> None:
    """Benchmark file loading performance."""
    # Performance test implementation
```

### UI Performance

- GUI operations must remain responsive
- Loading indicators for operations > 100ms
- Progress bars for operations > 1 second

## 🔒 Security Considerations

### Code Security

- Run security checks: `make security`
- No hardcoded secrets or API keys
- Validate all user inputs
- Use secure defaults

### AI Integration Security

- API keys must be configurable
- Implement rate limiting
- Sanitize code before sending to AI services
- Handle API failures gracefully

## 🏗️ Architecture Guidelines

### Module Organization

```
src/my_coding_agent/
├── core/          # Core functionality
├── gui/           # GUI components
├── agents/        # AI agent integration
├── plugins/       # Plugin system
├── config/        # Configuration management
└── assets/        # Static assets
```

### Design Patterns

- Use dependency injection for testability
- Implement observer pattern for UI updates
- Follow single responsibility principle
- Prefer composition over inheritance

## 🐛 Debugging

### Debug Mode

```bash
export MY_CODING_AGENT_DEBUG=true
python -m my_coding_agent
```

### Logging

- Use structured logging
- Include context in log messages
- Set appropriate log levels

## 📦 Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release PR
4. Tag release after merge
5. CI/CD handles package building and publishing

## 🤝 Getting Help

- 📧 Email: randy.herritt@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/thepeacefulprogrammer/my_coding_agent/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/thepeacefulprogrammer/my_coding_agent/discussions)

---

## 🎯 Quick Checklist

Before submitting your PR, ensure:

- [ ] Code follows style guidelines (`make lint` passes)
- [ ] All tests pass (`make test` passes)
- [ ] Security checks pass (`make security` passes)
- [ ] Documentation is updated
- [ ] Type hints are included
- [ ] Performance impact is considered
- [ ] Commit messages follow conventions

Thank you for contributing to **My Coding Agent**! 🚀 