# Unit tests for file_explorer.py

# TODO: Add tests for FileExplorer class once implemented
# - test_scan_directory
# - test_create_directory  
# - test_refresh

import os
import tempfile
from unittest.mock import patch, MagicMock

def test_file_explorer_class_exists():
    """Test that FileExplorer class can be imported"""
    from src.file_explorer import FileExplorer
    
    # Should be able to instantiate the class
    explorer = FileExplorer()
    assert explorer is not None, "Expected FileExplorer class to be instantiable"

def test_file_explorer_has_scan_directory_method():
    """Test that FileExplorer class has scan_directory method"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    assert hasattr(explorer, 'scan_directory'), "Expected FileExplorer to have scan_directory method"
    assert callable(explorer.scan_directory), "Expected scan_directory to be callable"

def test_file_explorer_has_create_directory_method():
    """Test that FileExplorer class has create_directory method"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    assert hasattr(explorer, 'create_directory'), "Expected FileExplorer to have create_directory method"
    assert callable(explorer.create_directory), "Expected create_directory to be callable"

def test_file_explorer_has_refresh_method():
    """Test that FileExplorer class has refresh method"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    assert hasattr(explorer, 'refresh'), "Expected FileExplorer to have refresh method"
    assert callable(explorer.refresh), "Expected refresh to be callable"

# Tests using tmp_path fixtures for scan_directory

def test_scan_directory_empty_directory(tmp_path):
    """Test scan_directory with an empty directory using tmp_path"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Scan empty directory
    result = explorer.scan_directory(str(tmp_path))
    
    # Should return empty lists
    assert result is not None, "Expected scan_directory to return a result"
    assert isinstance(result, dict), "Expected scan_directory to return a dictionary"
    assert 'files' in result, "Expected result to contain 'files' key"
    assert 'directories' in result, "Expected result to contain 'directories' key"
    assert result['files'] == [], "Expected empty files list for empty directory"
    assert result['directories'] == [], "Expected empty directories list for empty directory"

def test_scan_directory_with_files_only(tmp_path):
    """Test scan_directory with directory containing only files using tmp_path"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Create test files
    file1 = tmp_path / "document.txt"
    file2 = tmp_path / "script.py"
    file3 = tmp_path / "data.json"
    
    file1.write_text("Hello World")
    file2.write_text("print('Python')")
    file3.write_text('{"key": "value"}')
    
    # Scan directory
    result = explorer.scan_directory(str(tmp_path))
    
    # Should find all files
    assert len(result['files']) == 3, "Expected to find 3 files"
    assert len(result['directories']) == 0, "Expected to find 0 directories"
    
    # Check file names
    file_names = [os.path.basename(f) for f in result['files']]
    assert "document.txt" in file_names, "Expected to find document.txt"
    assert "script.py" in file_names, "Expected to find script.py"
    assert "data.json" in file_names, "Expected to find data.json"

def test_scan_directory_with_directories_only(tmp_path):
    """Test scan_directory with directory containing only subdirectories using tmp_path"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Create test directories
    dir1 = tmp_path / "folder1"
    dir2 = tmp_path / "folder2"
    dir3 = tmp_path / "nested"
    
    dir1.mkdir()
    dir2.mkdir()
    dir3.mkdir()
    
    # Scan directory
    result = explorer.scan_directory(str(tmp_path))
    
    # Should find all directories
    assert len(result['files']) == 0, "Expected to find 0 files"
    assert len(result['directories']) == 3, "Expected to find 3 directories"
    
    # Check directory names
    dir_names = [os.path.basename(d) for d in result['directories']]
    assert "folder1" in dir_names, "Expected to find folder1"
    assert "folder2" in dir_names, "Expected to find folder2"
    assert "nested" in dir_names, "Expected to find nested"

