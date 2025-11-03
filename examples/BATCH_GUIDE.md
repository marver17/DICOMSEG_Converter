# Batch Processing Guide

This guide explains how to use the batch processing feature to convert multiple files in parallel.

## Overview

The batch mode allows you to:
- Process multiple conversions from a CSV file
- Run conversions in parallel with multiple workers
- Perform dry-runs to preview commands
- Generate detailed logs
- Handle errors gracefully with continue-on-error mode

## CSV Format

Each conversion type requires specific columns in the CSV file:

### 1. RTSTRUCT to DICOM SEG (`rtstruct2seg`)

**Required columns:**
- `input1`: Path to DICOM series directory
- `input2`: Path to RTSTRUCT file

**Optional columns:**
- `output`: Output path for SEG file (auto-generated if omitted)
- `id`: Identifier for the job (for logging)
- `extra_args`: Additional arguments to pass to the command

**Example:** See `examples/batch_rtstruct2seg.csv`

```csv
id,input1,input2,output
patient_001,/data/patient001/CT,/data/patient001/RT/structures.dcm,/data/output/patient001_seg.dcm
patient_002,/data/patient002/CT,/data/patient002/RT/structures.dcm,
```

### 2. Volume to DICOM SEG (`dicomseg`)

**Required columns:**
- `inputImageList`: Path to segmentation volume (NIfTI, etc.)
- `inputDICOMDirectory`: Path to reference DICOM directory
- `outputDICOM`: Output path for DICOM SEG file
- `inputMetadata`: Path to metadata JSON file

**Optional columns:**
- `id`: Identifier for the job
- `extra_args`: Additional arguments

**Example:** See `examples/batch_dicomseg.csv`

```csv
id,inputImageList,inputDICOMDirectory,outputDICOM,inputMetadata
seg_001,/data/seg/patient001.nii.gz,/data/dicom/patient001,/data/output/patient001_seg.dcm,/data/metadata/patient001.json
```

### 3. DICOM to NIfTI (`dicom2nifti`)

**Required columns:**
- `input`: Path to DICOM series directory

**Optional columns:**
- `output`: Output path for NIfTI file (auto-generated if omitted)
- `id`: Identifier for the job

**Example:** See `examples/batch_dicom2nifti.csv`

```csv
id,input,output
nifti_001,/data/dicom/patient001,/data/nifti/patient001.nii.gz
```

### 4. DICOM SEG to NIfTI (`itkimage2`)

**Required columns:**
- `input`: Path to DICOM SEG file

**Optional columns:**
- `orientation`: Reorientation flag (`True`/`False`, default: `False`)
- `output`: Output directory (auto-generated if omitted)
- `id`: Identifier for the job

**Example:** See `examples/batch_itkimage2.csv`

```csv
id,input,orientation,output
seg2nii_001,/data/dicomseg/patient001.dcm,True,/data/nifti/patient001
```

## Usage Examples

### Basic Usage (Sequential Processing)

```bash
# Process RTSTRUCT conversions
./run_scripts batch rtstruct2seg --csv batch_rtstruct.csv --output-dir /data/output

# Process DICOM to NIfTI conversions
./run_scripts batch dicom2nifti --csv batch_dicom2nifti.csv --output-dir /data/nifti
```

### Parallel Processing

Use `--workers N` to process multiple jobs in parallel:

```bash
# Process with 4 parallel workers
./run_scripts batch rtstruct2seg --csv batch.csv --output-dir /data/output --workers 4
```

### Dry Run

Preview commands without executing them:

```bash
./run_scripts batch rtstruct2seg --csv batch.csv --dry-run
```

### With Logging

Generate detailed logs of all operations:

```bash
./run_scripts batch rtstruct2seg --csv batch.csv --output-dir /data/output --log-file batch.log
```

### Continue on Error

Continue processing even if some jobs fail:

```bash
./run_scripts batch rtstruct2seg --csv batch.csv --output-dir /data/output --continue-on-error
```

### Verbose Output

Show detailed output for each job:

```bash
./run_scripts batch rtstruct2seg --csv batch.csv --output-dir /data/output --verbose
```

### With Timeout

Set a timeout per job (in seconds):

```bash
./run_scripts batch rtstruct2seg --csv batch.csv --output-dir /data/output --timeout 300
```

## Docker Usage

### Mount CSV and Data Directories

```bash
docker run --rm \
  -v /path/to/batch.csv:/data/batch.csv \
  -v /path/to/input:/data/input \
  -v /path/to/output:/data/output \
  dicomconverter:latest \
  batch rtstruct2seg --csv /data/batch.csv --output-dir /data/output --workers 4
```

### With Logging

```bash
docker run --rm \
  -v /path/to/batch.csv:/data/batch.csv \
  -v /path/to/input:/data/input \
  -v /path/to/output:/data/output \
  -v /path/to/logs:/data/logs \
  dicomconverter:latest \
  batch rtstruct2seg \
    --csv /data/batch.csv \
    --output-dir /data/output \
    --log-file /data/logs/batch.log \
    --workers 4
```

## Command Reference

```bash
./run_scripts batch <command> --csv <file.csv> [options]

Commands:
  rtstruct2seg   Convert RTSTRUCT to DICOM SEG
  dicomseg       Convert volume to DICOM SEG
  dicom2nifti    Convert DICOM to NIfTI
  itkimage2      Convert DICOM SEG to NIfTI
  itkimage       Convert DICOM SEG to volume

Options:
  --csv FILE              CSV file with batch jobs (required)
  --output-dir DIR        Base output directory
  --workers N             Number of parallel workers (default: 1)
  --dry-run               Print commands without executing
  --continue-on-error     Continue if jobs fail
  --skip-validation       Skip validation of required fields
  --timeout SECONDS       Timeout per job (0 = no timeout)
  --log-file FILE         Write detailed log
  --verbose, -v           Verbose output
```

## Tips and Best Practices

1. **Start with dry-run**: Always test your CSV with `--dry-run` first to verify commands are correct.

2. **Use absolute paths**: Use absolute paths in CSV files to avoid confusion.

3. **Parallel processing**: Start with fewer workers (2-4) and increase based on your system's capacity.

4. **Logging**: Use `--log-file` for production runs to track all operations and debug issues.

5. **Error handling**: Use `--continue-on-error` for large batches where some failures are acceptable.

6. **Validation**: The script validates required fields by default. Use `--skip-validation` only if you're sure your CSV is correct.

7. **Timeout**: Set reasonable timeouts (e.g., 300-600 seconds) to prevent jobs from hanging indefinitely.

## Troubleshooting

### CSV parsing errors
- Ensure the first row contains column headers
- Check for proper CSV formatting (commas, quotes)
- Verify no extra spaces in column names

### Missing files
- Verify all input paths exist and are accessible
- Use absolute paths instead of relative paths
- Check file permissions

### Failed jobs
- Check the log file for detailed error messages
- Run a single job manually to isolate the issue
- Use `--verbose` to see stdout/stderr for each job

### Performance issues
- Reduce number of workers if system is overloaded
- Check disk I/O and memory usage
- Consider processing in smaller batches

## Examples Directory

The `examples/` directory contains sample CSV files for each conversion type:

- `batch_rtstruct2seg.csv` - RTSTRUCT to DICOM SEG
- `batch_dicomseg.csv` - Volume to DICOM SEG
- `batch_dicom2nifti.csv` - DICOM to NIfTI
- `batch_itkimage2.csv` - DICOM SEG to NIfTI

Copy and modify these templates for your own batch processing needs.
