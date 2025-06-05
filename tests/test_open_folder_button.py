from unittest.mock import patch, MagicMock
import sys

def test_gui_module_can_be_imported():
    """Test that the GUI module can be imported"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock()}):
        try:
            from src.gui import GUI
            assert True, "GUI module imported successfully"
        except ImportError as e:
            assert False, f"GUI module not found - needs to be implemented: {e}"

def test_open_folder_handler_exists():
    """Test that the GUI class has an open_folder_handler method"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock()}):
        try:
            from src.gui import GUI
            assert hasattr(GUI, 'open_folder_handler'), "Expected GUI to have open_folder_handler method"
            assert callable(GUI.open_folder_handler), "Expected open_folder_handler to be callable"
        except ImportError as e:
            assert False, f"GUI module not found - needs to be implemented: {e}" 