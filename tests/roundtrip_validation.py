#!/usr/bin/env python3
"""
Round-trip conversion validation with Dice coefficient calculation.

Tests the integrity of conversions by performing:
1. DICOM SEG → NIfTI → DICOM SEG (via metadata JSON)
2. Comparing original and round-trip converted images using Dice coefficient

Author: Based on validation approach for conversion pipelines
"""

import sys
import os
import json
import argparse
import SimpleITK as sitk
import numpy as np
from pathlib import Path


class RoundTripValidator:
    """Validates round-trip conversions using Dice coefficient."""
    
    def __init__(self, tolerance=0.95, verbose=False):
        """
        Initialize validator.
        
        Args:
            tolerance: Minimum Dice coefficient to pass (default: 0.95)
            verbose: Enable verbose output
        """
        self.tolerance = tolerance
        self.verbose = verbose
        self.results = []
        
    def calculate_dice(self, img1, img2):
        """
        Calculate Dice coefficient between two images.
        
        Args:
            img1: First SimpleITK image (binary or multi-label)
            img2: Second SimpleITK image (binary or multi-label)
            
        Returns:
            dict: Dice coefficients per label and overall
        """
        # Convert to numpy arrays
        arr1 = sitk.GetArrayFromImage(img1)
        arr2 = sitk.GetArrayFromImage(img2)
        
        if arr1.shape != arr2.shape:
            if self.verbose:
                print(f"  Warning: Shape mismatch {arr1.shape} vs {arr2.shape}")
            # Try to resample img2 to match img1
            resampler = sitk.ResampleImageFilter()
            resampler.SetReferenceImage(img1)
            resampler.SetInterpolator(sitk.sitkNearestNeighbor)
            img2_resampled = resampler.Execute(img2)
            arr2 = sitk.GetArrayFromImage(img2_resampled)
            if self.verbose:
                print(f"  Resampled to {arr2.shape}")
        
        # Find unique labels (excluding background 0)
        labels1 = np.unique(arr1[arr1 > 0])
        labels2 = np.unique(arr2[arr2 > 0])
        all_labels = np.unique(np.concatenate([labels1, labels2]))
        
        if len(all_labels) == 0:
            return {"overall": 0.0, "labels": {}, "warning": "No non-zero labels found"}
        
        dice_per_label = {}
        
        for label in all_labels:
            mask1 = (arr1 == label).astype(np.uint8)
            mask2 = (arr2 == label).astype(np.uint8)
            
            intersection = np.sum(mask1 * mask2)
            sum_masks = np.sum(mask1) + np.sum(mask2)
            
            if sum_masks == 0:
                dice = 0.0
            else:
                dice = 2.0 * intersection / sum_masks
            
            dice_per_label[int(label)] = float(dice)
        
        # Calculate overall Dice (mean of all labels)
        overall_dice = np.mean(list(dice_per_label.values()))
        
        return {
            "overall": float(overall_dice),
            "labels": dice_per_label,
            "label_count": len(all_labels)
        }
    
    def validate_geometry(self, img1, img2):
        """
        Validate that geometry matches between images.
        
        Returns:
            dict: Geometry comparison results
        """
        size1 = img1.GetSize()
        size2 = img2.GetSize()
        
        spacing1 = img1.GetSpacing()
        spacing2 = img2.GetSpacing()
        
        origin1 = img1.GetOrigin()
        origin2 = img2.GetOrigin()
        
        direction1 = img1.GetDirection()
        direction2 = img2.GetDirection()
        
        return {
            "size_match": size1 == size2,
            "size1": size1,
            "size2": size2,
            "spacing_match": np.allclose(spacing1, spacing2, rtol=1e-3),
            "spacing1": spacing1,
            "spacing2": spacing2,
            "origin_match": np.allclose(origin1, origin2, rtol=1.0),
            "origin1": origin1,
            "origin2": origin2,
            "direction_match": np.allclose(direction1, direction2, rtol=1e-3),
        }
    
    def validate_roundtrip(self, original_nifti, roundtrip_nifti, test_name=""):
        """
        Validate a round-trip conversion.
        
        Args:
            original_nifti: Path to original NIfTI file
            roundtrip_nifti: Path to round-trip converted NIfTI file
            test_name: Name of the test for reporting
            
        Returns:
            dict: Validation results
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Validating: {test_name}")
            print(f"{'='*60}")
            print(f"Original:   {original_nifti}")
            print(f"Round-trip: {roundtrip_nifti}")
        
        # Check files exist
        if not os.path.exists(original_nifti):
            return {
                "test_name": test_name,
                "status": "FAILED",
                "error": f"Original file not found: {original_nifti}"
            }
        
        if not os.path.exists(roundtrip_nifti):
            return {
                "test_name": test_name,
                "status": "FAILED",
                "error": f"Round-trip file not found: {roundtrip_nifti}"
            }
        
        try:
            # Load images
            img_original = sitk.ReadImage(str(original_nifti))
            img_roundtrip = sitk.ReadImage(str(roundtrip_nifti))
            
            # Validate geometry
            geometry = self.validate_geometry(img_original, img_roundtrip)
            
            if self.verbose:
                print(f"\nGeometry Check:")
                print(f"  Size match: {geometry['size_match']}")
                print(f"  Spacing match: {geometry['spacing_match']}")
                print(f"  Origin match: {geometry['origin_match']}")
                print(f"  Direction match: {geometry['direction_match']}")
            
            # Calculate Dice coefficient
            dice_results = self.calculate_dice(img_original, img_roundtrip)
            
            if self.verbose:
                print(f"\nDice Coefficient:")
                print(f"  Overall: {dice_results['overall']:.4f}")
                print(f"  Labels: {dice_results.get('label_count', 0)}")
                for label, dice in dice_results.get('labels', {}).items():
                    print(f"    Label {label}: {dice:.4f}")
            
            # Determine pass/fail
            passed = dice_results['overall'] >= self.tolerance
            
            result = {
                "test_name": test_name,
                "status": "PASSED" if passed else "FAILED",
                "dice_overall": dice_results['overall'],
                "dice_per_label": dice_results.get('labels', {}),
                "label_count": dice_results.get('label_count', 0),
                "geometry": geometry,
                "tolerance": self.tolerance,
            }
            
            if self.verbose:
                result_str = "PASSED" if passed else "FAILED"
                print(f"\nResult: {result_str}")
                if not passed:
                    print(f"  Dice {dice_results['overall']:.4f} < {self.tolerance} (tolerance)")
            
            self.results.append(result)
            return result
            
        except Exception as e:
            result = {
                "test_name": test_name,
                "status": "ERROR",
                "error": str(e)
            }
            if self.verbose:
                print(f"\n✗ ERROR: {e}")
            self.results.append(result)
            return result
    
    def generate_report(self, output_file=None):
        """
        Generate a summary report of all validations.
        
        Args:
            output_file: Optional path to save JSON report
            
        Returns:
            dict: Summary report
        """
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASSED')
        failed = sum(1 for r in self.results if r['status'] == 'FAILED')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        
        report = {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "success_rate": passed / total if total > 0 else 0.0
            },
            "results": self.results
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            if self.verbose:
                print(f"\nReport saved to: {output_file}")
        
        return report
    
    def print_summary(self):
        """Print a summary of validation results."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASSED')
        failed = sum(1 for r in self.results if r['status'] == 'FAILED')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        
        print("\n" + "="*60)
        print("ROUND-TRIP VALIDATION SUMMARY")
        print("="*60)
        print(f"Total tests:    {total}")
        print(f"Passed:         {passed}")
        print(f"Failed:         {failed}")
        print(f"Errors:         {errors}")
        print(f"Success rate:   {passed/total*100 if total > 0 else 0:.1f}%")
        print("="*60)
        
        if failed > 0 or errors > 0:
            print("\nFailed/Error tests:")
            for result in self.results:
                if result['status'] in ['FAILED', 'ERROR']:
                    print(f"  - {result['test_name']}")
                    if 'error' in result:
                        print(f"    Error: {result['error']}")
                    elif 'dice_overall' in result:
                        print(f"    Dice: {result['dice_overall']:.4f} < {result['tolerance']}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate round-trip DICOM SEG ↔ NIfTI conversions using Dice coefficient",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate single round-trip conversion
  %(prog)s --original seg_original.nii.gz --roundtrip seg_roundtrip.nii.gz
  
  # Validate with custom tolerance
  %(prog)s --original seg1.nii.gz --roundtrip seg2.nii.gz --tolerance 0.98
  
  # Batch validation from directory
  %(prog)s --batch-dir /path/to/test_output --report report.json
  
  # Verbose mode with detailed output
  %(prog)s --original seg1.nii.gz --roundtrip seg2.nii.gz --verbose
        """
    )
    
    parser.add_argument('--original', '-o', help='Original NIfTI file')
    parser.add_argument('--roundtrip', '-r', help='Round-trip converted NIfTI file')
    parser.add_argument('--batch-dir', '-b', help='Directory with test results (batch mode)')
    parser.add_argument('--tolerance', '-t', type=float, default=0.95,
                       help='Minimum Dice coefficient to pass (default: 0.95)')
    parser.add_argument('--report', help='Output JSON report file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    validator = RoundTripValidator(tolerance=args.tolerance, verbose=args.verbose)
    
    if args.batch_dir:
        # Batch mode: scan directory for round-trip pairs
        batch_dir = Path(args.batch_dir)
        if not batch_dir.exists():
            print(f"Error: Batch directory not found: {batch_dir}")
            return 1
        
        # Find all *_original.nii.gz and *_roundtrip.nii.gz pairs
        original_files = sorted(batch_dir.glob("*_original.nii.gz"))
        
        if len(original_files) == 0:
            print(f"Warning: No *_original.nii.gz files found in {batch_dir}")
            return 1
        
        for orig_file in original_files:
            # Find corresponding roundtrip file
            base_name = orig_file.stem.replace('_original', '')
            roundtrip_file = batch_dir / f"{base_name}_roundtrip.nii.gz"
            
            if roundtrip_file.exists():
                validator.validate_roundtrip(
                    str(orig_file),
                    str(roundtrip_file),
                    test_name=base_name
                )
            else:
                print(f"Warning: No round-trip file for {orig_file.name}")
        
    elif args.original and args.roundtrip:
        # Single file mode
        test_name = Path(args.original).stem
        validator.validate_roundtrip(args.original, args.roundtrip, test_name)
    else:
        parser.print_help()
        return 1
    
    # Print summary
    validator.print_summary()
    
    # Generate report if requested
    if args.report:
        validator.generate_report(args.report)
    
    # Return exit code based on results
    failed = sum(1 for r in validator.results if r['status'] != 'PASSED')
    return 1 if failed > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
