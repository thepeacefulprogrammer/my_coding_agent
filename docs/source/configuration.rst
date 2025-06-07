Configuration
=============

Overview
--------

My Coding Agent can be configured through various settings that control the appearance and behavior of the application.

Settings File
-------------

Configuration is stored in a settings file located at:

* **Linux/macOS**: ``~/.config/my_coding_agent/settings.json``
* **Windows**: ``%APPDATA%\my_coding_agent\settings.json``

Available Settings
------------------

Display Settings
~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "theme": "dark",
     "font_family": "Consolas",
     "font_size": 12,
     "line_numbers": true,
     "highlight_current_line": true,
     "show_whitespace": false,
     "word_wrap": false,
     "tab_width": 4
   }

Window Settings
~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "window_width": 1200,
     "window_height": 800,
     "splitter_position": 300
   }

Application Settings
~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "auto_detect_language": true,
     "max_file_size_mb": 10.0,
     "recent_files_count": 10
   }

Configuration API
-----------------

The configuration system is accessible programmatically through the Settings class:

.. code-block:: python

   from my_coding_agent.config import Settings

   settings = Settings()
   settings.theme = "light"
   settings.save()
