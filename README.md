# EUCAIM DICOM CONVERT
Complete system for DICOM file conversion with support for round-trip conversions, batch processing, and geometric validation.

> ⚠️ **SECURITY NOTICE**: This repository has undergone a comprehensive security assessment. See [QUICK_START_SECURITY.md](QUICK_START_SECURITY.md) for critical vulnerabilities and fixes. **Not production-ready** until P0 fixes are applied.

## 📋 Overview

This project provides Docker-based tools to convert DICOM files between different formats:

- **RT-STRUCT → DICOM SEG**: Convert RT structures to DICOM segmentations
- **DICOM SEG → NIfTI**: Extract segmentations to NIfTI format
- **NIfTI → DICOM SEG**: Convert NIfTI segmentations to DICOM SEG
- **DICOM → NIfTI**: Convert DICOM series to NIfTI volumes
- **Validated round-trip**: DICOM SEG → NIfTI → DICOM SEG with Dice coefficient verification
- **Batch Processing**: Parallel processing of multiple conversions via CSV

## 🏗️ Project Structure

```
DicomConverter/
├── src/
│   ├── dicom_conversion.py          # Main conversion script
│   ├── csv_batch.py                 # CSV batch processor
│   ├── image_validation.py          # Geometric validation
│   ├── nifti/                       # NIfTI conversion modules
│   └── rtstruct/                    # RT-STRUCT conversion modules
├── examples/
│   ├── batch_*.csv                  # Example CSV files
│   ├── BATCH_GUIDE.md               # Batch processing guide
│   └── VALIDATION_GUIDE.md          # Geometric validation guide
├── tests/
│   ├── README.md                    # Test suite documentation
│   ├── run_container_tests.sh       # Complete test suite (26 tests)
│   ├── roundtrip_validation.py      # Round-trip validation with Dice
│   └── quick_test.sh                # Quick test (build + run)
├── DATA/                             # Test data (EUCAIM, RT-STRUCT)
└── Dockerfile
```

## 🚀 Quick Start

### 1. Download Test Data

Before running conversions, download the test datasets from Google Drive:

**📥 [Download Test Data from Google Drive]()**

After downloading, extract the data into the `DATA/` directory:

```bash
# Extract downloaded data
unzip downloaded_data.zip -d DATA/

# Verify structure
ls -la DATA/
# Expected: EucaimShared/ and PedroShared/ directories
```

The test data includes:
- **EUCAIM datasets**: DICOM SEG samples for round-trip validation (AMBL-001, AMBL-004, LUNG1-001, interobs05)
- **RT-STRUCT examples**: RT structures with MR/CT images for conversion testing

### 2. Build the Container

```bash
docker build -t dicomconverter:latest .
```

### 2. Basic Conversions

#### RT-STRUCT → DICOM SEG

```bash
docker run --rm -v $(pwd)/DATA:/data dicomconverter:latest \
    rtstruct2seg \
    -d /data/PedroShared/EUCAIM_example_RTSTRUCT_001/MR/T2 \
    -i /data/PedroShared/EUCAIM_example_RTSTRUCT_001/RTSTRUCT/RS.dcm \
    -o /data/output/seg.dcm
```

#### DICOM SEG → NIfTI (Extraction)

```bash
docker run --rm -v $(pwd)/DATA:/data dicomconverter:latest \
    itkimage \
    -t nifti \
    --inputDICOM /data/RT-STRUCT/seg.dcm \
    --outputDirectory /data/output
```

**⚠️ Important**: Always use `-t nifti` to extract segmentations to NIfTI format.

#### NIfTI → DICOM SEG

```bash
docker run --rm -v $(pwd)/DATA:/data dicomconverter:latest \
    dicomseg \
    --inputImageList /data/output/1.nii.gz \
    --inputDICOMDirectory /data/DCM/ID_1 \
    --inputMetadata /data/output/meta.json \
    --outputDICOM /data/output/seg_from_nifti.dcm
```

**⚠️ Important**: The `dicomseg` command requires a JSON file with segment metadata.

#### DICOM → NIfTI (Volume)

