#!/usr/bin/env python3
"""
Generate HTML Test Report with Visual Comparisons

This script generates a comprehensive HTML report for DicomConverter tests,
including:
- Test summary statistics
- Visual comparison galleries for roundtrip tests
- Detailed per-test results
- Links to logs and validation reports

Usage:
    python3 generate_test_report.py --output-dir test_output --log-file test_log.txt
"""

import argparse
import json
import os
import re
from pathlib import Path
from datetime import datetime
import base64


def parse_test_log(log_file):
    """Parse test log file to extract test results"""
    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'tests': []
    }

    if not os.path.exists(log_file):
        return results

    with open(log_file, 'r') as f:
        content = f.read()

    # Extract test results using regex
    test_pattern = r'TEST \d+: (.+?)\n.*?Status: (PASSED|FAILED)'
    matches = re.findall(test_pattern, content, re.DOTALL)

    for test_name, status in matches:
        results['total'] += 1
        if status == 'PASSED':
            results['passed'] += 1
        else:
            results['failed'] += 1

        results['tests'].append({
            'name': test_name.strip(),
            'status': status
        })

    return results


def find_visual_comparisons(roundtrip_dir):
    """Find all visual comparison images in roundtrip directory"""
    visual_dirs = []

    if not os.path.exists(roundtrip_dir):
        return visual_dirs

    # Find all directories ending with _visual_comparison
    for item in sorted(os.listdir(roundtrip_dir)):
        item_path = os.path.join(roundtrip_dir, item)
        if os.path.isdir(item_path) and item.endswith('_visual_comparison'):
            images = sorted([
                f for f in os.listdir(item_path)
                if f.endswith('.png')
            ])

            if images:
                # Extract test name from directory
                test_name = item.replace('_visual_comparison', '').replace('_', ' ').title()

                visual_dirs.append({
                    'name': test_name,
                    'path': item_path,
                    'images': images
                })

    return visual_dirs


def encode_image_base64(image_path):
    """Encode image as base64 for embedding in HTML"""
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Warning: Could not encode image {image_path}: {e}")
        return None


