# DicomConverter Utilities

## Overview
This repository provides tools for segmentation files conversion in DicomSEG, with a primary focus on:
1.  **DICOM RTSTRUCT to DICOM SEG:** A Python script (`rtstruct/rtstruct2dcmseg.py`) converts DICOM Radiotherapy Structure Set (RTSTRUCT) files, along with their referenced DICOM image series, into DICOM Segmentation (SEG) objects. It can also optionally convert the individual Regions of Interest (ROIs) defined in the RTSTRUCT into separate NIfTI (.nii.gz) files.
2.  **Nifti Conversions via dcmqi and Custom Scripts:** The Docker image built from this repository also includes command-line tools from dcmqi (DICOM Quantitative Imaging Toolkit) and custom Python scripts for various conversions, such as:
    *   ITK image formats (NIfTI, NRRD) to/from DICOM SEG.
    *   DICOM series to NIfTI.
    *   DICOM SEG to NIfTI (custom alternative).

All functionalities are conveniently wrapped and accessible via the `run_scripts.sh` command within the Docker container.

## Core Functionalities (via `run_scripts.sh` in Docker)

This Python script leverages `pydicom`, `SimpleITK`, and `highdicom` for its operations.

### Features

*   Converts DICOM RTSTRUCT and its associated DICOM image series to a DICOM SEG file.
*   Optionally exports each ROI from the RTSTRUCT as an individual NIfTI file, spatially aligned with the reference DICOM series.
*   Allows customization of DICOM SEG segment properties (e.g., category, type) through an external YAML configuration file.
*   Provides detailed logging of the conversion process.
*   Can be run as a standalone Python script or via the provided Docker container.
*
### How it Works

1.  **Read DICOM Series:** The reference DICOM image series is read using SimpleITK to obtain image data and spatial information.
2.  **Read RTSTRUCT:** The DICOM RTSTRUCT file is parsed using `pydicom` to extract ROI names and contour data.
3.  **Rasterize Contours:** For each ROI, its 2D contours are rasterized onto a 3D mask volume corresponding to the reference DICOM series.
4.  **Create DICOM SEG:** The rasterized 3D masks are compiled into a DICOM SEG object using `highdicom`.

## Docker Usage

The recommended way to use these tools is via the provided Docker container.

### 1. Build the Docker Image

Navigate to the root directory of this repository (where the `Dockerfile` is located) and run:
   ```bash
   docker build -t dicomsegconverter .
   ```

**2. Run the Conversion using Docker:**
   Mount host directories for inputs (DICOM series, RTSTRUCT, config) and outputs (DICOM SEG, NIfTI, logs).

   ```bash
   docker run --rm \
       -v /path/to/your/dicom_series_folder:/data/dicom_series \
       -v /path/to/your/rtstruct_file.dcm:/data/rtstruct.dcm \
       -v /path/to/your/output_folder:/data/output \
       # -v /path/to/your/optional_config.yaml:/data/config.yaml \  # Optional config file
       dicomsegconverter \
       python /usr/dicomconverter/rtstruct/rtstruct2dcmseg.py \
           /data/dicom_series \
           /data/rtstruct.dcm \
           /data/output/segmentation.seg.dcm \
           # --config /data/config.yaml \  # Optional
           --log /data/output/logs \
   ```
   *Replace `/path/to/your/...` with actual paths on your host machine.*

#### Running the Python Script Locally

**1. Install Dependencies (if not already done):**
   ```bash
   pip install pydicom numpy SimpleITK scikit-image highdicom PyYAML shapely
   ```
   *(Or use `pip install -r requirements.txt` if you create one.)*

**2. Run the Script:**
   ```bash
   python /path/to/rtstruct2dcmseg.py \
       /path/to/dicom_series_folder \
       /path/to/rtstruct_file.dcm \
       /path/to/output/segmentation.seg.dcm \
       # --config /path/to/optional_config.yaml \
       --log /path/to/output/logs \
       # --output_nifti_dir /path/to/output/nifti_files # Optional: for NIfTI output (see note below)
   ```

### Command-line Arguments for `rtstruct2dcmseg.py`

