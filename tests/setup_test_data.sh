#!/bin/bash
#
# Setup Test Data for DicomConverter
#
# This script checks if test data is available and provides instructions
# for downloading from Google Drive if needed.
#
# Usage:
#   ./setup_test_data.sh
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/../DATA"
GOOGLE_DRIVE_LINK="https://drive.google.com/drive/folders/1FLlLN9bGlhCPa6_jy_l3aje10lnNPRsk?usp=drive_link"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}DicomConverter Test Data Setup${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

#==============================================================================
# Check if test data exists
#==============================================================================

check_data() {
    echo -e "${YELLOW}Checking for test data...${NC}"

    # Check if DATA directory exists
    if [ ! -d "$DATA_DIR" ]; then
        echo -e "${RED}✗ DATA directory not found: $DATA_DIR${NC}"
        return 1
    fi

    # Check for required subdirectories
    local missing=0

    if [ ! -d "$DATA_DIR/EucaimShared" ]; then
        echo -e "${RED}✗ Missing: DATA/EucaimShared/${NC}"
        missing=1
    else
        # Check for test subdirectories
        if [ ! -d "$DATA_DIR/EucaimShared/Test1" ] || \
           [ ! -d "$DATA_DIR/EucaimShared/Test2" ] || \
           [ ! -d "$DATA_DIR/EucaimShared/Test3" ]; then
            echo -e "${RED}✗ Missing test directories in EucaimShared/${NC}"
            missing=1
        else
            echo -e "${GREEN}✓ EucaimShared data found${NC}"
        fi
    fi

    if [ ! -d "$DATA_DIR/PedroShared" ]; then
        echo -e "${YELLOW}⊗ Optional: DATA/PedroShared/ (for RT-STRUCT tests)${NC}"
    else
        echo -e "${GREEN}✓ PedroShared data found${NC}"
    fi

    if [ $missing -eq 1 ]; then
        return 1
    fi

    echo ""
    echo -e "${GREEN}✓ All required test data found!${NC}"
    return 0
}

#==============================================================================
# Show download instructions
#==============================================================================

show_download_instructions() {
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Test Data Download Required${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "Test data is not available locally. Please download it from Google Drive:"
    echo ""
    echo -e "${BLUE}Google Drive Link:${NC}"
    echo "$GOOGLE_DRIVE_LINK"
    echo ""
    echo -e "${BLUE}Instructions:${NC}"
    echo "1. Open the Google Drive link in your browser"
    echo "2. Download the folder (it contains EucaimShared and PedroShared datasets)"
    echo "3. Extract the downloaded archive"
    echo "4. Move/copy the contents to: $DATA_DIR"
    echo ""
    echo -e "${BLUE}Expected directory structure:${NC}"
    echo "DATA/"
    echo "├── EucaimShared/"
    echo "│   ├── Test1/           # LUNG1-001 (CT)"
    echo "│   ├── Test2/           # interobs05 (CT)"
    echo "│   └── Test3/           # AMBL-001, AMBL-004 (MRI)"
    echo "└── PedroShared/         # Optional RT-STRUCT examples"
    echo "    ├── EUCAIM_example_RTSTRUCT_001/"
    echo "    └── EUCAIM_example_RTSTRUCT_002/"
    echo ""
}

#==============================================================================
# Interactive download prompt
#==============================================================================

prompt_download() {
    echo -e "${YELLOW}Would you like to view download instructions now?${NC}"
    read -p "View instructions? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        show_download_instructions
        echo ""
        read -p "Press Enter after you have downloaded and extracted the data..."
        echo ""

        # Re-check data
        if check_data; then
            echo -e "${GREEN}✓ Test data successfully set up!${NC}"
            return 0
        else
            echo -e "${RED}✗ Test data still not found. Please verify the installation.${NC}"
            return 1
        fi
    else
        echo ""
        echo -e "${RED}Test data is required to run tests.${NC}"
        echo "Run this script again when ready to download."
        return 1
    fi
}

#==============================================================================
# Main execution
#==============================================================================

main() {
    if check_data; then
        echo ""
        echo -e "${GREEN}Test environment ready!${NC}"
        echo "You can now run the test suite:"
        echo "  ./run_container_tests.sh"
        echo "  ./quick_test.sh"
        exit 0
    else
        echo ""
        if prompt_download; then
            exit 0
        else
            exit 1
        fi
    fi
}

# Run main
main
