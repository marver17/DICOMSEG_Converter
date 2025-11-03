# Container Testing Guide

## Overview

This document describes the comprehensive test suite for the DicomConverter Docker container. The tests validate all conversion functionalities using real data from the `DATA/` folder.

## Test Files

1. **`run_container_tests.sh`** - Main test runner (bash script)
   - Runs all conversion tests
   - Tests basic functionality
   - Tests batch processing
   - Generates test logs

2. **`test_container_validation.py`** - Output validation (Python script)
   - Validates DICOM file structure
   - Checks DICOM SEG segments
   - Generates detailed reports
   - Creates JSON validation results

## Prerequisites

### For Running Tests
- Docker installed and running
- DicomConverter image built
- DATA/ folder with test data present

### For Validation (Optional)
```bash
pip install pydicom SimpleITK
```

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t dicomconverter:latest .
```

### 2. Run All Tests

```bash
./run_container_tests.sh
```

Or specify a custom image name:
```bash
./run_container_tests.sh my-dicom-converter:v1.0
```

### 3. Validate Outputs

```bash
python test_container_validation.py test_output
```

## Test Coverage

### Test 0: Basic Functionality
- ✅ Container information command
- ✅ Container help command

### Test 1: RTSTRUCT Conversion (LUNG1-001)
- **Input**: LUNG1-001 CT series + RTSTRUCT
- **Output**: DICOM SEG file
- **Tests**: Basic RTSTRUCT to SEG conversion

### Test 2: RTSTRUCT with Structures (interobs05)
- **Input**: interobs05 CT series + RTSTRUCT with multiple structures
- **Output**: DICOM SEG with multiple segments
- **Tests**: Complex RTSTRUCT conversion

### Test 3: DICOM SEG to NIfTI (AMBL-001)
- **Input**: AMBL-001 DICOM SEG
- **Output**: NIfTI files
- **Tests**: SEG to NIfTI conversion (itkimage2)

### Test 4: Pedro's US Example (RTSTRUCT_001)
- **Input**: Ultrasound series + RTSTRUCT
- **Output**: DICOM SEG
- **Tests**: Multi-modality support (US)

### Test 5: Pedro's CT Example (RTSTRUCT_002)
- **Input**: CT series + RTSTRUCT
- **Output**: DICOM SEG
- **Tests**: Pedro's validated test case

### Test 6: Basic RT-STRUCT
- **Input**: Basic RT-STRUCT example
- **Output**: DICOM SEG
- **Tests**: Minimal RT-STRUCT conversion

### Test 7: Image Validation
- **Tests**: Validation module functionality
- **Checks**: Help command, basic validation

### Test 8: Batch Processing
- **Tests**: Batch CSV processing
- **Checks**: Dry-run mode, CSV parsing

### Test 9: CSV Batch Helper
- **Tests**: CSV batch helper directly
- **Checks**: Help command, basic functionality

## Test Data Structure

The tests use data from `DATA/` folder:

```
DATA/
├── EucaimShared/
│   ├── Test1/LUNG1-001/          # RTSTRUCT test
│   ├── Test2/interobs05/          # Complex RTSTRUCT
│   └── Test3/AMBL-001/            # DICOM SEG
├── PedroShared/
│   ├── EUCAIM_example_RTSTRUCT_001/  # US example
│   └── EUCAIM_example_RTSTRUCT_002/  # CT/MR examples
└── RT-STRUCT/                     # Basic examples
```

## Output Structure

Tests create outputs in `test_output/`:

```
test_output/
├── test_log_YYYYMMDD_HHMMSS.txt  # Detailed test log
├── test1_lung_seg.dcm             # Test 1 output
├── test2_interobs_seg.dcm         # Test 2 output
├── test3_ambl001_nifti/           # Test 3 outputs (multiple files)
├── test4_pedro_us_seg.dcm         # Test 4 output
├── test5_pedro_ct_seg.dcm         # Test 5 output
├── test6_basic_rt_seg.dcm         # Test 6 output
├── test_batch.csv                 # Batch test CSV
└── validation_report.json         # Validation results
```

## Understanding Test Results

### Test Runner Output

```
[TEST 1] Test Name
----------------------------------------
✓ PASSED - Output created: /path/to/output.dcm

