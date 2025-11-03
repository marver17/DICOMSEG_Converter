# Image Validation and Resampling Guide

## Overview

Based on Pedro's validation work on the Perproglio dataset, this module provides robust validation and automatic resampling to ensure segmentation masks are geometrically compatible with reference DICOM images before conversion.

## The Problem

When converting segmentations from NIfTI to DICOM SEG, mismatches in geometric properties can cause conversion failures or incorrect results. The four critical properties that must match are:

1. **Size** - Image dimensions (width × height × depth)
2. **Spacing** - Pixel/voxel spacing in mm
3. **Origin** - Physical coordinates of the image origin
4. **Direction** - Orientation matrix

## Solution

The validation module performs these checks automatically and can resample segmentations to match the reference image if needed.

## Installation

The validation scripts require SimpleITK:

```bash
# In your conda environment
conda activate dicomseg
pip install SimpleITK

# Or using conda
conda install -c simpleitk simpleitk
```

## Usage

### 1. Standalone Validation (CLI)

Check if a segmentation matches a reference image:

```bash
# Validate only (returns exit code 0 if match, 1 if mismatch)
python src/image_validation.py \
  --segmentation /path/to/seg.nii.gz \
  --reference /path/to/dicom_series \
  --validate-only \
  --verbose

# Validate and resample if needed
python src/image_validation.py \
  --segmentation /path/to/seg.nii.gz \
  --reference /path/to/dicom_series \
  --output /path/to/seg_resampled.nii.gz \
  --verbose

# Use linear interpolation (for intensity images)
python src/image_validation.py \
  --segmentation /path/to/intensity.nii.gz \
  --reference /path/to/dicom_series \
  --output /path/to/intensity_resampled.nii.gz \
  --interpolator linear \
  --verbose
```

### 2. Integration in Python Scripts

#### Quick validation check:

```python
from validation_wrapper import validate_segmentation_geometry

# Returns True if geometry matches, False otherwise
is_compatible = validate_segmentation_geometry(
    segmentation_path="seg.nii.gz",
    reference_path="/path/to/dicom",
    verbose=True
)

if not is_compatible:
    print("Segmentation needs resampling before conversion")
```

#### Prepare segmentation for conversion:

```python
from validation_wrapper import prepare_segmentation_for_conversion

# Automatically validates and resamples if needed
prepared_seg = prepare_segmentation_for_conversion(
    segmentation_path="seg.nii.gz",
    reference_path="/path/to/dicom",
    output_path="seg_resampled.nii.gz",  # Optional
    interpolator='nearest',  # Use 'nearest' for segmentations
    verbose=True
)

# Now use prepared_seg for your conversion
print(f"Use this file for conversion: {prepared_seg}")
```

#### Integration with DICOM SEG conversion:

```python
from validation_wrapper import validate_before_dicomseg_conversion

# Validates and auto-fixes before conversion
validated_seg = validate_before_dicomseg_conversion(
    nifti_seg_path="seg.nii.gz",
    dicom_reference_dir="/path/to/dicom",
    auto_fix=True,
    verbose=True
)

# Now proceed with itkimage2segimage conversion
# The validated_seg is guaranteed to be compatible
```

### 3. Integration with Existing Conversion Scripts

#### Example: Adding validation to dicomseg conversion

Before calling `itkimage2segimage`, validate the segmentation:

```python
# In your conversion script
from validation_wrapper import validate_before_dicomseg_conversion

# Your existing code
input_seg = "/path/to/segmentation.nii.gz"
reference_dicom = "/path/to/dicom_series"
output_dicomseg = "/path/to/output.dcm"

# Add validation step
try:
    validated_seg = validate_before_dicomseg_conversion(
        nifti_seg_path=input_seg,
        dicom_reference_dir=reference_dicom,
        auto_fix=True,
        verbose=True
    )
    
    # Use validated_seg instead of input_seg for conversion
    # ... proceed with your itkimage2segimage call
    
except ValueError as e:
    print(f"Validation failed: {e}")
    sys.exit(1)
```

### 4. Batch Validation

Create a simple script to validate multiple segmentations:

```python
#!/usr/bin/env python3
from pathlib import Path
from validation_wrapper import validate_segmentation_geometry

pairs = [
    ("seg1.nii.gz", "/data/dicom/patient1"),
    ("seg2.nii.gz", "/data/dicom/patient2"),
    ("seg3.nii.gz", "/data/dicom/patient3"),
]

results = []
for seg_path, ref_path in pairs:
    is_valid = validate_segmentation_geometry(seg_path, ref_path, verbose=False)
    results.append((seg_path, is_valid))
    status = "✓" if is_valid else "✗"
    print(f"{status} {seg_path}")

failed = [seg for seg, valid in results if not valid]
if failed:
    print(f"\n{len(failed)} segmentation(s) need resampling:")
    for seg in failed:
        print(f"  - {seg}")
```

