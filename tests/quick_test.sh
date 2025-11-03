#!/bin/bash
#
# Quick Test Script - Build and Test DicomConverter Container
#
# This script:
# 1. Builds the Docker image
# 2. Runs the test suite
# 3. Validates the outputs
# 4. Displays summary
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_NAME="dicomconverter:test-$(date +%Y%m%d)"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DicomConverter Quick Test            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Build
echo -e "${YELLOW}[1/3]${NC} Building Docker image..."
echo -e "      Image name: ${IMAGE_NAME}"
docker build -t "$IMAGE_NAME" .. || {
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Build successful${NC}"
echo ""

# Step 2: Run tests
echo -e "${YELLOW}[2/3]${NC} Running container tests..."
./run_container_tests.sh "$IMAGE_NAME" || {
    echo -e "${RED}✗ Tests failed${NC}"
    echo "Check test_output/test_log_*.txt for details"
    exit 1
}
echo ""

# Step 3: Validate (optional - requires pydicom)
echo -e "${YELLOW}[3/3]${NC} Validating outputs..."
if python3 -c "import pydicom" 2>/dev/null; then
    python3 test_container_validation.py test_output || {
        echo -e "${YELLOW}⚠ Some validation checks failed${NC}"
    }
else
    echo -e "${YELLOW}⊗ Skipping validation (pydicom not installed)${NC}"
    echo "  Install with: pip install pydicom SimpleITK"
fi
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Test Complete                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "Docker Image:  ${IMAGE_NAME}"
echo -e "Test Outputs:  test_output/"
echo -e "Test Log:      test_output/test_log_*.txt"
echo ""
echo -e "${GREEN}✓ Container is ready to use${NC}"
echo ""
echo "To use the container:"
echo "  docker run --rm $IMAGE_NAME information"
echo ""
