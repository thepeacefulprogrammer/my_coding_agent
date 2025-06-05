import os
import configparser

def test_pytest_ini_exists():
    assert os.path.isfile("pytest.ini"), "Expected 'pytest.ini' file to exist"

def test_pytest_ini_has_testpaths():
    config = configparser.ConfigParser()
    config.read("pytest.ini")
    assert "tool:pytest" in config, "Expected [tool:pytest] section in pytest.ini"
    assert "testpaths" in config["tool:pytest"], "Expected 'testpaths' in pytest configuration" 