## Interpolation Methods

Choose the appropriate interpolation method:

- **`nearest`** (default) - Use for **segmentation masks** (label images)
  - Preserves discrete label values
  - No interpolation between labels
  - Recommended for ROI/structure contours

- **`linear`** - Use for **intensity images**
  - Smooth interpolation
  - Good for grayscale/CT/MR images
  - Not suitable for segmentations (creates intermediate values)

- **`bspline`** - High-quality interpolation
  - Smoother than linear
  - Higher computational cost
  - Use for intensity images when quality is critical

## The Four Checks Explained

### 1. Size Check
```python
moving_size = moving_img.GetSize()       # e.g., (512, 512, 120)
reference_size = reference_img.GetSize()  # e.g., (512, 512, 120)
same_size = moving_size == reference_size
```
- Must match exactly
- Represents image dimensions in pixels/voxels
- Mismatch indicates different acquisition parameters or cropping

### 2. Spacing Check
```python
moving_spacing = moving_img.GetSpacing()       # e.g., (0.5, 0.5, 2.0) mm
reference_spacing = reference_img.GetSpacing()  # e.g., (0.5, 0.5, 2.0) mm
same_spacing = moving_spacing ≈ reference_spacing  # within tolerance
```
- Defines physical size of pixels/voxels
- Critical for accurate physical measurements
- Small differences (< 1e-5) are acceptable due to floating point precision

### 3. Origin Check
```python
moving_origin = moving_img.GetOrigin()       # e.g., (-128.0, -128.0, 0.0)
reference_origin = reference_img.GetOrigin()  # e.g., (-128.0, -128.0, 0.0)
same_origin = moving_origin ≈ reference_origin
```
- Physical coordinates of the image origin (first pixel)
- Defines position in physical space
- Mismatch can indicate different registration or coordinate systems

### 4. Direction Check
```python
moving_direction = moving_img.GetDirection()
# e.g., (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0) - Identity
reference_direction = reference_img.GetDirection()
same_direction = moving_direction ≈ reference_direction
```
- 3×3 rotation matrix flattened to 9 values
- Defines image orientation in physical space
- Mismatch indicates different orientation (e.g., LPS vs RAS)

## Troubleshooting

### Issue: "SimpleITK not found"
```bash
pip install SimpleITK
# or
conda install -c simpleitk simpleitk
```

### Issue: "Resampled image still has mismatches"
- Check tolerance setting (default 1e-5)
- Verify input images are valid
- Check for corrupted DICOM headers

### Issue: Resampling creates artifacts
- For segmentations, always use `--interpolator nearest`
- For intensity images, try `linear` or `bspline`
- Check input segmentation quality

### Issue: Memory error during resampling
- Large images may require more RAM
- Process one slice at a time if needed
- Consider downsampling before conversion

## Example Workflow

Complete workflow for converting a NIfTI segmentation to DICOM SEG:

```bash
#!/bin/bash

SEG="/path/to/segmentation.nii.gz"
REF_DICOM="/path/to/dicom_series"
METADATA="/path/to/metadata.json"
OUTPUT="/path/to/output_seg.dcm"

# Step 1: Validate and prepare segmentation
echo "Validating segmentation geometry..."
python src/image_validation.py \
  --segmentation "$SEG" \
  --reference "$REF_DICOM" \
  --output "${SEG%.nii.gz}_validated.nii.gz" \
  --verbose

if [ $? -eq 0 ]; then
    PREPARED_SEG="${SEG%.nii.gz}_validated.nii.gz"
    echo "✓ Validation successful"
else
    echo "✗ Validation failed"
    exit 1
fi

# Step 2: Convert to DICOM SEG
echo "Converting to DICOM SEG..."
./run_scripts dicomseg \
  --inputImageList "$PREPARED_SEG" \
  --inputDICOMDirectory "$REF_DICOM" \
  --outputDICOM "$OUTPUT" \
  --inputMetadata "$METADATA"

echo "✓ Conversion complete: $OUTPUT"
```

## Integration with Docker

Add validation step in Docker workflows:

```bash
docker run --rm \
  -v /path/to/data:/data \
  dicomconverter:latest \
  python3 /usr/dicomconverter/src/image_validation.py \
    --segmentation /data/seg.nii.gz \
    --reference /data/dicom \
    --output /data/seg_validated.nii.gz \
    --verbose
```

## Credits

Validation approach developed by Pedro during the Perproglio dataset conversion project.

The four-check validation (size, spacing, origin, direction) ensures geometric compatibility and has been successfully applied to convert segmentations that previously failed conversion.

## References

- SimpleITK Documentation: https://simpleitk.readthedocs.io/
- DICOM Coordinate Systems: https://dicom.innolitics.com/ciods
- Image Registration Concepts: https://itk.org/ITKSoftwareGuide/
