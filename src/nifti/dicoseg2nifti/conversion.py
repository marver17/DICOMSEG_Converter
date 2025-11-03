import SimpleITK as sitk
import numpy as np
import json
from dicomseg import dicomseg
from Reorientation import Reoriented
import re
import os

### TODO inserire log vari
def itk_create(image_array : np.array,origin : list,spacing : list,direction : list) : 
    """    Function to create sitkImage ready to save
    Args:
        image_array (np.array): Array of the image
        origin (list): origin of the image
        spacing (list): spacing of the image
        direction (list): direction of the image

    Returns:
        sitkImage
    """
    itk_image = sitk.GetImageFromArray(image_array) 
    ### set direction, origin and spacing to the image
    itk_image.SetOrigin(origin)
    itk_image.SetSpacing(spacing)
    itk_image.SetDirection(direction)
    return itk_image


def dict_information(dataset,segmentation_information)  :
    """
    Function to create metajson file

    Args:
        dataset (pydicom.dataset): header dicom from the dicomseg
        segmentation_information (list): information about the segments
    """
    content_creator_name = ""
    clinical_trial_series_id = ""
    clinical_trial_time_point_id = ""
    series_description = ""
    series_number = ""
    instance_number = ""
    
    if hasattr(dataset, 'ContentCreatorName'):
        content_creator_name = str(dataset.ContentCreatorName)

    if hasattr(dataset, 'ClinicalTrialSeriesID'):
        clinical_trial_series_id = str(dataset.ClinicalTrialSeriesID)

    if hasattr(dataset, 'ClinicalTrialTimePointID'):
        clinical_trial_time_point_id = str(dataset.ClinicalTrialTimePointID)

    if hasattr(dataset, 'SeriesDescription'):
        series_description = str(dataset.SeriesDescription)

    if hasattr(dataset, 'SeriesNumber'):
        series_number = str(dataset.SeriesNumber)

    if hasattr(dataset, 'InstanceNumber'):
        instance_number = str(dataset.InstanceNumber)

    # Create the dictionary with the checked values
    metajson= {
        "ContentCreatorName": content_creator_name,
        "ClinicalTrialSeriesID": clinical_trial_series_id,
        "ClinicalTrialTimePointID": clinical_trial_time_point_id,
        "SeriesDescription": series_description,
        "SeriesNumber": series_number,
        "InstanceNumber": instance_number,
    }
    
    #### segment attribute creation 
    multi_segments_attribute = [] 
    for key in segmentation_information : 
        info = segmentation_information[key]
        SegmentedPropertyCategoryCodeSequence = info[(0x0062, 0x0003)]
        SegmentedPropertyTypeCodeSequence = info[(0x0062, 0x000f)]
        content_creator_name = ""
        clinical_trial_series_id = ""
        clinical_trial_time_point_id = ""
        series_description = ""
        series_number = ""
        instance_number = ""
        # Initialize with empty strings
        CodeValue = ""
        CodingSchemeDesignator = ""
        CodeMeaning = ""

        CodeValueSegment = ""
        CodingSchemeDesignatorSegment = ""
        CodeMeaningSegment = ""

        # Check if SegmentedPropertyCategoryCodeSequence has at least one element and the necessary keys
        if not SegmentedPropertyCategoryCodeSequence.is_empty :
            category_code = SegmentedPropertyCategoryCodeSequence[0]
            CodeValue = category_code.get('CodeValue', "")
            CodingSchemeDesignator = category_code.get('CodingSchemeDesignator', "")
            CodeMeaning = category_code.get('CodeMeaning', "")

        # Check if SegmentedPropertyTypeCodeSequence has at least one element and the necessary keys
        if not SegmentedPropertyCategoryCodeSequence.is_empty:
            type_code = SegmentedPropertyTypeCodeSequence[0]
            CodeValueSegment = type_code.get('CodeValue', "")
            CodingSchemeDesignatorSegment = type_code.get('CodingSchemeDesignator', "")
            CodeMeaningSegment = type_code.get('CodeMeaning', "")

        #### dictionary creatrion
            
        segment_attributes = {
            "labelID": key,
            "SegmentDescription": info.SegmentDescription,
            "SegmentAlgorithmType": info.SegmentAlgorithmType,
            "SegmentedPropertyCategoryCodeSequence": {
                "CodeValue": CodeValue,
                "CodingSchemeDesignator": CodingSchemeDesignator,
                "CodeMeaning": CodeMeaning
            },
            "SegmentedPropertyTypeCodeSequence": {
                "CodeValue": CodeValueSegment,
                "CodingSchemeDesignator": CodingSchemeDesignatorSegment,
                "CodeMeaning": CodeMeaningSegment
            },
            }
        if  not info.SegmentAlgorithmType == "MANUAL" : 
            segment_algorithm_name = ""
            if hasattr(dataset, 'SegmentAlgorithmName'):
                segment_algorithm_name = info.SegmentAlgorithmName
            segment_attributes["SegmentAlgorithmName"] =  segment_algorithm_name

        
        # Conditionally add recommendedDisplayRGBValue if it exists
        if (0x0062, 0x000d) in info:
            segment_attributes["recommendedDisplayRGBValue"] = info[0x0062, 0x000d].value

        if hasattr(info, 'SegmentedPropertyTypeModifierCodeSequence') and info.SegmentedPropertyTypeModifierCodeSequence:
            modifier_code = info.SegmentedPropertyTypeModifierCodeSequence[0]
            segment_attributes["SegmentedPropertyTypeModifierCodeSequence"] = {
                "CodeValue": modifier_code.get('CodeValue', ""),
                "CodingSchemeDesignator": modifier_code.get('CodingSchemeDesignator', ""),
                "CodeMeaning": modifier_code.get('CodeMeaning', "")
            }    
        multi_segments_attribute.append(segment_attributes)
    metajson["segmentAttributes"] = multi_segments_attribute
    
    content_label = ""
    content_description = ""
    clinical_trial_coordinating_center_name = ""
    body_part_examined = ""

    
    if hasattr(dataset, 'ContentLabel'):
        content_label = dataset.ContentLabel

    if hasattr(dataset, 'ContentDescription'):
        content_description = dataset.ContentDescription

    if hasattr(dataset, 'ClinicalTrialCoordinatingCenterName'):
        clinical_trial_coordinating_center_name = dataset.ClinicalTrialCoordinatingCenterName

    if hasattr(dataset, 'BodyPartExamined'):
        body_part_examined = dataset.BodyPartExamined

    metajson.update({
    "ContentLabel": content_label,
    "ContentDescription": content_description,
    "ClinicalTrialCoordinatingCenterName": clinical_trial_coordinating_center_name,
    "BodyPartExamined": body_part_examined
})
    
    return metajson


