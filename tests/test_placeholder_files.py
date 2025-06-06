import os

def test_file_explorer_test_exists():
    assert os.path.isfile("tests/test_file_explorer.py"), "Expected 'tests/test_file_explorer.py' to exist" 