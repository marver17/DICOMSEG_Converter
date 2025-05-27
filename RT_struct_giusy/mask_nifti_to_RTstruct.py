# RT struct in python for GTV mask

import platipy

from pathlib import Path
from platipy.dicom.io.nifti_to_rtstruct import convert_nifti

#from platipy.imaging.tests.data import get_lung_dicom


path_dcm=r"../../Input/MOBL_OB/scans/8_t1_vibe_tra_pre_flip_12deg/DICOM"
path_nifti=r'../../Input/MOBL_OB/resources/MOBL_OB_seg/nifti/SDN_FDG_BCa_001_t1_vibe_tra_dyn_SUB_01.nii'
path_out = r'../../Input/MOBL_OB/'

#im = os.listdir(path_original)
#ma = os.listdir(path_RT)

#image1=natsort.natsorted(im)
#mask1=natsort.natsorted(ma)
#print(image1)
#print(mask1)

#print(list_rt_structs(path_RT+mask1[89]))

#i=151
#dcmrtstruct2nii(path_RT+ mask1[i], path_original+image1[i], path_out+image1[i], gzip=False)
#for i in range(79,80):
    #print(i)
    #print(image1[i])
    #structures=list_rt_structs(path_RT+mask1[i])

#dcmrtstruct2nii(path_RT+ mask1[i], path_original+image1[i], path_out+image1[i],gzip=False) 
convert_nifti(path_dcm, ['1,'+path_nifti], path_out+'test')