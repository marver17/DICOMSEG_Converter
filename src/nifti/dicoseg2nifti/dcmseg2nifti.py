#!/usr/bin/env python3
import argparse
from conversion import dicom2nifti
import os

def main():
    parser = argparse.ArgumentParser(description="Convert DICOMSEG files to NIfTI format.")
    parser.add_argument("--path_data", help="Path to the DICOM data directory")
    parser.add_argument("--save_data_dir", help="Directory of output")
    parser.add_argument("--orientation",required=False,default=False,help= "Use this option if you want set different orientation, you can pass to the function a path of a niftifile or string with orientation that follow R|L,A|P,S|I schema ")
    args = parser.parse_args()
    save_data_dir = os.path.join(args.save_data_dir,"niftiseg")

    os.makedirs(save_data_dir,exist_ok=True)
    
    print("Start Conversion ...")   
    if args.orientation == "False" : 
        orientation = False
        dicom2nifti(args.path_data, save_data_dir,orientation)
    else :
        dicom2nifti(args.path_data, save_data_dir,args.orientation)
    print("Done")

if __name__ == "__main__":
    main()