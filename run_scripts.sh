#!/bin/bash

function rtstruct2seg() {
    if [[ "$1" == "--help" || "$1" == "-h" || "$#" -lt 3 ]]; then
    conda run -n rtstruct rtstruct2dcmseg.py --help
        if [[ "$1" != "--help" && "$1" != "-h" && "$#" -lt 3 ]]; then
            echo "Errore: mancano argomenti obbligatori." >&2
            return 1
        fi
        return 0
    fi

    local dicom_series_path="$1"
    local rtstruct_path="$2"
    local output_seg_path="$3"
    shift 3 

    echo "Esecution of rtstruct2dcmseg..."
    conda run -n rtstruct rtstruct2dcmseg.py "$dicom_series_path" "$rtstruct_path" "$output_seg_path" "$@"
    echo "Finished execution of rtstruct2dcmseg."
}


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
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        python dcm2nifti --help
        return
    fi

    local input_path="$1"
    local output_path="$2"
    local compression=True
    local reorient=False

    echo "Converting DICOM to NIfTI..."
    dcm2nifti.py -path_input "$input_path" -path_output "$output_path" 
    echo "Conversion finished"
}

function dicomseg2nifti() {
    # Verifica se l'opzione --help o -h è stata passata come argomento
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        conda run -n dicomseg dcmseg2nifti.py --help
        return
    fi

    local path_input="$1"
    local save_data_dir="$2"
    local reorientation="${3:-False}"  # Impostiamo un valore predefinito se non viene fornito alcun valore

    conda run -n dicomseg dcmseg2nifti.py --path_data "$path_input" --save_data_dir "$save_data_dir" --orientation "$reorientation"
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
        rtstruct2seg)
            rtstruct2seg "${@:2}"
            ;;

        information)
            echo "Available functions:
                1. dicomseg
                2. itkimage
                3. itkimage2
                4. dicom2nifti
                5. rtstruct

            1. dicomseg: Converts volumetric segmentations (from ITK-supported formats) into DICOM Segmentation objects (dicomseg).
                         Uses 'itkimage2segimage' from dcmqi.
            2. itkimage: Performs the opposite conversion: from DICOM SEG to volumetric images (ITK formats).
                         Uses 'segimage2itkimage' from dcmqi.
               Authors of dcmqi: Andrey Fedorov (BWH), Christian Herz (BWH)
               dcmqi group: https://github.com/QIICR/dcmqi
            3. itkimage2: Converts DICOM SEG files to NIfTI format.
                          Uses the 'dcmseg2nifti.py' script. It is custom function, use it if you have problem of orientation using the dcmqi function.
            4. dicom2nifti: Converts a DICOM series to NIfTI format.
                            Uses the 'dcm2nifti.py' script (based on dicom2nifti).
            5. rtstruct2seg: Converts an RTSTRUCT file into a DICOM Segmentation file.
                             Uses the rtstruct2dcmseg.py' script.

            For detailed information on the use of each function, run:
                $0 <function_name> --help|-h
            Example:
                $0 dicomseg --help
            "
            ;;
        *)
            echo "Usage: $0 {dicomseg|itkimage|itkimage2|dicom2nifti|rtstruct2seg|information} [options]"
            exit 1
            ;;
    esac
}



main "$@"