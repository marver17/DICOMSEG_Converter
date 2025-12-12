#!/bin/bash
#
# Repository Cleanup Script
# Removes temporary files, old test outputs, and build artifacts
#

set -e

echo "==================================="
echo "Repository Cleanup"
echo "==================================="
echo ""

# Function to safely remove
safe_remove() {
    local path="$1"
    if [ -e "$path" ]; then
        echo "  Removing: $path"
        rm -rf "$path"
    fi
}

# Remove old test outputs (already deleted in git)
echo "[1/5] Cleaning old test outputs..."
safe_remove "test_run.log"
safe_remove "tests/test_run.log"
safe_remove "tests/KNOWN_ISSUES.md"
echo "  ✓ Done"
echo ""

# Remove Python cache
echo "[2/5] Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "  ✓ Done"
echo ""

# Remove temporary test outputs (keep directory structure)
echo "[3/5] Cleaning temporary test outputs..."
if [ -d "tests/test_output" ]; then
    find tests/test_output -type f -name "*.dcm" -delete 2>/dev/null || true
    find tests/test_output -type f -name "*.nii.gz" -delete 2>/dev/null || true
    find tests/test_output -type f -name "*.log" -delete 2>/dev/null || true
    find tests/test_output -type f -name "*.png" -delete 2>/dev/null || true
    echo "  ✓ Cleaned test_output/ (kept directory structure)"
fi
echo ""

# List remaining untracked files
echo "[4/5] Checking untracked files..."
UNTRACKED=$(git ls-files --others --exclude-standard | grep -v "^DATA/" | grep -v "^DELIVERABLE_EXAMPLES/" || true)
if [ -n "$UNTRACKED" ]; then
    echo "  New files (not in git):"
    echo "$UNTRACKED" | sed 's/^/    /'
else
    echo "  No untracked files (except DATA/ and DELIVERABLE_EXAMPLES/)"
fi
echo ""

# Summary
echo "[5/5] Summary"
echo "  Repository cleaned successfully!"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Add new files: git add <file>"
echo "  3. Commit changes: git commit -m 'Enhanced test suite with visual validation'"
echo ""

