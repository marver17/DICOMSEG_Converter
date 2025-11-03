# Container Testing - Quick Reference

## 🚀 Quick Start

```bash
# Build and test in one command
./quick_test.sh
```

## 📋 Test Files

1. **`quick_test.sh`** - One-command build & test
2. **`run_container_tests.sh`** - Comprehensive test suite  
3. **`test_container_validation.py`** - Output validation
4. **`TESTING_GUIDE.md`** - Complete documentation

## 🧪 Manual Testing

### Build Image
```bash
docker build -t dicomconverter:latest .
```

### Run Tests
```bash
./run_container_tests.sh
```

### Validate Outputs
```bash
python test_container_validation.py test_output
```

## ✅ Tests Included

- **Test 1-2**: RTSTRUCT to DICOM SEG conversions
- **Test 3**: DICOM SEG to NIfTI conversion
- **Test 4-5**: Pedro's validated examples (US, CT)
- **Test 6**: Basic RT-STRUCT conversion
- **Test 7**: Image validation module
- **Test 8-9**: Batch processing functionality

## 📊 Test Data

Tests use real data from `DATA/` folder:
- EucaimShared (LUNG1-001, interobs05, AMBL-001)
- PedroShared (RTSTRUCT examples)
- RT-STRUCT (basic examples)

## 📈 Expected Results

- ✅ All tests pass: Container fully functional
- ⊗ Some skipped: Missing optional test data (OK)
- ✗ Tests fail: Check logs in `test_output/`

## 🔍 Output Structure

```
test_output/
├── test_log_*.txt           # Detailed test log
├── test1_lung_seg.dcm       # RTSTRUCT conversions
├── test2_interobs_seg.dcm
├── test4_pedro_us_seg.dcm
├── test5_pedro_ct_seg.dcm
├── test6_basic_rt_seg.dcm
└── validation_report.json   # Validation results
```

## 📖 Full Documentation

See [`TESTING_GUIDE.md`](TESTING_GUIDE.md) for:
- Detailed test descriptions
- Troubleshooting guide
- Advanced usage
- CI/CD integration

## 🆘 Troubleshooting

### Tests fail?
1. Check `test_output/test_log_*.txt`
2. Verify DATA/ folder structure
3. Ensure Docker is running

### Build fails?
```bash
# Check Dockerfile syntax
docker build --no-cache -t dicomconverter:latest .
```

### Validation fails?
```bash
# Install dependencies
pip install pydicom SimpleITK
```

