#!/usr/bin/env python3
"""
Example script demonstrating image validation integration.

This shows how to integrate the validation checks into your conversion workflow.
Based on Pedro's approach for the Perproglio dataset.
"""

import sys
from pathlib import Path

# Import validation functions
try:
    from src.validation_wrapper import (
        validate_segmentation_geometry,
        prepare_segmentation_for_conversion,
        validate_before_dicomseg_conversion
    )
except ImportError:
    print("Error: validation_wrapper not found or SimpleITK not installed")
    print("Install with: pip install SimpleITK")
    sys.exit(1)


def example_1_quick_check():
    """Example 1: Quick validation check without resampling."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Quick Validation Check")
    print("="*60)
    
    segmentation = "/path/to/your/segmentation.nii.gz"
    reference = "/path/to/your/dicom_series"
    
    print(f"\nChecking: {segmentation}")
    print(f"Against: {reference}")
    
    is_valid = validate_segmentation_geometry(
        segmentation_path=segmentation,
        reference_path=reference,
        verbose=True
    )
    
    if is_valid:
        print("\n✓ Segmentation is geometrically compatible")
        print("  You can proceed with conversion directly")
    else:
        print("\n✗ Segmentation needs resampling")
        print("  Use prepare_segmentation_for_conversion() to fix")
    
    return is_valid


def example_2_prepare_with_resampling():
    """Example 2: Validate and resample if needed."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Validate and Prepare (with auto-resampling)")
    print("="*60)
    
    segmentation = "/path/to/your/segmentation.nii.gz"
    reference = "/path/to/your/dicom_series"
    output = "/path/to/your/segmentation_prepared.nii.gz"
    
    print(f"\nPreparing: {segmentation}")
    print(f"Reference: {reference}")
    print(f"Output: {output}")
    
    try:
        prepared_seg = prepare_segmentation_for_conversion(
            segmentation_path=segmentation,
            reference_path=reference,
            output_path=output,
            interpolator='nearest',  # Use 'nearest' for segmentations
            overwrite=True,
            verbose=True
        )
        
        print(f"\n✓ Prepared segmentation ready at: {prepared_seg}")
        print("  Use this file for your DICOM conversion")
        
        return prepared_seg
    
    except Exception as e:
        print(f"\n✗ Error during preparation: {e}")
        return None


def example_3_full_conversion_workflow():
    """Example 3: Complete workflow from validation to DICOM SEG conversion."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Complete Conversion Workflow")
    print("="*60)
    
    # Input files
    nifti_seg = "/path/to/your/segmentation.nii.gz"
    dicom_ref = "/path/to/your/dicom_series"
    metadata_json = "/path/to/your/metadata.json"
    output_dcm = "/path/to/your/output_seg.dcm"
    
    print("\nStep 1: Validate and prepare segmentation")
    print("-" * 40)
    
    try:
        # This will validate and resample if needed
        validated_seg = validate_before_dicomseg_conversion(
            nifti_seg_path=nifti_seg,
            dicom_reference_dir=dicom_ref,
            auto_fix=True,
            verbose=True
        )
        
        print(f"✓ Segmentation validated: {validated_seg}")
        
    except ValueError as e:
        print(f"✗ Validation failed: {e}")
        print("  Fix the segmentation manually or check input files")
        return False
    
    print("\nStep 2: Convert to DICOM SEG")
    print("-" * 40)
    print("Now you would call your conversion tool:")
    print(f"  itkimage2segimage \\")
    print(f"    --inputImageList {validated_seg} \\")
    print(f"    --inputDICOMDirectory {dicom_ref} \\")
    print(f"    --outputDICOM {output_dcm} \\")
    print(f"    --inputMetadata {metadata_json}")
    
    # Here you would actually call the conversion
    # For example:
    # subprocess.run([
    #     "itkimage2segimage",
    #     "--inputImageList", validated_seg,
    #     "--inputDICOMDirectory", dicom_ref,
    #     "--outputDICOM", output_dcm,
    #     "--inputMetadata", metadata_json
    # ])
    
    print("\n✓ Conversion workflow complete")
    return True


def example_4_batch_validation():
    """Example 4: Validate multiple segmentations in batch."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Batch Validation")
    print("="*60)
    
    # List of (segmentation, reference) pairs
    pairs = [
        ("/data/patient001/seg.nii.gz", "/data/patient001/dicom"),
        ("/data/patient002/seg.nii.gz", "/data/patient002/dicom"),
        ("/data/patient003/seg.nii.gz", "/data/patient003/dicom"),
    ]
    
    print(f"\nValidating {len(pairs)} segmentations...")
    print("-" * 40)
    
    results = []
    for seg_path, ref_path in pairs:
        patient_id = Path(seg_path).parent.name
        
        try:
            is_valid = validate_segmentation_geometry(
                segmentation_path=seg_path,
                reference_path=ref_path,
                verbose=False  # Quiet mode for batch
            )
            
            status = "✓" if is_valid else "✗"
            print(f"{status} {patient_id}: {'Compatible' if is_valid else 'Needs resampling'}")
            results.append((patient_id, is_valid))
            
        except Exception as e:
            print(f"✗ {patient_id}: Error - {e}")
            results.append((patient_id, False))
    
    # Summary
    print("\n" + "-" * 40)
    valid_count = sum(1 for _, valid in results if valid)
    total = len(results)
    print(f"Summary: {valid_count}/{total} segmentations are compatible")
    
    # List failures
    failures = [pid for pid, valid in results if not valid]
    if failures:
        print(f"\nSegmentations needing resampling:")
        for pid in failures:
            print(f"  - {pid}")
    
    return results


def main():
    """Main function - run all examples."""
    print("\n" + "="*70)
    print("IMAGE VALIDATION EXAMPLES")
    print("Based on Pedro's validation approach for Perproglio dataset")
    print("="*70)
    
    print("\nNote: Update the file paths in each example function before running")
    print("\nAvailable examples:")
    print("  1. Quick validation check (no resampling)")
    print("  2. Validate and prepare with auto-resampling")
    print("  3. Complete conversion workflow")
    print("  4. Batch validation")
    
    print("\n" + "-"*70)
    print("To run a specific example, uncomment the function call below:")
    print("-"*70)
    
    # Uncomment one of these to run:
    # example_1_quick_check()
    # example_2_prepare_with_resampling()
    # example_3_full_conversion_workflow()
    # example_4_batch_validation()
    
    print("\nFor actual usage, edit this script and update the file paths")
    print("or import the functions directly in your conversion scripts:")
    print("\n  from validation_wrapper import validate_before_dicomseg_conversion")


if __name__ == '__main__':
    main()
