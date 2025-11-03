#!/usr/bin/env python3
"""
Image Validation and Resampling for DICOM/NIfTI Conversion

This module provides validation and resampling utilities to ensure that
segmentation masks match the reference DICOM images in terms of:
- Size (dimensions)
- Spacing (pixel/voxel spacing)
- Origin (physical coordinates)
- Direction (orientation matrix)

Based on recommendations from Pedro's validation work on the Perproglio dataset.

Author: Adapted from Pedro's validation approach
"""

import SimpleITK as sitk
import numpy as np
import argparse
import sys
import os
from pathlib import Path
from typing import Tuple, Dict, Optional


class ImageValidator:
    """Validates and resamples segmentation masks to match reference images."""
    
    def __init__(self, tolerance: float = 1e-5, verbose: bool = False):
        """
        Initialize the validator.
        
        Args:
            tolerance: Tolerance for floating point comparisons
            verbose: Enable verbose output
        """
        self.tolerance = tolerance
        self.verbose = verbose
    
    def check_geometry_match(
        self, 
        moving_img: sitk.Image, 
        reference_img: sitk.Image
    ) -> Dict[str, bool]:
        """
        Check if two images have matching geometric properties.
        
        Performs the four essential checks:
        1. Same size (dimensions)
        2. Same spacing (pixel/voxel spacing)
        3. Same origin (physical coordinates)
        4. Same direction (orientation matrix)
        
        Args:
            moving_img: The image to be validated (typically the segmentation)
            reference_img: The reference image (typically the DICOM series)
        
        Returns:
            Dictionary with check results and detailed information
        """
        results = {}
        
        # Check 1: Same size
        moving_size = moving_img.GetSize()
        reference_size = reference_img.GetSize()
        results['same_size'] = moving_size == reference_size
        results['moving_size'] = moving_size
        results['reference_size'] = reference_size
        
        # Check 2: Same spacing
        moving_spacing = moving_img.GetSpacing()
        reference_spacing = reference_img.GetSpacing()
        results['same_spacing'] = self._compare_tuples(moving_spacing, reference_spacing)
        results['moving_spacing'] = moving_spacing
        results['reference_spacing'] = reference_spacing
        
        # Check 3: Same origin
        moving_origin = moving_img.GetOrigin()
        reference_origin = reference_img.GetOrigin()
        results['same_origin'] = self._compare_tuples(moving_origin, reference_origin)
        results['moving_origin'] = moving_origin
        results['reference_origin'] = reference_origin
        
        # Check 4: Same direction
        moving_direction = moving_img.GetDirection()
        reference_direction = reference_img.GetDirection()
        results['same_direction'] = self._compare_tuples(moving_direction, reference_direction)
        results['moving_direction'] = moving_direction
        results['reference_direction'] = reference_direction
        
        # Overall match
        results['all_match'] = (
            results['same_size'] and 
            results['same_spacing'] and 
            results['same_origin'] and 
            results['same_direction']
        )
        
        if self.verbose:
            self._print_results(results)
        
        return results
    
    def _compare_tuples(self, tuple1: tuple, tuple2: tuple) -> bool:
        """Compare two tuples with tolerance for floating point values."""
        if len(tuple1) != len(tuple2):
            return False
        return all(abs(a - b) < self.tolerance for a, b in zip(tuple1, tuple2))
    
    def _print_results(self, results: Dict) -> None:
        """Print validation results in a readable format."""
        print("\n" + "="*60)
        print("IMAGE GEOMETRY VALIDATION RESULTS")
        print("="*60)
        
        # Size check
        status = "✓" if results['same_size'] else "✗"
        print(f"\n{status} SIZE CHECK:")
        print(f"  Moving:    {results['moving_size']}")
        print(f"  Reference: {results['reference_size']}")
        
        # Spacing check
        status = "✓" if results['same_spacing'] else "✗"
        print(f"\n{status} SPACING CHECK:")
        print(f"  Moving:    {results['moving_spacing']}")
        print(f"  Reference: {results['reference_spacing']}")
        
        # Origin check
        status = "✓" if results['same_origin'] else "✗"
        print(f"\n{status} ORIGIN CHECK:")
        print(f"  Moving:    {results['moving_origin']}")
        print(f"  Reference: {results['reference_origin']}")
        
        # Direction check
        status = "✓" if results['same_direction'] else "✗"
        print(f"\n{status} DIRECTION CHECK:")
        print(f"  Moving:    {results['moving_direction']}")
        print(f"  Reference: {results['reference_direction']}")
        
        print("\n" + "="*60)
        if results['all_match']:
            print("✓ ALL CHECKS PASSED - Images are geometrically compatible")
        else:
            print("✗ MISMATCH DETECTED - Resampling required")
        print("="*60 + "\n")
    
    def resample_to_reference(
        self,
        moving_img: sitk.Image,
        reference_img: sitk.Image,
        interpolator: str = 'nearest',
        default_value: float = 0.0
    ) -> sitk.Image:
        """
        Resample the moving image to match the reference image geometry.
        
        This function performs interpolation to align the moving image
        (typically a segmentation) with the reference image geometry.
        
        Args:
            moving_img: Image to be resampled (segmentation)
            reference_img: Reference image (DICOM)
            interpolator: Interpolation method. Options:
                - 'nearest': Nearest neighbor (default for segmentations)
                - 'linear': Linear interpolation
                - 'bspline': B-spline interpolation
            default_value: Value for pixels outside the original image
        
        Returns:
            Resampled image matching the reference geometry
        """
        # Map interpolator string to SimpleITK constant
        interpolator_map = {
            'nearest': sitk.sitkNearestNeighbor,
            'linear': sitk.sitkLinear,
            'bspline': sitk.sitkBSpline,
        }
        
        if interpolator not in interpolator_map:
            raise ValueError(f"Unknown interpolator: {interpolator}. "
                           f"Choose from {list(interpolator_map.keys())}")
        
        interp_method = interpolator_map[interpolator]
        
        if self.verbose:
            print(f"\nResampling image using {interpolator} interpolation...")
            print(f"Target size: {reference_img.GetSize()}")
            print(f"Target spacing: {reference_img.GetSpacing()}")
        
        # Perform resampling
        resampled = sitk.Resample(
            moving_img,
            reference_img,
            sitk.Transform(),  # Identity transform
            interp_method,
            default_value,
            moving_img.GetPixelID()
        )
        
        if self.verbose:
            print("✓ Resampling completed successfully")
        
        return resampled
    
    def validate_and_resample(
        self,
        moving_img: sitk.Image,
        reference_img: sitk.Image,
        interpolator: str = 'nearest',
        auto_resample: bool = True
    ) -> Tuple[sitk.Image, Dict]:
        """
        Validate geometry and automatically resample if needed.
        
        Args:
            moving_img: Image to validate (segmentation)
            reference_img: Reference image (DICOM)
            interpolator: Interpolation method if resampling is needed
            auto_resample: Automatically resample if mismatch detected
        
        Returns:
            Tuple of (resampled_image, validation_results)
            If images match, returns (original_moving_img, validation_results)
        """
        # Validate geometry
        results = self.check_geometry_match(moving_img, reference_img)
        
        if results['all_match']:
            if self.verbose:
                print("Images match - no resampling needed")
            return moving_img, results
        
        if not auto_resample:
            if self.verbose:
                print("Mismatch detected but auto_resample=False")
            return moving_img, results
        
        # Resample to match reference
        if self.verbose:
            print("\nMismatch detected - performing automatic resampling...")
        
        resampled_img = self.resample_to_reference(
            moving_img, 
            reference_img, 
            interpolator=interpolator
        )
        
        # Verify the resampling worked
        verification = self.check_geometry_match(resampled_img, reference_img)
        results['resampled'] = True
        results['verification'] = verification
        
        if verification['all_match']:
            if self.verbose:
                print("✓ Resampling successful - images now match")
        else:
            print("⚠ Warning: Resampled image still has mismatches")
        
        return resampled_img, results


