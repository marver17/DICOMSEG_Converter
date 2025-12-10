#!/bin/bash
#
# Verify dcmqi binaries integrity using SHA256 checksums
# This script should be run:
# - During Docker build (at build time)
# - At container startup (optional, for runtime verification)
# - Manually for security audits
#

set -e

DCMQI_BIN_DIR="/usr/dicomconverter/src/nifti/dcmqi-function/bin"
CHECKSUM_FILE="$DCMQI_BIN_DIR/SHA256SUMS"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔐 Verifying dcmqi binaries integrity..."

# Check if checksums file exists
if [ ! -f "$CHECKSUM_FILE" ]; then
    echo -e "${RED}✗ ERROR: SHA256SUMS file not found!${NC}" >&2
    echo "  Expected location: $CHECKSUM_FILE" >&2
    echo "" >&2
    echo "  This is a critical security error." >&2
    echo "  The container may have been tampered with or built incorrectly." >&2
    exit 1
fi

# Change to binary directory
cd "$DCMQI_BIN_DIR"

# Verify checksums
echo "Checking SHA256 checksums against known-good values..."
if sha256sum -c SHA256SUMS --quiet 2>/dev/null; then
    echo -e "${GREEN}✓ All dcmqi binaries verified successfully${NC}"
    echo "  6 binaries checked:"
    echo "    - itkimage2paramap"
    echo "    - itkimage2segimage"
    echo "    - paramap2itkimage"
    echo "    - segimage2itkimage"
    echo "    - tid1500reader"
    echo "    - tid1500writer"
    exit 0
else
    echo -e "${RED}✗ SECURITY ALERT: Binary integrity check FAILED!${NC}" >&2
    echo "" >&2
    echo -e "${YELLOW}⚠ CRITICAL SECURITY WARNING ⚠${NC}" >&2
    echo "  One or more dcmqi binaries have been modified!" >&2
    echo "  The container may have been tampered with or compromised." >&2
    echo "" >&2
    echo "  DO NOT USE THIS CONTAINER IN PRODUCTION!" >&2
    echo "" >&2
    echo "  Actions to take:" >&2
    echo "  1. Rebuild the container from trusted sources" >&2
    echo "  2. Verify the integrity of your build environment" >&2
    echo "  3. Report this incident to your security team" >&2
    echo "" >&2
    
    # Show which files failed
    echo "Failed verification details:" >&2
    sha256sum -c SHA256SUMS 2>&1 | grep -i "failed" || true
    
    exit 1
fi
