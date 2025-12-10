#!/usr/bin/env python3

import argparse
import dicom2nifti
import os
import sys
from pathlib import Path

# SECURITY: Import path validator for input sanitization
try:
    from security.path_validator import PathValidator
    SECURITY_ENABLED = True
except ImportError:
    print("Warning: PathValidator not found. Running without path validation.", file=sys.stderr)
    SECURITY_ENABLED = False

def dicomconversion(args):
    """
    Convert DICOM directory to NIfTI format.
    
    Args:
        args: Parsed arguments with path_input and path_output
    """
    # SECURITY: Validate input paths
    if SECURITY_ENABLED:
        validator = PathValidator(
            allowed_base_paths=[
                '/data',
                '/home/ds/datasets',
                '/home/ds/persistent-shared-folder',
                str(Path.home() / 'datasets'),
                str(Path.home() / 'persistent-shared-folder')
            ],
            max_file_size_mb=5000
        )
        
        try:
            # Validate input directory exists and is accessible
            input_path = validator.validate_path(args.path_input, must_exist=True)
            if Path(input_path).is_dir():
                validator.validate_directory_size(Path(input_path))
            
            # Validate output path (doesn't need to exist yet)
            output_path = validator.validate_path(args.path_output, must_exist=False)
            
            # Update args with validated paths
            args.path_input = str(input_path)
            args.path_output = str(output_path)
            
        except ValueError as e:
            print(f"Error: Path validation failed: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.path_output):
        try:
            os.makedirs(args.path_output, exist_ok=True)
        except OSError as e:
            print(f"Error: Cannot create output directory: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Perform conversion
    try:
        dicom2nifti.convert_directory(args.path_input, args.path_output, True, False)
    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Convert DICOM to NIfTI.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s -path_input /path/to/dicom -path_output /path/to/nifti

Notes:
    - Output directory will be created if it doesn't exist
    - Input DICOM files must be in the same directory
    - One NIfTI file will be created for each DICOM series

For more information:
    https://github.com/icometrix/dicom2nifti
    """
    )
    
    parser.add_argument(
        '-path_input', 
        type=str,
        required=True,
        help='Directory containing DICOM files to convert'
    )
    
    parser.add_argument(
        '-path_output', 
        type=str, 
        required=True,
        help='Directory where to save converted NIfTI files'
    )

    args = parser.parse_args()
    dicomconversion(args)

if __name__ == "__main__":
    main()