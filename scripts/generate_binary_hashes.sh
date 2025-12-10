#!/bin/bash
#
# Generate SHA256 checksums for dcmqi binaries
# This script should be run whenever binaries are updated
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
DCMQI_BIN_DIR="$REPO_ROOT/src/nifti/dcmqi-function/bin"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔐 Generating SHA256 checksums for dcmqi binaries${NC}"
echo ""

if [ ! -d "$DCMQI_BIN_DIR" ]; then
    echo "Error: dcmqi binary directory not found: $DCMQI_BIN_DIR"
    exit 1
fi

cd "$DCMQI_BIN_DIR"

# Generate SHA256 for all dcmqi binaries
echo "Calculating checksums..."
sha256sum itkimage2paramap \
          itkimage2segimage \
          paramap2itkimage \
          segimage2itkimage \
          tid1500reader \
          tid1500writer > SHA256SUMS

echo -e "${GREEN}✓ Generated SHA256SUMS file:${NC}"
echo ""
cat SHA256SUMS
echo ""
echo -e "${GREEN}✓ File saved: src/nifti/dcmqi-function/bin/SHA256SUMS${NC}"
echo ""
echo "Note: Commit this file to git to enable verification during build"