def generate_html_report(output_dir, log_file):
    """Generate comprehensive HTML test report"""

    # Parse test results
    test_results = parse_test_log(log_file)

    # Find visual comparisons
    roundtrip_dir = os.path.join(output_dir, 'roundtrip')
    visual_comparisons = find_visual_comparisons(roundtrip_dir)

    # Check for validation report
    validation_report = os.path.join(output_dir, 'validation_report.json')
    validation_data = None
    if os.path.exists(validation_report):
        try:
            with open(validation_report, 'r') as f:
                validation_data = json.load(f)
        except:
            pass

    # Generate HTML
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DicomConverter Test Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        header .timestamp {{ opacity: 0.9; font-size: 0.9em; }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .stat-card .number {{
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }}

        .stat-card .label {{
            color: #666;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }}

        .stat-card.total .number {{ color: #667eea; }}
        .stat-card.passed .number {{ color: #48bb78; }}
        .stat-card.failed .number {{ color: #f56565; }}

        .section {{
            padding: 30px;
            border-bottom: 1px solid #e2e8f0;
        }}

        .section:last-child {{ border-bottom: none; }}

        .section h2 {{
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 1.8em;
            display: flex;
            align-items: center;
        }}

        .section h2::before {{
            content: '';
            width: 4px;
            height: 28px;
            background: #667eea;
            margin-right: 12px;
            border-radius: 2px;
        }}

        .visual-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .visual-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #e2e8f0;
        }}

        .visual-card h3 {{
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.1em;
        }}

        .visual-card img {{
            width: 100%;
            border-radius: 4px;
            border: 1px solid #cbd5e0;
            margin-bottom: 10px;
            cursor: pointer;
            transition: transform 0.2s;
        }}

        .visual-card img:hover {{
            transform: scale(1.02);
        }}

        .image-count {{
            text-align: center;
            color: #718096;
            font-size: 0.9em;
            margin-top: 10px;
        }}

        .test-list {{
            list-style: none;
        }}

        .test-item {{
            padding: 15px;
            border-left: 4px solid #e2e8f0;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .test-item.passed {{ border-left-color: #48bb78; }}
        .test-item.failed {{ border-left-color: #f56565; }}

        .test-status {{
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
        }}

        .test-status.passed {{
            background: #c6f6d5;
            color: #22543d;
        }}

        .test-status.failed {{
            background: #fed7d7;
            color: #742a2a;
        }}

        .no-data {{
            text-align: center;
            padding: 40px;
            color: #a0aec0;
            font-style: italic;
        }}

        .file-links {{
            background: #edf2f7;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }}

        .file-links h3 {{
            margin-bottom: 15px;
            color: #2d3748;
        }}

        .file-links ul {{
            list-style: none;
        }}

        .file-links li {{
            padding: 8px 0;
        }}

        .file-links a {{
            color: #667eea;
            text-decoration: none;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}

        .file-links a:hover {{
            text-decoration: underline;
        }}

        /* Modal for full-size images */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            cursor: pointer;
        }}

        .modal img {{
            display: block;
            margin: auto;
            max-width: 95%;
            max-height: 95%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}

        .modal:hover {{
            opacity: 0.95;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏥 DicomConverter Test Report</h1>
            <div class="timestamp">Generated: {timestamp}</div>
        </header>

        <div class="summary">
            <div class="stat-card total">
                <div class="label">Total Tests</div>
                <div class="number">{test_results['total']}</div>
            </div>
            <div class="stat-card passed">
                <div class="label">Passed</div>
                <div class="number">{test_results['passed']}</div>
            </div>
            <div class="stat-card failed">
                <div class="label">Failed</div>
                <div class="number">{test_results['failed']}</div>
            </div>
        </div>
"""

    # Visual Comparisons Section
    if visual_comparisons:
        html_content += """
        <div class="section">
            <h2>📊 Visual Comparisons (Roundtrip Tests)</h2>
            <p>Side-by-side comparison of original DICOM SEG vs roundtrip-converted DICOM SEG.
            Click on any image to view full size.</p>
"""

        for vc in visual_comparisons:
            html_content += f"""
            <div class="visual-card">
                <h3>{vc['name']}</h3>
                <div class="visual-grid">
"""
            # Show first 3 images as thumbnails
            for img in vc['images'][:3]:
                img_path = os.path.join(vc['path'], img)
                img_base64 = encode_image_base64(img_path)

                if img_base64:
                    html_content += f"""
                    <img src="data:image/png;base64,{img_base64}"
                         alt="{img}"
                         onclick="showModal(this.src)" />
"""

            html_content += f"""
                </div>
                <div class="image-count">
                    {len(vc['images'])} comparison images generated
                </div>
            </div>
"""

        html_content += """
        </div>
"""
    else:
        html_content += """
        <div class="section">
            <h2>📊 Visual Comparisons</h2>
            <div class="no-data">
                No visual comparison images found.
                Visual comparisons are generated for successful roundtrip tests.
            </div>
        </div>
"""

    # Test Results Section
    if test_results['tests']:
        html_content += """
        <div class="section">
            <h2>✅ Test Results</h2>
            <ul class="test-list">
"""

        for test in test_results['tests']:
            status_class = test['status'].lower()
            html_content += f"""
                <li class="test-item {status_class}">
                    <span>{test['name']}</span>
                    <span class="test-status {status_class}">{test['status']}</span>
                </li>
"""

        html_content += """
            </ul>
        </div>
"""

    # File Links Section
    html_content += f"""
        <div class="section">
            <div class="file-links">
                <h3>📁 Additional Files</h3>
                <ul>
                    <li>📄 <a href="{os.path.basename(log_file)}">Test Log (detailed execution trace)</a></li>
"""

    if validation_data:
        html_content += """
                    <li>📊 <a href="validation_report.json">Validation Report (JSON)</a></li>
"""

    if os.path.exists(roundtrip_dir):
        html_content += """
                    <li>📂 <a href="roundtrip/">Roundtrip Test Outputs</a></li>
"""

    html_content += """
                </ul>
            </div>
        </div>
    </div>

    <!-- Modal for full-size images -->
    <div id="imageModal" class="modal" onclick="hideModal()">
        <img id="modalImage" />
    </div>

    <script>
        function showModal(src) {
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImage').src = src;
        }

        function hideModal() {
            document.getElementById('imageModal').style.display = 'none';
        }

        // ESC key to close modal
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                hideModal();
            }
        });
    </script>
</body>
</html>
"""

    # Write HTML report
    report_path = os.path.join(output_dir, 'test_report.html')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return report_path


def main():
    parser = argparse.ArgumentParser(
        description='Generate HTML test report with visual comparisons'
    )
    parser.add_argument(
        '--output-dir',
        required=True,
        help='Test output directory'
    )
    parser.add_argument(
        '--log-file',
        required=True,
        help='Path to test log file'
    )

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.output_dir):
        print(f"Error: Output directory not found: {args.output_dir}")
        return 1

    if not os.path.exists(args.log_file):
        print(f"Warning: Log file not found: {args.log_file}")
        print("Report will be generated with limited information")

    # Generate report
    try:
        report_path = generate_html_report(args.output_dir, args.log_file)
        print(f"✓ HTML report generated: {report_path}")
        print(f"  Open in browser: file://{os.path.abspath(report_path)}")
        return 0
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
