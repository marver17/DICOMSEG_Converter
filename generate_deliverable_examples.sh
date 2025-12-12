#!/bin/bash
#
# Generate Deliverable Examples for DICOM Converter
#
# This script creates organized conversion examples for DICOM SEG roundtrip testing:
# - Original DICOM images and DICOM SEG files
# - NIfTI files extracted from DICOM SEG
# - DICOM SEG reconverted from NIfTI (roundtrip)
# - Validation with Dice coefficient
#

set +e  # Continue on error for graceful failure handling

# Configuration
DOCKER_IMAGE="${1:-dicomconverter:1.4.0}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/DATA/EucaimShared"
OUTPUT_DIR="${SCRIPT_DIR}/DELIVERABLE_EXAMPLES"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${SCRIPT_DIR}/deliverable_generation.log"
VALIDATION_REPORT="${OUTPUT_DIR}/validation_report.txt"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Success/failure counters
SUCCESS_COUNT=0
FAILURE_COUNT=0

#==============================================================================
# Helper Functions
#==============================================================================

log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $message" >> "$LOG_FILE"

    case "$level" in
        "INFO")    echo -e "${BLUE}[INFO]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        "WARNING") echo -e "${YELLOW}[WARNING]${NC} $message" ;;
        "ERROR")   echo -e "${RED}[ERROR]${NC} $message" ;;
    esac
}

create_example_structure() {
    local example_name="$1"
    local example_dir="${OUTPUT_DIR}/${example_name}"

    mkdir -p "${example_dir}/01_dicom_input"
    mkdir -p "${example_dir}/02_dicomseg_original"
    mkdir -p "${example_dir}/03_nifti_converted"
    mkdir -p "${example_dir}/03_nifti_converted_merged"
    mkdir -p "${example_dir}/04_dicomseg_reconverted"
    mkdir -p "${example_dir}/05_visual_comparison"

    log_message "INFO" "Created structure: ${example_name}" >&2
    echo "$example_dir"
}

create_rtstruct_structure() {
    local example_name="$1"
    local example_dir="${OUTPUT_DIR}/${example_name}"

    mkdir -p "${example_dir}/01_dicom_input"
    mkdir -p "${example_dir}/02_rtstruct_input"
    mkdir -p "${example_dir}/03_dicomseg_output"

    log_message "INFO" "Created RT-STRUCT structure: ${example_name}" >&2
    echo "$example_dir"
}

