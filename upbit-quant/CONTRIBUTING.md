# Contributing to UPbit Quantitative Trading Platform

Thank you for your interest in contributing to UPbit Quant! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)

## 🤝 Code of Conduct

This project follows a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [contact information].

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/UPbit-Quant.git
   cd UPbit-Quant
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/original-username/UPbit-Quant.git
   ```

## 🛠️ Development Setup

### Prerequisites

- Python 3.8 or higher
- pip or conda
- Git
- Docker (optional)

### Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

4. **Set up configuration**:
   ```bash
   cp config.env.example .env
   # Edit .env with your configuration
   ```

5. **Run tests** to ensure everything works:
   ```bash
   pytest
   ```

## 📝 Contributing Guidelines

### Types of Contributions

We welcome several types of contributions:

- **Bug fixes**: Fix issues and bugs
- **New features**: Add new functionality
- **Documentation**: Improve documentation
- **Tests**: Add or improve tests
- **Performance**: Optimize performance
- **Refactoring**: Improve code structure

### Before You Start

1. **Check existing issues** and pull requests
2. **Create an issue** for significant changes
3. **Discuss** your approach with maintainers
4. **Fork** the repository and create a feature branch

### Branch Naming

Use descriptive branch names:

- `feature/add-new-algorithm`
- `bugfix/fix-trading-bot-error`
- `docs/update-readme`
- `test/add-integration-tests`

## 🔄 Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation as needed
   - Follow the code style guidelines

3. **Test your changes**:
   ```bash
   pytest
   black upbit_quant tests
   flake8 upbit_quant tests
   mypy upbit_quant
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: description of changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Use a clear, descriptive title
   - Provide a detailed description
   - Reference related issues
   - Include screenshots for UI changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

## 🐛 Issue Guidelines

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check if it's already fixed** in the latest version
3. **Gather information** about your environment

### Issue Templates

Use the appropriate issue template:

- **Bug Report**: For reporting bugs
- **Feature Request**: For requesting new features
- **Documentation**: For documentation issues
- **Question**: For asking questions

### Bug Report Template

```markdown
**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- Package version: [e.g., 1.0.0]

**Additional context**
Any other relevant information.
```

## 🎨 Code Style

### Python Code Style

We follow these style guidelines:

- **PEP 8**: Python code style guide
- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **isort**: Import sorting

### Code Formatting

```bash
# Format code with Black
black upbit_quant tests

# Sort imports with isort
isort upbit_quant tests

# Check code style with flake8
flake8 upbit_quant tests
```

### Type Hints

Use type hints for better code documentation:

```python
from typing import List, Dict, Optional

def calculate_returns(prices: List[float]) -> Dict[str, float]:
    """Calculate returns from price data."""
    # Implementation
    pass
```

### Docstrings

Follow Google docstring style:

```python
def train_model(data: List[float], epochs: int = 100) -> Model:
    """Train a machine learning model.
    
    Args:
        data: Training data
        epochs: Number of training epochs
        
    Returns:
        Trained model
        
    Raises:
        ValueError: If data is empty
    """
    # Implementation
    pass
```

## 🧪 Testing

### Test Structure

```
tests/
├── test_core/           # Core functionality tests
├── test_utils/          # Utility function tests
├── test_main/           # Main application tests
├── test_integration/    # Integration tests
└── conftest.py         # Test configuration
```

### Writing Tests

```python
import pytest
from upbit_quant.utils.validation import validate_price

class TestValidatePrice:
    """Test price validation."""
    
    def test_valid_price(self):
        """Test valid price validation."""
        result = validate_price("100.50")
        assert result == Decimal('100.50')
    
    def test_invalid_price(self):
        """Test invalid price validation."""
        with pytest.raises(ValidationError):
            validate_price("invalid")
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_core/test_config.py

# Run tests with coverage
pytest --cov=upbit_quant --cov-report=html

# Run tests in parallel
pytest -n auto
```

## 📚 Documentation

### Documentation Standards

- **Clear and concise**: Write clear, easy-to-understand documentation
- **Examples**: Include code examples
- **Up-to-date**: Keep documentation current with code changes
- **Comprehensive**: Cover all public APIs

### Documentation Types

- **README**: Project overview and setup
- **API Documentation**: Function and class documentation
- **Tutorials**: Step-by-step guides
- **Examples**: Code examples and use cases

### Updating Documentation

1. **Update docstrings** for new functions/classes
2. **Update README** for new features
3. **Add examples** for complex functionality
4. **Update type hints** for better IDE support

## 🚀 Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number updated
- [ ] CHANGELOG updated
- [ ] Release notes prepared

## 🤔 Questions?

If you have questions about contributing:

- **Check the documentation** first
- **Search existing issues** for similar questions
- **Create a new issue** with the "question" label
- **Join our discussions** on GitHub Discussions

## 🙏 Recognition

Contributors will be recognized in:

- **README**: List of contributors
- **Release notes**: Credit for contributions
- **Documentation**: Attribution for significant contributions

Thank you for contributing to UPbit Quant! 🚀