def dicom2nifti(path_data, save_data_dir,orientation) : 
    
    dcmseg = dicomseg(path_data)
    dcmfile = dcmseg.get_dcmseg()
    overlap = dcmseg.check_overlap()
    label_key = dcmseg.get_LabelInformation()
    
    #TODO insert 4D vector 
    dim_seg  = list(dcmfile._segment_data[1].shape)
    #### 
    segmentation = np.empty(dim_seg)    
    origin = dcmfile.origin
    direction = dcmfile.direction.flatten().tolist()
    spacing = dcmfile.spacing
    #### insert saving json file 
    dataset = dcmfile.dataset
    segmentation_information = dcmfile.segment_infos
    meta_json = dict_information(dataset,segmentation_information)
    with open(os.path.join(save_data_dir,"meta_file.json"), 'w') as fp:
        json.dump(meta_json, fp,indent=4)
    
    #### orientation check
    r = Reoriented()
    pattern = r'^[RL][AP][SI]$'
    if orientation == False :
        pass
    elif bool(re.match(pattern, orientation))  :
        r.SetReference(orientation)
    else : 
        image = sitk.ReadImage(orientation)
        r.SetReference(image)
    #### ################################################
    for index in label_key :  
        key = label_key[index]
        label  = dcmfile._segment_data[index]
        if overlap  : 
            path_save = os.path.join(save_data_dir,key + ".nii.gz")
            if orientation == False : 
                sitk_image = itk_create(label,origin,spacing,direction)
            else : 
                sitk_image = r(itk_create(label,origin,spacing,direction))
            sitk.WriteImage(sitk_image,path_save)
        else : 
            segmentation += index*label
    if not overlap : 
        if orientation == False : 
            sitk_image = itk_create(segmentation,origin,spacing,direction)
        else : 
            sitk_image = r(itk_create(segmentation,origin,spacing,direction))
        sitk.WriteImage(sitk_image,os.path.join(save_data_dir,"segmentation.nii.gz"))
    
