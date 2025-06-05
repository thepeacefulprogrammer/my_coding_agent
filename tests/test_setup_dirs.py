import os

def test_src_directory_exists():
    assert os.path.isdir("src"), "Expected 'src' directory to exist"

def test_tests_directory_exists():
    assert os.path.isdir("tests"), "Expected 'tests' directory to exist" 