```bash
docker run --rm -v $(pwd)/DATA:/data dicomconverter:latest \
    dicom2nifti \
    -i /data/EucaimShared/Test1/LUNG1-001/09-18-2008-StudyID-NA-69331 \
    -o /data/output/volume.nii.gz
```

### 3. Batch Processing

Process multiple conversions in parallel from CSV files.

#### Overview

The batch mode allows you to:
- Process multiple conversions from a CSV file
- Run conversions in parallel with multiple workers
- Perform dry-runs to preview commands
- Generate detailed logs
- Handle errors gracefully with continue-on-error mode

#### CSV Format

Each conversion type requires specific columns in the CSV file:

**RTSTRUCT to DICOM SEG (`rtstruct2seg`)**

Required columns: `input1` (DICOM series dir), `input2` (RTSTRUCT file)  
Optional: `output`, `id`, `extra_args`

```csv
id,input1,input2,output
patient_001,/data/patient001/CT,/data/patient001/RT/structures.dcm,/data/output/patient001_seg.dcm
patient_002,/data/patient002/CT,/data/patient002/RT/structures.dcm,
```

**Volume to DICOM SEG (`dicomseg`)**

Required: `inputImageList`, `inputDICOMDirectory`, `outputDICOM`, `inputMetadata`

```csv
id,inputImageList,inputDICOMDirectory,outputDICOM,inputMetadata
seg_001,/data/seg/patient001.nii.gz,/data/dicom/patient001,/data/output/patient001_seg.dcm,/data/metadata/patient001.json
```

**DICOM to NIfTI (`dicom2nifti`)**

Required: `input` (DICOM series dir)  
Optional: `output`, `id`

```csv
id,input,output
nifti_001,/data/dicom/patient001,/data/nifti/patient001.nii.gz
```

**DICOM SEG to NIfTI (`itkimage2`)**

Required: `input` (DICOM SEG file)  
Optional: `orientation`, `output`, `id`

```csv
id,input,orientation,output
seg2nii_001,/data/dicomseg/patient001.dcm,True,/data/nifti/patient001
```

#### Usage Examples

**Basic sequential processing:**

```bash
docker run --rm -v $(pwd):/workspace dicomconverter:latest \
    batch /workspace/examples/batch_rtstruct2seg.csv \
    --output-dir /workspace/output
```

**Parallel processing with 4 workers:**

```bash
docker run --rm -v $(pwd):/workspace dicomconverter:latest \
    batch /workspace/examples/batch_rtstruct2seg.csv \
    --workers 4 \
    --log-file /workspace/batch.log
```

**Dry run (preview commands):**

```bash
docker run --rm -v $(pwd):/workspace dicomconverter:latest \
    batch /workspace/examples/batch_rtstruct2seg.csv \
    --dry-run
```

**Continue on error:**

```bash
docker run --rm -v $(pwd):/workspace dicomconverter:latest \
    batch /workspace/examples/batch_rtstruct2seg.csv \
    --workers 4 \
    --continue-on-error \
    --log-file /workspace/batch.log
```

#### Available Options

```
--csv FILE              CSV file with batch jobs (required)
--output-dir DIR        Base output directory
--workers N             Number of parallel workers (default: 1)
--dry-run               Print commands without executing
--continue-on-error     Continue if jobs fail
--timeout SECONDS       Timeout per job (0 = no timeout)
--log-file FILE         Write detailed log
--verbose, -v           Verbose output
```

#### Tips and Best Practices

1. **Start with dry-run**: Always test your CSV with `--dry-run` first
2. **Use absolute paths**: Avoid confusion with relative paths
3. **Parallel processing**: Start with 2-4 workers, adjust based on system capacity
4. **Logging**: Use `--log-file` for production runs to track operations
5. **Error handling**: Use `--continue-on-error` for large batches
6. **Timeout**: Set reasonable timeouts (300-600 seconds) to prevent hanging

**Example CSV files available in:** `examples/batch_*.csv`

## 🔄 Round-Trip and Validation

### Round-Trip Conversion

The system supports validated round-trip conversions with Dice coefficient:

```
DICOM SEG → NIfTI → DICOM SEG (with Dice ≥ 0.95 verification)
```

**Round-trip process:**
0. **Convert DICOM images to NIfTI** (for overlay visualization with segmentations)
1. Extract segmentations from DICOM SEG to NIfTI (`itkimage -t nifti` command)
2. Add missing metadata with `algorithm_name_correction.py`
3. Re-convert NIfTI files to DICOM SEG (`dicomseg` command)
4. Calculate Dice coefficient between original and re-converted DICOM SEG

**Overlay visualization:**

The round-trip process now includes conversion of the original DICOM images to NIfTI format. This allows you to:
- Load both the image and segmentation NIfTI files in viewers like ITK-SNAP or 3D Slicer
- Visually verify segmentation overlay on the original images
- Compare original vs round-trip segmentations side-by-side

**Example files generated:**
- `ambl001_image.nii.gz` - Original DICOM images converted to NIfTI
- `ambl001_step1/*.nii.gz` - Segmentation files from DICOM SEG
- `ambl001_final/*.nii.gz` - Segmentation files after round-trip

### Geometric Validation

Each conversion includes automatic validation on 4 parameters:

1. **Size**: Image dimensions (x, y, z)
2. **Spacing**: Voxel spacing (mm)
3. **Origin**: Coordinate system origin (mm)
4. **Direction**: Axis orientation

**Validation example:**

```bash
docker run --rm -v $(pwd)/DATA:/data dicomconverter:latest \
    python3 /usr/dicomconverter/src/image_validation.py \
    --segmentation /data/seg.nii.gz \
    --reference /data/image.nii.gz \
    --tolerance-spacing 0.01 \
    --tolerance-origin 0.1
```

**See [`examples/VALIDATION_GUIDE.md`](examples/VALIDATION_GUIDE.md) for complete documentation.**

## 🧪 Testing

### Quick Test (Recommended)

```bash
cd tests
./quick_test.sh
```

Automatically executes:
1. Docker container build
2. All 26 tests
3. Output validation
4. Final report

### Complete Suite

```bash
cd tests
./run_container_tests.sh
```

**Available tests:**
- **Test 1-4**: Basic conversions and help
- **Test 5-8**: RT-STRUCT → DICOM SEG (4 real datasets)
- **Test 9**: DICOM SEG → NIfTI
- **Test 10**: Cross-validation between conversion paths
- **Test 11**: Round-trip with Dice coefficient (4 datasets)
- **Test 12**: Batch round-trip processing (3 workers, 3 datasets)
- **Test 13**: Visualization comparisons (optional)

**Round-trip results:**
- AMBL-001: Dice 1.0000 (2 segments)
- AMBL-004: Dice 1.0000 (1 segment)
- LUNG1-001: Round-trip OK (4 segments)
- interobs05: Round-trip OK (10 segments)

**See [`tests/README.md`](tests/README.md) for complete test documentation.**

## 📊 Supported Formats

### Input
- **DICOM**: DICOM series, RT-STRUCT, DICOM SEG
- **ITK Images**: NIfTI (.nii, .nii.gz), NRRD (.nrrd), MetaImage (.mha, .mhd)

### Output
- **DICOM SEG**: Segmentations in DICOM format
- **NIfTI**: Volumes and segmentations (.nii.gz)

## 📝 Main Commands

### Available Modes

```bash
docker run --rm dicomconverter:latest <mode> [options]
```

**Modes:**
- `rtstruct2seg` - Convert RT-STRUCT to DICOM SEG
- `itkimage` - Extract segmentations from DICOM SEG (`-t nifti`)
- `dicomseg` - Convert NIfTI to DICOM SEG
- `dicom2nifti` - Convert DICOM series to NIfTI
- `batch` - Process CSV file with multiple conversions

### Batch Processing Options

```bash
--workers N          Number of parallel processes (default: 1)
--dry-run            Show commands without executing
--log-file FILE      Save log to file
--continue-on-error  Continue even if errors occur
```

### Validation Options

