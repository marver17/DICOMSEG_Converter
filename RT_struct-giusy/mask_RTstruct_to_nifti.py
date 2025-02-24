# RT struct in python for GTV mask

import os
import numpy as np
import SimpleITK as sitk
from dcmrtstruct2nii import dcmrtstruct2nii, list_rt_structs
import natsort

#path="//192.168.179.170/BCU_Ricerca/Input/TCIA_H&N_PT_CT/Head-Neck-PET-CT/HN-CHUM-001/08-27-1885-PANC. avec C.A. SPHRE ORL   tte et cou  -TP-74220/1.000000-RTstructCTsim-CTPET-CT-45294/"
#path_original="//192.168.179.170/BCU_Ricerca/Input/TCIA_H&N_PT_CT/Head-Neck-PET-CT/HN-CHUM-001/08-27-1885-PANC. avec C.A. SPHRE ORL   tte et cou  -TP-74220/3.000000-StandardFull-07232"
#path_out="//192.168.179.170/BCU_Ricerca/Input/TCIA_H&N_PT_CT/Head-Neck-PET-CT/HN-CHUM-001/08-27-1885-PANC. avec C.A. SPHRE ORL   tte et cou  -TP-74220/"

path_RT="//192.168.179.170/mvalentino/prova_RTstruct/RT_PET/"
path_original="//192.168.179.170/mvalentino/prova_RTstruct/Pet_image/"
path_out="//192.168.179.170/mvalentino/prova_RTstruct/PET_output/"


im = os.listdir(path_original)
ma = os.listdir(path_RT)

image1=natsort.natsorted(im)
mask1=natsort.natsorted(ma)
print(image1)
print(mask1)



#print(list_rt_structs(path_RT+mask1[89]))

#i=151
#dcmrtstruct2nii(path_RT+ mask1[i], path_original+image1[i], path_out+image1[i], gzip=False)
for i in range(79,80):
    print(i)
    #print(image1[i])
    #structures=list_rt_structs(path_RT+mask1[i])
    """structures='GTV', 'GTV n', 'GTV 70', 'GTV1', 'GTV2', 'GTV3', 'GTV langue','GTVlarynx',
    'GTVp G','GTVp D', 'GTVp', 'GTV-p', 'GTV Primaire', 'GTV t', 'GTV T', 'GTV 2 T', 'GTVt',
    'GTV primaire','GTV Primaire','GTV Primaire 70', 'GTV T irm','GTV-P', 'GTV 67','gtv pet', 'GTV BOT',
    'GTV 67.5', 'GTV 67.5Gy', 'GTV primary_70GY','GTV_67.5gy', 'GTV_67.5gy', 'GTV_70Gy', 'GTV_T_67.5gy',
    'GTV_67.5', 'GTV_69Gy', 'GTV1 reperage', 'GTV1 fusion TEP', 'GTV TEP', 'GTV-gg1', 'GTV-gg2', 'GTV_675gy', 'GTV_675GY'"""

    
    dcmrtstruct2nii(path_RT+ mask1[i], path_original+image1[i], path_out+image1[i],gzip=False) 


       

        
        


    

