import os
import json
import shutil
import stat
import glob
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP

# Helper function to safely resolve paths
def safe_path(path: str, base_path: str = None) -> Path:
    """Safely resolve a path, preventing directory traversal attacks"""
    if base_path:
        base = Path(base_path).resolve()
        target = (base / path).resolve()
        # Ensure the target path is within the base path
        if not str(target).startswith(str(base)):
            raise ValueError(f"Path {path} is outside the allowed directory")
        return target
    else:
        return Path(path).resolve()

def _format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def register_file_system_tools(mcp: FastMCP):
    """Register all file system related tools"""
    
    @mcp.tool
    def read_file(file_path: str, encoding: str = "utf-8") -> str:
        """
        Read the contents of a file.
        
        Args:
            file_path: Path to the file to read
            encoding: Text encoding to use (default: utf-8)
        
        Returns:
            The contents of the file as a string
        """
        try:
            path = safe_path(file_path)
            if not path.exists():
                return f"Error: File '{file_path}' does not exist"
            if not path.is_file():
                return f"Error: '{file_path}' is not a file"
            
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @mcp.tool
    def write_file(file_path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True) -> str:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write to the file
            encoding: Text encoding to use (default: utf-8)
            create_dirs: Whether to create parent directories if they don't exist
        
        Returns:
            Success message or error description
        """
        try:
            path = safe_path(file_path)
            
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return f"Successfully wrote {len(content)} characters to '{file_path}'"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    @mcp.tool
    def delete_file(file_path: str) -> str:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file to delete
        
        Returns:
            Success message or error description
        """
        try:
            path = safe_path(file_path)
            if not path.exists():
                return f"Error: File '{file_path}' does not exist"
            if not path.is_file():
                return f"Error: '{file_path}' is not a file"
            
            path.unlink()
            return f"Successfully deleted file '{file_path}'"
        except Exception as e:
            return f"Error deleting file: {str(e)}"

    @mcp.tool
    def list_directory(dir_path: str = ".", include_hidden: bool = False, detailed: bool = False) -> str:
        """
        List the contents of a directory.
        
        Args:
            dir_path: Path to the directory to list (default: current directory)
            include_hidden: Whether to include hidden files/directories
            detailed: Whether to include detailed information (size, permissions, etc.)
        
        Returns:
            Directory listing as formatted text
        """
        try:
            path = safe_path(dir_path)
            if not path.exists():
                return f"Error: Directory '{dir_path}' does not exist"
            if not path.is_dir():
                return f"Error: '{dir_path}' is not a directory"
            
            items = []
            for item in path.iterdir():
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                if detailed:
                    stat_info = item.stat()
                    size = stat_info.st_size
                    modified = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    is_dir = "DIR" if item.is_dir() else "FILE"
                    permissions = oct(stat.S_IMODE(stat_info.st_mode))
                    items.append(f"{is_dir:4} {size:>10} {permissions:>6} {modified} {item.name}")
                else:
                    items.append(f"{'[DIR]' if item.is_dir() else '[FILE]'} {item.name}")
            
            if not items:
                return f"Directory '{dir_path}' is empty"
            
            header = "TYPE       SIZE  PERMS       MODIFIED           NAME" if detailed else "CONTENTS"
            return f"Directory listing for '{dir_path}':\n{header}\n" + "\n".join(sorted(items))
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    @mcp.tool
    def create_directory(dir_path: str, parents: bool = True) -> str:
        """
        Create a directory.
        
        Args:
            dir_path: Path to the directory to create
            parents: Whether to create parent directories if they don't exist
        
        Returns:
            Success message or error description
        """
        try:
            path = safe_path(dir_path)
            if path.exists():
                return f"Error: Directory '{dir_path}' already exists"
            
            path.mkdir(parents=parents, exist_ok=False)
            return f"Successfully created directory '{dir_path}'"
        except Exception as e:
            return f"Error creating directory: {str(e)}"

    @mcp.tool
    def delete_directory(dir_path: str, recursive: bool = False) -> str:
        """
        Delete a directory.
        
        Args:
            dir_path: Path to the directory to delete
            recursive: Whether to delete the directory and all its contents
        
        Returns:
            Success message or error description
        """
        try:
            path = safe_path(dir_path)
            if not path.exists():
                return f"Error: Directory '{dir_path}' does not exist"
            if not path.is_dir():
                return f"Error: '{dir_path}' is not a directory"
            
            if recursive:
                shutil.rmtree(path)
                return f"Successfully deleted directory '{dir_path}' and all its contents"
            else:
                path.rmdir()  # Only works on empty directories
                return f"Successfully deleted empty directory '{dir_path}'"
        except Exception as e:
            return f"Error deleting directory: {str(e)}"

    @mcp.tool
    def search_files(pattern: str, directory: str = ".", recursive: bool = True, case_sensitive: bool = False) -> str:
        """
        Search for files matching a pattern.
        
        Args:
            pattern: Glob pattern to search for (e.g., "*.py", "test_*.txt")
            directory: Directory to search in (default: current directory)
            recursive: Whether to search subdirectories
            case_sensitive: Whether the search should be case-sensitive
        
        Returns:
            List of matching files
        """
        try:
            base_path = safe_path(directory)
            if not base_path.exists():
                return f"Error: Directory '{directory}' does not exist"
            if not base_path.is_dir():
                return f"Error: '{directory}' is not a directory"
            
            if recursive:
                search_pattern = str(base_path / "**" / pattern)
                matches = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = str(base_path / pattern)
                matches = glob.glob(search_pattern)
            
            if not case_sensitive:
                # For case-insensitive search, we need to manually filter
                all_files = []
                for root, dirs, files in os.walk(base_path) if recursive else [(base_path, [], os.listdir(base_path))]:
                    for file in files:
                        if not case_sensitive:
                            if pattern.lower() in file.lower() or glob.fnmatch.fnmatch(file.lower(), pattern.lower()):
                                all_files.append(os.path.join(root, file))
                        else:
                            if glob.fnmatch.fnmatch(file, pattern):
                                all_files.append(os.path.join(root, file))
                matches = all_files if not case_sensitive else matches
            
            if not matches:
                return f"No files found matching pattern '{pattern}' in '{directory}'"
            
            # Convert to relative paths and sort
            relative_matches = [os.path.relpath(match, base_path) for match in matches]
            return f"Found {len(matches)} files matching '{pattern}':\n" + "\n".join(sorted(relative_matches))
        except Exception as e:
            return f"Error searching files: {str(e)}"

    @mcp.tool
    def get_file_info(file_path: str) -> str:
        """
        Get detailed information about a file or directory.
        
        Args:
            file_path: Path to the file or directory
        
        Returns:
            Detailed information including size, permissions, timestamps, etc.
        """
        try:
            path = safe_path(file_path)
            if not path.exists():
                return f"Error: '{file_path}' does not exist"
            
            stat_info = path.stat()
            
            info = {
                "path": str(path),
                "name": path.name,
                "type": "directory" if path.is_dir() else "file",
                "size": stat_info.st_size,
                "size_human": _format_size(stat_info.st_size),
                "permissions": oct(stat.S_IMODE(stat_info.st_mode)),
                "owner_uid": stat_info.st_uid,
                "group_gid": stat_info.st_gid,
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            }
            
            if path.is_file():
                info["extension"] = path.suffix
                
            return json.dumps(info, indent=2)
        except Exception as e:
            return f"Error getting file info: {str(e)}"

    @mcp.tool
    def copy_file(source_path: str, destination_path: str, overwrite: bool = False) -> str:
        """
        Copy a file from source to destination.
        
        Args:
            source_path: Path to the source file
            destination_path: Path to the destination
            overwrite: Whether to overwrite the destination if it exists
        
        Returns:
            Success message or error description
        """
        try:
            src = safe_path(source_path)
            dst = safe_path(destination_path)
            
            if not src.exists():
                return f"Error: Source file '{source_path}' does not exist"
            if not src.is_file():
                return f"Error: Source '{source_path}' is not a file"
            
            if dst.exists() and not overwrite:
                return f"Error: Destination '{destination_path}' already exists. Use overwrite=True to replace it"
            
            # Create parent directories if they don't exist
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src, dst)
            return f"Successfully copied '{source_path}' to '{destination_path}'"
        except Exception as e:
            return f"Error copying file: {str(e)}"

    @mcp.tool
    def move_file(source_path: str, destination_path: str, overwrite: bool = False) -> str:
        """
        Move a file from source to destination.
        
        Args:
            source_path: Path to the source file
            destination_path: Path to the destination
            overwrite: Whether to overwrite the destination if it exists
        
        Returns:
            Success message or error description
        """
        try:
            src = safe_path(source_path)
            dst = safe_path(destination_path)
            
            if not src.exists():
                return f"Error: Source '{source_path}' does not exist"
            
            if dst.exists() and not overwrite:
                return f"Error: Destination '{destination_path}' already exists. Use overwrite=True to replace it"
            
            # Create parent directories if they don't exist
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src), str(dst))
            return f"Successfully moved '{source_path}' to '{destination_path}'"
        except Exception as e:
            return f"Error moving file: {str(e)}"

    @mcp.tool
    def format_json_file(filepath: str) -> str:
        """Format/pretty-print a JSON file"""
        try:
            path = safe_path(filepath)
            if not path.exists():
                return f"Error: File '{filepath}' does not exist"
            if not path.is_file():
                return f"Error: '{filepath}' is not a file"
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return f"Successfully formatted JSON file '{filepath}'"
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON in file '{filepath}': {str(e)}"
        except Exception as e:
            return f"Error formatting JSON file: {str(e)}"

    @mcp.tool
    def validate_json_file(filepath: str) -> str:
        """Check if a JSON file is valid"""
        try:
            path = safe_path(filepath)
            if not path.exists():
                return f"Error: File '{filepath}' does not exist"
            if not path.is_file():
                return f"Error: '{filepath}' is not a file"
            
            with open(path, 'r', encoding='utf-8') as f:
                json.load(f)
            
            return f"JSON file '{filepath}' is valid"
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON in file '{filepath}': {str(e)}"
        except Exception as e:
            return f"Error validating JSON file: {str(e)}"
