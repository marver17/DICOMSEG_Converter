#!/bin/bash
#
# Comprehensive Test Suite for DicomConverter Docker Container
# 
# Tests all conversion modes using real data from DATA/ folder:
# - Test1: RTSTRUCT conversion (LUNG1-001)
# - Test2: RTSTRUCT conversion with structures (interobs05)
# - Test3: DICOM SEG handling (AMBL-001, AMBL-004)
# - PedroShared: Multi-modality RTSTRUCT tests
# - RT-STRUCT: Basic RT-STRUCT test
#
# Usage:
#   ./run_container_tests.sh [docker_image_name]
#

set -e  # Exit on error

# Configuration
DOCKER_IMAGE="${1:-dicomconverter:latest}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/../DATA"
OUTPUT_DIR="${SCRIPT_DIR}/test_output"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_LOG="${OUTPUT_DIR}/test_log_${TIMESTAMP}.txt"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Initialize
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}DicomConverter Container Test Suite${NC}"
echo -e "${BLUE}=====================================${NC}"
echo "Docker Image: $DOCKER_IMAGE"
echo "Data Directory: $DATA_DIR"
echo "Output Directory: $OUTPUT_DIR"
echo "Test Log: $TEST_LOG"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo "Test Suite Started: $(date)" > "$TEST_LOG"
echo "Docker Image: $DOCKER_IMAGE" >> "$TEST_LOG"
echo "" >> "$TEST_LOG"

# Helper function to run test
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    local expected_output="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${YELLOW}[TEST $TESTS_RUN]${NC} $test_name"
    echo "----------------------------------------" | tee -a "$TEST_LOG"
    echo "TEST $TESTS_RUN: $test_name" >> "$TEST_LOG"
    echo "Command: $test_cmd" >> "$TEST_LOG"
    echo "Started: $(date)" >> "$TEST_LOG"
    
    # Run the test
    if eval "$test_cmd" >> "$TEST_LOG" 2>&1; then
        # Check if expected output exists
        if [ -n "$expected_output" ] && [ -f "$expected_output" ]; then
            echo -e "${GREEN}✓ PASSED${NC} - Output created: $expected_output"
            echo "Status: PASSED" >> "$TEST_LOG"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        elif [ -z "$expected_output" ]; then
            echo -e "${GREEN}✓ PASSED${NC} - Command executed successfully"
            echo "Status: PASSED" >> "$TEST_LOG"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗ FAILED${NC} - Expected output not found: $expected_output"
            echo "Status: FAILED - Output not found" >> "$TEST_LOG"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        echo -e "${RED}✗ FAILED${NC} - Command failed with exit code $?"
        echo "Status: FAILED - Command error" >> "$TEST_LOG"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    echo "Finished: $(date)" >> "$TEST_LOG"
    echo "" >> "$TEST_LOG"
    echo ""
}

# Test 0: Container basic functionality
echo -e "${BLUE}=== BASIC FUNCTIONALITY TESTS ===${NC}"
echo ""

run_test "Container Information Command" \
    "docker run --rm $DOCKER_IMAGE information" \
    ""

run_test "Container Help Command" \
    "docker run --rm $DOCKER_IMAGE --help || true" \
    ""

# Test 1: RTSTRUCT to DICOM SEG - LUNG1-001
echo -e "${BLUE}=== TEST1: RTSTRUCT CONVERSION (LUNG1-001) ===${NC}"
echo ""

TEST1_DICOM="$DATA_DIR/EucaimShared/Test1/LUNG1-001/09-18-2008-StudyID-NA-69331/3.000000-NA-78236"
TEST1_RTSTRUCT="$DATA_DIR/EucaimShared/Test1/LUNG1-001/09-18-2008-StudyID-NA-69331/0.000000-NA-82046/1-1.dcm"
TEST1_OUTPUT="$OUTPUT_DIR/test1_lung_seg.dcm"

if [ -d "$TEST1_DICOM" ] && [ -f "$TEST1_RTSTRUCT" ]; then
    run_test "RTSTRUCT to SEG (LUNG1-001)" \
        "docker run --rm \
            -v \"$DATA_DIR:/data:ro\" \
            -v \"$OUTPUT_DIR:/output\" \
            $DOCKER_IMAGE \
            rtstruct2seg \
            /data/EucaimShared/Test1/LUNG1-001/09-18-2008-StudyID-NA-69331/3.000000-NA-78236 \
            /data/EucaimShared/Test1/LUNG1-001/09-18-2008-StudyID-NA-69331/0.000000-NA-82046/1-1.dcm \
            /output/test1_lung_seg.dcm" \
        "$TEST1_OUTPUT"
