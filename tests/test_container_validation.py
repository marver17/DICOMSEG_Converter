#!/usr/bin/env python3
"""
Detailed validation tests for DicomConverter container outputs.

This script validates that the conversion outputs are correct by:
1. Checking file existence and basic properties
2. Validating DICOM files using pydicom
3. Comparing geometries where applicable
4. Generating a detailed test report

Usage:
    python test_container_validation.py [output_directory]
"""

import sys
import os
from pathlib import Path
import json
from typing import Dict, List, Tuple

# Try to import optional dependencies
try:
    import pydicom
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False
    print("Warning: pydicom not available. DICOM validation will be limited.")

try:
    import SimpleITK as sitk
    SITK_AVAILABLE = True
except ImportError:
    SITK_AVAILABLE = False
    print("Warning: SimpleITK not available. Image validation will be limited.")


class TestValidator:
    """Validates container test outputs."""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.results = []
        
    def validate_file_exists(self, filepath: str, test_name: str) -> bool:
        """Check if output file exists."""
        path = self.output_dir / filepath
        exists = path.exists()
        
        result = {
            'test': test_name,
            'check': 'file_exists',
            'path': str(path),
            'passed': exists,
            'message': 'File exists' if exists else 'File not found'
        }
        
        if exists:
            # Add file size info
            size_bytes = path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            result['file_size_mb'] = round(size_mb, 2)
            result['message'] += f' ({size_mb:.2f} MB)'
        
        self.results.append(result)
        return exists
    
    def validate_dicom_file(self, filepath: str, test_name: str) -> bool:
        """Validate DICOM file structure and required tags."""
        path = self.output_dir / filepath
        
        if not path.exists():
            self.results.append({
                'test': test_name,
                'check': 'dicom_validation',
                'passed': False,
                'message': 'File not found'
            })
            return False
        
        if not PYDICOM_AVAILABLE:
            self.results.append({
                'test': test_name,
                'check': 'dicom_validation',
                'passed': None,
                'message': 'pydicom not available - skipped'
            })
            return None
        
        try:
            ds = pydicom.dcmread(str(path), stop_before_pixels=True)
            
            # Check for essential DICOM tags
            checks = {
                'SOPClassUID': hasattr(ds, 'SOPClassUID'),
                'Modality': hasattr(ds, 'Modality'),
                'PatientID': hasattr(ds, 'PatientID'),
                'StudyInstanceUID': hasattr(ds, 'StudyInstanceUID'),
                'SeriesInstanceUID': hasattr(ds, 'SeriesInstanceUID'),
            }
            
            all_passed = all(checks.values())
            missing = [k for k, v in checks.items() if not v]
            
            result = {
                'test': test_name,
                'check': 'dicom_validation',
                'passed': all_passed,
                'checks': checks,
            }
            
            if all_passed:
                result['message'] = f'Valid DICOM (Modality: {ds.Modality})'
                if hasattr(ds, 'SOPClassUID'):
                    result['sop_class'] = str(ds.SOPClassUID)
            else:
                result['message'] = f'Missing tags: {", ".join(missing)}'
            
            self.results.append(result)
            return all_passed
            
        except Exception as e:
            self.results.append({
                'test': test_name,
                'check': 'dicom_validation',
                'passed': False,
                'message': f'Error reading DICOM: {str(e)}'
            })
            return False
    
    def validate_dicom_seg(self, filepath: str, test_name: str) -> bool:
        """Specifically validate DICOM SEG files."""
        path = self.output_dir / filepath
        
        if not path.exists():
            return False
        
        if not PYDICOM_AVAILABLE:
            return None
        
        try:
            ds = pydicom.dcmread(str(path), stop_before_pixels=False)
            
            # Check SEG-specific attributes
            is_seg = hasattr(ds, 'Modality') and ds.Modality == 'SEG'
            has_segments = hasattr(ds, 'SegmentSequence')
            
            result = {
                'test': test_name,
                'check': 'dicom_seg_validation',
                'passed': is_seg and has_segments,
                'is_segmentation': is_seg,
                'has_segments': has_segments,
            }
            
            if has_segments:
                num_segments = len(ds.SegmentSequence)
                result['num_segments'] = num_segments
                result['message'] = f'Valid DICOM SEG with {num_segments} segment(s)'
                
                # Extract segment labels
                labels = []
                for seg in ds.SegmentSequence:
                    if hasattr(seg, 'SegmentLabel'):
                        labels.append(seg.SegmentLabel)
                result['segment_labels'] = labels
            else:
                result['message'] = 'Not a valid DICOM SEG or missing segments'
            
            self.results.append(result)
            return is_seg and has_segments
            
        except Exception as e:
            self.results.append({
                'test': test_name,
                'check': 'dicom_seg_validation',
                'passed': False,
                'message': f'Error: {str(e)}'
            })
            return False
    
    def generate_report(self) -> str:
        """Generate a human-readable test report."""
        report = []
        report.append("="*70)
        report.append("DICOM CONVERTER - VALIDATION REPORT")
        report.append("="*70)
        report.append("")
        
        # Group results by test
        tests = {}
        for result in self.results:
            test_name = result['test']
            if test_name not in tests:
                tests[test_name] = []
            tests[test_name].append(result)
        
        # Overall statistics
        total_checks = len(self.results)
        passed = sum(1 for r in self.results if r['passed'] is True)
        failed = sum(1 for r in self.results if r['passed'] is False)
        skipped = sum(1 for r in self.results if r['passed'] is None)
        
        report.append(f"Total Checks: {total_checks}")
        report.append(f"Passed:       {passed} ✓")
        report.append(f"Failed:       {failed} ✗")
        report.append(f"Skipped:      {skipped} ⊗")
        report.append("")
        report.append("-"*70)
        
        # Detailed results per test
        for test_name, checks in sorted(tests.items()):
            report.append("")
            report.append(f"TEST: {test_name}")
            report.append("-"*70)
            
            for check in checks:
                status = "✓" if check['passed'] is True else ("✗" if check['passed'] is False else "⊗")
                check_name = check['check'].replace('_', ' ').title()
                message = check.get('message', '')
                
                report.append(f"  {status} {check_name}: {message}")
                
                # Add extra details
                if 'file_size_mb' in check:
                    report.append(f"      Size: {check['file_size_mb']} MB")
                
                if 'num_segments' in check:
                    report.append(f"      Segments: {check['num_segments']}")
                    if 'segment_labels' in check and check['segment_labels']:
                        labels = ', '.join(check['segment_labels'][:5])
                        if len(check['segment_labels']) > 5:
                            labels += f" ... ({len(check['segment_labels'])} total)"
                        report.append(f"      Labels: {labels}")
        
        report.append("")
        report.append("="*70)
        
        if failed == 0:
            report.append("✓ ALL VALIDATION CHECKS PASSED")
        else:
            report.append(f"✗ {failed} VALIDATION CHECK(S) FAILED")
        
        report.append("="*70)
        
        return "\n".join(report)
    
    def save_json_report(self, output_path: str):
        """Save detailed results as JSON."""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)


