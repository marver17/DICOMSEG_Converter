#!/usr/bin/env python3

import argparse
import dicom2nifti
import os

def dicomconversion(args):
    if not os.path.exists(args.path_output) : 
        os.makedirs(args.path_output) 
        
    dicom2nifti.convert_directory(args.path_input, args.path_output, True, False)

def main():
    parser = argparse.ArgumentParser(description='Convert DICOM to NIfTI.')
    parser.add_argument('-path_input', type=str, help='Path to input DICOM directory')
    parser.add_argument('-path_output', type=str, help='Path to output NIfTI directory')
    args = parser.parse_args()

    dicomconversion(args)

if __name__ == "__main__":
    main()
