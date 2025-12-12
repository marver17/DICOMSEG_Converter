# Test Suite - DICOM Converter

Complete documentation for the DICOM Converter test suite.

## 📋 Overview

The test suite includes 26+ automated tests that validate:
- Basic conversions (RT-STRUCT, DICOM SEG, NIfTI)
- Round-trip conversions with Dice coefficient
- Cross-validation between conversion paths
- Geometric validation (size, spacing, origin, direction)
- **NEW:** Visual comparison images for roundtrip validation

## 🔧 Test Data Setup

**IMPORTANT:** Test data is required before running tests.

### Automatic Setup (Recommended)

```bash
cd tests
./setup_test_data.sh
```

This script checks if test data is available and provides instructions for downloading from Google Drive if needed.

### Manual Download

If automatic setup doesn't work, download test data manually:

**Google Drive Link:** https://drive.google.com/drive/folders/1FLlLN9bGlhCPa6_jy_l3aje10lnNPRsk?usp=drive_link

**Expected directory structure:**
```
DATA/
├── EucaimShared/
│   ├── Test1/           # LUNG1-001 (CT)
│   ├── Test2/           # interobs05 (CT)
│   └── Test3/           # AMBL-001, AMBL-004 (MRI)
└── PedroShared/         # Optional RT-STRUCT examples
    ├── EUCAIM_example_RTSTRUCT_001/
    └── EUCAIM_example_RTSTRUCT_002/
```

Extract the downloaded data to `/home/mario/Repository/DicomConverter/DATA/`.

## 🚀 Quick Execution

### Complete Test (Recommended)

```bash
cd tests
./quick_test.sh
```

This script:
0. Checks/downloads test data automatically
1. Builds the Docker container from the main directory
2. Executes all tests automatically
3. Generates detailed report with results
4. Generates visual comparison images for roundtrip tests

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
5. **NEW:** Generate visual comparison images

**Results:**

| Dataset | Segments | Dice Coefficient | Visual Images | Status |
|---------|----------|------------------|---------------|--------|
| AMBL-001 | 2 | 1.0000 | ✅ 5 slices | ✅ PASS |
| AMBL-004 | 1 | 1.0000 | ✅ 5 slices | ✅ PASS |
| LUNG1-001 | 4 | N/A* | ✅ 5 slices | ✅ PASS |
| interobs05 | 10 | 0.9987 | ✅ 5 slices | ✅ PASS |

*LUNG1-001 creates separate files for overlapping segments

### 🎨 Visual Comparison (NEW)

For each successful roundtrip test, the suite automatically generates visual comparison images:

**What it does:**
- Compares **original DICOM SEG** vs **reconverted DICOM SEG** side-by-side
- Selects 5 representative slices where segmentation is present
- Creates PNG images with colored overlay on CT/MRI images
- Shows pixel count statistics for each slice

**Output Location:**
```
test_output/
└── roundtrip/
    ├── ambl001_visual_comparison/
    │   ├── slice_028_comparison.png
    │   ├── slice_030_comparison.png
    │   ├── slice_032_comparison.png
    │   ├── slice_146_comparison.png
    │   └── slice_148_comparison.png
    ├── ambl004_visual_comparison/
    ├── lung1_visual_comparison/
    └── interobs05_visual_comparison/
```

**Image Format:**
```
┌─────────────────────────────────────┐
│  Slice 45/134                       │
├──────────────────┬──────────────────┤
│  Original SEG    │  Reconverted SEG │
│  [CT + overlay]  │  [CT + overlay]  │
│  1234 pixels     │  1230 pixels     │
└──────────────────┴──────────────────┘
        Difference: 0.32%
```

**How to view:**
- Open PNG files with any image viewer
- Compare visually for quality assessment
- Verify segmentation boundaries are preserved

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

## 📊 Test Reports

### HTML Interactive Report (NEW)

After running tests, an interactive HTML report is automatically generated with:

**Features:**
- 📈 Summary statistics (Total/Passed/Failed tests)
- 🎨 Visual comparison galleries with embedded images
- ✅ Detailed per-test results with status indicators
- 📁 Links to detailed logs and validation reports
- 🖼️ Click-to-zoom functionality for comparison images

**Location:**
```
test_output/test_report.html
```

**How to view:**
```bash
# Open in default browser
xdg-open test_output/test_report.html

# Or with specific browser
firefox test_output/test_report.html
```

**Screenshot:**
```
╔═══════════════════════════════════════════════╗
║   DicomConverter Test Report                  ║
╠═══════════════════════════════════════════════╣
║                                               ║
║  📊 Summary:  26 Total  |  24 Passed  | 2 Failed ║
║                                               ║
║  🎨 Visual Comparisons (Roundtrip Tests)      ║
║  ┌─────────────┬─────────────┬─────────────┐ ║
║  │ AMBL-001    │ AMBL-004    │ LUNG1-001   │ ║
║  │ [images]    │ [images]    │ [images]    │ ║
║  └─────────────┴─────────────┴─────────────┘ ║
║                                               ║
║  ✅ Test Results:                             ║
║  ├─ ✓ AMBL-001 - Step 1: DICOM SEG → NIfTI  ║
║  ├─ ✓ AMBL-001 - Step 2: NIfTI → DICOM SEG  ║
║  ├─ ✓ AMBL-001 - Step 4: Dice=1.0000        ║
║  └─ ✓ AMBL-001 - Visual comparison (5 imgs) ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

### Other Reports

- **Text Log:** `test_output/test_log_TIMESTAMP.txt` - Detailed execution trace with timestamps
- **JSON Report:** `test_output/validation_report.json` - Structured validation results (if generated)
- **Console Output:** Real-time color-coded test results during execution

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

