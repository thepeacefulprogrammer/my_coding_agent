"""GUI components for the Code Viewer application.

This module provides the graphical user interface components including
chat widgets, message display, and other UI elements.

## Components

- **ChatWidget**: Main chat interface for user interactions
- **MessageDisplay**: Component for displaying chat messages
- **ThemeAwareWidget**: Base widget with theme support

## Usage

>>> from code_viewer.gui import widgets
>>> from code_viewer.gui.styles import apply_dark_theme

## Chat Widget

The chat widget provides a complete chat interface:

```python
from code_viewer.gui.chat_widget import ChatWidget

chat = ChatWidget()
chat.add_user_message("Hello, AI!")
chat.show()
```

## Message Display

For custom message display:

```python
from code_viewer.gui.components.message_display import MessageDisplay

display = MessageDisplay()
display.add_message("Hello", "user")
```
"""

from __future__ import annotations

# GUI module version
__version__ = "0.1.0"

# Module metadata
__author__ = "Randy Herritt"
__email__ = "randy.herritt@gmail.com"

# GUI components will be imported as they're implemented
# from . import widgets
# from . import styles

# Import main GUI components
from .chat_widget import ChatWidget
from .chat_widget_v2 import SimplifiedChatWidget
from .components.message_display import MessageDisplay

__all__ = [
    "ChatWidget",
    "SimplifiedChatWidget",
    "MessageDisplay",
]
