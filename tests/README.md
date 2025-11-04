# Test Suite - DICOM Converter

Complete documentation for the DICOM Converter test suite.

## 📋 Overview

The test suite includes 26 automated tests that validate:
- Basic conversions (RT-STRUCT, DICOM SEG, NIfTI)
- Round-trip conversions with Dice coefficient
- Cross-validation between conversion paths
- Geometric validation (size, spacing, origin, direction)

## 🚀 Quick Execution

### Complete Test (Recommended)

```bash
cd tests
./quick_test.sh
```

This script:
1. Builds the Docker container from the main directory
2. Executes all 24 tests automatically
3. Generates detailed report with results

### Tests Only (No Build)

```bash
cd tests
./run_container_tests.sh
```

Runs the complete suite assuming the container is already built.

## 📊 Available Tests

### TEST 1-4: Basic Conversions and Help
- Test help for main commands
- Verify basic container functionality

### TEST 5-8: RT-STRUCT → DICOM SEG

Tests on 4 real datasets:

| Test | Dataset | Segments | Description |
|------|---------|----------|-------------|
| 5 | LUNG1-001 | 4 | Lung CT |
| 6 | interobs05 | 10 | Multi-segment |
| 7 | AMBL-001 | 2 | MRI Breast |
| 8 | Pedro Example | Various | Complex RT-STRUCT |

### TEST 9: DICOM SEG → NIfTI

Extract segmentations from DICOM SEG to NIfTI:
- Uses `itkimage -t nifti` command
- Generates separate files for each segment
- Includes JSON file with metadata

### TEST 10: Cross-Validation

Comparison between conversion paths:
```
Path A: RT-STRUCT → DICOM SEG → NIfTI
Path B: RT-STRUCT → NIfTI (direct)
```

**Results**: Dice coefficient = 1.0000 (identical)

### TEST 11: Round-Trip with Dice

Round-trip conversion: **DICOM SEG → NIfTI → DICOM SEG**

**Process:**
1. Extract NIfTI from DICOM SEG (`itkimage -t nifti`)
2. Correct metadata (`algorithm_name_correction.py`)
3. Re-convert to DICOM SEG (`dicomseg`)
4. Calculate Dice coefficient

**Results:**

| Dataset | Segments | Dice Coefficient | Status |
|---------|----------|------------------|--------|
| AMBL-001 | 2 | 1.0000 | ✅ PASS |
| AMBL-004 | 1 | 1.0000 | ✅ PASS |
| LUNG1-001 | 4 | N/A* | ✅ PASS |
| interobs05 | 10 | 0.9987 | ✅ PASS |

*LUNG1-001 creates separate files for overlapping segments

### TEST 12: Batch Round-Trip Processing

Batch processing of multiple round-trip extractions using CSV file:

**Process:**
1. Create CSV with multiple DICOM SEG files
2. Run batch extraction with 3 parallel workers
3. Verify all datasets extracted successfully
4. Check batch processing log

**Datasets processed:**
- AMBL-001 (2 segments, merged)
- AMBL-004 (1 segment, merged)
- interobs05 (10 segments, separate files)

**Features tested:**
- Parallel processing with `--workers 3`
- CSV-based batch configuration
- Logging with `--log-file`
- Continue-on-error handling

**Example CSV format:**
```csv
id,input,orientation,output
ambl001,/data/.../seg.dcm,False,/output/batch_roundtrip/ambl001
ambl004,/data/.../seg.dcm,False,/output/batch_roundtrip/ambl004
```

**Results:** All 3 datasets extracted successfully in batch mode

### TEST 13: Visualization (Optional)

Generate comparative images (requires image.nii.gz file):
- Comparison of axial, sagittal, coronal views
- Overlay of original vs converted segmentations

**Note**: Currently commented out in automated tests.

## 🔧 Main Files and Scripts

### Test Scripts

- **`quick_test.sh`**: Build + complete tests (recommended)
- **`run_container_tests.sh`**: Complete suite (24 tests)
- **`test_container_validation.py`**: Automatic output validation

### Validation Scripts

- **`roundtrip_validation.py`**: Dice coefficient calculation for round-trip
  - Loads original and re-converted DICOM SEG
  - Calculates Dice for each segment
  - Generates JSON report
  
- **`visualization_comparison.py`**: Visualization comparisons
  - Multi-view (axial, sagittal, coronal)
  - Segmentation overlay
  - PNG image saving

- **`algorithm_name_correction.py`**: Metadata correction
  - Adds missing SegmentAlgorithmName
  - Required for step 2 of round-trip

## 📁 Output Structure

```
tests/
├── test_output/
│   ├── TEST_5_LUNG1-001/              # Test 5 output
│   │   ├── seg.dcm                    # Generated DICOM SEG
│   │   └── logs/
│   ├── TEST_10_cross_conversion/      # Test 10 output
│   │   ├── pathA/
│   │   │   ├── seg.dcm
│   │   │   └── *.nii.gz
│   │   └── pathB/
│   │       └── *.nii.gz
│   └── roundtrip/                     # Round-trip test output
│       ├── ambl001_image.nii.gz       # Original DICOM images (for overlay)
│       ├── ambl001_step1/             # Extracted segmentation NIfTI
│       ├── ambl001_pathA/             # Original merged segmentation
│       ├── ambl001_roundtrip.dcm      # Re-converted DICOM SEG
│       ├── ambl001_final/             # Final extracted segmentation
│       ├── ambl004_image.nii.gz       # AMBL-004 images
│       ├── ambl004_step1/
│       ├── lung1001_image.nii.gz      # LUNG1-001 images
│       ├── lung1001_step1/
│       ├── interobs05_image.nii.gz    # interobs05 images
│       └── interobs05_step1/
```