*   `dicom_series_path`: (Positional) Path to the directory containing the reference DICOM image series.
*   `rtstruct_path`: (Positional) Path to the input DICOM RTSTRUCT (.dcm) file.
*   `output_seg_path`: (Positional) Full path for the output DICOM SEG file (e.g., `/output/segmentation.seg.dcm`).
*   `--config <path>`: (Optional) Path to a YAML configuration file for customizing segment properties.
*   `--log <directory_path>`: (Optional) Path to the directory where log files will be saved. Defaults to `./logs` in the script's current working directory if run locally, or relative to the container's CWD.
*   `--output_nifti_dir <directory_path>`: (Optional) Path to the directory where NIfTI files for each ROI will be saved.
    *   **Note:** As of the last review of `rtstruct2dcmseg.py`, this command-line argument might not be implemented in the `argparse` section. If you need this functionality via CLI, ensure the script is updated to include and handle this argument, then call the `create_nift_seg` method.

### Configuration File for `rtstruct2dcmseg.py`

Customize DICOM SEG segment properties using a YAML file. ROI names in the config are matched case-insensitively against those in the RTSTRUCT.

**Example `config.yaml`:**
```yaml
segments:
  ROI_NAME_1_IN_RTSTRUCT: # Use the exact ROI name from your RTSTRUCT
    category:
      code: "T-D0050"      # SNOMED CT Code for 'Tissue'
      scheme: "SRT"
      meaning: "Tissue"
    type:
      code: "M-80003"      # SNOMED CT Code for 'Neoplasm, Malignant'
      scheme: "SRT"
      meaning: "Malignant Neoplasm"
    # color: [255, 0, 0] # RGB color - Note: highdicom's SegmentDescription doesn't directly take this.
                         # The script uses a default color list.

  ANOTHER_ROI_NAME:
    category:
      code: "T-62000"      # Example: 'Kidney'
      scheme: "SRT"
      meaning: "Kidney"
    type:
      code: "RID6041"      # Example: 'Organ' from RadLex
      scheme: "RADLEX"
      meaning: "Organ"
```

If an ROI is not in the config, or properties are missing, defaults are used:
*   **Default Category:** Tissue (SRT: T-D0050)
*   **Default Type:** Tumor (SRT: M-03000)

---

## 2. Additional dcmqi Utilities (in Docker Environment)

The Docker image (`dicomsegconverter`) also includes command-line tools from the dcmqi (DICOM Quantitative Imaging Toolkit) library, made available through the Conda environment specified in the `Dockerfile`. These tools support other types of conversions:

*   **ITK image formats (NIfTI, NRRD, etc.) to DICOM SEG:** Typically using `itkimage2image`.
*   **DICOM SEG to ITK image formats:** Typically using `segimage2itkimage`.
*   **DICOM series to NIfTI:** Often handled by tools like `dcm2niix` (which might be part of the dcmqi ecosystem or a related dependency) or a Python script wrapper.

The `Dockerfile` adds `/usr/dicomconverter/nifti/dcmqi-function/bin` and `/usr/dicomconverter/nifti/dicoseg2nifti` to the `PATH`, suggesting these tools or wrappers are available. The `run_scripts.sh` file copied into the Docker image might also provide convenient aliases or entrypoints for these.

### Example Usage (for dcmqi tools via Docker)

These examples are illustrative and assume scripts/aliases like `dicomseg`, `itkimage`, `dicom2nifti` are available in the Docker image's PATH (as suggested by the previous `Readme.md` for a similar image and the current Dockerfile setup). You might need to invoke the specific `dcmqi` executables directly (e.g., `itkimage2image`, `segimage2itkimage`). **Refer to the official `dcmqi` documentation for precise command-line arguments and tool names.**

1.  **ITK image to DICOM SEG (Example using a hypothetical `dicomseg` script/alias):**
    ```bash
    docker run --rm -v /your/data_folder:/data dicomsegconverter \
        dicomseg --inputImageList /data/itkfile.nii.gz \
                 --inputMetadata /data/metadata.json \
                 --inputDICOMDirectory /data/DICOM_series_folder \
                 --outputDICOM /data/output_dicomseg.dcm
    ```

2.  **DICOM SEG to ITK image (Example using a hypothetical `itkimage` script/alias):**
    ```bash
    docker run --rm -v /your/data_folder:/data dicomsegconverter \
        itkimage --inputDICOM /data/input_dicomseg.dcm \
                 -p output_itkfile -t nifti \
                 --outputDirectory /data/itk_output_folder
    ```

3.  **DICOM series to NIfTI (Example using a hypothetical `dicom2nifti` script/alias):**
    ```bash
    docker run --rm -v /your/data_folder:/data dicomsegconverter \
        dicom2nifti /data/DICOM_series_folder /data/nifti_output_folder
    ```

---


## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

Apache 2.0
