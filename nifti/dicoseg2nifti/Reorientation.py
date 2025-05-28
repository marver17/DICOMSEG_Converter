import numpy as np
import SimpleITK as sitk
import re



def get_orientation_string(direction):
    """
    Determine the orientation string from the direction cosines

    Args:
        direction (tuple): direction of orientation

    Returns:
        str : orientation of image
    """
    orientation = ""
    for i in range(0, 3):
        if direction[i*3] > 0:
            orientation += "R"
        elif direction[i*3] < 0:
            orientation += "L"
        if direction[i*3+1] > 0:
            orientation += "A"
        elif direction[i*3+1] < 0:
            orientation += "P"
        if direction[i*3+2] > 0:
            orientation += "S"
        elif direction[i*3+2] < 0:
            orientation += "I"
    return orientation


def flip_axis(image : sitk.Image, vector_of_flippin) : 
    """
        Flip axis
    """
    image_array = sitk.GetArrayFromImage(image)
    vector_of_flippin = tuple(2 if x == 0 else 0 if x == 2 else x for x in vector_of_flippin)  ### in according to sitk convention
    print(f"Axis to flip {vector_of_flippin}")
    return np.flip(image_array,vector_of_flippin).astype(np.uint8)

def calculate_new_direction(image : sitk.Image, changing : list)  :
    """
    Calulate new direction evaluated respect from new orientation

    Args:
        image (sitk.Image): image to reoriented
        chanching (list): list with the changing of the orientation
    """
    D = np.reshape(np.array(image.GetDirection()),(3,3))
    
    ### i go to define reflection matrix 
    
    Fx =np.array([[-1,0,0], [0 ,1 ,0], [0 ,0 ,1]])
    Fy =np.array([[1,0,0], [0 ,-1 ,0], [0 ,0 ,1]])
    Fz =np.array([[1,0,0], [0 ,1 ,0], [0 ,0 ,-1]])
    changing_vec = [True if x in changing else False for x in range(0, 3)]  
    X_flip = changing_vec[0]
    Y_flip = changing_vec[1]
    Z_flip = changing_vec[2]
    
    if X_flip  : 
        D = D*Fx
    if Y_flip : 
        D = D*Fy
    if Z_flip : 
        D = D*Fz
    
    return D.flatten()

def calculate_new_origin(image : sitk.Image, changing : list)  :
    """
    Calulate new origin evaluated respect from new orientation

    Args:
        image (sitk.Image): image to reoriented
        chanching (list): list with the changing of the orientation
    """
    old_origin = image.TransformIndexToPhysicalPoint((0,0,0))
    spacing = image.GetSpacing()
    shape = image.GetSize()
    new_origin = np.copy(old_origin)
    for n,x in enumerate(changing) : 
        if x != 0 : 
            new_origin[n] = x * (shape[n] - 1)*spacing[n] + old_origin[n] 
    return new_origin

class difference_evaluation () : 

    def __init__(self,origin : str ,destination : str) :
        """
            Useful for definition reorientation modification
        Args:
            origin (str): string with origin orientation
            destination (str): string with destination orientation
        """
        self.origin = origin 
        self.destination = destination 
        self.__difference = []
        
    def evaluate_difference(self) :
        """
        Find the difference

        Raises:
            ValueError: Dimension of the origin orientation and destination reference

        Returns:
           list : list with 0 if the direction is the same otherwise 0
        """
        if len(self.origin) != len(self.destination) : 
            raise ValueError(f"Dimension of the origin orientation and destination reference is different : {len(self.origin)}|{len(self.destination)}")
        for i in range(len(self.origin)):
            if self.origin[i] == self.destination[i]:
                self.__difference.append(0)
            else:
                self.__difference.append(1)
        return self.__difference
    
    def check_difference(self) :
        """
        True if the are differences, False if not
        """
        if len(self.__difference) == 0 : 
            self.evaluate_difference()
        if np.sum(self.__difference) == 0 : 
            check = False
        else :
            check = True
        return check
    
    def flip_definition(self) :  
        """
        Definition of what axis need to flipped
       """
        if len(self.__difference) == 0 : 
            self.evaluate_difference()
        return  tuple([n for n,x in enumerate(self.__difference) if x == True ])


    
    def origin_verse_change(self) : 
        """
         How the origin is changed
        """
        if len(self.__difference) == 0 : 
            self.evaluate_difference()  
        POSITIVE = 1
        NEGATIVE = -1
        INVARIANT = 0
        origin_chang = []
        for n,x  in enumerate(self.__difference) : 
            if x== 0 : 
                origin_chang.append(INVARIANT)
            elif x == 1 : 
                if n == 0 :
                    if self.origin[n] == "R" : 
                        origin_chang.append(POSITIVE)
                    else : 
                        origin_chang.append(NEGATIVE)
                elif n == 1 : 
                    if self.origin[n] == "A" :
                        origin_chang.append(POSITIVE)
                    else : 
                        origin_chang.append(NEGATIVE)
                elif n ==2 : 
                    if self.origin[n] == "S" :
                        origin_chang.append(POSITIVE)
                    else : 
                        origin_chang.append(NEGATIVE)
        return origin_chang
    
    
    
class Reoriented() : 
    
    def __init__(self) :
        """
        Reorient SITK images
        """
        self.reference = ""
    
    def SetReference(self,reference : sitk.Image ) : 
        """
        Use this method to set the reference for the reorientation

        Args:
            reference (sitk.Image | str):  Referenced Orientation, i can use sitk Image or str (e.g RAS,RPS etc)
        """

        if type(reference) == sitk.Image  :
            
            direction = reference.GetDirection()
            self.referenced_orientation = get_orientation_string(direction)
    
        elif type(reference) == str : 
            
            ### check if the pattern is correct
            pattern = r'^[RL][AP][SI]$'
            if bool(re.match(pattern, reference))  :
                self.referenced_orientation = reference     
            else  : 
                raise ValueError(f"Orientation {reference} doesn't follow R|L,A|P,S|I schema")
        else:
            raise TypeError(f"Orientation {reference} doesn't follow R|L,A|P,S|I schema")

        
    def __call__(self,image_to_reorieted) : 
        direction = image_to_reorieted.GetDirection()
        orientation = get_orientation_string(direction)
        diff_evv = difference_evaluation(orientation,self.referenced_orientation)
        check_diff = diff_evv.check_difference()
        if check_diff : 
            or_dif = diff_evv.origin_verse_change()
            flip_vector = diff_evv.flip_definition()        
            new_origin = calculate_new_origin(image_to_reorieted,or_dif)
            new_direction = calculate_new_direction(image_to_reorieted,flip_vector)
            spacing = image_to_reorieted.GetSpacing()
            pixel_image = flip_axis(image_to_reorieted,flip_vector)
            new_image = sitk.GetImageFromArray(pixel_image)
            new_image.SetDirection(new_direction)
            new_image.SetOrigin(new_origin)
            new_image.SetSpacing(spacing)
            return new_image
        elif check_diff == False : 
            print("Nothing to reorient, the images have the same orientation")
            return image_to_reorieted