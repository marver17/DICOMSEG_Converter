import json
import argparse

def update_segment_algorithm_name(file_path, default_name="AutomaticSegmentation"):
    # Leggi il file JSON
    with open(file_path, 'r') as file:
        data = json.load(file)

    for segment_list in data['segmentAttributes']:
        for segment in segment_list:
            if segment.get('SegmentAlgorithmType') != 'MANUAL':
                if 'SegmentAlgorithmName' not in segment:
                    # Use default name instead of interactive input
                    segment['SegmentAlgorithmName'] = default_name
                    print(f"Added SegmentAlgorithmName='{default_name}' for Label ID {segment['labelID']}")

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update SegmentAlogithmName tag ")
    parser.add_argument("file_path", type=str, help="Path of Json")
    args = parser.parse_args()
    update_segment_algorithm_name(args.file_path)