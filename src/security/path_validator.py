#!/usr/bin/env python3
"""
Path Validator - Secure file path validation and sanitization
Implements security controls for EUCAIM Risk Assessment compliance
"""

import os
from pathlib import Path
from typing import Union, List, Optional


class PathValidator:
    """
    Validates and sanitizes file paths for security.
    
    Prevents:
    - Path traversal attacks
    - Access to unauthorized directories
    - Symlink attacks
    - Excessively large files
    """
    
    def __init__(self, allowed_base_paths: List[str], max_file_size_mb: int = 5000):
        """
        Initialize the path validator.
        
        Args:
            allowed_base_paths: List of directories where file access is permitted
            max_file_size_mb: Maximum allowed file size in MB (default: 5GB)
        """
        # Resolve all allowed base paths to absolute paths
        self.allowed_bases = [Path(p).resolve() for p in allowed_base_paths]
        self.max_file_size_mb = max_file_size_mb
        
        # Validate that allowed bases exist
        for base in self.allowed_bases:
            if not base.exists():
                raise ValueError(f"Allowed base path does not exist: {base}")
    
    def validate_path(
        self, 
        user_path: Union[str, Path], 
        must_exist: bool = False,
        allow_symlinks: bool = False
    ) -> Path:
        """
        Validate that a path is safe and within allowed directories.
        
        Args:
            user_path: Path provided by user
            must_exist: If True, raises error if path doesn't exist
            allow_symlinks: If True, allows symlinks (default: False for security)
            
        Returns:
            Resolved safe path
            
        Raises:
            ValueError: If path is unsafe or outside allowed directories
        """
        if not user_path:
            raise ValueError("Path cannot be empty")
        
        try:
            # Convert to Path object and resolve
            path_obj = Path(user_path)
            
            # Check for obvious malicious patterns before resolving
            path_str = str(path_obj)
            if '..' in path_str:
                # Note: This is a basic check. resolve() will handle it properly
                # but we catch obvious attempts early
                pass  # Will be caught by the allowed_bases check
            
            # Resolve to absolute path (follows symlinks)
            resolved = path_obj.resolve()
            
            # Check if within allowed base paths
            is_allowed = any(
                self._is_subpath(resolved, base) 
                for base in self.allowed_bases
            )
            
            if not is_allowed:
                raise ValueError(
                    f"Access denied: Path '{user_path}' is outside allowed directories. "
                    f"Allowed directories: {[str(b) for b in self.allowed_bases]}"
                )
            
            # Check if it's a symlink (security risk)
            if path_obj.is_symlink() and not allow_symlinks:
                raise ValueError(
                    f"Symlinks not allowed for security reasons: {user_path}"
                )
            
            # Check existence if required
            if must_exist and not resolved.exists():
                raise ValueError(f"Path does not exist: {user_path}")
            
            return resolved
            
        except Exception as e:
            # Re-raise ValueError, wrap other exceptions
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Invalid path '{user_path}': {str(e)}")
    
    def validate_file_size(
        self, 
        filepath: Path, 
        max_size_mb: Optional[int] = None
    ) -> bool:
        """
        Check that file size is within limits.
        
        Args:
            filepath: Path to file
            max_size_mb: Maximum allowed size in MB (uses instance default if None)
            
        Returns:
            True if size is OK
            
        Raises:
            ValueError: If file is too large
        """
        if not filepath.is_file():
            raise ValueError(f"Not a file: {filepath}")
        
        max_size = max_size_mb or self.max_file_size_mb
        size_bytes = filepath.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb > max_size:
            raise ValueError(
                f"File too large: {size_mb:.1f} MB exceeds limit of {max_size} MB. "
                f"File: {filepath.name}"
            )
        
        return True
    
    def validate_directory_size(
        self, 
        dirpath: Path, 
        max_size_mb: Optional[int] = None
    ) -> bool:
        """
        Check that total directory size is within limits.
        
        Args:
            dirpath: Path to directory
            max_size_mb: Maximum allowed total size in MB
            
        Returns:
            True if size is OK
            
        Raises:
            ValueError: If directory is too large
        """
        if not dirpath.is_dir():
            raise ValueError(f"Not a directory: {dirpath}")
        
        max_size = max_size_mb or self.max_file_size_mb
        total_size = 0
        file_count = 0
        
        # Walk directory and sum file sizes
        for root, dirs, files in os.walk(dirpath):
            for file in files:
                file_path = Path(root) / file
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        size_mb = total_size / (1024 * 1024)
        
        if size_mb > max_size:
            raise ValueError(
                f"Directory too large: {size_mb:.1f} MB exceeds limit of {max_size} MB. "
                f"Directory: {dirpath.name} ({file_count} files)"
            )
        
        return True
    
    def _is_subpath(self, path: Path, base: Path) -> bool:
        """
        Check if path is a subpath of base.
        
        Args:
            path: Path to check
            base: Base path
            
        Returns:
            True if path is under base
        """
        try:
            # Check if path is relative to base
            path.relative_to(base)
            return True
        except ValueError:
            return False
    
    def sanitize_for_logging(self, path: Union[str, Path]) -> str:
        """
        Sanitize a path for safe logging (remove sensitive parts).
        
        Args:
            path: Path to sanitize
            
        Returns:
            Sanitized path string safe for logging
        """
        path_str = str(path)
        
        # Replace sensitive base paths with placeholders
        replacements = [
            ('/home/', '~'),
            (str(Path.home()), '~'),
        ]
        
        # Replace known sensitive patterns
        for old, new in replacements:
            path_str = path_str.replace(old, new)
        
        # Show only the last 3 components for additional privacy
        path_parts = Path(path_str).parts
        if len(path_parts) > 3:
            path_str = '.../' + '/'.join(path_parts[-3:])
        
        return path_str


# Example usage and testing
if __name__ == '__main__':
    import sys
    
    print("PathValidator - Security Test Suite\n")
    
    # Test configuration
    allowed_dirs = ['/data', '/tmp']
    validator = PathValidator(allowed_dirs, max_file_size_mb=100)
    
    # Test cases
    test_cases = [
        ('/data/test.dcm', True, "Valid path in allowed directory"),
        ('/data/../etc/passwd', False, "Path traversal attempt"),
        ('/home/user/file.dcm', False, "Path outside allowed directories"),
        ('/data/subdir/../../data/file.dcm', True, "Complex but valid path"),
    ]
    
    print("Running validation tests:\n")
    for test_path, should_pass, description in test_cases:
        try:
            result = validator.validate_path(test_path)
            if should_pass:
                print(f"✓ PASS: {description}")
                print(f"  Path: {test_path} -> {result}")
            else:
                print(f"✗ FAIL: {description}")
                print(f"  Expected to fail but passed: {test_path}")
        except ValueError as e:
            if not should_pass:
                print(f"✓ PASS: {description}")
                print(f"  Correctly rejected: {test_path}")
                print(f"  Reason: {str(e)[:80]}...")
            else:
                print(f"✗ FAIL: {description}")
                print(f"  Expected to pass but failed: {test_path}")
                print(f"  Error: {e}")
        print()
    
    print("\nTest completed.")
