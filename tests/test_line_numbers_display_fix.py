import unittest
from unittest.mock import Mock, patch, MagicMock, call
import tkinter as tk
from src.code_editor import CodeEditor
from src.syntax_manager import SyntaxManager


class TestLineNumbersDisplayFix(unittest.TestCase):
    """Test that line numbers display properly after content insertion."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.parent_frame = tk.Frame(self.root)
        self.syntax_manager = SyntaxManager()
        self.scrollbar = tk.Scrollbar(self.root)
    
    def tearDown(self):
        """Clean up test environment."""
        try:
            if hasattr(self, 'root') and self.root:
                self.root.destroy()
        except Exception:
            pass
    
    @patch('src.code_editor.CodeView')
    def test_line_numbers_refreshed_after_content_insertion(self, mock_codeview):
        """Test that line numbers are refreshed after content is inserted."""
        # Create mock widget with line numbers
        mock_widget = Mock()
        mock_line_numbers = Mock()
        mock_widget._line_numbers = mock_line_numbers
        mock_widget.highlight_all = Mock()
        mock_widget.after_idle = Mock()
        mock_widget.after = Mock()
        mock_widget.winfo_exists = Mock(return_value=True)
        mock_line_numbers.winfo_exists = Mock(return_value=True)
        mock_codeview.return_value = mock_widget
        
        # Create CodeEditor with line numbers enabled
        editor = CodeEditor(
            self.parent_frame,
            self.syntax_manager,
            scrollbar=self.scrollbar,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Set the mock widget as current
        editor.current_widget = mock_widget
        
        # Update content directly
        content = "line 1\nline 2\nline 3\nline 4\nline 5"
        editor._update_widget_content_directly(mock_widget, content)
        
        # Verify that scheduling was called to schedule the refresh
        self.assertTrue(mock_widget.after.called or mock_widget.after_idle.called, 
                       "Refresh scheduling should be called")
        
        # Execute the scheduled refresh function manually to verify it works
        refresh_func = None
        if mock_widget.after.call_args:
            refresh_func = mock_widget.after.call_args[0][1]  # after() has delay as first arg
        elif mock_widget.after_idle.call_args:
            refresh_func = mock_widget.after_idle.call_args[0][0]
            
        if refresh_func:
            refresh_func()  # Execute the scheduled function
            
            # Now verify that the refresh methods were called
            mock_widget.highlight_all.assert_called()
            # Line numbers redraw should be scheduled 
            total_scheduling_calls = mock_widget.after_idle.call_count + mock_widget.after.call_count
            self.assertTrue(total_scheduling_calls >= 1,
                           "Refresh scheduling should be called at least once")
        
        # Verify content was inserted
        mock_widget.delete.assert_called_with("1.0", tk.END)
        mock_widget.insert.assert_called_with("1.0", content)
    
    @patch('src.code_editor.CodeView')
    def test_line_numbers_refresh_handles_errors_gracefully(self, mock_codeview):
        """Test that line numbers refresh errors don't break content insertion."""
        # Create mock widget with failing refresh methods
        mock_widget = Mock()
        mock_line_numbers = Mock()
        mock_line_numbers.redraw = Mock(side_effect=Exception("Redraw failed"))
        mock_widget._line_numbers = mock_line_numbers
        mock_widget.highlight_all = Mock(side_effect=Exception("Highlight failed"))
        mock_widget.after_idle = Mock()
        mock_widget.after = Mock()
        mock_widget.winfo_exists = Mock(return_value=True)
        mock_line_numbers.winfo_exists = Mock(return_value=True)
        mock_codeview.return_value = mock_widget
        
        # Create CodeEditor
        editor = CodeEditor(
            self.parent_frame,
            self.syntax_manager,
            show_line_numbers=True
        )
        
        # Set the mock widget as current
        editor.current_widget = mock_widget
        
        # Update content - should not raise an exception despite refresh failures
        content = "line 1\nline 2\nline 3"
        try:
            editor._update_widget_content_directly(mock_widget, content)
            test_passed = True
        except Exception:
            test_passed = False
        
        # Verify that content insertion still worked despite refresh failures
        self.assertTrue(test_passed, "Content insertion should work even if refresh fails")
        mock_widget.delete.assert_called_with("1.0", tk.END)
        mock_widget.insert.assert_called_with("1.0", content)
        
        # Verify that scheduling was attempted
        self.assertTrue(mock_widget.after.called or mock_widget.after_idle.called, 
                       "Refresh scheduling should be attempted even with failing methods")
    
    @patch('src.code_editor.CodeView')
    def test_file_content_update_triggers_line_numbers_refresh(self, mock_codeview):
        """Test that update_file_content triggers line numbers refresh."""
        # Create mock widget with line numbers
        mock_widget = Mock()
        mock_line_numbers = Mock()
        mock_widget._line_numbers = mock_line_numbers
        mock_widget.highlight_all = Mock()
        mock_widget.after_idle = Mock()
        mock_widget.after = Mock()
        mock_widget.bind = Mock()
        mock_widget.winfo_exists = Mock(return_value=True)
        mock_line_numbers.winfo_exists = Mock(return_value=True)
        mock_codeview.return_value = mock_widget
        
        # Create CodeEditor with line numbers enabled
        editor = CodeEditor(
            self.parent_frame,
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Update file content (this should trigger refresh)
        python_content = "def hello():\n    print('Hello, World!')\n    return 42"
        widget = editor.update_file_content(python_content, filename="test.py")
        
        # Verify that widget was created with line numbers
        self.assertIsNotNone(widget)
        call_kwargs = mock_codeview.call_args[1]
        self.assertEqual(call_kwargs['linenums_border'], 1)
        
        # Verify that <<Modified>> event binding was set up (check all calls)
        bind_calls = mock_widget.bind.call_args_list
        
        # Should have called bind for <<Modified>> and scroll events
        event_names = [call[0][0] for call in bind_calls]
        self.assertIn("<<Modified>>", event_names, "<<Modified>> event should be bound")
        
        # Should also have scroll events bound
        expected_scroll_events = ['<MouseWheel>', '<Button-4>', '<Button-5>', '<Key-Up>', '<Key-Down>']
        for event in expected_scroll_events:
            self.assertIn(event, event_names, f"Scroll event {event} should be bound")
        
        # All bindings should use add=True
        for call in bind_calls:
            self.assertTrue(call[1]['add'], "All event bindings should use add=True")
        
        # Verify that refresh scheduling was called during content update
        self.assertTrue(mock_widget.after.called or mock_widget.after_idle.called, 
                       "Line numbers refresh should be scheduled")
    
    @patch('src.code_editor.CodeView')
    def test_widget_without_line_numbers_attribute_handled_gracefully(self, mock_codeview):
        """Test that widgets without _line_numbers attribute are handled gracefully."""
        # Create mock widget without line numbers attribute
        mock_widget = Mock()
        # Don't set _line_numbers attribute
        mock_widget.highlight_all = Mock()
        mock_widget.after_idle = Mock()
        mock_widget.after = Mock()
        mock_widget.winfo_exists = Mock(return_value=True)
        mock_codeview.return_value = mock_widget
        
        # Create CodeEditor
        editor = CodeEditor(
            self.parent_frame,
            self.syntax_manager,
            show_line_numbers=False  # Line numbers disabled
        )
        
        # Set the mock widget as current
        editor.current_widget = mock_widget
        
        # Update content - should work even without line numbers
        content = "some content"
        editor._update_widget_content_directly(mock_widget, content)
        
        # Verify that refresh scheduling was attempted (for syntax highlighting)
        self.assertTrue(mock_widget.after.called or mock_widget.after_idle.called, 
                       "Refresh scheduling should happen even without line numbers")
        
        # Execute the scheduled refresh to verify it works without line numbers
        if mock_widget.after_idle.call_args:
            refresh_func = mock_widget.after_idle.call_args[0][0]
            refresh_func()  # Should not raise exception even without _line_numbers
        
        # Verify content was inserted
        mock_widget.delete.assert_called_with("1.0", tk.END)
        mock_widget.insert.assert_called_with("1.0", content)


if __name__ == '__main__':
    unittest.main() 