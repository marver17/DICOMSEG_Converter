#!/usr/bin/env python3

import argparse
import dicom2nifti
import os

def dicomconversion(args):
    if not os.path.exists(args.path_output) : 
        os.makedirs(args.path_output) 
        
    dicom2nifti.convert_directory(args.path_input, args.path_output, True, False)

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