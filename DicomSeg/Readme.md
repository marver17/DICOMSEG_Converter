# DicomSeg Conversion 

This container performs a conversion from the volumetric segmentation(s) stored as labelled pixels one of the formats supported by ITK to DICOM Segmentation Object (dicomseg) and vice versa. Based on the work of the dcmqi group.
ITK formats are: NRRD, NIfTI, MHD, etc. 
## Conversion Pipeline 

For the conversion to dicomseg three inputs are needed : 
1.  DICOM files of the images 
2.  ITK files with the volumentric segmentation(s)
3.  Json file with extra metadata that will be encode inside dicomseg

A useful tool To generate a JSON files for the dicom SEG converter http://qiicr.org/dcmqi/#/seg.

## How does it work ?

There are three possibilities : 

1. From itk image to dicomseg

        docker run  mariov687/dicomseg:latest dicomseg
    
2. From itk image to dicomseg

        docker run  mariov687/dicomseg:latest itkimage

3. Dicom Files to nifti files
    docker run  mariov687/dicomseg:latest dicom2nifti

To retrieve help about the container we can do :
    
    docker run -v mariov687/dicomseg:latest information

### How to share images with container

Docker containers cannot directly access the host filesystem. To pass files to the dcmqi converter and access output files , use the -v argument to specify directories for file exchange.

    -v HOST_DIR:CONTAINER_DIR

### How to dicomseg conversion works

The dicomseg conversion use the itkimage2segimage of the dcmqi group. 

These are the arguments of the function : 

    --returnparameterfile <std::string>
        Filename in which to write simple return parameters (int, float,
        int-vector, etc.) as opposed to bulk return parameters (image,
        geometry, transform, measurement, table).

    --processinformationaddress <std::string>
        Address of a structure to store process information (progress, abort,
        etc.). (default: 0)

    --xml
        Produce xml description of command line arguments (default: 0)

        --echo
        Echo the command line arguments (default: 0)

    --verbose
        Display more verbose output, useful for troubleshooting. (default: 0)

    --useLabelIDAsSegmentNumber
        Use label IDs from ITK images as Segment Numbers in DICOM. Only works
        if label IDs are consecutively numbered starting from 1, otherwise
        conversion will fail. (default: 0)

    --skip
        Skip empty slices while encoding segmentation image. By default, empty
        slices will not be encoded, resulting in a smaller output file size.
        (default: 0)

    --inputImageList <std::vector<std::string>>
        Comma-separated list of file names of the segmentation images in a
        format readable by ITK (NRRD, NIfTI, MHD, etc.). Each of the
        individual files can contain one or more labels (segments). Segments
        from different files are allowed to overlap. See documentation for
        details.

    --inputDICOMDirectory <std::string>
        Directory with the DICOM files corresponding to the original image
        that was segmented.

    --inputDICOMList <std::vector<std::string>>
        Comma-separated list of DICOM images that correspond to the original
        image that was segmented. This means you must have access to the
        original data in DICOM in order to use the converter (at least for
        now).
    --outputDICOM <std::string>
        File name of the DICOM SEG object that will store the result of
        conversion.

    --inputMetadata <std::string>
        JSON file containing the meta-information that describes the
        measurements to be encoded. See documentation for details.

    --,  --ignore_rest
        Ignores the rest of the labeled arguments following this flag.

    --version
        Displays version information and exits.

    -h,  --help
        Displays usage information and exits.

### How to itkimage conversion works

The itkimage conversion use the segimage2itkimage of the dcmqi group. 

These are the arguments of the function : 

    --returnparameterfile <std::string>
        Filename in which to write simple return parameters (int, float,
        int-vector, etc.) as opposed to bulk return parameters (image,
        geometry, transform, measurement, table).

    --processinformationaddress <std::string>
        Address of a structure to store process information (progress, abort,
        etc.). (default: 0)

    --xml
        Produce xml description of command line arguments (default: 0)

    --echo
        Echo the command line arguments (default: 0)

    --mergeSegments
        Save all segments into a single file. When segments are
        non-overlapping, output is a single 3D file. If overlapping, single 4D
        following conventions of 3D Slicer segmentations format. Only
        supported when the output is NRRD for now. (default: 0)

    --verbose
        Display more verbose output, useful for troubleshooting. (default: 0)

    -t <nrrd|mhd|mha|nii|nifti|hdr|img>,  --outputType <nrrd|mhd|mha|nii
        |nifti|hdr|img>
        Output file format for the resulting image data. (default: nrrd)

    -p <std::string>,  --prefix <std::string>
        Prefix for output file.

    --outputDirectory <std::string>
        Directory to store individual segments saved using the output format
        specified files. When specified, file names will contain prefix,
        followed by the segment number.

    --inputDICOM <std::string>
        File name of the input DICOM Segmentation image object.

    --,  --ignore_rest
        Ignores the rest of the labeled arguments following this flag.

    --version
        Displays version information and exits.

    -h,  --help
        Displays usage information and exits.


### How to dicom to nifti conversion works 

The conversion in nifti from dicom files use a python library dicom2nifti 

These are the arguments of the function : 
   
    <input_path>: Path to the input DICOM files.
    <output_path>: Path to save the output NIfTI files.
    -h, --help: Show this help message.

## Example

These are two examples, one for each modality :

1. From itk file  to dicomseg file 
        
        docker run -v DicomsegTest:/tmp mariov687/dicomseg:latest dicomseg --inputImageList /tmp/itkfile.nii.gz --inputMetadata /tmp/metadata.json --inputDICOMDirectory /tmp/DICOM --outputDICOM /tmp/dicomsegfile.dcm`

2. From dicomseg file to itk file

        docker run  -v DicomsegTest:/tmp  mariov687/dicomseg:latest itkimage  --inputDICOM /tmp/dicomsegfile.dcm -p itkfile -t nifti --       outputDirectory /tmp

3. From dicom2nifti 

        docker run  -v DicomsegTest:/tmp  mariov687/dicomseg:latest dicom2nifiti   /tmp/dicomfolder  /tmp/niftifolder