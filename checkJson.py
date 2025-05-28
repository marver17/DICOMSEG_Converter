import json
import os

MANDATORY_FIELDS = {
    'SegmentDescription': None,
    'SegmentAlgorithmType': None,
    'SegmentedPropertyCategoryCodeSequence': ['CodeValue', 'CodingSchemeDesignator', 'CodeMeaning'],
    'SegmentedPropertyTypeCodeSequence': ['CodeValue', 'CodingSchemeDesignator', 'CodeMeaning'],
    'labelID': None
}

CONDITIONAL_FIELDS = {
    'SegmentAlgorithmType': {
        'conditions': lambda value: value != 'MANUAL',
        'required_fields': ['SegmentAlgorithmName']
    },
    'SegmentType': {
        'conditions': lambda value: value == 'TISSUE',
        'required_fields': ['SegmentedPropertyTypeCodeSequence']
    },
    'SegmentedPropertyCategoryCodeSequence': {
        'conditions': lambda value: isinstance(value, list) and len(value) > 0,
        'required_subfields': ['CodeValue', 'CodingSchemeDesignator', 'CodeMeaning']
    },
    'SegmentedPropertyTypeCodeSequence': {
        'conditions': lambda value: isinstance(value, list) and len(value) > 0,
        'required_subfields': ['CodeValue', 'CodingSchemeDesignator', 'CodeMeaning']
    }
}

def check_mandatory_fields(json_data):
    """
    Verifica che tutti i campi obbligatori, inclusi eventuali sottocampi, siano presenti in ciascun segmento.
    Gestisce anche la logica condizionale per i campi basata sui valori di altri campi.

    Parameters:
    -----------
    json_data : dict
        Il contenuto del file JSON già caricato.

    Returns:
    --------
    bool
        True se tutti i campi obbligatori sono presenti, False altrimenti.
    
    missing_fields : dict
        Un dizionario che elenca i campi e sottocampi mancanti per ciascun segmento.
    """
    missing_fields = {}

    # Itera attraverso tutti i segmenti nel file JSON
    for i, segment_list in enumerate(json_data.get('segmentAttributes', [])):
        for j, segment in enumerate(segment_list):
            segment_missing = []

            # Verifica i campi obbligatori e i sottocampi
            for field, subfields in MANDATORY_FIELDS.items():
                if field not in segment:
                    segment_missing.append(field)
                elif subfields:  # Se ci sono sottocampi obbligatori
                    if isinstance(segment[field], list) and len(segment[field]) > 0:
                        sequence_item = segment[field][0]  # Considera il primo elemento della sequenza
                        missing_subfields = [subfield for subfield in subfields if subfield not in sequence_item]
                        if missing_subfields:
                            segment_missing.append(f"{field}: missing {missing_subfields}")
                    else:
                        segment_missing.append(f"{field}: expected a non-empty sequence")
            
            # Verifica i campi condizionali complessi
            for field, condition_info in CONDITIONAL_FIELDS.items():
                if field in segment:
                    # Se la condizione è soddisfatta, verifica i campi richiesti
                    condition_met = condition_info['conditions'](segment[field])
                    if condition_met:
                        if 'required_fields' in condition_info:
                            for required_field in condition_info['required_fields']:
                                if required_field not in segment:
                                    segment_missing.append(f"Missing conditional field {required_field} due to {field} value")
                        # Verifica sottocampi condizionali, se presenti
                        if 'required_subfields' in condition_info:
                            if isinstance(segment[field], list) and len(segment[field]) > 0:
                                sequence_item = segment[field][0]  # Controlla il primo elemento della sequenza
                                for subfield in condition_info['required_subfields']:
                                    if subfield not in sequence_item:
                                        segment_missing.append(f"{field}: missing subfield {subfield}")
                            else:
                                segment_missing.append(f"{field}: expected a non-empty sequence")

            if segment_missing:
                missing_fields[f"Segment {i + 1} (LabelID {segment.get('labelID', 'Unknown')})"] = segment_missing

    return len(missing_fields) == 0, missing_fields

def check_json_file(file_path):
    """
    Legge un file JSON e verifica se contiene tutti i campi obbligatori per i segmenti, inclusi i sottocampi e i campi condizionali.

    Parameters:
    -----------
    file_path : str
        Percorso al file JSON.

    Returns:
    --------
    None
        Stampa un messaggio se il file JSON è valido o elenca i campi mancanti.
    """
    # Leggi il file JSON
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Controlla la presenza dei campi obbligatori
    all_fields_present, missing_fields = check_mandatory_fields(data)

    if all_fields_present:
        print(f"Il file {file_path} contiene tutti i campi obbligatori.")
    else:
        print(f"Il file {file_path} è mancante dei seguenti campi:")
        for segment, fields in missing_fields.items():
            print(f"  - {segment}: {fields}")

def check_directory(directory):
    """
    Verifica tutti i file JSON in una directory.

    Parameters:
    -----------
    directory : str
        Il percorso della directory contenente i file JSON.

    Returns:
    --------
    None
        Stampa i risultati per ciascun file JSON.
    """
    # Itera tra tutti i file nella directory
    for file_name in os.listdir(directory):
        if file_name.endswith(".json"):
            file_path = os.path.join(directory, file_name)
            check_json_file(file_path)

# Esempio di utilizzo
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check for mandatory and conditional fields in DICOM SEG JSON files")
    parser.add_argument("directory", type=str, help="Path to the directory containing JSON files")
    args = parser.parse_args()

    check_directory(args.directory)
