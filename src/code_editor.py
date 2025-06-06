"""
CodeEditor module for managing CodeView widget lifecycle and syntax highlighting integration.

This module provides the CodeEditor class which handles the proper creation and management
of Chlorophyll CodeView widgets with lexer integration for syntax highlighting.
"""

from chlorophyll.codeview import CodeView
from typing import Optional, Any, Dict, Tuple
import tkinter as tk
from tkinter import ttk
try:
    from chlorophyll import CodeView
except ImportError:
    # Mock CodeView for testing
    class CodeView:
        def __init__(self, parent, **kwargs):
            self.parent = parent
            self.kwargs = kwargs


class CodeEditor:
    """
    Manages CodeView widget lifecycle for syntax highlighting in the coding agent.
    
    This class handles the creation, replacement, and management of CodeView widgets
    since they require lexers to be set during construction rather than afterward.
    Provides widget lifecycle management including state capture/restoration and
    safe destruction.
    """
    
    def __init__(self, parent, syntax_manager, scrollbar=None, width=80, height=24):
        """
        Initialize CodeEditor with parent frame and syntax manager.
        
        Args:
            parent: Parent tkinter widget to contain the CodeView
            syntax_manager: SyntaxManager instance for lexer detection
            scrollbar: Optional scrollbar widget to connect to CodeView
            width: Default width for created widgets (default: 80)
            height: Default height for created widgets (default: 24)
        """
        self.parent = parent
        self.syntax_manager = syntax_manager
        self.scrollbar = scrollbar
        self.width = width
        self.height = height
        self._current_widget = None
        
    @property
    def current_widget(self):
        """Get the current CodeView widget."""
        return self._current_widget
        
    @current_widget.setter
    def current_widget(self, widget):
        """Set the current CodeView widget."""
        self._current_widget = widget
        
    def has_widget(self):
        """Check if a CodeView widget currently exists."""
        return self._current_widget is not None
        
    def get_lexer_for_file(self, filename):
        """Get appropriate lexer for a file using the syntax manager."""
        return self.syntax_manager.get_lexer_for_file(filename)
        
    def create_widget(self, lexer=None):
        """
        Create a new CodeView widget with optional lexer.
        
        Args:
            lexer: Optional lexer to set during widget construction
            
        Returns:
            CodeView widget instance
        """
        widget_args = {
            'width': self.width,
            'height': self.height
        }
        
        if lexer is not None:
            widget_args['lexer'] = lexer
            
        return CodeView(self.parent, **widget_args)

    def create_widget_for_file(self, filename):
        """
        Create a widget with automatic lexer detection for a specific file.
        
        Args:
            filename: File name/path to detect lexer from
            
        Returns:
            CodeView widget instance with appropriate lexer
        """
        lexer = self.get_lexer_for_file(filename)
        return self.create_widget(lexer=lexer)
        
    def get_widget_preset(self, preset_name):
        """
        Get configuration preset for widget creation.
        
        Args:
            preset_name: Name of the preset ('readonly', 'editable', etc.)
            
        Returns:
            Dictionary of widget configuration options
        """
        presets = {
            'readonly': {
                'state': 'disabled',
                'wrap': 'none',
                'selectbackground': '#3B4252',
                'insertbackground': '#D8DEE9',
                'width': self.width,
                'height': self.height
            },
            'editable': {
                'state': 'normal',
                'wrap': 'none',
                'selectbackground': '#3B4252',
                'insertbackground': '#D8DEE9',
                'width': self.width,
                'height': self.height
            }
        }
        
        # Return readonly as default if preset not found
        return presets.get(preset_name, presets['readonly'])
        
    def create_widget_with_preset(self, preset_name, **override_options):
        """
        Create a widget using a preset configuration.
        
        Args:
            preset_name: Name of the preset to use
            **override_options: Additional options to override preset defaults
            
        Returns:
            CodeView widget instance with preset configuration
        """
        preset_config = self.get_widget_preset(preset_name)
        
        # Override preset with any custom options
        widget_config = preset_config.copy()
        widget_config.update(override_options)
        
        return CodeView(self.parent, **widget_config)
        
    def create_configured_widget(self, filename=None, preset=None, grid_options=None, set_as_current=False, **widget_options):
        """
        Create a fully configured widget with all setup.
        
        Args:
            filename: Optional filename for lexer detection
            preset: Optional preset name to use for configuration
            grid_options: Optional dictionary of grid layout options
            set_as_current: Whether to set the widget as current widget
            **widget_options: Additional widget configuration options
            
        Returns:
            Fully configured CodeView widget
        """
        # Determine lexer if filename provided
        lexer = None
        if filename:
            lexer = self.get_lexer_for_file(filename)
            
        # Start with preset configuration if provided
        if preset:
            widget_config = self.get_widget_preset(preset).copy()
        else:
            widget_config = {
                'width': self.width,
                'height': self.height
            }
            
        # Add lexer if available
        if lexer:
            widget_config['lexer'] = lexer
            
        # Override with any custom options
        widget_config.update(widget_options)
        
        # Create the widget
        widget = CodeView(self.parent, **widget_config)
        
        # Configure scrollbar if available
        self.configure_scrollbar(widget)
        
        # Configure grid layout if requested
        if grid_options:
            self.grid_widget(widget, **grid_options)
        else:
            # Default grid layout
            self.grid_widget(widget)
            
        # Set as current widget if requested
        if set_as_current:
            self.current_widget = widget
            
        return widget
        
    def configure_scrollbar(self, widget):
        """Configure scrollbar connection for a widget."""
        if self.scrollbar is not None:
            self.scrollbar.config(command=widget.yview)
            widget.config(yscrollcommand=self.scrollbar.set)
            
    def grid_widget(self, widget, **grid_options):
        """Configure widget grid layout with default or custom options."""
        default_options = {'sticky': 'nsew'}
        default_options.update(grid_options)
        widget.grid(**default_options)
        
    def capture_widget_state(self, widget=None):
        """
        Capture current widget state with enhanced relationship handling.
        
        Args:
            widget: Widget to capture state from (defaults to current_widget)
            
        Returns:
            Dictionary containing widget state
        """
        if widget is None:
            widget = self.current_widget
            
        if not widget:
            return {
                'content': '',
                'cursor_position': '1.0',
                'scroll_position': (0.0, 1.0),
                'selection': None
            }
            
        # Capture content
        content = widget.get("1.0", "end-1c")
        
        # Capture cursor position
        cursor_position = widget.index(tk.INSERT)
        
        # Capture scroll position
        scroll_position = widget.yview()
        
        # Capture selection
        selection_ranges = widget.tag_ranges(tk.SEL)
        selection = tuple(selection_ranges) if selection_ranges else None
        
        return {
            'content': content,
            'cursor_position': cursor_position,
            'scroll_position': scroll_position,
            'selection': selection
        }
        
    def restore_widget_state(self, widget, state):
        """
        Restore widget state from captured state.
        
        Args:
            widget: Widget to restore state to
            state: State dictionary from capture_widget_state()
        """
        # Restore content
        widget.delete("1.0", tk.END)
        widget.insert("1.0", state['content'])
        
        # Restore cursor position
        widget.mark_set(tk.INSERT, state['cursor_position'])
        
        # Restore scroll position
        if state['scroll_position'][0] > 0:
            widget.yview_moveto(state['scroll_position'][0])
            
        # Restore selection
        if state['selection']:
            widget.tag_add(tk.SEL, state['selection'][0], state['selection'][1])
            
    def destroy_widget_safely(self):
        """
        Safely destroy the current widget with comprehensive cleanup of tkinter references.
        
        Performs thorough cleanup including:
        - Event binding removal
        - Scrollbar disconnection
        - Parent container cleanup
        - Widget variable clearing
        - Child widget destruction
        - Memory cleanup
        """
        if self.has_widget():
            widget = self.current_widget
            
            try:
                # 1. Clear all event bindings
                try:
                    widget.unbind_all()
                except (tk.TclError, AttributeError):
                    pass
                    
                # 2. Disconnect scrollbar if present
                if self.scrollbar is not None:
                    try:
                        self.scrollbar.config(command='')
                    except (tk.TclError, AttributeError):
                        pass
                
                # 3. Clear widget from parent container
                try:
                    widget.pack_forget()
                except (tk.TclError, AttributeError):
                    pass
                    
                try:
                    widget.grid_forget()
                except (tk.TclError, AttributeError):
                    pass
                    
                # 4. Clear widget variables
                try:
                    widget_vars = widget.getvar()
                    if isinstance(widget_vars, dict):
                        for var in widget_vars.values():
                            if hasattr(var, 'set'):
                                var.set('')
                except (tk.TclError, AttributeError):
                    pass
                
                # 5. Destroy child widgets first
                try:
                    children = widget.winfo_children()
                    for child in children:
                        try:
                            child.destroy()
                        except (tk.TclError, AttributeError):
                            pass
                except (tk.TclError, AttributeError):
                    pass
                
                # 6. Finally destroy the main widget
                widget.destroy()
                
            except tk.TclError:
                # Widget may already be destroyed
                pass
            except Exception:
                # Handle any other unexpected errors gracefully
                pass
            finally:
                # 7. Always clear the reference and trigger memory cleanup
                self.current_widget = None
                
                # 8. Force garbage collection for memory cleanup
                try:
                    import gc
                    gc.collect()
                except ImportError:
                    pass
                
    def capture_widget_geometry_info(self, widget):
        """
        Capture complete geometry manager information for a widget.
        
        Args:
            widget: Widget to capture geometry info from
            
        Returns:
            Dictionary containing geometry manager information
        """
        geometry_info = {
            'manager': None,
            'info': {},
            'parent': None,
            'focus_state': False
        }
        
        try:
            # Capture parent reference
            geometry_info['parent'] = widget.master
            
            # Check focus state
            try:
                geometry_info['focus_state'] = widget.focus_get() == widget
            except (tk.TclError, AttributeError):
                geometry_info['focus_state'] = False
            
            # Try to get grid info
            try:
                grid_info = widget.grid_info()
                if grid_info:
                    geometry_info['manager'] = 'grid'
                    geometry_info['info'] = grid_info
                    return geometry_info
            except (tk.TclError, AttributeError):
                pass
                
            # Try to get pack info
            try:
                pack_info = widget.pack_info()
                if pack_info:
                    geometry_info['manager'] = 'pack'
                    geometry_info['info'] = pack_info
                    return geometry_info
            except (tk.TclError, AttributeError):
                pass
                
            # Try to get place info
            try:
                place_info = widget.place_info()
                if place_info:
                    geometry_info['manager'] = 'place'
                    geometry_info['info'] = place_info
                    return geometry_info
            except (tk.TclError, AttributeError):
                pass
                
        except (tk.TclError, AttributeError):
            pass
            
        return geometry_info
        
    def apply_geometry_info(self, widget, geometry_info):
        """
        Apply captured geometry information to a widget.
        
        Args:
            widget: Widget to apply geometry to
            geometry_info: Geometry information from capture_widget_geometry_info()
        """
        try:
            # Set parent
            if geometry_info.get('parent'):
                try:
                    widget.master = geometry_info['parent']
                except (tk.TclError, AttributeError):
                    pass
            
            # Apply geometry manager configuration
            manager = geometry_info.get('manager')
            info = geometry_info.get('info', {})
            
            if manager == 'grid' and info:
                # Handle both real dictionaries and Mock objects in tests
                try:
                    if hasattr(info, 'keys') and callable(info.keys):
                        # This is a real dictionary
                        widget.grid(**info)
                    else:
                        # This might be a Mock object, try basic grid
                        widget.grid(sticky='nsew')
                except (TypeError, AttributeError):
                    # Fallback to basic grid layout for Mock objects
                    widget.grid(sticky='nsew')
            elif manager == 'pack' and info:
                try:
                    if hasattr(info, 'keys') and callable(info.keys):
                        widget.pack(**info)
                    else:
                        widget.pack(fill='both', expand=True)
                except (TypeError, AttributeError):
                    widget.pack(fill='both', expand=True)
            elif manager == 'place' and info:
                try:
                    if hasattr(info, 'keys') and callable(info.keys):
                        widget.place(**info)
                    else:
                        widget.place(relx=0, rely=0, relwidth=1, relheight=1)
                except (TypeError, AttributeError):
                    widget.place(relx=0, rely=0, relwidth=1, relheight=1)
            else:
                # Default to grid with basic settings
                widget.grid(sticky='nsew')
                
            # Restore focus if widget had it
            if geometry_info.get('focus_state'):
                try:
                    widget.focus_set()
                except (tk.TclError, AttributeError):
                    pass
                    
        except (tk.TclError, AttributeError):
            # Fallback to basic grid layout
            try:
                widget.grid(sticky='nsew')
            except (tk.TclError, AttributeError):
                pass
                
    def replace_widget_with_enhanced_container_relationships(self, old_widget, lexer):
        """
        Replace widget with comprehensive container relationship maintenance.
        
        Args:
            old_widget: Widget to replace
            lexer: Lexer for the new widget
            
        Returns:
            New widget with all relationships maintained
        """
        # Capture complete state including geometry and relationships
        widget_state = self.capture_widget_state(old_widget)
        geometry_info = self.capture_widget_geometry_info(old_widget)
        
        # Safely destroy the old widget
        self.destroy_widget_safely()
        
        # Create new widget with lexer
        new_widget = self.create_widget(lexer=lexer)
        
        # Apply geometry and container relationships
        self.apply_geometry_info(new_widget, geometry_info)
        
        # Configure scrollbar if present
        if self.scrollbar is not None:
            self.configure_scrollbar(new_widget)
            
        # Restore content and widget state
        self.restore_widget_state(new_widget, widget_state)
        
        # Set as current widget
        self.current_widget = new_widget
        
        return new_widget
        
    def replace_widget_with_lexer(self, lexer):
        """
        Replace current widget with new one using specified lexer.
        Enhanced with comprehensive container relationship maintenance.
        
        Args:
            lexer: Lexer to use for the new widget
            
        Returns:
            New CodeView widget with lexer applied
        """
        if not self.has_widget():
            # No current widget, create new one
            new_widget = self.create_widget(lexer=lexer)
            self.configure_scrollbar(new_widget)
            self.grid_widget(new_widget)
            self.current_widget = new_widget
            return new_widget
            
        # Enhanced replacement with container relationship maintenance
        return self.replace_widget_with_enhanced_container_relationships(self.current_widget, lexer)
        
    def setup_initial_widget(self, **grid_options):
        """
        Set up initial widget without syntax highlighting.
        
        Args:
            **grid_options: Grid layout options
            
        Returns:
            Created and configured widget
        """
        # Create basic widget without lexer
        widget = self.create_widget()
        
        # Configure scrollbar
        self.configure_scrollbar(widget)
        
        # Configure grid layout
        if grid_options:
            self.grid_widget(widget, **grid_options)
        else:
            self.grid_widget(widget)
            
        # Set as current widget
        self.current_widget = widget
        
        return widget
        
    def update_file_content(self, content, filename=None):
        """
        Update widget content with optional syntax highlighting.
        
        Args:
            content: Text content to display
            filename: Optional filename for syntax highlighting
            
        Returns:
            Widget containing the updated content
        """
        # Create widget if none exists
        if not self.has_widget():
            self.current_widget = self.create_widget()
            self.configure_scrollbar(self.current_widget)
            self.grid_widget(self.current_widget)
            
        # Determine if we need syntax highlighting
        if filename:
            lexer = self.get_lexer_for_file(filename)
            if lexer:
                # Replace widget with syntax highlighting
                widget = self.replace_widget_with_lexer(lexer)
            else:
                # No lexer found, update content directly
                widget = self.current_widget
                self._update_widget_content_directly(widget, content)
        else:
            # No filename provided, update content directly
            widget = self.current_widget
            self._update_widget_content_directly(widget, content)
            
        return widget
        
    def _update_widget_content_directly(self, widget, content):
        """Update widget content without changing lexer."""
        # Enable widget for editing
        widget.config(state='normal')
            
        # Update content
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        
        # Set to disabled (read-only) for file viewing
        widget.config(state='disabled')
        
    def set_readonly_state(self, readonly=True):
        """Set widget to read-only or editable state."""
        if self.has_widget():
            state = 'disabled' if readonly else 'normal'
            self.current_widget.config(state=state)
            
    def get_content(self):
        """Get current content from widget."""
        if self.has_widget():
            return self.current_widget.get("1.0", "end-1c")
        return ""
        
    def clear_content(self):
        """Clear widget content."""
        if self.has_widget():
            widget = self.current_widget
            # Enable widget for editing
            widget.config(state='normal')
                
            # Clear content
            widget.delete("1.0", tk.END)
            
            # Set to disabled (read-only)
            widget.config(state='disabled') 