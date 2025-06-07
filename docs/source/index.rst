My Coding Agent Documentation
==============================

Welcome to **My Coding Agent** - an epic code viewer with AI agent integration!

.. image:: https://img.shields.io/badge/python-3.9+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/license-Proprietary-red.svg
   :alt: License

.. image:: https://img.shields.io/badge/code%20style-ruff-000000.svg
   :target: https://github.com/astral-sh/ruff
   :alt: Code style: Ruff

**My Coding Agent** is a modern, feature-rich code viewing application that combines
intuitive GUI design with powerful AI agent capabilities. Built with Python and 
following the latest development best practices.

Key Features
------------

* 🎨 **Modern GUI**: Beautiful, responsive interface built with modern UI frameworks
* 🤖 **AI Integration**: Seamless integration with coding agents for enhanced productivity
* 🔍 **Advanced Code Viewing**: Syntax highlighting, line numbers, and smart navigation
* 🎯 **Extensible**: Plugin architecture for custom functionality
* 🛡️ **Type-Safe**: Full type hints and static analysis support
* 📚 **Well-Documented**: Comprehensive documentation with examples

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install my-coding-agent

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from my_coding_agent import CodeViewer
   
   # Create a code viewer instance
   viewer = CodeViewer()
   
   # Load and display a file
   viewer.load_file("example.py")
   viewer.show()

Documentation Sections
----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   tutorials/index
   configuration
   plugins

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index
   api/core
   api/gui
   api/agents
   api/plugins

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   contributing
   development
   testing
   release_notes

.. toctree::
   :maxdepth: 1
   :caption: About

   changelog
   license
   authors

API Reference
-------------

The complete API documentation is auto-generated from docstrings:

.. autosummary::
   :toctree: _autosummary
   :template: custom-module-template.rst
   :recursive:

   my_coding_agent

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Contributing
============

We welcome contributions! Please see our :doc:`contributing` guide for details.

License
=======

This project is proprietary software. See :doc:`license` for details.

Support
=======

* 📧 Email: randy.herritt@gmail.com
* 🐛 Issues: `GitHub Issues <https://github.com/thepeacefulprogrammer/my_coding_agent/issues>`_
* 💬 Discussions: `GitHub Discussions <https://github.com/thepeacefulprogrammer/my_coding_agent/discussions>`_ 