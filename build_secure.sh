#!/bin/bash
#
# Secure Build Script for DicomConverter
# Builds Docker image with version tracking and security controls
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== DicomConverter Secure Build ===${NC}\n"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Get version information
if [ -f "VERSION" ]; then
    VERSION=$(cat VERSION)
else
    echo -e "${YELLOW}Warning: VERSION file not found, using 'dev'${NC}"
    VERSION="dev"
fi

GIT_COMMIT=$(git rev-parse --short HEAD)
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
BUILDER=$(whoami)

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}Warning: You have uncommitted changes${NC}"
    GIT_COMMIT="${GIT_COMMIT}-dirty"
fi

echo "Build Information:"
echo "  Version:    ${VERSION}"
echo "  Git Commit: ${GIT_COMMIT}"
echo "  Git Branch: ${GIT_BRANCH}"
echo "  Build Date: ${BUILD_DATE}"
echo "  Builder:    ${BUILDER}"
echo ""

# Image name
IMAGE_NAME="dicomconverter"
REGISTRY="${REGISTRY:-}"  # Can be set via environment variable

if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}"
fi

# Build the image
echo -e "${GREEN}Building Docker image...${NC}"

docker build \
    --build-arg VERSION="${VERSION}" \
    --build-arg GIT_COMMIT="${GIT_COMMIT}" \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg GIT_BRANCH="${GIT_BRANCH}" \
    --label "org.opencontainers.image.created=${BUILD_DATE}" \
    --label "org.opencontainers.image.revision=${GIT_COMMIT}" \
    --label "org.opencontainers.image.version=${VERSION}" \
    --label "org.opencontainers.image.title=EUCAIM DicomConverter" \
    --label "org.opencontainers.image.vendor=EUCAIM" \
    --label "org.opencontainers.image.source=https://github.com/marver17/DicomConverter" \
    -t "${FULL_IMAGE_NAME}:${VERSION}" \
    -t "${FULL_IMAGE_NAME}:${GIT_COMMIT}" \
    -t "${FULL_IMAGE_NAME}:latest" \
    .

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Build successful!${NC}"
    echo ""
    echo "Tagged as:"
    echo "  - ${FULL_IMAGE_NAME}:${VERSION}"
    echo "  - ${FULL_IMAGE_NAME}:${GIT_COMMIT}"
    echo "  - ${FULL_IMAGE_NAME}:latest"
else
    echo -e "\n${RED}✗ Build failed${NC}"
    exit 1
fi

# Security scan (if Trivy is installed)
if command -v trivy &> /dev/null; then
    echo -e "\n${GREEN}Running security scan with Trivy...${NC}"
    
    trivy image \
        --severity HIGH,CRITICAL \
        --exit-code 0 \
        "${FULL_IMAGE_NAME}:${VERSION}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Security scan completed${NC}"
    else
        echo -e "${YELLOW}⚠ Security issues found (see above)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Trivy not installed, skipping security scan${NC}"
    echo "  Install with: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin"
fi

# Generate SBOM (Software Bill of Materials) if syft is installed
if command -v syft &> /dev/null; then
    echo -e "\n${GREEN}Generating SBOM...${NC}"
    
    SBOM_FILE="sbom-${VERSION}-${GIT_COMMIT}.json"
    syft "${FULL_IMAGE_NAME}:${VERSION}" -o json > "${SBOM_FILE}"
    
    echo -e "${GREEN}✓ SBOM saved to: ${SBOM_FILE}${NC}"
else
    echo -e "${YELLOW}⚠ Syft not installed, skipping SBOM generation${NC}"
    echo "  Install with: curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin"
fi

# Save build metadata
BUILD_INFO_FILE="build-info-${VERSION}-${GIT_COMMIT}.json"
cat > "${BUILD_INFO_FILE}" << EOF
{
  "version": "${VERSION}",
  "git_commit": "${GIT_COMMIT}",
  "git_branch": "${GIT_BRANCH}",
  "build_date": "${BUILD_DATE}",
  "builder": "${BUILDER}",
  "image": "${FULL_IMAGE_NAME}:${VERSION}"
}
EOF

echo -e "\n${GREEN}✓ Build metadata saved to: ${BUILD_INFO_FILE}${NC}"

# Instructions
echo -e "\n${GREEN}=== Next Steps ===${NC}"
echo ""
echo "1. Test the image:"
echo "   docker run --rm ${FULL_IMAGE_NAME}:${VERSION} version"
echo ""
echo "2. Run the test suite:"
echo "   ./tests/quick_test.sh"
echo ""

if [ -n "$REGISTRY" ]; then
    echo "3. Push to registry:"
    echo "   docker push ${FULL_IMAGE_NAME}:${VERSION}"
    echo "   docker push ${FULL_IMAGE_NAME}:${GIT_COMMIT}"
    echo ""
fi

echo "4. Deploy with specific version:"
echo "   docker run --rm \\"
echo "     --memory=\"8g\" \\"
echo "     --cpus=\"4.0\" \\"
echo "     -v \$(pwd)/DATA:/data \\"
echo "     ${FULL_IMAGE_NAME}:${VERSION} \\"
echo "     [command]"
echo ""

echo -e "${GREEN}Build complete!${NC}"