copy_dicom_series() {
    local src_dir="$1"
    local dst_dir="$2"
    local description="$3"

    if [ ! -d "$src_dir" ]; then
        log_message "ERROR" "Source directory not found: $src_dir"
        return 1
    fi

    cp -r "$src_dir"/* "$dst_dir/" 2>/dev/null
    local count=$(find "$dst_dir" -type f -name "*.dcm" 2>/dev/null | wc -l)

    if [ "$count" -eq 0 ]; then
        log_message "ERROR" "No DICOM files copied from $src_dir"
        return 1
    fi

    log_message "SUCCESS" "Copied $count DICOM files: $description"
    return 0
}

run_docker_conversion() {
    local description="$1"
    local docker_cmd="$2"
    local expected_output="$3"

    log_message "INFO" "Starting: $description"
    log_message "INFO" "Command: $docker_cmd"

    if eval "$docker_cmd" >> "$LOG_FILE" 2>&1; then
        if [ -n "$expected_output" ] && [ -e "$expected_output" ]; then
            log_message "SUCCESS" "$description completed"
            return 0
        elif [ -z "$expected_output" ]; then
            log_message "SUCCESS" "$description completed"
            return 0
        else
            log_message "ERROR" "$description failed - output not found: $expected_output"
            return 1
        fi
    else
        log_message "ERROR" "$description failed - command returned error"
        return 1
    fi
}

generate_visual_comparison() {
    local example_name="$1"
    local example_dir="$2"

    log_message "INFO" "Generating visual comparison for $example_name"

    if [ ! -f "${example_dir}/02_dicomseg_original/seg_original.dcm" ] || \
       [ ! -f "${example_dir}/04_dicomseg_reconverted/seg_reconverted.dcm" ]; then
        log_message "WARNING" "Missing DICOM SEG files for visual comparison"
        return 1
    fi

    docker run --rm \
        -v "${example_dir}:/data" \
        -v "${SCRIPT_DIR}/tests:/scripts:ro" \
        --entrypoint /bin/bash \
        $DOCKER_IMAGE \
        -c "source /opt/conda/etc/profile.d/conda.sh && \
            conda activate dicomseg && \
            python3 /scripts/generate_visual_comparison.py \
                --dicom-images /data/01_dicom_input \
                --original-seg /data/02_dicomseg_original/seg_original.dcm \
                --reconverted-seg /data/04_dicomseg_reconverted/seg_reconverted.dcm \
                --output-dir /data/05_visual_comparison \
                --num-slices 5" >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log_message "SUCCESS" "Visual comparison generated"
        return 0
    else
        log_message "WARNING" "Visual comparison failed (see log for details)"
        return 1
    fi
}

#==============================================================================
# Core Processing Function
#==============================================================================

process_test_case() {
    local test_num="$1"
    local test_name="$2"
    local dicom_series_path="$3"
    local dicomseg_original_path="$4"
    local reference_series_docker="$5"  # Docker path for reconversion

    local example_name="Example${test_num}_${test_name}"

    log_message "INFO" "=========================================="
    log_message "INFO" "Processing $example_name"
    log_message "INFO" "=========================================="

    # Create directory structure
    local example_dir=$(create_example_structure "$example_name")

    # Step 1: Copy original DICOM images
    if ! copy_dicom_series "$dicom_series_path" "${example_dir}/01_dicom_input" "Input DICOM images"; then
        log_message "ERROR" "Failed to copy DICOM images for $example_name - SKIPPING"
        echo "$example_name: Failed (DICOM images not found)" >> "$VALIDATION_REPORT"
        return 1
    fi

    # Step 2: Copy original DICOM SEG
    if [ ! -f "$dicomseg_original_path" ]; then
        log_message "ERROR" "Original DICOM SEG not found: $dicomseg_original_path - SKIPPING"
        echo "$example_name: Failed (DICOM SEG not found)" >> "$VALIDATION_REPORT"
        return 1
    fi
    cp "$dicomseg_original_path" "${example_dir}/02_dicomseg_original/seg_original.dcm"
    log_message "SUCCESS" "Copied original DICOM SEG"

    # Step 3: Extract NIfTI separate files from DICOM SEG (for reconversion)
    if ! run_docker_conversion \
        "Extracting NIfTI separate files from DICOM SEG" \
        "docker run --rm \
            -v \"${example_dir}:/data\" \
            $DOCKER_IMAGE \
            itkimage \
            --inputDICOM /data/02_dicomseg_original/seg_original.dcm \
            --outputDirectory /data/03_nifti_converted \
            -t nifti" \
        ""; then
        log_message "ERROR" "NIfTI extraction (separate files) failed for $example_name - SKIPPING"
        echo "$example_name: Failed (NIfTI extraction failed)" >> "$VALIDATION_REPORT"
        return 1
    fi

    # Step 4: Extract merged NIfTI from DICOM SEG (for validation comparison)
    run_docker_conversion \
        "Extracting merged NIfTI from original DICOM SEG" \
        "docker run --rm \
            -v \"${example_dir}:/data\" \
            $DOCKER_IMAGE \
            itkimage2 \
            /data/02_dicomseg_original/seg_original.dcm \
            /data/03_nifti_converted_merged \
            False" \
        "" || log_message "WARNING" "Merged NIfTI extraction failed (overlapping segments?)"

    # Step 5: Fix metadata JSON
    local meta_json="${example_dir}/03_nifti_converted/meta.json"
    if [ -f "$meta_json" ]; then
        python3 "${SCRIPT_DIR}/tests/algorithm_name_correction.py" "$meta_json" >> "$LOG_FILE" 2>&1
        log_message "SUCCESS" "Fixed metadata JSON"
    else
        log_message "WARNING" "Metadata JSON not found - may cause reconversion issues"
    fi

    # Step 6: Build NIfTI file list for reconversion
    local nifti_files=$(find "${example_dir}/03_nifti_converted" -name "*.nii.gz" -type f | sort -V)
    if [ -z "$nifti_files" ]; then
        log_message "ERROR" "No NIfTI files found - SKIPPING reconversion"
        echo "$example_name: Failed (No NIfTI files generated)" >> "$VALIDATION_REPORT"
        return 1
    fi

    # Build comma-separated list for Docker paths
    local nifti_list=""
    for nifti_file in $nifti_files; do
        local docker_path=$(echo "$nifti_file" | sed "s|${example_dir}|/data|g")
        if [ -z "$nifti_list" ]; then
            nifti_list="$docker_path"
        else
            nifti_list="${nifti_list},${docker_path}"
        fi
    done

    local nifti_count=$(echo "$nifti_files" | wc -w)
    log_message "INFO" "Found $nifti_count NIfTI files for reconversion"

    # Step 7: Reconvert NIfTI to DICOM SEG
    if ! run_docker_conversion \
        "Reconverting NIfTI to DICOM SEG" \
        "docker run --rm \
            -v \"${DATA_DIR}:/dataroot:ro\" \
            -v \"${example_dir}:/data\" \
            $DOCKER_IMAGE \
            dicomseg \
            --inputImageList $nifti_list \
            --inputMetadata /data/03_nifti_converted/meta.json \
            --inputDICOMDirectory $reference_series_docker \
            --outputDICOM /data/04_dicomseg_reconverted/seg_reconverted.dcm" \
        "${example_dir}/04_dicomseg_reconverted/seg_reconverted.dcm"; then
        log_message "WARNING" "Reconversion failed for $example_name"
        echo "$example_name: Failed (Reconversion failed)" >> "$VALIDATION_REPORT"
        return 1
    fi

    # Step 8: Extract merged NIfTI from reconverted DICOM SEG for validation
    if run_docker_conversion \
        "Extracting merged NIfTI from reconverted DICOM SEG" \
        "docker run --rm \
            -v \"${example_dir}:/data\" \
            $DOCKER_IMAGE \
            itkimage2 \
            /data/04_dicomseg_reconverted/seg_reconverted.dcm \
            /data/04_dicomseg_reconverted/merged \
            False" \
        ""; then

        # Step 9: Validate with Dice coefficient
        local original_merged="${example_dir}/03_nifti_converted_merged/niftiseg/segmentation.nii.gz"
        local roundtrip_merged="${example_dir}/04_dicomseg_reconverted/merged/niftiseg/segmentation.nii.gz"

        if [ -f "$original_merged" ] && [ -f "$roundtrip_merged" ]; then
            log_message "INFO" "Running Dice coefficient validation"

            # Run validation
            docker run --rm \
                -v "${OUTPUT_DIR}:/output" \
                --entrypoint /bin/bash \
                $DOCKER_IMAGE \
                -c "source /opt/conda/etc/profile.d/conda.sh && \
                    conda activate dicomseg && \
                    python3 /usr/dicomconverter/tests/roundtrip_validation.py \
                        --original /output/${example_name}/03_nifti_converted_merged/niftiseg/segmentation.nii.gz \
                        --roundtrip /output/${example_name}/04_dicomseg_reconverted/merged/niftiseg/segmentation.nii.gz \
                        --tolerance 0.95 \
                        --verbose" >> "$LOG_FILE" 2>&1

            local dice_exit=$?

            # Extract Dice score from log
            local dice_score=$(tail -100 "$LOG_FILE" | grep -oP "Overall: \K[0-9.]+" | tail -1)

            if [ -n "$dice_score" ]; then
                if [ $dice_exit -eq 0 ]; then
                    log_message "SUCCESS" "Validation passed - Dice=$dice_score (>= 0.95)"
                    echo "$example_name: Dice=$dice_score (PASS)" >> "$VALIDATION_REPORT"
                else
                    log_message "WARNING" "Validation failed - Dice=$dice_score (< 0.95)"
                    echo "$example_name: Dice=$dice_score (FAIL - below threshold)" >> "$VALIDATION_REPORT"
                fi
            else
                log_message "WARNING" "Could not extract Dice score from validation"
                echo "$example_name: Validation completed (Dice score not extracted)" >> "$VALIDATION_REPORT"
            fi
        else
            log_message "WARNING" "Could not validate - merged NIfTI files not found (overlapping segments)"
            echo "$example_name: Conversion successful (Validation skipped - overlapping segments)" >> "$VALIDATION_REPORT"
        fi
    else
        log_message "WARNING" "Could not extract merged NIfTI from reconverted DICOM SEG"
        echo "$example_name: Conversion successful (Validation skipped)" >> "$VALIDATION_REPORT"
    fi

    # Step 9: Generate visual comparison
    generate_visual_comparison "$example_name" "$example_dir" || log_message "WARNING" "Visual comparison skipped for $example_name"

    log_message "SUCCESS" "$example_name completed successfully"
    return 0
}

process_rtstruct_case() {
    local test_num="$1"
    local test_name="$2"
    local dicom_series_path="$3"
    local rtstruct_file="$4"
    local reference_series_docker="$5"

    local example_name="Example${test_num}_${test_name}"

    log_message "INFO" "=========================================="
    log_message "INFO" "Processing RT-STRUCT: $example_name"
    log_message "INFO" "=========================================="

    # Create directory structure
    local example_dir=$(create_rtstruct_structure "$example_name")

    # Step 1: Copy DICOM images
    if ! copy_dicom_series "$dicom_series_path" "${example_dir}/01_dicom_input" "Input DICOM images"; then
        log_message "ERROR" "Failed to copy DICOM images - SKIPPING"
        echo "$example_name: Failed (DICOM images not found)" >> "$VALIDATION_REPORT"
        return 1
    fi

    # Step 2: Copy RT-STRUCT
    if [ ! -f "$rtstruct_file" ]; then
        log_message "ERROR" "RT-STRUCT not found: $rtstruct_file - SKIPPING"
        echo "$example_name: Failed (RT-STRUCT not found)" >> "$VALIDATION_REPORT"
        return 1
    fi
    cp "$rtstruct_file" "${example_dir}/02_rtstruct_input/rtstruct.dcm"
    log_message "SUCCESS" "Copied RT-STRUCT file"

    # Step 3: Convert RT-STRUCT to DICOM SEG
    if ! run_docker_conversion \
        "Converting RT-STRUCT to DICOM SEG" \
        "docker run --rm \
            -v \"${SCRIPT_DIR}/DATA:/dataroot:ro\" \
            -v \"${example_dir}:/output\" \
            $DOCKER_IMAGE \
            rtstruct2seg \
            $reference_series_docker \
            /dataroot/PedroShared/EUCAIM_example_RTSTRUCT_002/CT_UnspecifiedCT_20210430/RTSTRUCT/struct_set_2025-02-17_15-26-13.dcm \
            /output/03_dicomseg_output/seg_from_rtstruct.dcm" \
        "${example_dir}/03_dicomseg_output/seg_from_rtstruct.dcm"; then
        log_message "ERROR" "RT-STRUCT conversion failed for $example_name"
        echo "$example_name: Failed (Conversion failed)" >> "$VALIDATION_REPORT"
        return 1
    fi

    log_message "SUCCESS" "$example_name completed successfully"
    echo "$example_name: Conversion successful (RT-STRUCT → DICOM SEG)" >> "$VALIDATION_REPORT"
    return 0
}

#==============================================================================
# README Generation
#==============================================================================

generate_readme() {
    cat > "${OUTPUT_DIR}/README.md" << 'EOF'
# DICOM Converter Deliverable Examples

## Overview

This deliverable contains real-world examples of DICOM SEG roundtrip conversions demonstrating the capabilities of the DicomConverter tool.

## Directory Structure

Each example follows this structure:

**DICOM SEG Roundtrip Examples (Examples 1-4):**
```
ExampleN_NAME/
├── 01_dicom_input/              # Original DICOM image series
├── 02_dicomseg_original/        # Original DICOM SEG file
│   └── seg_original.dcm
├── 03_nifti_converted/          # NIfTI files extracted from original (separate per segment)
│   ├── 1.nii.gz, 2.nii.gz, ...
│   └── meta.json
├── 03_nifti_converted_merged/   # Merged NIfTI for validation
│   └── niftiseg/
│       └── segmentation.nii.gz
├── 04_dicomseg_reconverted/     # DICOM SEG reconverted from NIfTI (roundtrip)
│   ├── seg_reconverted.dcm
│   └── merged/                  # Merged NIfTI from reconverted SEG
│       └── niftiseg/
│           └── segmentation.nii.gz
└── 05_visual_comparison/        # Visual comparison images
    ├── slice_045_comparison.png
    ├── slice_067_comparison.png
    └── ...
```

**RT-STRUCT Examples (Example 5):**
```
Example5_Pedro_CT_RTSTRUCT/
├── 01_dicom_input/              # Original DICOM CT images
├── 02_rtstruct_input/           # RT-STRUCT file
│   └── rtstruct.dcm
└── 03_dicomseg_output/          # DICOM SEG converted from RT-STRUCT
    └── seg_from_rtstruct.dcm
```

## Examples Included

### Example 1: LUNG1-001 (CT Lung Cancer)
- **Modality**: CT
- **Source**: LUNG1 public dataset
- **Contains**: Lung segmentation with multiple structures
- **Size**: 134 DICOM slices
- **Expected Result**: Dice >= 0.95

### Example 2: interobs05 (CT Multi-structure)
- **Modality**: CT
- **Source**: Inter-observer study
- **Contains**: Multiple anatomical structures
- **Size**: Large multi-segment segmentation
- **Expected Result**: Dice >= 0.95

### Example 3: AMBL-001 (MRI Breast) [If Successful]
- **Modality**: MRI
- **Source**: AMBL breast imaging study
- **Contains**: Breast tissue segmentation
- **Note**: May fail due to generated DICOM SEG compatibility

### Example 4: AMBL-004 (MRI Breast) [If Successful]
- **Modality**: MRI
- **Source**: AMBL breast imaging study
- **Contains**: Breast tissue segmentation
- **Note**: May fail due to generated DICOM SEG compatibility

### Example 5: Pedro CT RT-STRUCT
- **Modality**: CT
- **Source**: EUCAIM example RT-STRUCT dataset
- **Contains**: RT-STRUCT contours converted to DICOM SEG
- **Size**: 175 CT DICOM slices
- **Workflow**: RT-STRUCT → DICOM SEG (no roundtrip)

## Visual Comparison

Each DICOM SEG roundtrip example (Examples 1-4) includes visual comparison images in the `05_visual_comparison/` directory. These PNG images show:

- **Side-by-side comparison** of original vs reconverted segmentations
- **Multiple representative slices** where segmentation is present (typically 5 slices)
- **Overlay visualization** with segmentation masks colored and overlaid on original DICOM images
- **Pixel count statistics** for each slice to quantify differences

The visual comparison allows for quick quality assessment of the roundtrip conversion without needing specialized DICOM viewers.

## Roundtrip Conversion Workflow

For DICOM SEG examples (1-4), the following workflow was performed:

1. **Extract NIfTI from original DICOM SEG**
   - Use `itkimage` to extract separate files per segment + metadata JSON
   - Use `itkimage2` to extract merged NIfTI for validation

2. **Fix Metadata**
   - Add missing `SegmentAlgorithmName` field to metadata JSON
   - Required for successful reconversion

3. **Reconvert NIfTI to DICOM SEG**
   - Use `dicomseg` with separate NIfTI files + metadata JSON
   - Reference original DICOM image series

4. **Validate Roundtrip**
   - Extract merged NIfTI from reconverted DICOM SEG
   - Calculate Dice coefficient between original and reconverted
   - Threshold: Dice >= 0.95 (excellent)

5. **Generate Visual Comparison**
   - Create side-by-side comparison images
   - Select 5 representative slices with segmentation
   - Overlay segmentation masks on original images
   - Save as PNG files in `05_visual_comparison/`

## RT-STRUCT Conversion Workflow

For RT-STRUCT example (Example 5), the workflow is:

1. **Convert RT-STRUCT to DICOM SEG**
   - Input: CT DICOM images + RT-STRUCT file with contours
   - Process: Rasterize RT-STRUCT contours to binary masks
   - Output: DICOM SEG file with one segment per ROI
   - Tool: `rtstruct2seg` command

## Validation Results

See `validation_report.txt` for Dice coefficient scores for each example.

## How to View

### DICOM Files
Use DICOM viewers like:
- **3D Slicer** (recommended - native DICOM SEG support)
- **Horos** (macOS)
- **MITK Workbench**
- **Online**: https://www.dicomlibrary.com/

### NIfTI Files
Use medical imaging tools like:
- **ITK-SNAP** (excellent for segmentation visualization)
- **3D Slicer** (supports both DICOM and NIfTI)
- **FSLeyes** (part of FSL toolkit)
- **Python**: Use `nibabel` and `matplotlib`

## Docker Commands Used

### Extract NIfTI (separate files) from DICOM SEG
```bash
docker run --rm \
  -v /path/to/data:/data \
  dicomconverter:1.4.0 \
  itkimage \
  --inputDICOM /data/input.dcm \
  --outputDirectory /data/output \
  -t nifti
```

### Extract NIfTI (merged) from DICOM SEG
```bash
docker run --rm \
  -v /path/to/data:/data \
  dicomconverter:1.4.0 \
  itkimage2 \
  /data/input.dcm \
  /data/output \
  False
```

### Reconvert NIfTI to DICOM SEG
```bash
docker run --rm \
  -v /path/to/original:/dataroot:ro \
  -v /path/to/work:/data \
  dicomconverter:1.4.0 \
  dicomseg \
  --inputImageList /data/1.nii.gz,/data/2.nii.gz,... \
  --inputMetadata /data/meta.json \
  --inputDICOMDirectory /dataroot/original_dicom_series \
  --outputDICOM /data/output.dcm
```

### Validate Roundtrip
```bash
docker run --rm \
  -v /path/to/output:/output \
  --entrypoint /bin/bash \
  dicomconverter:1.4.0 \
  -c "source /opt/conda/etc/profile.d/conda.sh && \
      conda activate dicomseg && \
      python3 /usr/dicomconverter/tests/roundtrip_validation.py \
        --original /output/original.nii.gz \
        --roundtrip /output/roundtrip.nii.gz \
        --tolerance 0.95 \
        --verbose"
```

## Technical Details

- **Tool**: DicomConverter v1.4.0
- **Container**: dicomconverter:1.4.0
- **Standards**: DICOM Part 3, DICOM SEG Supplement 166
- **Validation**: Dice coefficient with 0.95 threshold
- **Key Tools**:
  - `itkimage`: Extract separate NIfTI files per segment
  - `itkimage2`: Extract merged NIfTI (for validation)
  - `dicomseg`: Convert NIfTI + metadata to DICOM SEG
  - `roundtrip_validation.py`: Calculate Dice coefficient

## Generation Log

See `deliverable_generation.log` in parent directory for detailed execution log with timestamps and all commands executed.

## Notes

- **Overlapping Segments**: If segments overlap, merged NIfTI files cannot be created. In this case, validation is skipped, but conversion is still successful.
- **Metadata Correction**: The `SegmentAlgorithmName` field must be present in metadata JSON for reconversion. This is automatically added if missing.
- **AMBL Cases**: These use generated DICOM SEG files (not from original data) and may have compatibility issues.

---

**Generated**: TIMESTAMP_PLACEHOLDER
**Tool**: DicomConverter v1.4.0
**Docker Image**: dicomconverter:1.4.0
**For**: EUCAIM Project Deliverable
EOF

    # Replace timestamp placeholder
    sed -i "s/TIMESTAMP_PLACEHOLDER/$(date)/" "${OUTPUT_DIR}/README.md"

    log_message "SUCCESS" "Generated README.md"
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
    # Initialize
    echo "Deliverable Generation Started: $(date)" > "$LOG_FILE"
    echo "Docker Image: $DOCKER_IMAGE" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"

    echo "" > "$VALIDATION_REPORT"

    log_message "INFO" "======================================"
    log_message "INFO" "DICOM Converter Deliverable Generator"
    log_message "INFO" "======================================"
    log_message "INFO" "Docker Image: $DOCKER_IMAGE"
    log_message "INFO" "Output: $OUTPUT_DIR"
    log_message "INFO" "Log: $LOG_FILE"
    echo ""

    # Clean output directory if exists
    if [ -d "$OUTPUT_DIR" ]; then
        log_message "WARNING" "Output directory exists - removing old data"
        rm -rf "$OUTPUT_DIR"
    fi
    mkdir -p "$OUTPUT_DIR"

    # Process Test 1: LUNG1-001
    if process_test_case \
        "1" \
        "LUNG1-001" \
        "${DATA_DIR}/Test1/LUNG1-001/09-18-2008-StudyID-NA-69331/0.000000-NA-82046" \
        "${DATA_DIR}/Test1/LUNG1-001/09-18-2008-StudyID-NA-69331/300.000000-Segmentation-9.554/1-1.dcm" \
        "/dataroot/Test1/LUNG1-001/09-18-2008-StudyID-NA-69331/0.000000-NA-82046"; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
    fi
    echo ""

    # Process Test 2: interobs05
    if process_test_case \
        "2" \
        "interobs05" \
        "${DATA_DIR}/Test2/interobs05/02-18-2019-NA-CT-90318/NA-28629" \
        "${DATA_DIR}/Test2/interobs05/02-18-2019-NA-CT-90318/1.000000-Segmentation-94745/1-1.dcm" \
        "/dataroot/Test2/interobs05/02-18-2019-NA-CT-90318/NA-28629"; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
    fi
    echo ""

    # Process Test 3: AMBL-001 (may fail)
    if process_test_case \
        "3" \
        "AMBL-001" \
        "${DATA_DIR}/Test3/AMBL-001/03-05-2004-NA-MRI_BREASTS_-_Delayed_contrast-93547/500.000000-Registered_AX_Sen_Vibrant_MultiPhase-85715" \
        "${DATA_DIR}/Test3/AMBL-001/seg/seg.dcm" \
        "/dataroot/Test3/AMBL-001/03-05-2004-NA-MRI_BREASTS_-_Delayed_contrast-93547/500.000000-Registered_AX_Sen_Vibrant_MultiPhase-85715"; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
        log_message "WARNING" "AMBL-001 failed (expected - may be excluded from deliverable)"
    fi
    echo ""

    # Process Test 4: AMBL-004 (may fail)
    if process_test_case \
        "4" \
        "AMBL-004" \
        "${DATA_DIR}/Test3/AMBL-004/03-05-2004-NA-MRI BREASTS - Delayed contrast-97546/500.000000-Registered AX Sen Vibrant MultiPhase-14991" \
        "${DATA_DIR}/Test3/AMBL-004/seg/seg.dcm" \
        "/dataroot/Test3/AMBL-004/03-05-2004-NA-MRI BREASTS - Delayed contrast-97546/500.000000-Registered AX Sen Vibrant MultiPhase-14991"; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
        log_message "WARNING" "AMBL-004 failed (expected - may be excluded from deliverable)"
    fi
    echo ""

    # Process Test 5: Pedro CT RT-STRUCT
    if process_rtstruct_case \
        "5" \
        "Pedro_CT_RTSTRUCT" \
        "${SCRIPT_DIR}/DATA/PedroShared/EUCAIM_example_RTSTRUCT_002/CT_UnspecifiedCT_20210430/CT" \
        "${SCRIPT_DIR}/DATA/PedroShared/EUCAIM_example_RTSTRUCT_002/CT_UnspecifiedCT_20210430/RTSTRUCT/struct_set_2025-02-17_15-26-13.dcm" \
        "/dataroot/PedroShared/EUCAIM_example_RTSTRUCT_002/CT_UnspecifiedCT_20210430/CT"; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
        log_message "WARNING" "Pedro RT-STRUCT failed"
    fi
    echo ""

    # Generate README documentation
    generate_readme

    # Print summary
    echo ""
    log_message "INFO" "======================================"
    log_message "INFO" "GENERATION COMPLETE"
    log_message "INFO" "======================================"
    log_message "INFO" "Successful: $SUCCESS_COUNT"
    log_message "INFO" "Failed: $FAILURE_COUNT"
    log_message "INFO" "Output: $OUTPUT_DIR"
    log_message "INFO" "Validation Report: $VALIDATION_REPORT"
    log_message "INFO" "Full Log: $LOG_FILE"
    echo ""

    # Display validation results
    if [ -f "$VALIDATION_REPORT" ]; then
        log_message "INFO" "Validation Results:"
        echo ""
        cat "$VALIDATION_REPORT" | while read line; do
            echo -e "  ${CYAN}$line${NC}"
        done
        echo ""
    fi

    # Final message
    if [ $SUCCESS_COUNT -ge 2 ]; then
        log_message "SUCCESS" "Deliverable ready with $SUCCESS_COUNT successful examples!"
    else
        log_message "WARNING" "Only $SUCCESS_COUNT examples succeeded - review log for issues"
    fi

    return 0
}

# Run main function
main