## 🎯 Important Commands

### Manual Round-Trip

To execute a complete manual round-trip with image overlay:

```bash
# Step 0: Convert original DICOM images to NIfTI (for overlay visualization)
docker run --rm -v $(pwd)/DATA:/data dicomconverter:test-20251104 \
    dicom2nifti \
    -i /data/DCM/ID_1 \
    -o /data/step0_image/image.nii.gz

# Step 1: Extract NIfTI from DICOM SEG
docker run --rm -v $(pwd)/DATA:/data dicomconverter:test-20251104 \
    itkimage -t nifti \
    --inputDICOM /data/seg.dcm \
    --outputDirectory /data/step1_nifti

# Step 2: Correct metadata
docker run --rm -v $(pwd)/DATA:/data dicomconverter:test-20251104 \
    python3 /usr/dicomconverter/tests/algorithm_name_correction.py \
    /data/step1_nifti

# Step 3: Re-convert to DICOM SEG
# (for each NIfTI + JSON file)
docker run --rm -v $(pwd)/DATA:/data dicomconverter:test-20251104 \
    dicomseg \
    --inputImageList /data/step1_nifti/1.nii.gz \
    --inputDICOMDirectory /data/DCM/ID_1 \
    --inputMetadata /data/step1_nifti/1-meta.json \
    --outputDICOM /data/step3_reconverted/1.dcm

# Step 4: Calculate Dice
python3 roundtrip_validation.py \
    /data/seg.dcm \
    /data/step3_reconverted/1.dcm \
    --output-dir /data/step4_validation

# Optional: Load image.nii.gz and segmentation NIfTI files in viewer for overlay
```

### Manual Cross-Validation

```bash
# Path A: RT-STRUCT → DICOM SEG → NIfTI
docker run --rm -v $(pwd)/DATA:/data dicomconverter:test-20251104 \
    rtstruct2seg -d /data/DCM -i /data/rtstruct.dcm -o /data/pathA/seg.dcm

docker run --rm -v $(pwd)/DATA:/data dicomconverter:test-20251104 \
    itkimage -t nifti \
    --inputDICOM /data/pathA/seg.dcm \
    --outputDirectory /data/pathA/nifti

# Path B: RT-STRUCT → NIfTI (direct, if supported)
# Compare with Dice
python3 roundtrip_validation.py \
    /data/pathA/nifti/1.dcm \
    /data/pathB/1.nii.gz \
    --output-dir /data/comparison
```

## 🔍 Results Interpretation

### Dice Coefficient

The Dice coefficient measures overlap between two segmentations:

```
Dice = 2 × |A ∩ B| / (|A| + |B|)
```

**Values:**
- **1.0000**: Perfect (identical)
- **≥ 0.95**: Excellent (round-trip threshold)
- **≥ 0.90**: Good (cross-validation threshold)
- **< 0.90**: Requires investigation

### Geometric Validation

4 automatic checks with configurable tolerances:

| Parameter | Description | Default Tolerance |
|-----------|-------------|-------------------|
| Size | Dimensions (x,y,z) | Exact |
| Spacing | Voxel spacing (mm) | 0.01 mm |
| Origin | Coordinate origin (mm) | 0.1 mm |
| Direction | Axis orientation | 0.01 |

## ⚠️ Important Notes

### Correct Commands

**✅ CORRECT:**
```bash
# NIfTI extraction
itkimage -t nifti --inputDICOM seg.dcm --outputDirectory output/

# NIfTI → DICOM SEG conversion
dicomseg --inputImageList 1.nii.gz --inputDICOMDirectory DCM/ ...
```

**❌ WRONG:**
```bash
# DON'T use these commands
itkimage --outputType nifti ...         # Wrong syntax
itkimage2segimage ...                   # Obsolete command
```

### Overlapping Segments

Datasets like LUNG1-001 contain overlapping segments that:
- Are saved in separate DICOM SEG files
- Cannot be merged into a single file
- Require individual validation per segment

### Missing Metadata

The `itkimage -t nifti` command generates JSON without `SegmentAlgorithmName`.  
**Solution**: Use `algorithm_name_correction.py` before step 3.

## 🐛 Troubleshooting

### Tests fail

```bash
# Verify container build
cd /home/mario/Repository/DicomConverter
docker build -t dicomconverter:test-20251104 .

# Verify permissions
chmod +x tests/*.sh

# Detailed log
cd tests
./run_container_tests.sh 2>&1 | tee test.log
```

### Low Dice coefficient

```bash
# Verify file geometry
python3 -c "
import SimpleITK as sitk
img1 = sitk.ReadImage('file1.dcm')
img2 = sitk.ReadImage('file2.dcm')
print('Size:', img1.GetSize(), img2.GetSize())
print('Spacing:', img1.GetSpacing(), img2.GetSpacing())
print('Origin:', img1.GetOrigin(), img2.GetOrigin())
"
```

### Files not found

```bash
# Verify data structure
ls -R DATA/EucaimShared/Test3/AMBL-001/

# Verify Docker mount
docker run --rm -v $(pwd)/DATA:/data dicomconverter:test-20251104 \
    ls -la /data/EucaimShared/Test3/AMBL-001/
```

## 📚 References

### Main Documentation
- **[`../README.md`](../README.md)**: Container usage guide
- **[`../examples/BATCH_GUIDE.md`](../examples/BATCH_GUIDE.md)**: Batch processing
- **[`../examples/VALIDATION_GUIDE.md`](../examples/VALIDATION_GUIDE.md)**: Geometric validation

### Related Scripts
- **`../src/image_validation.py`**: Geometric validation
- **`../src/dicom_conversion.py`**: Basic conversions
- **`../src/csv_batch.py`**: Batch processing

