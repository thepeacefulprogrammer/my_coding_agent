# My Coding Agent 🚀

[![CI](https://github.com/thepeacefulprogrammer/my_coding_agent/workflows/CI/badge.svg)](https://github.com/thepeacefulprogrammer/my_coding_agent/actions)
[![codecov](https://codecov.io/gh/thepeacefulprogrammer/my_coding_agent/branch/main/graph/badge.svg)](https://codecov.io/gh/thepeacefulprogrammer/my_coding_agent)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://github.com/python/mypy)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![License: Proprietary](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

**An epic code viewer with AI agent integration** - built with modern Python best practices and designed for the future of coding.

## ✨ Features

- 🎨 **Modern GUI**: Beautiful, responsive interface with syntax highlighting
- 🤖 **AI Integration**: Seamless coding agent integration for enhanced productivity
- 🔍 **Advanced Code Analysis**: Intelligent code insights and suggestions
- 🎯 **Extensible Architecture**: Plugin system for custom functionality
- 🛡️ **Type-Safe**: Full type hints and static analysis
- 📚 **Comprehensive Documentation**: Auto-generated API docs with examples
- ⚡ **High Performance**: Optimized for large codebases

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when released)
pip install my-coding-agent

# Or install from source
git clone https://github.com/thepeacefulprogrammer/my_coding_agent.git
cd my_coding_agent
pip install -e .
```

### Basic Usage

```python
from my_coding_agent import CodeViewer

# Create and show code viewer
viewer = CodeViewer()
viewer.load_file("example.py")
viewer.show()
```

## 🛠️ Development Setup

```bash
# Clone the repository
git clone https://github.com/thepeacefulprogrammer/my_coding_agent.git
cd my_coding_agent

# Complete development setup
make setup-dev

# Run all checks
make check-all
```

## 🧪 Quality Assurance

This project maintains high code quality through:

- **100% Type Coverage**: Full type hints with mypy checking
- **90%+ Test Coverage**: Comprehensive test suite with pytest
- **Security Scanning**: Automated vulnerability detection with bandit
- **Code Quality**: Linting and formatting with Ruff
- **Documentation**: Auto-generated API docs with Sphinx
- **Performance Testing**: Benchmarking with pytest-benchmark

### Development Commands

```bash
make lint          # Run all linting tools
make test          # Run test suite
make test-cov      # Run tests with coverage
make security      # Run security scans
make docs          # Build documentation
make performance   # Run benchmarks
```

## 📚 Documentation

- **[API Documentation](https://thepeacefulprogrammer.github.io/my_coding_agent)** - Auto-generated from docstrings
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development guidelines and standards
- **[Architecture Overview](docs/architecture.md)** - System design and patterns

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for detailed guidelines on:

- Code style and standards
- Testing requirements
- Documentation expectations
- Performance guidelines
- Security considerations

## 📊 Project Status

This project follows semantic versioning and maintains:

- ✅ **Modern Python Practices**: Python 3.8+ with latest tooling
- ✅ **CI/CD Pipeline**: Automated testing across Python versions
- ✅ **Security First**: Regular vulnerability scanning
- ✅ **Documentation Driven**: Comprehensive docs with examples
- ✅ **Performance Focused**: Benchmarking and optimization

## 🏗️ Architecture

```
src/my_coding_agent/
├── core/          # Core functionality
├── gui/           # GUI components
├── agents/        # AI agent integration
├── plugins/       # Plugin system
├── config/        # Configuration management
└── assets/        # Static resources
```

## 🔒 License

This project is proprietary software. See [LICENSE](LICENSE) for details.

## 📞 Support

- 📧 **Email**: randy.herritt@gmail.com
- 🐛 **Issues**: Please contact via email for now
- 💬 **Questions**: Feel free to reach out via email

---

*Built with ❤️ using modern Python best practices*