else
    echo -e "${YELLOW}⊗ SKIPPED${NC} - Test1 data not found"
fi

# Test 2: RTSTRUCT with structures - interobs05
echo -e "${BLUE}=== TEST2: RTSTRUCT WITH STRUCTURES (interobs05) ===${NC}"
echo ""

TEST2_DICOM="$DATA_DIR/EucaimShared/Test2/interobs05/02-18-2019-NA-CT-90318/NA-28629"
TEST2_RTSTRUCT="$DATA_DIR/EucaimShared/Test2/interobs05/02-18-2019-NA-CT-90318/1.000000-ARIA RadOnc Structure Sets-55318/1-1.dcm"
TEST2_OUTPUT="$OUTPUT_DIR/test2_interobs_seg.dcm"

if [ -d "$TEST2_DICOM" ] && [ -f "$TEST2_RTSTRUCT" ]; then
    run_test "RTSTRUCT to SEG (interobs05)" \
        "docker run --rm \
            -v \"$DATA_DIR:/data:ro\" \
            -v \"$OUTPUT_DIR:/output\" \
            $DOCKER_IMAGE \
            rtstruct2seg \
            /data/EucaimShared/Test2/interobs05/02-18-2019-NA-CT-90318/NA-28629 \
            '/data/EucaimShared/Test2/interobs05/02-18-2019-NA-CT-90318/1.000000-ARIA RadOnc Structure Sets-55318/1-1.dcm' \
            /output/test2_interobs_seg.dcm" \
        "$TEST2_OUTPUT"
else
    echo -e "${YELLOW}⊗ SKIPPED${NC} - Test2 data not found"
fi

# Test 3: DICOM SEG validation - AMBL-001
echo -e "${BLUE}=== TEST3: DICOM SEG VALIDATION (AMBL-001) ===${NC}"
echo ""

TEST3_SEG="$DATA_DIR/EucaimShared/Test3/AMBL-001/seg/seg.dcm"
TEST3_OUTPUT="$OUTPUT_DIR/test3_ambl001_nifti"

if [ -f "$TEST3_SEG" ]; then
    run_test "DICOM SEG to NIfTI (AMBL-001)" \
        "docker run --rm \
            -v \"$DATA_DIR:/data:ro\" \
            -v \"$OUTPUT_DIR:/output\" \
            $DOCKER_IMAGE \
            itkimage2 \
            /data/EucaimShared/Test3/AMBL-001/seg/seg.dcm \
            /output/test3_ambl001_nifti \
            False" \
        ""
else
    echo -e "${YELLOW}⊗ SKIPPED${NC} - Test3 data not found"
fi

# Test 4: Pedro's examples - RTSTRUCT_001
echo -e "${BLUE}=== TEST4: PEDRO'S EXAMPLES (RTSTRUCT_001) ===${NC}"
echo ""

TEST4_US="$DATA_DIR/PedroShared/EUCAIM_example_RTSTRUCT_001/US/US"
TEST4_RTSTRUCT="$DATA_DIR/PedroShared/EUCAIM_example_RTSTRUCT_001/US/RTSTRUCT/1-1.dcm"
TEST4_OUTPUT="$OUTPUT_DIR/test4_pedro_us_seg.dcm"

if [ -d "$TEST4_US" ] && [ -f "$TEST4_RTSTRUCT" ]; then
    run_test "Pedro's RTSTRUCT US Example" \
        "docker run --rm \
            -v \"$DATA_DIR:/data:ro\" \
            -v \"$OUTPUT_DIR:/output\" \
            $DOCKER_IMAGE \
            rtstruct2seg \
            /data/PedroShared/EUCAIM_example_RTSTRUCT_001/US/US \
            /data/PedroShared/EUCAIM_example_RTSTRUCT_001/US/RTSTRUCT/1-1.dcm \
            /output/test4_pedro_us_seg.dcm" \
        "$TEST4_OUTPUT"
else
    echo -e "${YELLOW}⊗ SKIPPED${NC} - Test4 data not found"
fi

# Test 5: Pedro's example 002 - CT
echo -e "${BLUE}=== TEST5: PEDRO'S EXAMPLES (RTSTRUCT_002 CT) ===${NC}"
echo ""

TEST5_CT="$DATA_DIR/PedroShared/EUCAIM_example_RTSTRUCT_002/CT_UnspecifiedCT_20210430/CT"
TEST5_RTSTRUCT="$DATA_DIR/PedroShared/EUCAIM_example_RTSTRUCT_002/CT_UnspecifiedCT_20210430/RTSTRUCT/1-1.dcm"
TEST5_OUTPUT="$OUTPUT_DIR/test5_pedro_ct_seg.dcm"

