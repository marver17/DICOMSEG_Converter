#!/usr/bin/env python3
"""
Wrapper functions to integrate image validation into conversion workflows.

This module provides high-level functions that can be easily integrated
into existing conversion scripts (dicomseg, rtstruct2seg, etc.) to ensure
geometric compatibility between segmentations and reference images.
"""

from pathlib import Path
from typing import Optional, Union
import sys

# Add parent directory to path to import image_validation
sys.path.insert(0, str(Path(__file__).parent))

try:
    from image_validation import ImageValidator, load_image
    import SimpleITK as sitk
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Please ensure SimpleITK is installed: pip install SimpleITK")
    sys.exit(1)


def validate_segmentation_geometry(
    segmentation_path: Union[str, Path],
    reference_path: Union[str, Path],
    verbose: bool = False
) -> bool:
    """
    Quick validation check for segmentation geometry.
    
    Args:
        segmentation_path: Path to segmentation file
        reference_path: Path to reference image/DICOM directory
        verbose: Print detailed validation info
    
    Returns:
        True if geometry matches, False otherwise
    """
    validator = ImageValidator(verbose=verbose)
    
    seg_img = load_image(str(segmentation_path))
    ref_img = load_image(str(reference_path))
    
    results = validator.check_geometry_match(seg_img, ref_img)
    
    return results['all_match']


def prepare_segmentation_for_conversion(
    segmentation_path: Union[str, Path],
    reference_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    interpolator: str = 'nearest',
    overwrite: bool = False,
    verbose: bool = False
) -> str:
    """
    Validate and prepare segmentation for DICOM conversion.
    
    This function:
    1. Validates the segmentation against the reference image
    2. If mismatch detected, resamples the segmentation
    3. Saves the prepared segmentation to output_path
    4. Returns the path to the prepared segmentation
    
    Args:
        segmentation_path: Path to original segmentation
        reference_path: Path to reference image/DICOM directory
        output_path: Path for resampled segmentation (optional)
                    If None, uses {segmentation_stem}_resampled{ext}
        interpolator: Interpolation method ('nearest', 'linear', 'bspline')
        overwrite: Overwrite output file if exists
        verbose: Print detailed info
    
    Returns:
        Path to the prepared segmentation (may be original if no resampling needed)
    
    Raises:
        FileExistsError: If output exists and overwrite=False
        ValueError: If validation/resampling fails
    """
    segmentation_path = Path(segmentation_path)
    reference_path = Path(reference_path)
    
    # Determine output path
    if output_path is None:
        output_path = segmentation_path.parent / f"{segmentation_path.stem}_resampled{segmentation_path.suffix}"
    else:
        output_path = Path(output_path)
    
    # Check if output exists
    if output_path.exists() and not overwrite:
        if verbose:
            print(f"Output already exists: {output_path}")
        return str(output_path)
    
    # Load images
    if verbose:
        print(f"Loading segmentation: {segmentation_path}")
        print(f"Loading reference: {reference_path}")
    
    seg_img = load_image(str(segmentation_path))
    ref_img = load_image(str(reference_path))
    
    # Validate and resample
    validator = ImageValidator(verbose=verbose)
    prepared_img, results = validator.validate_and_resample(
        seg_img,
        ref_img,
        interpolator=interpolator,
        auto_resample=True
    )
    
    # Decide what to return
    if results['all_match']:
        # No resampling needed - return original path
        if verbose:
            print("✓ Segmentation is already compatible - no resampling needed")
        return str(segmentation_path)
    elif results.get('resampled', False):
        # Resampling was performed - save and return new path
        if verbose:
            print(f"Saving resampled segmentation to: {output_path}")
        sitk.WriteImage(prepared_img, str(output_path))
        if verbose:
            print(f"✓ Resampled segmentation saved successfully")
        return str(output_path)
    else:
        raise ValueError("Validation failed and resampling was not performed")


def validate_before_dicomseg_conversion(
    nifti_seg_path: Union[str, Path],
    dicom_reference_dir: Union[str, Path],
    auto_fix: bool = True,
    verbose: bool = False
) -> str:
    """
    Validate and prepare NIfTI segmentation for DICOM SEG conversion.
    
    Specifically designed to be called before itkimage2segimage (dicomseg conversion).
    
    Args:
        nifti_seg_path: Path to NIfTI segmentation
        dicom_reference_dir: Path to reference DICOM directory
        auto_fix: Automatically resample if mismatch detected
        verbose: Print detailed info
    
    Returns:
        Path to validated/resampled segmentation ready for conversion
    
    Raises:
        ValueError: If validation fails and auto_fix=False
    """
    if verbose:
        print("\n" + "="*60)
        print("PRE-CONVERSION VALIDATION")
        print("="*60)
    
    validator = ImageValidator(verbose=verbose)
    
    seg_img = load_image(str(nifti_seg_path))
    ref_img = load_image(str(dicom_reference_dir))
    
    results = validator.check_geometry_match(seg_img, ref_img)
    
    if results['all_match']:
        if verbose:
            print("✓ Segmentation is compatible - proceeding with conversion")
        return str(nifti_seg_path)
    
    if not auto_fix:
        raise ValueError(
            "Segmentation geometry does not match reference image. "
            "Set auto_fix=True to automatically resample, or manually fix the segmentation."
        )
    
    # Auto-fix by resampling
    output_path = Path(nifti_seg_path).parent / f"{Path(nifti_seg_path).stem}_resampled.nii.gz"
    
    if verbose:
        print(f"\n⚠ Mismatch detected - resampling to: {output_path}")
    
    return prepare_segmentation_for_conversion(
        nifti_seg_path,
        dicom_reference_dir,
        output_path=output_path,
        interpolator='nearest',
        overwrite=True,
        verbose=verbose
    )


# Example usage function
def example_usage():
    """Demonstrate usage of validation functions."""
    
    print("Example 1: Quick validation check")
    print("-" * 40)
    is_valid = validate_segmentation_geometry(
        segmentation_path="/path/to/segmentation.nii.gz",
        reference_path="/path/to/dicom_series",
        verbose=True
    )
    print(f"Geometry matches: {is_valid}\n")
    
    print("Example 2: Prepare segmentation for conversion")
    print("-" * 40)
    prepared_path = prepare_segmentation_for_conversion(
        segmentation_path="/path/to/segmentation.nii.gz",
        reference_path="/path/to/dicom_series",
        output_path="/path/to/segmentation_resampled.nii.gz",
        verbose=True
    )
    print(f"Prepared segmentation: {prepared_path}\n")
    
    print("Example 3: Validate before DICOM SEG conversion")
    print("-" * 40)
    ready_path = validate_before_dicomseg_conversion(
        nifti_seg_path="/path/to/segmentation.nii.gz",
        dicom_reference_dir="/path/to/dicom_series",
        auto_fix=True,
        verbose=True
    )
    print(f"Ready for conversion: {ready_path}")


if __name__ == '__main__':
    print("Image Validation Wrapper Functions")
    print("="*60)
    print("Import this module to use validation in your conversion scripts:")
    print()
    print("from validation_wrapper import (")
    print("    validate_segmentation_geometry,")
    print("    prepare_segmentation_for_conversion,")
    print("    validate_before_dicomseg_conversion")
    print(")")
    print()
    print("See example_usage() function for usage examples.")