def test_scan_directory_mixed_content(tmp_path):
    """Test scan_directory with mixed files and directories using tmp_path"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Create mixed content
    file1 = tmp_path / "readme.md"
    file2 = tmp_path / "config.ini"
    dir1 = tmp_path / "src"
    dir2 = tmp_path / "tests"
    
    file1.write_text("# Project Readme")
    file2.write_text("[section]\nkey=value")
    dir1.mkdir()
    dir2.mkdir()
    
    # Add nested content
    nested_file = dir1 / "main.py"
    nested_file.write_text("# Main module")
    
    # Scan top-level directory
    result = explorer.scan_directory(str(tmp_path))
    
    # Should find files and directories (but not nested content)
    assert len(result['files']) == 2, "Expected to find 2 files"
    assert len(result['directories']) == 2, "Expected to find 2 directories"
    
    # Check content
    file_names = [os.path.basename(f) for f in result['files']]
    dir_names = [os.path.basename(d) for d in result['directories']]
    
    assert "readme.md" in file_names, "Expected to find readme.md"
    assert "config.ini" in file_names, "Expected to find config.ini"
    assert "src" in dir_names, "Expected to find src directory"
    assert "tests" in dir_names, "Expected to find tests directory"
    
    # Should not include nested files
    assert "main.py" not in file_names, "Expected not to find nested files"

def test_scan_directory_hidden_files_excluded(tmp_path):
    """Test that scan_directory excludes hidden files using tmp_path"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Create visible and hidden files
    visible_file = tmp_path / "visible.txt"
    hidden_file = tmp_path / ".hidden"
    hidden_dir = tmp_path / ".git"
    
    visible_file.write_text("visible content")
    hidden_file.write_text("hidden content")
    hidden_dir.mkdir()
    
    # Scan directory
    result = explorer.scan_directory(str(tmp_path))
    
    # Should only find visible content
    assert len(result['files']) == 1, "Expected to find 1 visible file"
    assert len(result['directories']) == 0, "Expected to find 0 visible directories"
    
    file_names = [os.path.basename(f) for f in result['files']]
    assert "visible.txt" in file_names, "Expected to find visible file"
    assert ".hidden" not in file_names, "Expected to exclude hidden files"

def test_scan_directory_updates_current_directory(tmp_path):
    """Test that scan_directory updates current_directory attribute using tmp_path"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Initially no current directory
    assert explorer.current_directory is None, "Expected initial current_directory to be None"
    
    # Scan directory
    result = explorer.scan_directory(str(tmp_path))
    
    # Should update current_directory
    assert explorer.current_directory == str(tmp_path), "Expected current_directory to be updated"
    assert result is not None, "Expected scan to succeed"

def test_scan_directory_file_extensions(tmp_path):
    """Test scan_directory correctly identifies various file extensions using tmp_path"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Create files with various extensions
    extensions = ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md']
    for i, ext in enumerate(extensions):
        file_path = tmp_path / f"file{i}{ext}"
        file_path.write_text(f"content for {ext} file")
    
    # Scan directory
    result = explorer.scan_directory(str(tmp_path))
    
    # Should find all files
    assert len(result['files']) == len(extensions), f"Expected to find {len(extensions)} files"
    assert len(result['directories']) == 0, "Expected to find 0 directories"
    
    # Check all extensions are represented
    found_extensions = set()
    for file_path in result['files']:
        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(filename)
        found_extensions.add(ext)
    
    assert found_extensions == set(extensions), "Expected all file extensions to be found"

