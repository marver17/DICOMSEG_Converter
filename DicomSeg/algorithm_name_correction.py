#!/usr/bin/env python3

import json
import argparse

def update_segment_algorithm_name(file_path):
    # Leggi il file JSON
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