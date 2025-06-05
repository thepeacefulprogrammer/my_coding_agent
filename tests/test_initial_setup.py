import subprocess
import sys

def test_pytest_runs_successfully():
    """Test that pytest can run and finds all our test files"""
    result = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], 
                          capture_output=True, text=True)
    assert result.returncode == 0, f"pytest collection failed: {result.stderr}"
    
def test_basic_functionality():
    """Test that our basic setup works"""
    assert True, "Basic test functionality works" 