def test_scan_directory_special_characters(tmp_path):
    """Test scan_directory handles files/dirs with special characters using tmp_path"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Create files and directories with special characters
    special_file = tmp_path / "file with spaces.txt"
    hyphen_file = tmp_path / "file-with-hyphens.log"
    underscore_dir = tmp_path / "dir_with_underscores"
    number_dir = tmp_path / "123numbers"
    
    special_file.write_text("content")
    hyphen_file.write_text("log content")
    underscore_dir.mkdir()
    number_dir.mkdir()
    
    # Scan directory
    result = explorer.scan_directory(str(tmp_path))
    
    # Should find all items
    assert len(result['files']) == 2, "Expected to find 2 files"
    assert len(result['directories']) == 2, "Expected to find 2 directories"
    
    # Check names
    file_names = [os.path.basename(f) for f in result['files']]
    dir_names = [os.path.basename(d) for d in result['directories']]
    
    assert "file with spaces.txt" in file_names, "Expected to find file with spaces"
    assert "file-with-hyphens.log" in file_names, "Expected to find file with hyphens"
    assert "dir_with_underscores" in dir_names, "Expected to find dir with underscores"
    assert "123numbers" in dir_names, "Expected to find dir starting with numbers"

def test_refresh_requires_initial_scan():
    """Test that refresh requires an initial scan_directory call"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Calling refresh without prior scan should return None or handle gracefully
    result = explorer.refresh()
    assert result is None, "Expected refresh to return None when no directory has been scanned"

def test_refresh_rescans_current_directory():
    """Test that refresh re-scans the current directory"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initial scan
        initial_result = explorer.scan_directory(temp_dir)
        
        # Create a new file after the initial scan
        new_file = os.path.join(temp_dir, "new_file.txt")
        with open(new_file, 'w') as f:
            f.write("new content")
        
        # Refresh should detect the new file
        refresh_result = explorer.refresh()
        
        # Should return updated directory contents
        assert refresh_result is not None, "Expected refresh to return updated directory contents"
        assert isinstance(refresh_result, dict), "Expected refresh to return a dictionary"
        assert 'files' in refresh_result, "Expected refresh result to contain 'files' key"
        assert 'directories' in refresh_result, "Expected refresh result to contain 'directories' key"
        
        # Should find the new file
        file_names = [os.path.basename(f) for f in refresh_result['files']]
        assert "new_file.txt" in file_names, "Expected refresh to detect newly created file"

def test_refresh_maintains_current_directory():
    """Test that refresh maintains the current directory state"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Scan directory
        explorer.scan_directory(temp_dir)
        
        # Should have current_directory attribute set
        assert hasattr(explorer, 'current_directory'), "Expected explorer to have current_directory attribute"
        assert explorer.current_directory == temp_dir, "Expected current_directory to be set to scanned directory"
        
        # Refresh should maintain the same directory
        explorer.refresh()
        assert explorer.current_directory == temp_dir, "Expected refresh to maintain current_directory"

def test_refresh_with_directory_changes():
    """Test refresh detects various directory changes"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create initial structure
        initial_file = os.path.join(temp_dir, "initial.txt")
        with open(initial_file, 'w') as f:
            f.write("initial")
        
        # Initial scan
        initial_result = explorer.scan_directory(temp_dir)
        initial_files = [os.path.basename(f) for f in initial_result['files']]
        
        # Make changes: add file, add directory, remove file
        new_file = os.path.join(temp_dir, "added.txt")
        new_dir = os.path.join(temp_dir, "new_subdir")
        
        with open(new_file, 'w') as f:
            f.write("added")
        os.mkdir(new_dir)
        os.remove(initial_file)
        
        # Refresh should detect all changes
        refresh_result = explorer.refresh()
        
        refreshed_files = [os.path.basename(f) for f in refresh_result['files']]
        refreshed_dirs = [os.path.basename(d) for d in refresh_result['directories']]
        
        # Should find new file but not old file
        assert "added.txt" in refreshed_files, "Expected refresh to detect new file"
        assert "initial.txt" not in refreshed_files, "Expected refresh to detect removed file"
        
        # Should find new directory
        assert "new_subdir" in refreshed_dirs, "Expected refresh to detect new directory"

def test_refresh_handles_permission_errors():
    """Test that refresh handles permission errors gracefully"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initial scan
        explorer.scan_directory(temp_dir)
        
        # Mock os.listdir to raise PermissionError on refresh
        with patch('src.file_explorer.os.listdir', side_effect=PermissionError("Permission denied")):
            result = explorer.refresh()
            
            # Should handle the error gracefully
            assert result is None, "Expected refresh to handle permission errors gracefully"

