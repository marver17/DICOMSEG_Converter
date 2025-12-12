#!/usr/bin/env python3
"""
Generate visual comparison images for DICOM SEG roundtrip validation.

This script creates side-by-side comparison images showing:
- Original DICOM SEG overlay on DICOM images
- Reconverted DICOM SEG overlay on DICOM images

For multiple slices where segmentation is present.
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pydicom
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib import cm
import SimpleITK as sitk

try:
    from pydicom_seg import SegmentReader
except ImportError:
    print("Warning: pydicom_seg not available, using fallback methods")
    SegmentReader = None


def load_dicom_series(dicom_dir):
    """Load DICOM series and return sorted array and metadata."""
    reader = sitk.ImageSeriesReader()
    dicom_files = reader.GetGDCMSeriesFileNames(str(dicom_dir))

    if not dicom_files:
        raise ValueError(f"No DICOM files found in {dicom_dir}")

    reader.SetFileNames(dicom_files)
    image = reader.Execute()

    # Convert to numpy array (Z, Y, X)
    array = sitk.GetArrayFromImage(image)

    return array, image, dicom_files


def load_dicom_seg(seg_file):
    """Load DICOM SEG and return segmentation array."""
    if SegmentReader is not None:
        try:
            reader = SegmentReader()
            result = reader.read(str(seg_file))

            # Get the image and convert to numpy
            seg_image = result.image
            seg_array = sitk.GetArrayFromImage(seg_image)

            return seg_array
        except Exception as e:
            print(f"pydicom_seg failed: {e}, using SimpleITK")

    # Fallback: try to load as regular image
    try:
        image = sitk.ReadImage(str(seg_file))
        seg_array = sitk.GetArrayFromImage(image)
        return seg_array
    except Exception as e:
        print(f"Failed to load DICOM SEG with SimpleITK: {e}")
        raise


def find_slices_with_segmentation(seg_array, min_pixels=10):
    """Find slice indices where segmentation exists."""
    slices_with_seg = []

    for i in range(seg_array.shape[0]):
        slice_data = seg_array[i]
        if np.count_nonzero(slice_data) >= min_pixels:
            slices_with_seg.append(i)

    return slices_with_seg


def normalize_image(img_array):
    """Normalize image to 0-1 range for display."""
    img_min = np.min(img_array)
    img_max = np.max(img_array)

    if img_max > img_min:
        return (img_array - img_min) / (img_max - img_min)
    else:
        return np.zeros_like(img_array)


def create_overlay(image_slice, seg_slice, alpha=0.5, colormap='jet'):
    """Create RGB overlay of segmentation on grayscale image."""
    # Normalize image to 0-1
    img_normalized = normalize_image(image_slice)

    # Convert grayscale to RGB
    img_rgb = np.stack([img_normalized] * 3, axis=-1)

    # Create segmentation overlay
    seg_mask = seg_slice > 0

    if np.any(seg_mask):
        # Get colormap
        cmap = cm.get_cmap(colormap)

        # Normalize segmentation values
        seg_normalized = normalize_image(seg_slice)

        # Apply colormap
        seg_colored = cmap(seg_normalized)[:, :, :3]  # RGB only

        # Blend with image where segmentation exists
        img_rgb[seg_mask] = (1 - alpha) * img_rgb[seg_mask] + alpha * seg_colored[seg_mask]

    return img_rgb


def select_representative_slices(slice_indices, num_slices=5):
    """Select evenly distributed slices from available indices."""
    if len(slice_indices) <= num_slices:
        return slice_indices

    # Select evenly distributed slices
    step = len(slice_indices) / num_slices
    selected = [slice_indices[int(i * step)] for i in range(num_slices)]

    return selected


def generate_comparison_images(dicom_dir, original_seg, reconverted_seg, output_dir, num_slices=5):
    """Generate comparison images for multiple slices."""
    print(f"Loading DICOM series from {dicom_dir}...")
    dicom_array, dicom_image, dicom_files = load_dicom_series(dicom_dir)

    print(f"Loading original DICOM SEG from {original_seg}...")
    orig_seg_array = load_dicom_seg(original_seg)

    print(f"Loading reconverted DICOM SEG from {reconverted_seg}...")
    reconv_seg_array = load_dicom_seg(reconverted_seg)

    # Check dimensions match
    if dicom_array.shape != orig_seg_array.shape:
        print(f"Warning: DICOM shape {dicom_array.shape} != original SEG shape {orig_seg_array.shape}")
        # Try to match dimensions
        min_z = min(dicom_array.shape[0], orig_seg_array.shape[0])
        dicom_array = dicom_array[:min_z]
        orig_seg_array = orig_seg_array[:min_z]
        reconv_seg_array = reconv_seg_array[:min_z]

    # Find slices with segmentation
    print("Finding slices with segmentation...")
    orig_slices = find_slices_with_segmentation(orig_seg_array)
    reconv_slices = find_slices_with_segmentation(reconv_seg_array)

    # Use union of slices
    all_slices = sorted(set(orig_slices + reconv_slices))

    if not all_slices:
        print("Warning: No slices with segmentation found!")
        return 0

    print(f"Found {len(all_slices)} slices with segmentation")

    # Select representative slices
    selected_slices = select_representative_slices(all_slices, num_slices)
    print(f"Selected {len(selected_slices)} slices for visualization: {selected_slices}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate comparison for each selected slice
    for slice_idx in selected_slices:
        print(f"Generating comparison for slice {slice_idx}/{dicom_array.shape[0]}...")

        # Create figure
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle(f'Slice {slice_idx + 1}/{dicom_array.shape[0]}', fontsize=14, fontweight='bold')

        # Get slices
        dicom_slice = dicom_array[slice_idx]
        orig_seg_slice = orig_seg_array[slice_idx]
        reconv_seg_slice = reconv_seg_array[slice_idx]

        # Create overlays
        orig_overlay = create_overlay(dicom_slice, orig_seg_slice)
        reconv_overlay = create_overlay(dicom_slice, reconv_seg_slice)

        # Plot original
        axes[0].imshow(orig_overlay)
        axes[0].set_title('Original DICOM SEG', fontsize=12, fontweight='bold')
        axes[0].axis('off')

        # Count pixels
        orig_pixels = np.count_nonzero(orig_seg_slice)
        axes[0].text(0.02, 0.02, f'{orig_pixels} pixels',
                     transform=axes[0].transAxes,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                     fontsize=10)

        # Plot reconverted
        axes[1].imshow(reconv_overlay)
        axes[1].set_title('Reconverted DICOM SEG', fontsize=12, fontweight='bold')
        axes[1].axis('off')

        # Count pixels
        reconv_pixels = np.count_nonzero(reconv_seg_slice)
        axes[1].text(0.02, 0.02, f'{reconv_pixels} pixels',
                     transform=axes[1].transAxes,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                     fontsize=10)

        # Calculate difference
        if orig_pixels > 0:
            diff_percent = abs(reconv_pixels - orig_pixels) / orig_pixels * 100
            fig.text(0.5, 0.02, f'Difference: {diff_percent:.2f}%',
                     ha='center', fontsize=10,
                     bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

        plt.tight_layout()

        # Save figure
        output_file = Path(output_dir) / f'slice_{slice_idx:03d}_comparison.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"  Saved: {output_file.name}")

    print(f"\nGenerated {len(selected_slices)} comparison images in {output_dir}")
    return len(selected_slices)


def main():
    parser = argparse.ArgumentParser(
        description='Generate visual comparison images for DICOM SEG roundtrip validation'
    )
    parser.add_argument('--dicom-images', required=True,
                        help='Directory containing original DICOM images')
    parser.add_argument('--original-seg', required=True,
                        help='Original DICOM SEG file')
    parser.add_argument('--reconverted-seg', required=True,
                        help='Reconverted DICOM SEG file')
    parser.add_argument('--output-dir', required=True,
                        help='Output directory for comparison images')
    parser.add_argument('--num-slices', type=int, default=5,
                        help='Number of slices to visualize (default: 5)')

    args = parser.parse_args()

    # Validate inputs
    if not os.path.isdir(args.dicom_images):
        print(f"Error: DICOM images directory not found: {args.dicom_images}")
        sys.exit(1)

    if not os.path.isfile(args.original_seg):
        print(f"Error: Original DICOM SEG not found: {args.original_seg}")
        sys.exit(1)

    if not os.path.isfile(args.reconverted_seg):
        print(f"Error: Reconverted DICOM SEG not found: {args.reconverted_seg}")
        sys.exit(1)

    try:
        num_generated = generate_comparison_images(
            args.dicom_images,
            args.original_seg,
            args.reconverted_seg,
            args.output_dir,
            args.num_slices
        )

        if num_generated > 0:
            print(f"\nSuccess! Generated {num_generated} comparison images.")
            sys.exit(0)
        else:
            print("\nWarning: No comparison images generated.")
            sys.exit(1)

    except Exception as e:
        print(f"\nError generating comparison images: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
