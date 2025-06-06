import os

class FileExplorer:
    """File explorer class for scanning directories and managing file listings"""
    
    def __init__(self):
        """Initialize the FileExplorer"""
        self.current_directory = None  # Track the currently scanned directory
    
    def scan_directory(self, path):
        """
        Scan a directory and return information about files and subdirectories
        
        Args:
            path (str): Directory path to scan
            
        Returns:
            dict: Dictionary with 'files' and 'directories' keys containing lists of paths,
                  or None if the directory cannot be accessed
        """
        try:
            # Check if path exists and is a directory
            if not os.path.exists(path) or not os.path.isdir(path):
                return None
            
            # Get directory contents
            entries = os.listdir(path)
            
            files = []
            directories = []
            
            for entry in entries:
                # Skip hidden files (those starting with .)
                if entry.startswith('.'):
                    continue
                
                full_path = os.path.join(path, entry)
                
                if os.path.isfile(full_path):
                    files.append(full_path)
                elif os.path.isdir(full_path):
                    directories.append(full_path)
            
            # Update current directory on successful scan
            self.current_directory = path
            
            return {
                'files': files,
                'directories': directories
            }
            
        except (OSError, PermissionError):
            # Handle permission errors and other OS errors gracefully
            return None
    
    def create_directory(self, parent_path, new_name):
        """
        Create a new directory in the specified parent path
        
        Args:
            parent_path (str): Path to the parent directory
            new_name (str): Name of the new directory to create
            
        Returns:
            str: Full path of the created directory, or None if creation failed
        """
        try:
            # Validate inputs
            if not new_name or not isinstance(new_name, str):
                return None
            
            # Clean the folder name (strip whitespace)
            cleaned_name = new_name.strip()
            if not cleaned_name:
                return None
            
            # Check if parent path exists and is a directory
            if not os.path.exists(parent_path) or not os.path.isdir(parent_path):
                return None
            
            # Create the full path for the new directory
            new_directory_path = os.path.join(parent_path, cleaned_name)
            
            # Check if directory already exists
            if os.path.exists(new_directory_path):
                return None
            
            # Create the directory
            os.mkdir(new_directory_path)
            
            return new_directory_path
            
        except (OSError, PermissionError):
            # Handle permission errors and other OS errors gracefully
            return None
    
    def refresh(self):
        """
        Re-scan the current directory to detect any changes
        
        Returns:
            dict: Updated directory contents, or None if no directory has been scanned
                  or if refresh failed
        """
        if self.current_directory is None:
            return None
        
        # Re-scan the current directory
        return self.scan_directory(self.current_directory)
    
    def read_file(self, path):
        """
        Read the contents of a file
        
        Args:
            path (str): Path to the file to read
            
        Returns:
            str: File contents as a string, or None if the file cannot be read
        """
        try:
            # Check if path exists and is a file
            if not os.path.exists(path) or not os.path.isfile(path):
                return None
            
            # Try to read the file with UTF-8 encoding first
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    return file.read()
            except UnicodeDecodeError:
                # If UTF-8 fails, try with default encoding and error handling
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as file:
                        return file.read()
                except UnicodeDecodeError:
                    # If it's truly binary, return None
                    return None
                    
        except (OSError, PermissionError, IOError):
            # Handle file access errors gracefully
            return None 