def test_refresh_updates_explorer_state():
    """Test that refresh updates the explorer's internal state"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initial scan
        initial_result = explorer.scan_directory(temp_dir)
        
        # Mock scan_directory to verify it's called by refresh
        with patch.object(explorer, 'scan_directory', return_value={'files': ['test'], 'directories': []}) as mock_scan:
            result = explorer.refresh()
            
            # Should call scan_directory with current directory
            mock_scan.assert_called_once_with(explorer.current_directory)
            
            # Should return the result from scan_directory
            assert result == {'files': ['test'], 'directories': []}, "Expected refresh to return scan_directory result"

def test_create_directory_with_valid_inputs():
    """Test create_directory with valid parent path and new name"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        new_folder_name = "test_new_folder"
        
        # Create the directory
        result = explorer.create_directory(temp_dir, new_folder_name)
        
        # Should return the full path of created directory
        expected_path = os.path.join(temp_dir, new_folder_name)
        assert result == expected_path, f"Expected create_directory to return {expected_path}"
        
        # Directory should actually exist
        assert os.path.exists(expected_path), "Expected directory to be created on filesystem"
        assert os.path.isdir(expected_path), "Expected created path to be a directory"

def test_create_directory_with_invalid_parent():
    """Test create_directory with non-existent parent directory"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Try to create directory in non-existent parent
    result = explorer.create_directory("/non/existent/path", "new_folder")
    
    # Should handle error gracefully and return None
    assert result is None, "Expected create_directory to return None for invalid parent path"

def test_create_directory_with_empty_name():
    """Test create_directory with empty or invalid folder name"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with empty string
        result = explorer.create_directory(temp_dir, "")
        assert result is None, "Expected create_directory to return None for empty name"
        
        # Test with whitespace-only string
        result = explorer.create_directory(temp_dir, "   ")
        assert result is None, "Expected create_directory to return None for whitespace-only name"
        
        # Test with None
        result = explorer.create_directory(temp_dir, None)
        assert result is None, "Expected create_directory to return None for None name"

def test_create_directory_with_existing_folder():
    """Test create_directory when folder already exists"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        existing_folder = "existing_folder"
        existing_path = os.path.join(temp_dir, existing_folder)
        
        # Create the folder first
        os.mkdir(existing_path)
        
        # Try to create it again
        result = explorer.create_directory(temp_dir, existing_folder)
        
        # Should handle gracefully and return None
        assert result is None, "Expected create_directory to return None when folder already exists"

def test_create_directory_with_permission_error():
    """Test create_directory handles permission errors gracefully"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Mock os.mkdir to raise PermissionError
    with patch('src.file_explorer.os.mkdir', side_effect=PermissionError("Permission denied")):
        result = explorer.create_directory("/some/path", "new_folder")
        
        # Should handle the error gracefully
        assert result is None, "Expected create_directory to handle permission errors gracefully"

