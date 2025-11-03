#!/usr/bin/env python3
"""
CSV Batch Processor for DicomConverter
Reads a CSV file and executes batch conversions with support for:
- All conversion modes (rtstruct2seg, dicomseg, dicom2nifti, itkimage2)
- Dry-run mode
- Parallel execution
- Per-row logging
- Error handling and continue-on-error
"""

import csv
import sys
import os
import argparse
import subprocess
import shlex
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional


class BatchProcessor:
    def __init__(self, args):
        self.args = args
        self.script_path = "/usr/dicomconverter/run_scripts"
        self.errors = []
        
    def build_command(self, cmd: str, row: Dict[str, str]) -> List[str]:
        """Build shell command based on the conversion type and CSV row."""
        
        if cmd == 'rtstruct2seg':
            input1 = row.get('input1', '').strip()
            input2 = row.get('input2', '').strip()
            output = row.get('output', '').strip()
            
            if not output and self.args.output_dir:
                # Generate output filename from input2 (RTSTRUCT file)
                output_name = Path(input2).stem + '.dcm'
                output = str(Path(self.args.output_dir) / output_name)
            
            extra_args = row.get('extra_args', '').strip()
            
            cmd_parts = [self.script_path, 'rtstruct2seg', input1, input2, output]
            if extra_args:
                cmd_parts.extend(shlex.split(extra_args))
            
            return cmd_parts
        
        elif cmd == 'dicomseg':
            # For dicomseg, build command from all CSV columns
            cmd_parts = [self.script_path, 'dicomseg']
            
            for key, value in row.items():
                value = value.strip()
                if not value or key in ['id', 'extra_args']:
                    continue
                cmd_parts.append(f'--{key}')
                cmd_parts.append(value)
            
            # Add extra_args if present
            extra_args = row.get('extra_args', '').strip()
            if extra_args:
                cmd_parts.extend(shlex.split(extra_args))
            
            return cmd_parts
        
        elif cmd == 'dicom2nifti':
            input_path = row.get('input', '').strip()
            output = row.get('output', '').strip()
            
            if not output and self.args.output_dir:
                output_name = Path(input_path).stem + '.nii.gz'
                output = str(Path(self.args.output_dir) / output_name)
            
            return [self.script_path, 'dicom2nifti', input_path, output]
        
        elif cmd == 'itkimage2':
            input_path = row.get('input', '').strip()
            orientation = row.get('orientation', 'False').strip()
            output = row.get('output', '').strip()
            
            if not output and self.args.output_dir:
                output = str(Path(self.args.output_dir) / Path(input_path).stem)
            
            return [self.script_path, 'itkimage2', input_path, output, orientation]
        
        elif cmd == 'itkimage':
            # Generic command builder for itkimage
            cmd_parts = [self.script_path, 'itkimage']
            
            for key, value in row.items():
                value = value.strip()
                if not value or key in ['id', 'extra_args']:
                    continue
                cmd_parts.append(f'--{key}')
                cmd_parts.append(value)
            
            extra_args = row.get('extra_args', '').strip()
            if extra_args:
                cmd_parts.extend(shlex.split(extra_args))
            
            return cmd_parts
        
        else:
            raise ValueError(f"Unsupported command: {cmd}")
    
    def validate_row(self, cmd: str, row: Dict[str, str], row_num: int) -> Optional[str]:
        """Validate that required fields are present in the row."""
        
        required_fields = {
            'rtstruct2seg': ['input1', 'input2'],
            'dicomseg': ['inputImageList', 'inputDICOMDirectory', 'outputDICOM', 'inputMetadata'],
            'dicom2nifti': ['input'],
            'itkimage2': ['input'],
            'itkimage': ['inputDICOM', 'outputDirectory']
        }
        
        if cmd not in required_fields:
            return None
        
        missing = []
        for field in required_fields[cmd]:
            if not row.get(field, '').strip():
                missing.append(field)
        
        if missing:
            return f"Row {row_num}: missing required fields: {', '.join(missing)}"
        
        return None
    
    def run_one(self, cmd: str, row: Dict[str, str], row_num: int) -> tuple:
        """Execute one conversion job."""
        
        row_id = row.get('id', f'row_{row_num}')
        
        # Validate row
        validation_error = self.validate_row(cmd, row, row_num)
        if validation_error and not self.args.skip_validation:
            return (row_id, 1, validation_error, '')
        
        try:
            command = self.build_command(cmd, row)
        except Exception as e:
            error_msg = f"Failed to build command for {row_id}: {str(e)}"
            return (row_id, 1, error_msg, '')
        
        if self.args.dry_run:
            cmd_str = ' '.join(shlex.quote(p) for p in command)
            return (row_id, 0, f"[DRY-RUN] {cmd_str}", '')
        
        # Create output directory if needed
        if self.args.output_dir:
            os.makedirs(self.args.output_dir, exist_ok=True)
        
        # Execute command
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.args.timeout if self.args.timeout > 0 else None
            )
            
            return (row_id, result.returncode, result.stdout, result.stderr)
        
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {self.args.timeout}s"
            return (row_id, 124, '', error_msg)
        
        except Exception as e:
            return (row_id, 1, '', str(e))
    
    def process_csv(self):
        """Main processing loop."""
        
        if not os.path.exists(self.args.csv):
            print(f"Error: CSV file '{self.args.csv}' not found", file=sys.stderr)
            return 1
        
        # Read CSV
        with open(self.args.csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            print("Warning: CSV file is empty or has no data rows", file=sys.stderr)
            return 0
        
        print(f"Processing {len(rows)} rows from {self.args.csv}")
        print(f"Command: {self.args.command}")
        print(f"Workers: {self.args.workers}")
        print(f"Dry-run: {self.args.dry_run}")
        print("-" * 60)
        
        # Process rows
        if self.args.workers == 1:
            # Sequential processing
            results = []
            for i, row in enumerate(rows, 1):
                result = self.run_one(self.args.command, row, i)
                results.append(result)
                self._print_result(result, i, len(rows))
        else:
            # Parallel processing
            results = []
            with ThreadPoolExecutor(max_workers=self.args.workers) as executor:
                futures = {
                    executor.submit(self.run_one, self.args.command, row, i): i
                    for i, row in enumerate(rows, 1)
                }
                
                for future in as_completed(futures):
                    row_num = futures[future]
                    result = future.result()
                    results.append(result)
                    self._print_result(result, row_num, len(rows))
        
        # Summary
        print("-" * 60)
        print(f"Completed: {len(results)} jobs")
        
        success_count = sum(1 for r in results if r[1] == 0)
        failure_count = len(results) - success_count
        
        print(f"Success: {success_count}")
        print(f"Failed: {failure_count}")
        
        if self.args.log_file:
            self._write_log(results)
            print(f"Log written to: {self.args.log_file}")
        
        # Return non-zero if any job failed (unless continue-on-error)
        if failure_count > 0 and not self.args.continue_on_error:
            return 1
        
        return 0
    
    def _print_result(self, result: tuple, row_num: int, total: int):
        """Print result of one job."""
        row_id, exit_code, stdout, stderr = result
        
        status = "✓" if exit_code == 0 else "✗"
        print(f"[{row_num}/{total}] {status} {row_id} (exit: {exit_code})")
        
        if stdout and self.args.verbose:
            print(f"  stdout: {stdout[:200]}")
        
        if stderr:
            print(f"  stderr: {stderr[:200]}", file=sys.stderr)
    
    def _write_log(self, results: List[tuple]):
        """Write detailed log file."""
        with open(self.args.log_file, 'w') as f:
            f.write("row_id,exit_code,stdout,stderr\n")
            for row_id, exit_code, stdout, stderr in results:
                # Escape quotes and newlines for CSV
                stdout_esc = stdout.replace('"', '""').replace('\n', '\\n')
                stderr_esc = stderr.replace('"', '""').replace('\n', '\\n')
                f.write(f'"{row_id}",{exit_code},"{stdout_esc}","{stderr_esc}"\n')


def main():
    parser = argparse.ArgumentParser(
        description='Batch processor for DicomConverter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process RTSTRUCT conversions
  csv_batch.py rtstruct2seg --csv input.csv --output-dir /data/output
  
  # Dry-run to see commands without executing
  csv_batch.py dicomseg --csv batch.csv --dry-run
  
  # Parallel processing with 4 workers
  csv_batch.py dicom2nifti --csv files.csv --output-dir /data/nifti --workers 4
  
CSV Format Examples:
  rtstruct2seg: input1,input2,output (optional)
  dicomseg: inputImageList,inputDICOMDirectory,outputDICOM,inputMetadata
  dicom2nifti: input,output (optional)
  itkimage2: input,orientation,output (optional)
        """
    )
    
    parser.add_argument('command', 
                       choices=['rtstruct2seg', 'dicomseg', 'dicom2nifti', 'itkimage2', 'itkimage'],
                       help='Conversion command to execute')
    
    parser.add_argument('--csv', required=True,
                       help='CSV file with batch jobs (first row = header)')
    
    parser.add_argument('--output-dir', 
                       help='Base output directory (can be overridden in CSV)')
    
    parser.add_argument('--workers', type=int, default=1,
                       help='Number of parallel workers (default: 1)')
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Print commands without executing')
    
    parser.add_argument('--continue-on-error', action='store_true',
                       help='Continue processing even if jobs fail')
    
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip validation of required fields')
    
    parser.add_argument('--timeout', type=int, default=0,
                       help='Timeout per job in seconds (0 = no timeout)')
    
    parser.add_argument('--log-file',
                       help='Write detailed log to file')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    processor = BatchProcessor(args)
    sys.exit(processor.process_csv())


if __name__ == '__main__':
    main()