```bash
--tolerance-spacing FLOAT    Tolerance for spacing (default: 0.01 mm)
--tolerance-origin FLOAT     Tolerance for origin (default: 0.1 mm)
--tolerance-direction FLOAT  Tolerance for direction (default: 0.01)
--resample                   Enable automatic resampling
--interpolation METHOD       Method: nearest, linear, bspline (default: nearest)
```

## 🛠️ Main Dependencies

- **Python 3.9+**
- **SimpleITK**: Image manipulation and validation
- **pydicom**: DICOM read/write
- **dcmqi**: DICOM-QI conversion tools
- **plastimatch**: RT-STRUCT conversion
- **Miniconda**: Environment management

## 📚 Documentation

### Guides
- **[`examples/BATCH_GUIDE.md`](examples/BATCH_GUIDE.md)**: Batch processing guide with CSV format
- **[`examples/VALIDATION_GUIDE.md`](examples/VALIDATION_GUIDE.md)**: Geometric validation guide
- **[`tests/README.md`](tests/README.md)**: Complete test suite documentation

### Example Files
- **`examples/batch_*.csv`**: Example CSV files for each mode
- **`examples/validation_examples.py`**: Practical validation examples

## 🐛 Troubleshooting

### Container won't start

```bash
# Check build logs
docker build -t dicomconverter:latest . 2>&1 | tee build.log

# Test help command
docker run --rm dicomconverter:latest rtstruct2seg --help
```

### Conversion errors

```bash
# Enable detailed logging
docker run --rm -v $(pwd)/DATA:/data dicomconverter:latest \
    rtstruct2seg -i /data/input.dcm -d /data/dicom -o /data/output.dcm \
    2>&1 | tee conversion.log
```

### Geometric errors

```bash
# Use validation to diagnose
docker run --rm -v $(pwd)/DATA:/data dicomconverter:latest \
    python3 /usr/dicomconverter/src/image_validation.py \
    --segmentation /data/seg.nii.gz \
    --reference /data/ref.nii.gz \
    --verbose
```

## 🔒 Security

This project has undergone a comprehensive security assessment following the EUCAIM risk framework. 

### ⚠️ Current Status: NOT PRODUCTION-READY

**Critical vulnerabilities identified**:
- 🔴 Hardcoded password in Docker container
- 🔴 World-writable log directory (chmod 777)
- 🔴 Command injection risk (eval in bash scripts)
- 🔴 No input path validation
- 🔴 Unverified external dependencies

### 📚 Security Documentation

For detailed information about security issues and fixes:

1. **Quick Start**: [QUICK_START_SECURITY.md](QUICK_START_SECURITY.md) - Overview and immediate actions
2. **Full Report**: [SECURITY_IMPROVEMENTS_RECOMMENDATIONS.md](SECURITY_IMPROVEMENTS_RECOMMENDATIONS.md) - Complete 35+ page analysis
3. **Implementation**: [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) - Step-by-step task tracker
4. **Policy**: [SECURITY.md](SECURITY.md) - Official security policy
5. **Index**: [SECURITY_DOCUMENTATION_INDEX.md](SECURITY_DOCUMENTATION_INDEX.md) - Navigation guide

### 🔧 Secure Build

Use the secure build script with version tracking:

```bash
# Build with security enhancements
./build_secure.sh

# Scan for vulnerabilities
trivy image dicomconverter:latest
```

### 🛡️ Security Features (Post-Fix)

Once security fixes are applied:

- ✅ Non-root container execution
- ✅ Input path validation and sanitization
- ✅ Centralized audit logging (JSON format)
- ✅ Resource limits enforcement
- ✅ Dependency vulnerability scanning
- ✅ Version tracking and integrity verification

### 📋 Before Production Deployment

- [ ] Apply all P0 (critical) fixes from checklist
- [ ] Integrate PathValidator for input validation
- [ ] Enable AuditLogger for compliance
- [ ] Configure resource limits in deployment
- [ ] Run security scan (0 CRITICAL vulnerabilities)
- [ ] Obtain EUCAIM security team approval

See [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) for complete deployment checklist.

## 📄 License

See LICENSE file for details.
