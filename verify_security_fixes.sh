#!/bin/bash
#
# Security Fix Verification Script
# Verifies that all P0 critical security fixes have been applied
#

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "DicomConverter Security Fix Verification"
echo "=========================================="
echo ""

PASSED=0
FAILED=0

# Test 1: Check password removed from Dockerfile
echo -n "Test 1: Password removed from Dockerfile... "
if grep -q "chpasswd" Dockerfile; then
    echo -e "${RED}FAILED${NC}"
    echo "  Found 'chpasswd' in Dockerfile - password still present!"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
fi

# Test 2: Check logs directory permissions
echo -n "Test 2: Logs directory permissions fixed... "
if grep -q "chmod 777 /logs" Dockerfile; then
    echo -e "${RED}FAILED${NC}"
    echo "  Found 'chmod 777' - insecure permissions still present!"
    FAILED=$((FAILED + 1))
elif grep -q "chmod 755 /logs" Dockerfile; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "  Could not verify permissions change"
    FAILED=$((FAILED + 1))
fi

# Test 3: Check eval() removed from run_scripts.sh
echo -n "Test 3: eval() removed from run_scripts.sh... "
# Exclude comments - only check for actual eval execution
EVAL_COUNT=$(grep "eval" src/run_scripts.sh | grep -v "^\s*#" | grep -v "# SECURITY FIX" | wc -l || true)
if [ "$EVAL_COUNT" -gt 0 ]; then
    echo -e "${RED}FAILED${NC}"
    echo "  Found $EVAL_COUNT instance(s) of 'eval' in run_scripts.sh"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
fi

# Test 4: Check PathValidator imported in csv_batch.py
echo -n "Test 4: PathValidator integrated in csv_batch.py... "
if grep -q "from security.path_validator import PathValidator" src/csv_batch.py; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAILED${NC}"
    echo "  PathValidator not imported in csv_batch.py"
    FAILED=$((FAILED + 1))
fi

# Test 5: Check PathValidator integrated in dicom_conversion.py
echo -n "Test 5: PathValidator integrated in dicom_conversion.py... "
if grep -q "from security.path_validator import PathValidator" src/dicom_conversion.py; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAILED${NC}"
    echo "  PathValidator not imported in dicom_conversion.py"
    FAILED=$((FAILED + 1))
fi

# Test 6: Check VERSION.json creation in Dockerfile
echo -n "Test 6: VERSION.json creation in Dockerfile... "
if grep -q "VERSION.json" Dockerfile; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "  VERSION.json creation not found in Dockerfile"
fi

# Test 7: Python syntax check
echo -n "Test 7: Python files syntax check... "
if python3 -m py_compile src/csv_batch.py src/dicom_conversion.py src/security/path_validator.py src/security/audit_logger.py 2>/dev/null; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAILED${NC}"
    echo "  Python syntax errors found"
    FAILED=$((FAILED + 1))
fi

# Test 8: Bash syntax check
echo -n "Test 8: Bash script syntax check... "
if bash -n src/run_scripts.sh 2>/dev/null; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAILED${NC}"
    echo "  Bash syntax errors found in run_scripts.sh"
    FAILED=$((FAILED + 1))
fi

# Test 9: Check security modules exist
echo -n "Test 9: Security modules present... "
if [ -f "src/security/path_validator.py" ] && [ -f "src/security/audit_logger.py" ]; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAILED${NC}"
    echo "  Security modules not found"
    FAILED=$((FAILED + 1))
fi

# Test 10: Check for hardcoded secrets
echo -n "Test 10: No hardcoded secrets in code... "
SECRET_PATTERNS="password|secret|api_key|token"
if grep -rI -E "$SECRET_PATTERNS" src/ --exclude-dir=__pycache__ | grep -v "path_validator\|audit_logger\|# SECURITY" | grep -q .; then
    echo -e "${YELLOW}WARNING${NC}"
    echo "  Potential secrets found - manual review needed"
    grep -rI -E "$SECRET_PATTERNS" src/ --exclude-dir=__pycache__ | grep -v "path_validator\|audit_logger\|# SECURITY" | head -5
else
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
fi

# Test 11: Check SHA256SUMS file exists for dcmqi binaries
echo -n "Test 11: SHA256 checksums file present... "
if [ -f "src/nifti/dcmqi-function/bin/SHA256SUMS" ]; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAILED${NC}"
    echo "  SHA256SUMS file not found in src/nifti/dcmqi-function/bin/"
    FAILED=$((FAILED + 1))
fi

# Test 12: Verify SHA256SUMS has correct number of entries
echo -n "Test 12: SHA256 checksums file valid... "
if [ -f "src/nifti/dcmqi-function/bin/SHA256SUMS" ]; then
    NUM_HASHES=$(wc -l < src/nifti/dcmqi-function/bin/SHA256SUMS)
    if [ "$NUM_HASHES" -eq 6 ]; then
        echo -e "${GREEN}PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}FAILED${NC}"
        echo "  Expected 6 checksums, found $NUM_HASHES"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}FAILED${NC}"
    echo "  SHA256SUMS file not found"
    FAILED=$((FAILED + 1))
fi

# Test 13: Check binary verification script exists and is executable
echo -n "Test 13: Binary verification script present... "
if [ -f "src/security/verify_binaries.sh" ] && [ -x "src/security/verify_binaries.sh" ]; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAILED${NC}"
    echo "  verify_binaries.sh not found or not executable"
    FAILED=$((FAILED + 1))
fi

# Test 14: Verify Dockerfile includes SHA256 verification
echo -n "Test 14: Dockerfile includes hash verification... "
if grep -q "SHA256SUMS" Dockerfile && grep -q "sha256sum -c" Dockerfile; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "  SHA256 verification not found in Dockerfile"
fi

# Summary
echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo -e "Tests Passed: ${GREEN}$PASSED${NC}"
echo -e "Tests Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical security fixes verified!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Build the container: docker build -t dicomconverter:1.4.0-secure ."
    echo "  2. Run tests: ./tests/quick_test.sh"
    echo "  3. Security scan: trivy image dicomconverter:1.4.0-secure"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some security fixes are missing or incomplete!${NC}"
    echo ""
    echo "Please review the failed tests above and apply the necessary fixes."
    echo "See IMPLEMENTATION_CHECKLIST.md for detailed instructions."
    echo ""
    exit 1
fi
