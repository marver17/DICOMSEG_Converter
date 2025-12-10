# Security Improvements Summary

This directory contains security enhancements implemented following the EUCAIM risk assessment.

## Critical Fixes Applied (P0)

### 1. Dockerfile Security Hardening
**File**: `Dockerfile.secure`

**Changes**:
- ✅ **Removed hardcoded password** (line 51-52 in original)
  - Previously: `RUN echo "ds:password" | chpasswd`
  - Now: Password removed entirely, authentication delegated to platform

- ✅ **Fixed /logs directory permissions**
  - Previously: `chmod 777` (world-writable, security risk)
  - Now: `chmod 755` with proper ownership (ds:ds can write, others cannot)

- ✅ **Added build metadata and versioning**
  - VERSION.json with git commit, build date, version
  - OCI labels for container registry integration
  - Enables verification that deployed container matches validated version

### 2. Path Validation Module
**File**: `src/security/path_validator.py`

**Features**:
- Whitelist-based path validation (prevents directory traversal)
- File size limit enforcement (prevents DoS)
- Symlink detection and blocking (prevents symlink attacks)
- Safe path sanitization for logging

**Usage**:
```python
from security.path_validator import PathValidator

validator = PathValidator(
    allowed_base_paths=['/data', '/home/ds/datasets'],
    max_file_size_mb=5000
)

# Validate and sanitize user input
safe_path = validator.validate_path(user_input, must_exist=True)
validator.validate_file_size(safe_path)
```

### 3. Centralized Audit Logging
**File**: `src/security/audit_logger.py`

**Features**:
- Structured JSON logging for SIEM integration
- Security event tracking with severity levels
- Conversion lifecycle logging (start/end/duration)
- Resource usage monitoring
- Path sanitization for GDPR compliance

**Usage**:
```python
from security.audit_logger import get_audit_logger

logger = get_audit_logger()

# Log conversion operations
logger.log_conversion_start(
    conversion_type='rtstruct2seg',
    input_path='/data/input.dcm',
    output_path='/data/output.dcm',
    user_id='user123',
    job_id='job_456'
)

# Log security events
logger.log_security_event(
    event_type='unauthorized_access_attempt',
    severity='high',
    description='User attempted to access /etc/passwd',
    user_id='suspicious_user'
)
```

## Build and Deployment Tools

### Secure Build Script
**File**: `build_secure.sh`

**Features**:
- Automatic version tagging from git
- Security scanning with Trivy (if installed)
- SBOM generation with Syft (if installed)
- Build metadata tracking
- Multi-tag support (version, commit, latest)

**Usage**:
```bash
# Make executable
chmod +x build_secure.sh

# Build with version tracking
./build_secure.sh

# With custom registry
REGISTRY=eucaim-registry.io ./build_secure.sh
```

### Version File
**File**: `VERSION`

Single source of truth for version number. Used by build script.

### Security Policy
**File**: `SECURITY.md`

Documents:
- Supported versions
- Vulnerability reporting process
- Security measures implemented
- Known limitations
- Compliance information

## Integration Guide

### Step 1: Update Existing Code

To integrate security modules into existing code:

```python
# In csv_batch.py
from security.path_validator import PathValidator
from security.audit_logger import get_audit_logger

class BatchProcessor:
    def __init__(self, args):
        self.args = args
        
        # Add path validator
        self.path_validator = PathValidator(
            allowed_base_paths=['/data', '/home/ds/datasets'],
            max_file_size_mb=5000
        )
        
        # Add audit logger
        self.audit_logger = get_audit_logger()
    
    def run_one(self, cmd, row, row_id):
        # Validate paths
        input_path = self.path_validator.validate_path(
            row.get('input1'), 
            must_exist=True
        )
        
        # Log start
        job_id = f"{cmd}_{row_id}_{int(time.time())}"
        self.audit_logger.log_conversion_start(
            conversion_type=cmd,
            input_path=str(input_path),
            output_path=row.get('output'),
            job_id=job_id
        )
        
        # ... existing execution code ...
```

### Step 2: Update Dockerfile

Replace current `Dockerfile` with `Dockerfile.secure`:

```bash
# Backup current Dockerfile
mv Dockerfile Dockerfile.old

# Use secure version
mv Dockerfile.secure Dockerfile

# Or build directly
docker build -f Dockerfile.secure -t dicomconverter:latest .
```

### Step 3: Run Scripts Refactoring (P0 - Required)

