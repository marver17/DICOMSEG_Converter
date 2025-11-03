import pydicom
import pydicom_seg
import numpy as np
import itertools
##TODO finish the documentation


def has_overlap(matrix1 : np.array, matrix2 : np.array):
    """
    Check the presence of overlap in image 

    Args:
        matrix1 (np.array) 
        matrix2 (np.array)
    Returns:
        bool: presence of the overlap
    """
    overlap = (matrix1 != 0) & (matrix2 != 0)
    return np.any(overlap)



class dicomseg() : 
    def __init__(self, dataDir) : 
        dcm = pydicom.dcmread(dataDir)
        reader = pydicom_seg.SegmentReader() 
        self.__dcmseg = reader.read(dcm) 
    
    def get_dcmseg(self): 
        return self.__dcmseg
    
    def get_LabelInformation(self) : 
        label_key = {self.__dcmseg.dataset.SegmentSequence[(index - 1)].SegmentNumber:self.__dcmseg.dataset.SegmentSequence[(index - 1)].SegmentDescription for index in self.__dcmseg.available_segments }
        return label_key
    
    def check_overlap(self) : 
        number_label = len(self.__dcmseg.available_segments)
        overlap = False

        if number_label == 1  :
            print("There is just one label")
            return overlap
        elif number_label >  1 : 
            combinations = itertools.combinations(range(len(self.__dcmseg.available_segments)), 2)
            for i, j in combinations:
                if has_overlap(self.__dcmseg._segment_data[i + 1], self.__dcmseg._segment_data[j + 1]):
                    overlap = True
                    break  
            return overlap
    
    def get_overlapping_labels(self) : 
        overlap  = self.check_overlap()
        ovelapping_label = list()
        if not overlap  :
            print("There is just one label")
        elif  overlap : 
            label_name = self.get_LabelInformation()
            combinations = itertools.combinations(range(len(self.__dcmseg.available_segments)), 2)
            for i, j in combinations : 
                if has_overlap(self.__dcmseg._segment_data[i + 1], self.__dcmseg._segment_data[j + 1]):
                    ovelapping_label.append([i+1,j+1])
                    print(f"Overlapping labels : {label_name[i+1],label_name[j+1]}")
            return ovelapping_label

