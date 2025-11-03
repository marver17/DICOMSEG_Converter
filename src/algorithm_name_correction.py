#!/usr/bin/env python3

import json
import argparse

def update_segment_algorithm_name(file_path):
    """
    Updates the 'SegmentAlgorithmName' field in a JSON file for non-manual segments.

    This function reads a JSON file, iterates through the 'segmentAttributes' list, 
    and checks each segment's 'SegmentAlgorithmType'. If the type is not 'MANUAL' 
    and the 'SegmentAlgorithmName' field is missing, it prompts the user to input 
    a value for 'SegmentAlgorithmName' for the corresponding segment.

    After updating the segments, the modified JSON is saved back to the same file.

    Parameters:
    -----------
    file_path : str
        The path to the JSON file to be updated.

    Returns:
    --------
    None
        The function directly updates the JSON file and does not return any value.

    Notes:
    ------
    - The function assumes that the 'segmentAttributes' field is a list of lists, 
      where each inner list contains dictionaries representing segments.
    - The user is prompted to input the 'SegmentAlgorithmName' value for each segment 
      that is not 'MANUAL' and lacks a 'SegmentAlgorithmName'.
    - The updated JSON file is written back with the same file name.
    """

    with open(file_path, 'r') as file:
        data = json.load(file)

    for segment_list in data['segmentAttributes']:
        for segment in segment_list:
            if segment.get('SegmentAlgorithmType') != 'MANUAL':
                if 'SegmentAlgorithmName' not in segment:
                    segment['SegmentAlgorithmName'] = input(f"Enter the SegmentAlgorithmName for the label ID {segment['labelID']}: ")

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update the SegmentAlgorithmName field in a JSON file")
    parser.add_argument("file_path", type=str, help="JSON file path")
    args = parser.parse_args()
    update_segment_algorithm_name(args.file_path)
