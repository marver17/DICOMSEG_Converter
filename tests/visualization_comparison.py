#!/usr/bin/env python3
"""
Visualization tool for comparing DICOM images with segmentations.
Creates side-by-side plots showing:
- DICOM image with DICOM SEG overlay
- NIfTI image with NIfTI segmentation overlay
- RT-STRUCT overlays (if applicable)
"""

import argparse
import sys
import os
import numpy as np
import SimpleITK as sitk
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for Docker
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import pydicom
from pathlib import Path


def load_dicom_series(dicom_dir):
    """Load DICOM series as SimpleITK image."""
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(str(dicom_dir))
    if not dicom_names:
        raise ValueError(f"No DICOM files found in {dicom_dir}")
    reader.SetFileNames(dicom_names)
    return reader.Execute()


def load_dicom_seg(seg_file):
    """Load DICOM SEG file."""
    # For now, we'll use itkimage to extract it
    # In production, use pydicom-seg or similar
    return sitk.ReadImage(str(seg_file))


def get_middle_slice(image):
    """Get the middle slice index for a 3D image."""
    size = image.GetSize()
    return size[2] // 2 if len(size) == 3 else 0


def normalize_image(array):
    """Normalize image array to 0-1 range."""
    arr_min, arr_max = array.min(), array.max()
    if arr_max > arr_min:
        return (array - arr_min) / (arr_max - arr_min)
    return array


def create_overlay(image_array, seg_array, alpha=0.3):
    """Create RGB overlay of image with segmentation."""
    # Normalize image to 0-1
    img_norm = normalize_image(image_array)
    
    # Create RGB image (grayscale)
    rgb = np.stack([img_norm, img_norm, img_norm], axis=-1)
    
    # Create colored overlay for each label
    unique_labels = np.unique(seg_array[seg_array > 0])
    
    # Color map for different labels
    colors = [
        [1.0, 0.0, 0.0],  # Red
        [0.0, 1.0, 0.0],  # Green
        [0.0, 0.0, 1.0],  # Blue
        [1.0, 1.0, 0.0],  # Yellow
        [1.0, 0.0, 1.0],  # Magenta
        [0.0, 1.0, 1.0],  # Cyan
    ]
    
    for i, label in enumerate(unique_labels):
        mask = seg_array == label
        color = colors[i % len(colors)]
        for c in range(3):
            rgb[:, :, c] = np.where(mask, 
                                   rgb[:, :, c] * (1 - alpha) + color[c] * alpha,
                                   rgb[:, :, c])
    
    return rgb


