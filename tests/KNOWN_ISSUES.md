# Known Issues and Limitations

## Test Results Summary (Last Updated: 2025-01-04)

### ✅ Working Datasets (Full Round-Trip Success)
- **AMBL-001**: Dice 1.0000 (2 segments: Nipple_L, Nipple_R)
- **AMBL-004**: Dice 1.0000 (1 segment: Nipple_L)

Both datasets complete the full round-trip cycle:
1. DICOM SEG → NIfTI (separate files per segment)
2. NIfTI → DICOM SEG (using original metadata JSON)
3. DICOM SEG → NIfTI (merged extraction for validation)
4. Dice coefficient comparison: Original vs Round-trip

### ⚠️ Failing Datasets

#### LUNG1-001 (4 segments: GTV-1, Lung-Left, Lung-Right, Spinal-Cord)
- **Status**: Round-trip DICOM creation succeeds (Step 2), but Step 3 extraction fails
- **Issue**: `itkimage2` with `False` parameter creates 4 separate files (GTV-1.nii.gz, Lung-Left.nii.gz, etc.) instead of merged `segmentation.nii.gz`
- **Possible Cause**: Segments may be overlapping, preventing automatic merging
- **Next Steps**: 
  - Investigate if segments overlap using SimpleITK
  - Consider manual merging with different label priorities
  - Or accept separate files and modify Dice validation accordingly

#### interobs05 (10 segments)
- **Status**: Step 2 (NIfTI → DICOM SEG) fails
- **Error**: `ERROR: Failed to match label from image to the segment metadata!`
- **Issue**: Label IDs in the 10 extracted NIfTI files don't match metadata JSON expectations
- **Possible Causes**:
  - File naming/ordering mismatch (1.nii.gz through 10.nii.gz vs expected segment order)
  - Label ID values inside NIfTI files don't correspond to JSON segmentAttributes[].labelID
  - Complex segment structure with non-sequential label IDs
- **Next Steps**:
  - Inspect actual voxel label values in each NIfTI file
  - Compare with labelID values in meta.json
  - Check if segment ordering matches file numbering

## Round-trip Conversion Requirements (SOLVED)

### Original Issue (Now Fixed)
Initial attempts to use merged NIfTI files with modified JSON metadata failed.

### Working Solution
The correct approach for round-trip conversion:

1. **Extract separate segment files** (not merged):
   ```bash
   itkimage --inputDICOM seg.dcm --outputDirectory output --outputType nifti
   # Creates: 1.nii.gz, 2.nii.gz, ..., N.nii.gz, meta.json
   ```

2. **Use original metadata JSON** (unmodified):
   - Do not modify segmentAttributes count
   - Each NIfTI file corresponds to one segmentAttributes entry
   - Files must match the number of segments in JSON

3. **Convert back to DICOM SEG**:
   ```bash
   itkimage2segimage --inputImageList seg_files --inputMetadata meta.json \
                     --inputDICOMDirectory ref_series --outputDICOM output.dcm
   ```

This approach achieves perfect Dice 1.0000 for AMBL-001 and AMBL-004.

### Potential Solutions
1. **Use dcmqi reference examples**: Find working metadata JSON examples from dcmqi repository
2. **Schema validation**: Use dcmqi online validator (http://qiicr.org/dcmqi/#/validators) to identify missing/incorrect fields
3. **Separate segments**: Instead of merged file, create individual NIfTI files for each segment (matching segmentAttributes count)
4. **Alternative tools**: Investigate other DICOM SEG creation tools (e.g., pydicom-seg, highdicom)

### Workaround
For now, use the cross-conversion tests (Tests 9-13) which successfully validate that:
- Different conversion tools produce identical results (Dice = 1.0000)
- Segmentation geometry and data are preserved through conversion
- DICOM SEG → NIfTI conversion is reliable and reversible

### References
- dcmqi GitHub: https://github.com/QIICR/dcmqi
- dcmqi validators: http://qiicr.org/dcmqi/#/validators
- Test logs: `tests/test_output/test_log_*.txt`