[TEST 2] Test Name
✗ FAILED - Command failed with exit code 1

⊗ SKIPPED - Test data not found
```

### Final Summary

```
====================================
TEST SUMMARY
====================================
Total Tests:  9
Passed:       7
Failed:       0

✓ ALL TESTS PASSED!
```

### Validation Report

The validation script provides:
- File existence checks
- DICOM structure validation
- DICOM SEG segment analysis
- File size information
- Segment labels and counts

## Troubleshooting

### Issue: "Docker image not found"
```bash
# Build the image first
docker build -t dicomconverter:latest .
```

### Issue: "DATA folder not found"
```bash
# Ensure you run tests from repository root
cd /path/to/DicomConverter
./run_container_tests.sh
```

### Issue: "Test data not found" (tests skipped)
- Some test data might not be present
- Skipped tests won't affect overall pass/fail
- Check DATA/ folder structure

### Issue: "Permission denied"
```bash
# Make scripts executable
chmod +x run_container_tests.sh
chmod +x test_container_validation.py
```

### Issue: "Container failed to start"
- Check Docker daemon is running
- Check image was built successfully
- Check for port conflicts if using ports

## Advanced Usage

### Run Specific Tests Only

Edit `run_container_tests.sh` and comment out tests you don't want:

```bash
# Comment out tests
# run_test "Test Name" "command" "output"
```

### Test with Different Data

1. Add your data to `DATA/` folder
2. Add new test to `run_container_tests.sh`:

```bash
run_test "My Custom Test" \
    "docker run --rm \
        -v \"$DATA_DIR:/data:ro\" \
        -v \"$OUTPUT_DIR:/output\" \
        $DOCKER_IMAGE \
        rtstruct2seg \
        /data/my_data/dicom \
        /data/my_data/rtstruct.dcm \
        /output/my_output.dcm" \
    "$OUTPUT_DIR/my_output.dcm"
```

### Custom Validation

Add custom checks to `test_container_validation.py`:

```python
# Add to main() function
validator.validate_dicom_seg("my_output.dcm", "My Custom Test")
```

### Batch Testing

Create a CSV with multiple test cases:

```csv
id,input1,input2,output
case1,/data/patient1/ct,/data/patient1/rt.dcm,/output/case1.dcm
case2,/data/patient2/ct,/data/patient2/rt.dcm,/output/case2.dcm
```

Run batch test:

```bash
docker run --rm \
  -v $(pwd)/DATA:/data:ro \
  -v $(pwd)/test_output:/output \
  dicomconverter:latest \
  batch rtstruct2seg \
  --csv /output/my_batch.csv \
  --workers 2 \
  --log-file /output/batch_log.csv
```

## Continuous Integration

### Example GitHub Actions Workflow

```yaml
name: Container Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t dicomconverter:test .
      
      - name: Run tests
        run: ./run_container_tests.sh dicomconverter:test
      
      - name: Validate outputs
        run: |
          pip install pydicom SimpleITK
          python test_container_validation.py test_output
      
      - name: Upload test artifacts
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_output/
```

## Performance Benchmarks

Typical test execution times (approximate):

- Container startup: ~1-2 seconds
- RTSTRUCT conversion: ~5-15 seconds
- DICOM SEG conversion: ~10-30 seconds
- Batch processing (3 files): ~30-60 seconds
- Full test suite: ~2-5 minutes

## Expected Results

All tests should pass on a properly configured system. Common pass rates:

- ✅ 100% - All data present, all conversions supported
- ✅ 90%+ - Some test data missing (skipped tests)
- ⚠️ 80%- - Check for missing dependencies or data issues
- ❌ <50% - Container configuration problem

## Support

If tests fail:

1. Check Docker logs: `docker logs <container_id>`
2. Check test log: `test_output/test_log_*.txt`
3. Run validation: `python test_container_validation.py test_output`
4. Check DATA/ folder structure
5. Verify all dependencies in Dockerfile

## Credits

Test suite developed to validate conversions using:
- EUCAIM project test data
- Pedro's validated examples (Perproglio dataset)
- Basic RT-STRUCT examples

Validation approach based on Pedro's geometry checks (size, spacing, origin, direction).
