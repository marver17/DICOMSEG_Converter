#!/bin/bash

function dicomseg() {
    local returnparameterfile=""
    local processinformationaddress=""
    local xml=false
    local echo=false
    local verbose=false
    local useLabelIDAsSegmentNumber=false
    local skip=false
    local inputImageList=""
    local inputDICOMDirectory=""
    local inputDICOMList=""
    local outputDICOM=""
    local inputMetadata=""
    local outputType="nrrd"
    local prefix=""
    local outputDirectory=""
    local inputDICOM=""

    while [[ $# -gt 0 ]]; do
        key="$1"
        case $key in
            --returnparameterfile)
                returnparameterfile="$2"
                shift
                shift
                ;;
            --processinformationaddress)
                processinformationaddress="$2"
                shift
                shift
                ;;
            --xml)
                xml=true
                shift
                ;;
            --echo)
                echo=true
                shift
                ;;
            --verbose)
                verbose=true
                shift
                ;;
            --useLabelIDAsSegmentNumber)
                useLabelIDAsSegmentNumber=true
                shift
                ;;
            --skip)
                skip=true
                shift
                ;;
            --inputImageList)
                inputImageList="$2"
                shift
                shift
                ;;
            --inputDICOMDirectory)
                inputDICOMDirectory="$2"
                shift
                shift
                ;;
            --inputDICOMList)
                inputDICOMList="$2"
                shift
                shift
                ;;
            --outputDICOM)
                outputDICOM="$2"
                shift
                shift
                ;;
            --inputMetadata)
                inputMetadata="$2"
                shift
                shift
                ;;
            --outputType)
                outputType="$2"
                shift
                shift
                ;;
            -p)
                prefix="$2"
                shift
                shift
                ;;
            --outputDirectory)
                outputDirectory="$2"
                shift
                shift
                ;;
            --inputDICOM)
                inputDICOM="$2"
                shift
                shift
                ;;
            -h|--help)
                help_itkimage2segimage
                exit 0
                ;;
            *)
                shift
                ;;
        esac
    done

    ## run the command using eval 
    comando="itkimage2segimage --returnparameterfile \"$returnparameterfile\" \
                              --processinformationaddress \"$processinformationaddress\" \
                              --xml \"$xml\" \
                              --echo \"$echo\" \
                              --verbose \"$verbose\" \
                              --useLabelIDAsSegmentNumber \"$useLabelIDAsSegmentNumber\" \
                              --skip \"$skip\" \
                              --inputImageList \"$inputImageList\" \
                              --inputDICOMDirectory \"$inputDICOMDirectory\" \
                              --inputDICOMList \"$inputDICOMList\" \
                              --outputDICOM \"$outputDICOM\" \
                              --inputMetadata \"$inputMetadata\" \
                              --outputType \"$outputType\" \
                              -p \"$prefix\" \
                              --outputDirectory \"$outputDirectory\" \
                              --inputDICOM \"$inputDICOM\""

    eval "$comando"
}


function itkimage() {
    local returnparameterfile=""
    local processinformationaddress=""
    local xml=false
    local echo=false
    local mergeSegments=false
    local verbose=false
    local outputType="nrrd"
    local prefix=""
    local outputDirectory=""
    local inputDICOM=""

    
    while [[ $# -gt 0 ]]; do
        key="$1"
        case $key in
            --returnparameterfile)
                returnparameterfile="$2"
                shift
                shift
                ;;
            --processinformationaddress)
                processinformationaddress="$2"
                shift
                shift
                ;;
            --xml)
                xml=true
                shift
                ;;
            --echo)
                echo=true
                shift
                ;;
            --mergeSegments)
                mergeSegments=true
                shift
                ;;
            --verbose)
                verbose=true
                shift
                ;;
            -t)
                outputType="$2"
                shift
                shift
                ;;
            -p)
                prefix="$2"
                shift
                shift
                ;;
            --outputDirectory)
                outputDirectory="$2"
                shift
                shift
                ;;
            --inputDICOM)
                inputDICOM="$2"
                shift
                shift
                ;;
            -h|--help)
                help_segimage2itkimage
                exit 0
                ;;
            *)
                shift
                ;;
        esac
    done
    echo "Conversione in dicom Seg"
    comando="segimage2itkimage --returnparameterfile \"$returnparameterfile\" \
                              --processinformationaddress \"$processinformationaddress\" \
                              --xml \"$xml\" \
                              --echo \"$echo\" \
                              --mergeSegments \"$mergeSegments\" \
                              --verbose \"$verbose\" \
                              -t \"$outputType\" \
                              -p \"$prefix\" \
                              --outputDirectory \"$outputDirectory\" \
                              --inputDICOM \"$inputDICOM\""

    eval "$comando"
}

function dicom2nifti() {
    local input_path="$1"
    local output_path="$2"
    local compression=True
    local reorient=False

    echo "Converting DICOM to NIfTI..."
    python /usr/dcmqi/bin/dcm2nifti.py -path_input "$input_path" -path_output "$output_path" 
    echo "Conversion finished"
}

function main() {
    case "$1" in
        dicomseg)
                dicomseg "${@:2}"
            ;;
        itkimage)
                itkimage "${@:2}"
            ;;
        dicom2nifti)
                dicom2nifti  "$2"  "$3"
            ;;
        information)
            echo "Three different choices:
                1. dicomseg
                2. itkimage
                3. dicom2nifti
            The first converts the volumetric segmentation(s) stored as labeled pixels using any of the formats supported by ITK into 
            DICOM Segmentation Object (dicomseg). The second function performs the opposite conversion. 
            The third function converts DICOM to NIfTI using the dicom2nifti library in a Conda environment named 'dicomseg'.
            The authors of these functions are:
                Andrey Fedorov(BWH), Christian Herz(BWH)
            dcmqi group https://github.com/QIICR/dcmqi revision: 1922a09 tag: v1.3.1
            To get information about the use of these functions, do:
                dicomsegconv dicomseg|itkimage|dicom2nifti --help|-h
            "
            ;;
        *)
            echo "Usage: $0 {dicomseg|itkimage|dicom2nifti|information} [options]"
            exit 1
            ;;
    esac
}

main "$@"