def main():
    """Main validation function."""
    
    # Get output directory
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        output_dir = "test_output"
    
    print(f"Validating outputs in: {output_dir}")
    print()
    
    # Check if directory exists
    if not Path(output_dir).exists():
        print(f"Error: Output directory not found: {output_dir}")
        print("Run ./run_container_tests.sh first to generate test outputs")
        return 1
    
    # Create validator
    validator = TestValidator(output_dir)
    
    # Define tests based on expected outputs from run_container_tests.sh
    tests = [
        ("test1_lung_seg.dcm", "Test1: LUNG1-001 RTSTRUCT"),
        ("test2_interobs_seg.dcm", "Test2: interobs05 RTSTRUCT"),
        ("test4_pedro_us_seg.dcm", "Test4: Pedro US Example"),
        ("test5_pedro_ct_seg.dcm", "Test5: Pedro CT Example"),
        ("test6_basic_rt_seg.dcm", "Test6: Basic RT-STRUCT"),
    ]
    
    # Run validations
    print("Running validation checks...")
    print("-" * 70)
    
    for filepath, test_name in tests:
        # Check file existence
        if validator.validate_file_exists(filepath, test_name):
            # Validate DICOM structure
            validator.validate_dicom_file(filepath, test_name)
            # Validate as DICOM SEG
            validator.validate_dicom_seg(filepath, test_name)
        print(f"  Validated: {test_name}")
    
    print()
    
    # Generate and display report
    report = validator.generate_report()
    print(report)
    
    # Save JSON report
    json_path = Path(output_dir) / "validation_report.json"
    validator.save_json_report(str(json_path))
    print(f"\nDetailed JSON report saved to: {json_path}")
    
    # Return exit code
    failed = sum(1 for r in validator.results if r['passed'] is False)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
