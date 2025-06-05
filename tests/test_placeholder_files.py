import os

def test_file_explorer_test_exists():
    assert os.path.isfile("tests/test_file_explorer.py"), "Expected 'tests/test_file_explorer.py' to exist"

def test_gui_test_exists():
    assert os.path.isfile("tests/test_gui.py"), "Expected 'tests/test_gui.py' to exist" 