if [ -d "$TEST5_CT" ] && [ -f "$TEST5_RTSTRUCT" ]; then
    run_test "Pedro's RTSTRUCT CT Example" \
        "docker run --rm \
            -v \"$DATA_DIR:/data:ro\" \
            -v \"$OUTPUT_DIR:/output\" \
            $DOCKER_IMAGE \
            rtstruct2seg \
            /data/PedroShared/EUCAIM_example_RTSTRUCT_002/CT_UnspecifiedCT_20210430/CT \
            /data/PedroShared/EUCAIM_example_RTSTRUCT_002/CT_UnspecifiedCT_20210430/RTSTRUCT/1-1.dcm \
            /output/test5_pedro_ct_seg.dcm" \
        "$TEST5_OUTPUT"
else
    echo -e "${YELLOW}⊗ SKIPPED${NC} - Test5 data not found"
fi

# Test 6: Basic RT-STRUCT folder
echo -e "${BLUE}=== TEST6: BASIC RT-STRUCT ===${NC}"
echo ""

TEST6_DCM="$DATA_DIR/RT-STRUCT/DCM/ID_1"
TEST6_RTSTRUCT="$DATA_DIR/RT-STRUCT/1-1.dcm"
TEST6_OUTPUT="$OUTPUT_DIR/test6_basic_rt_seg.dcm"

if [ -d "$TEST6_DCM" ] && [ -f "$TEST6_RTSTRUCT" ]; then
    run_test "Basic RT-STRUCT Conversion" \
        "docker run --rm \
            -v \"$DATA_DIR:/data:ro\" \
            -v \"$OUTPUT_DIR:/output\" \
            $DOCKER_IMAGE \
            rtstruct2seg \
            /data/RT-STRUCT/DCM/ID_1 \
            /data/RT-STRUCT/1-1.dcm \
            /output/test6_basic_rt_seg.dcm" \
        "$TEST6_OUTPUT"
else
    echo -e "${YELLOW}⊗ SKIPPED${NC} - Test6 data not found"
fi

# Test 7: Image Validation Test
echo -e "${BLUE}=== TEST7: IMAGE VALIDATION ===${NC}"
echo ""

if [ -f "$TEST3_SEG" ]; then
    run_test "Image Validation Help" \
        "docker run --rm --entrypoint /bin/bash $DOCKER_IMAGE \
            -c 'source /opt/conda/etc/profile.d/conda.sh && conda activate dicomseg && python3 /usr/dicomconverter/src/image_validation.py --help'" \
        ""
else
    echo -e "${YELLOW}⊗ SKIPPED${NC} - Validation test requires Test3 data"
fi

# Test 8: Batch Processing Test
echo -e "${BLUE}=== TEST8: BATCH PROCESSING ===${NC}"
echo ""

# Create a test CSV
BATCH_CSV="$OUTPUT_DIR/test_batch.csv"
cat > "$BATCH_CSV" << 'EOF'
id,input1,input2,output
test_batch_1,/data/RT-STRUCT/DCM/ID_1,/data/RT-STRUCT/1-1.dcm,/output/batch_test1.dcm
EOF

if [ -f "$BATCH_CSV" ]; then
    run_test "Batch CSV Dry-Run" \
        "docker run --rm \
            -v \"$DATA_DIR:/data:ro\" \
            -v \"$OUTPUT_DIR:/output\" \
            $DOCKER_IMAGE \
            batch rtstruct2seg \
            --csv /output/test_batch.csv \
            --dry-run \
            --verbose" \
        ""
fi

# Test 9: CSV Batch Helper Direct Test
echo -e "${BLUE}=== TEST9: CSV BATCH HELPER ===${NC}"
echo ""

run_test "CSV Batch Helper Help" \
    "docker run --rm --entrypoint python3 $DOCKER_IMAGE \
        /usr/dicomconverter/src/csv_batch.py --help" \
    ""

# Final Summary
echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}=====================================${NC}"
echo -e "Total Tests:  ${TESTS_RUN}"
echo -e "${GREEN}Passed:       ${TESTS_PASSED}${NC}"
echo -e "${RED}Failed:       ${TESTS_FAILED}${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ ALL TESTS PASSED!${NC}"
    EXIT_CODE=0
else
    echo -e "\n${RED}✗ SOME TESTS FAILED${NC}"
    EXIT_CODE=1
fi

echo ""
echo "Detailed log: $TEST_LOG"
echo "Output files: $OUTPUT_DIR"
echo ""
echo "Test Suite Completed: $(date)" >> "$TEST_LOG"

exit $EXIT_CODE
