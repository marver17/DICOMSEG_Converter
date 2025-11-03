# Image Validation Module

## Quick Start

Install dependencies:
```bash
pip install SimpleITK numpy
# or
pip install -r src/validation_requirements.txt
```

Validate a segmentation:
```bash
python src/image_validation.py \
  --segmentation seg.nii.gz \
  --reference /path/to/dicom \
  --output seg_validated.nii.gz \
  --verbose
```

## The Four Critical Checks

1. ✓ **Size** - Image dimensions must match exactly
2. ✓ **Spacing** - Pixel/voxel spacing must match
3. ✓ **Origin** - Physical origin coordinates must match  
4. ✓ **Direction** - Orientation matrix must match

## Files

- **`image_validation.py`** - Core validation and resampling logic (CLI tool)
- **`validation_wrapper.py`** - High-level functions for integration
- **`validation_requirements.txt`** - Python dependencies
- **`examples/VALIDATION_GUIDE.md`** - Complete documentation
- **`examples/validation_examples.py`** - Usage examples