def test_create_directory_validates_and_cleans_name():
    """Test that create_directory cleans and validates folder names"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with name that has leading/trailing whitespace
        folder_name = "  clean_folder  "
        
        result = explorer.create_directory(temp_dir, folder_name)
        
        # Should create with cleaned name
        expected_path = os.path.join(temp_dir, "clean_folder")
        assert result == expected_path, "Expected create_directory to clean folder name"
        assert os.path.exists(expected_path), "Expected directory to be created with cleaned name"

def test_scan_directory_with_valid_path():
    """Test scan_directory with a valid directory path"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Create a temporary directory with some files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files and directories
        test_file1 = os.path.join(temp_dir, "test1.txt")
        test_file2 = os.path.join(temp_dir, "test2.py")
        test_dir = os.path.join(temp_dir, "subdir")
        
        with open(test_file1, 'w') as f:
            f.write("test content")
        with open(test_file2, 'w') as f:
            f.write("print('hello')")
        os.mkdir(test_dir)
        
        # Scan the directory
        result = explorer.scan_directory(temp_dir)
        
        # Should return a data structure containing the files and directories
        assert result is not None, "Expected scan_directory to return a result"
        assert isinstance(result, dict), "Expected scan_directory to return a dictionary"
        
        # Should contain information about files and directories
        assert 'files' in result, "Expected result to contain 'files' key"
        assert 'directories' in result, "Expected result to contain 'directories' key"
        
        # Check that files are detected
        assert len(result['files']) >= 2, "Expected to find at least 2 files"
        file_names = [os.path.basename(f) for f in result['files']]
        assert "test1.txt" in file_names, "Expected to find test1.txt"
        assert "test2.py" in file_names, "Expected to find test2.py"
        
        # Check that directories are detected
        assert len(result['directories']) >= 1, "Expected to find at least 1 directory"
        dir_names = [os.path.basename(d) for d in result['directories']]
        assert "subdir" in dir_names, "Expected to find subdir"

def test_scan_directory_with_invalid_path():
    """Test scan_directory with an invalid/non-existent path"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Test with non-existent path
    result = explorer.scan_directory("/non/existent/path")
    
    # Should handle error gracefully and return None or empty result
    assert result is None or result == {'files': [], 'directories': []}, \
        "Expected scan_directory to handle invalid paths gracefully"

def test_scan_directory_with_permission_error():
    """Test scan_directory handles permission errors gracefully"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    # Mock os.listdir to raise PermissionError
    with patch('src.file_explorer.os.listdir', side_effect=PermissionError("Permission denied")):
        result = explorer.scan_directory("/some/path")
        
        # Should handle the error gracefully
        assert result is None or result == {'files': [], 'directories': []}, \
            "Expected scan_directory to handle permission errors gracefully"

def test_scan_directory_returns_full_paths():
    """Test that scan_directory returns full paths for files and directories"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_file = os.path.join(temp_dir, "test.txt")
        test_dir = os.path.join(temp_dir, "subdir")
        
        with open(test_file, 'w') as f:
            f.write("test")
        os.mkdir(test_dir)
        
        result = explorer.scan_directory(temp_dir)
        
        # Files should be full paths
        assert all(os.path.isabs(f) for f in result['files']), \
            "Expected all file paths to be absolute"
        
        # Directories should be full paths
        assert all(os.path.isabs(d) for d in result['directories']), \
            "Expected all directory paths to be absolute"
        
        # Paths should start with the scanned directory
        assert all(f.startswith(temp_dir) for f in result['files']), \
            "Expected all file paths to be under the scanned directory"
        assert all(d.startswith(temp_dir) for d in result['directories']), \
            "Expected all directory paths to be under the scanned directory"

def test_scan_directory_excludes_hidden_files():
    """Test that scan_directory excludes hidden files by default"""
    from src.file_explorer import FileExplorer
    
    explorer = FileExplorer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create visible and hidden files
        visible_file = os.path.join(temp_dir, "visible.txt")
        hidden_file = os.path.join(temp_dir, ".hidden.txt")
        
        with open(visible_file, 'w') as f:
            f.write("visible")
        with open(hidden_file, 'w') as f:
            f.write("hidden")
        
        result = explorer.scan_directory(temp_dir)
        
        # Should find visible file but not hidden file
        file_names = [os.path.basename(f) for f in result['files']]
        assert "visible.txt" in file_names, "Expected to find visible file"
        assert ".hidden.txt" not in file_names, "Expected to exclude hidden files"

def test_placeholder():
    """Placeholder test to ensure file exists and pytest runs"""
    assert True 