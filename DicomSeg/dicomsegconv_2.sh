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

    ## run the comand using eval 
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

function dicomseg2nifti() {
    # Verifica se l'opzione --help o -h è stata passata come argomento
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        dcmseg2nifti.py --help
        return
    fi

    local path_input="$1"
    local save_data_dir="$2"
    local reorientation="${3:-False}"  # Impostiamo un valore predefinito se non viene fornito alcun valore

    dcmseg2nifti.py --path_data "$path_input" --save_data_dir "$save_data_dir" --orientation "$reorientation"
}

function main() {
    case "$1" in
        dicomseg)
            itkimage2segimage "${@:2}"
            ;;
        itkimage)
            segimage2itkimage "${@:2}"
            ;;
        itkimage2)
            dicomseg2nifti "$2" "$3" "$4"  # Chiamiamo la funzione dicomseg2nifti con il valore fornito o il valore predefinito
            ;;
        dicom2nifti)
            dicom2nifti "$2" "$3"
            ;;
        information)
            echo "Two different choices:
                1. dicomseg
                2. itkimage
                3. itkimage2
                3. dicom2nifti

            The first converts the volumetric segmentation(s) stored as labeled pixels using any of the formats supported by ITK into 
            DICOM Segmentation Object (dicomseg). On the other hand, the second function performs the opposite conversion.
            The authors of these functions are:
                Andrey Fedorov (BWH), Christian Herz (BWH)
            dcmqi group https://github.com/QIICR/dcmqi revision: 1922a09 tag: v1.3.1
            For the conversion of dicomseg files to nifti there is another function, based on Python, and it is the third function
            The fourth function converts DICOM to NIfTI using the dicom2nifti library in a Conda environment named 'dicomseg'.
            To have information about the use of these functions do:
                dicomsegconv dicomseg|itkimage|dicom2nifti --help|-h
            "
            ;;
        *)
            echo "Usage: $0 {dicomseg|itkimage|itkimage2|dicom2nifti|information} [options]"
            exit 1
            ;;
    esac
}

main "$@"