**File to modify**: `src/run_scripts.sh`

Remove `eval()` usage in functions `dicomseg()` and `itkimage()`:

```bash
# BEFORE (lines 131-148):
comando="itkimage2segimage --returnparameterfile \"$returnparameterfile\" ..."
eval "$comando"

# AFTER (secure):
itkimage2segimage \
    --returnparameterfile "$returnparameterfile" \
    --processinformationaddress "$processinformationaddress" \
    --xml "$xml" \
    --echo "$echo" \
    --verbose "$verbose" \
    --useLabelIDAsSegmentNumber "$useLabelIDAsSegmentNumber" \
    --skip "$skip" \
    --inputImageList "$inputImageList" \
    --inputDICOMDirectory "$inputDICOMDirectory" \
    --inputDICOMList "$inputDICOMList" \
    --outputDICOM "$outputDICOM" \
    --inputMetadata "$inputMetadata" \
    --outputType "$outputType" \
    -p "$prefix" \
    --outputDirectory "$outputDirectory" \
    --inputDICOM "$inputDICOM"
```

Apply same pattern to the `itkimage()` function around line 220.

## Testing Security Improvements

### Test Path Validator

```bash
# Run standalone tests
docker run --rm dicomconverter:latest \
    python3 /usr/dicomconverter/src/security/path_validator.py
```

Expected output: Series of PASS/FAIL tests showing validation working.

### Test Audit Logger

```bash
# Run standalone tests
docker run --rm -v $(pwd)/test_logs:/logs dicomconverter:latest \
    python3 /usr/dicomconverter/src/security/audit_logger.py

# Check generated logs
cat test_logs/audit_*.jsonl | jq .
```

### Test Secure Build

```bash
# Build with versioning
./build_secure.sh

# Verify version in container
docker run --rm dicomconverter:latest cat /usr/dicomconverter/VERSION.json

# Check labels
docker inspect dicomconverter:latest | jq '.[0].Config.Labels'
```

## Security Scanning

### Vulnerability Scanning with Trivy

```bash
# Install Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | \
    sh -s -- -b /usr/local/bin

# Scan image
trivy image --severity HIGH,CRITICAL dicomconverter:latest

# Generate report
trivy image --format json --output trivy-report.json dicomconverter:latest
```

### Dependency Scanning

```bash
# Python dependencies
pip install safety
safety check --file src/rtstruct/requirements.txt
safety check --file src/nifti/ENV.yml  # May need conversion to requirements.txt
```

## Remaining Work (P1/P2)

### P1 - High Priority (Before Production)

1. **Resource Limits**
   - Add to deployment manifests (Docker Compose, K8s)
   - Implement runtime resource monitoring

2. **Run Scripts Refactoring**
   - Remove all `eval()` usage (see Step 3 above)
   - Test all conversion modes after refactoring

3. **Error Handling**
   - Implement SecureErrorHandler (see main recommendations doc)
   - Integrate into all conversion modules

4. **Integration Testing**
   - Test security modules with real data
   - Verify audit logs are complete
   - Validate path restrictions work as expected

### P2 - Medium Priority (Post-Deployment)

1. **CI/CD Integration**
   - Add GitHub Actions for security scanning
   - Automate vulnerability checks on PRs
   - Generate SBOM on every build

2. **Monitoring**
   - Implement health check endpoint
   - Set up log aggregation (if EUCAIM provides)
   - Configure alerting for security events

3. **Documentation**
   - Update README with security features
   - Create deployment guide for EUCAIM
   - Document incident response procedures

## Support and Questions

For questions about these security improvements:

1. Review the detailed recommendations in `SECURITY_IMPROVEMENTS_RECOMMENDATIONS.md`
2. Check the code comments in the security modules
3. Open an issue on GitHub with label `security`
4. Contact EUCAIM security team for platform-specific guidance

## Compliance Checklist

Before deploying to EUCAIM production:

- [ ] All P0 fixes applied and tested
- [ ] Dockerfile.secure in use (no hardcoded passwords)
- [ ] Path validator integrated in all user input points
- [ ] Audit logger configured and logs are being written
- [ ] Resource limits set in deployment configuration
- [ ] Security scan shows 0 CRITICAL vulnerabilities
- [ ] Version tracking enabled (VERSION.json present)
- [ ] SECURITY.md reviewed and approved
- [ ] Integration testing passed
- [ ] EUCAIM security team approval obtained

---

**Last Updated**: 2025-12-10  
**Security Revision**: 1.0
