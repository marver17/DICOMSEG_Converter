#!/usr/bin/env python3
"""
Convert a DICOM series directory to a single NIfTI file using SimpleITK.
This script properly reads DICOM image series (not segmentations).
"""

import argparse
import SimpleITK as sitk
import sys
import os

def convert_dicom_series_to_nifti(dicom_dir, output_file):
    """
    Convert a DICOM series to NIfTI format.
    
    Args:
        dicom_dir: Directory containing DICOM files
        output_file: Output NIfTI file path
    """
    try:
        # Read DICOM series
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(dicom_dir)
        
        if not dicom_names:
            print(f"Error: No DICOM series found in {dicom_dir}", file=sys.stderr)
            return False
            
        print(f"Found {len(dicom_names)} DICOM files in series")
        
        reader.SetFileNames(dicom_names)
        reader.MetaDataDictionaryArrayUpdateOn()
        reader.LoadPrivateTagsOn()
        
        # Read the image
        image = reader.Execute()
        
        # Get image info
        print(f"Image size: {image.GetSize()}")
        print(f"Image spacing: {image.GetSpacing()}")
        print(f"Image origin: {image.GetOrigin()}")
        
        # Create output directory if needed
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Write NIfTI file
        sitk.WriteImage(image, output_file, useCompression=True)
        print(f"Successfully converted to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"Error converting DICOM series: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Convert DICOM series to NIfTI format using SimpleITK',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s -i /path/to/dicom/series -o /path/to/output.nii.gz
    
Notes:
    - Input directory should contain a single DICOM series
    - Output will be compressed NIfTI (.nii.gz)
    - Uses SimpleITK's GDCM reader for proper DICOM parsing
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input directory containing DICOM series'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output NIfTI file path (.nii.gz)'
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input):
        print(f"Error: Input directory does not exist: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    success = convert_dicom_series_to_nifti(args.input, args.output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
