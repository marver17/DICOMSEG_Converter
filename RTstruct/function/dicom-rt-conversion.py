
import os
from pyradise.fileio.writing import ImageFileFormat  # Classe base per i formati di scrittura in PyRaDiSe
from pydicom_seg import SegmentationDataset         # Importa il costruttore del dataset DICOM-SEG

class DicomSegFileFormat(ImageFileFormat):
    """
    Classe per la conversione diretta dei dati di segmentazione in formato DICOM-SEG.
    """
    # Definisce l'estensione di file di default per i file DICOM-SEG
    extension = ".dcmseg"
    
    def write(self, subject, filename, **kwargs):
        """
        Scrive i dati di segmentazione contenuti in 'subject' in un file DICOM-SEG.
        
        Parametri:
            subject: oggetto che contiene i dati di segmentazione e le serie di riferimento.
                     Si assume che disponga dei metodi:
                        - get_segmentation_data() : restituisce un array (o struttura) con i dati di segmentazione.
                        - get_referenced_series() : restituisce le informazioni della serie DICOM originale.
            filename: percorso completo del file di output.
            **kwargs: eventuali parametri aggiuntivi da passare al costruttore di SegmentationDataset.
        """
        # Recupera i dati di segmentazione dall'oggetto subject
        segmentation_data = subject.get_segmentation_data()
        
        # Recupera le serie DICOM di riferimento (es. immagini originali)
        referenced_series = subject.get_referenced_series()
        
        # Creazione del dataset DICOM-SEG utilizzando pydicom-seg.
        # Eventuali parametri specifici per la conversione possono essere passati tramite kwargs.
        seg_dataset = SegmentationDataset(
            segmentation_data=segmentation_data,
            referenced_series=referenced_series,
            **kwargs
        )
        
        # Salva il dataset nel file specificato
        seg_dataset.save_as(filename)
