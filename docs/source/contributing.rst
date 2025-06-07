Contributing
============

We welcome contributions to My Coding Agent!

Development Setup
-----------------

1. Fork the repository
2. Clone your fork locally
3. Create a development environment:

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"

4. Install pre-commit hooks:

.. code-block:: bash

   pre-commit install

Development Guidelines
----------------------

* Follow PEP 8 style guidelines
* Use type hints for all new code
* Write tests for new functionality
* Update documentation as needed

Running Tests
-------------

.. code-block:: bash

   pytest

Code Style
----------

We use Ruff for code formatting and linting:

.. code-block:: bash

   ruff check .
   ruff format .

Submitting Changes
------------------

1. Create a feature branch
2. Make your changes
3. Run tests and ensure they pass
4. Submit a pull request with a clear description