def load_image(path: str) -> sitk.Image:
    """
    Load an image from file (supports DICOM series and NIfTI).
    
    Args:
        path: Path to image file or DICOM directory
    
    Returns:
        SimpleITK Image object
    """
    path_obj = Path(path)
    
    if path_obj.is_dir():
        # Assume DICOM series
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(str(path))
        if not dicom_names:
            raise ValueError(f"No DICOM files found in {path}")
        reader.SetFileNames(dicom_names)
        return reader.Execute()
    else:
        # Single file (NIfTI, etc.)
        return sitk.ReadImage(str(path))


def main():
    parser = argparse.ArgumentParser(
        description='Validate and resample segmentation masks to match reference images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate segmentation against reference DICOM
  %(prog)s --segmentation seg.nii.gz --reference /path/to/dicom --validate-only
  
  # Validate and resample if needed
  %(prog)s --segmentation seg.nii.gz --reference /path/to/dicom --output seg_resampled.nii.gz
  
  # Use linear interpolation instead of nearest neighbor
  %(prog)s --segmentation seg.nii.gz --reference /path/to/dicom --output seg_resampled.nii.gz --interpolator linear
  
  # Batch validation (check only, no resampling)
  %(prog)s --segmentation seg.nii.gz --reference /path/to/dicom --validate-only --verbose

Based on validation approach by Pedro for the Perproglio dataset.
        """
    )
    
    parser.add_argument('--segmentation', '-s', required=True,
                       help='Path to segmentation image (NIfTI or DICOM)')
    
    parser.add_argument('--reference', '-r', required=True,
                       help='Path to reference image (DICOM directory or file)')
    
    parser.add_argument('--output', '-o',
                       help='Output path for resampled segmentation')
    
    parser.add_argument('--interpolator', '-i',
                       choices=['nearest', 'linear', 'bspline'],
                       default='nearest',
                       help='Interpolation method (default: nearest for segmentations)')
    
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate, do not resample')
    
    parser.add_argument('--tolerance', type=float, default=1e-5,
                       help='Tolerance for floating point comparisons (default: 1e-5)')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Load images
    try:
        if args.verbose:
            print(f"Loading segmentation from: {args.segmentation}")
        seg_img = load_image(args.segmentation)
        
        if args.verbose:
            print(f"Loading reference from: {args.reference}")
        ref_img = load_image(args.reference)
    except Exception as e:
        print(f"Error loading images: {e}", file=sys.stderr)
        return 1
    
    # Initialize validator
    validator = ImageValidator(tolerance=args.tolerance, verbose=args.verbose)
    
    # Validate
    if args.validate_only:
        results = validator.check_geometry_match(seg_img, ref_img)
        return 0 if results['all_match'] else 1
    
    # Validate and resample if needed
    resampled_img, results = validator.validate_and_resample(
        seg_img,
        ref_img,
        interpolator=args.interpolator,
        auto_resample=True
    )
    
    # Save output if specified
    if args.output:
        if results.get('resampled', False):
            if args.verbose:
                print(f"\nSaving resampled image to: {args.output}")
            sitk.WriteImage(resampled_img, args.output)
            print(f"✓ Resampled segmentation saved to: {args.output}")
        else:
            if args.verbose:
                print(f"\nNo resampling needed. Saving original to: {args.output}")
            sitk.WriteImage(seg_img, args.output)
            print(f"✓ Segmentation saved to: {args.output}")
    
    return 0 if results['all_match'] or results.get('resampled', False) else 1


if __name__ == '__main__':
    sys.exit(main())