def plot_comparison(dicom_img, dicom_seg, nifti_img, nifti_seg, 
                   output_file, title="Segmentation Comparison",
                   slice_idx=None):
    """Create comparison plot."""
    
    # Get arrays
    dicom_array = sitk.GetArrayFromImage(dicom_img)
    dicom_seg_array = sitk.GetArrayFromImage(dicom_seg)
    nifti_array = sitk.GetArrayFromImage(nifti_img)
    nifti_seg_array = sitk.GetArrayFromImage(nifti_seg)
    
    # Get middle slice if not specified
    if slice_idx is None:
        slice_idx = dicom_array.shape[0] // 2
    
    # Extract slices
    dicom_slice = dicom_array[slice_idx, :, :]
    dicom_seg_slice = dicom_seg_array[slice_idx, :, :]
    nifti_slice = nifti_array[slice_idx, :, :]
    nifti_seg_slice = nifti_seg_array[slice_idx, :, :]
    
    # Create overlays
    dicom_overlay = create_overlay(dicom_slice, dicom_seg_slice)
    nifti_overlay = create_overlay(nifti_slice, nifti_seg_slice)
    
    # Create figure with 2x2 subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    # DICOM image
    axes[0, 0].imshow(dicom_slice, cmap='gray')
    axes[0, 0].set_title('DICOM Image')
    axes[0, 0].axis('off')
    
    # DICOM with segmentation overlay
    axes[0, 1].imshow(dicom_overlay)
    axes[0, 1].set_title('DICOM + DICOM SEG Overlay')
    axes[0, 1].axis('off')
    
    # NIfTI image
    axes[1, 0].imshow(nifti_slice, cmap='gray')
    axes[1, 0].set_title('NIfTI Image')
    axes[1, 0].axis('off')
    
    # NIfTI with segmentation overlay
    axes[1, 1].imshow(nifti_overlay)
    axes[1, 1].set_title('NIfTI + NIfTI SEG Overlay')
    axes[1, 1].axis('off')
    
    # Add slice information
    fig.text(0.5, 0.02, f'Slice: {slice_idx + 1}/{dicom_array.shape[0]}', 
             ha='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved visualization to: {output_file}")
    plt.close()


def plot_multiview(image, segmentation, output_file, title="Multi-View Segmentation"):
    """Create axial, sagittal, and coronal views."""
    
    img_array = sitk.GetArrayFromImage(image)
    seg_array = sitk.GetArrayFromImage(segmentation)
    
    # Get middle slices for each view
    axial_idx = img_array.shape[0] // 2
    sagittal_idx = img_array.shape[2] // 2
    coronal_idx = img_array.shape[1] // 2
    
    # Extract slices
    axial_img = img_array[axial_idx, :, :]
    axial_seg = seg_array[axial_idx, :, :]
    
    sagittal_img = img_array[:, :, sagittal_idx]
    sagittal_seg = seg_array[:, :, sagittal_idx]
    
    coronal_img = img_array[:, coronal_idx, :]
    coronal_seg = seg_array[:, coronal_idx, :]
    
    # Create overlays
    axial_overlay = create_overlay(axial_img, axial_seg)
    sagittal_overlay = create_overlay(sagittal_img, sagittal_seg)
    coronal_overlay = create_overlay(coronal_img, coronal_seg)
    
    # Create figure
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    # Axial view
    axes[0, 0].imshow(axial_img, cmap='gray')
    axes[0, 0].set_title('Axial - Image')
    axes[0, 0].axis('off')
    
    axes[1, 0].imshow(axial_overlay)
    axes[1, 0].set_title('Axial - Overlay')
    axes[1, 0].axis('off')
    
    # Sagittal view
    axes[0, 1].imshow(sagittal_img, cmap='gray')
    axes[0, 1].set_title('Sagittal - Image')
    axes[0, 1].axis('off')
    
    axes[1, 1].imshow(sagittal_overlay)
    axes[1, 1].set_title('Sagittal - Overlay')
    axes[1, 1].axis('off')
    
    # Coronal view
    axes[0, 2].imshow(coronal_img, cmap='gray')
    axes[0, 2].set_title('Coronal - Image')
    axes[0, 2].axis('off')
    
    axes[1, 2].imshow(coronal_overlay)
    axes[1, 2].set_title('Coronal - Overlay')
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved multi-view visualization to: {output_file}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize DICOM and NIfTI segmentations for comparison"
    )
    parser.add_argument("--original-dicom", "--dicom-seg", dest="dicom_seg",
                       required=True, help="DICOM SEG file")
    parser.add_argument("--original-ref", "--dicom-dir", dest="dicom_dir",
                       required=True, help="Directory containing reference DICOM series")
    parser.add_argument("--nifti-ref", "--nifti-image", dest="nifti_image",
                       required=True, help="NIfTI reference image file")
    parser.add_argument("--nifti-seg", required=True,
                       help="NIfTI segmentation file")
    parser.add_argument("--output", required=True,
                       help="Output image file (PNG)")
    parser.add_argument("--title", default="Segmentation Comparison",
                       help="Plot title")
    parser.add_argument("--multiview", action="store_true",
                       help="Create multi-view (axial/sagittal/coronal) plot")
    parser.add_argument("--slice", type=int,
                       help="Slice index to visualize (default: middle)")
    
    args = parser.parse_args()
    
    try:
        print(f"Loading DICOM series from: {args.dicom_dir}")
        dicom_img = load_dicom_series(args.dicom_dir)
        
        print(f"Loading DICOM SEG: {args.dicom_seg}")
        # For DICOM SEG, we assume it's already converted to NIfTI format
        # In production, you'd use proper DICOM SEG reading
        dicom_seg = sitk.ReadImage(args.dicom_seg)
        
        print(f"Loading NIfTI image: {args.nifti_image}")
        nifti_img = sitk.ReadImage(args.nifti_image)
        
        print(f"Loading NIfTI segmentation: {args.nifti_seg}")
        nifti_seg = sitk.ReadImage(args.nifti_seg)
        
        if args.multiview:
            # Create multi-view plot for NIfTI
            plot_multiview(nifti_img, nifti_seg, args.output, args.title)
        else:
            # Create comparison plot
            plot_comparison(dicom_img, dicom_seg, nifti_img, nifti_seg,
                          args.output, args.title, args.slice)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
