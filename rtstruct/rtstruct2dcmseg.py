import os
import pydicom
import numpy as np
import SimpleITK as sitk
from skimage.draw import polygon
import highdicom as hd
from datetime import datetime
from highdicom.sr.coding import CodedConcept
import yaml
from pathlib import Path
from typing import Dict, Optional
import logging
from shapely.geometry import Polygon,MultiPolygon


class DicomSegmentationConverter:
    def __init__(self, dicom_series_path, rtstruct_path, output_seg_path, config_path: Optional[str] = None, log_path: Optional[str] = None):
        # Configurazione del logging
        self.logger = self._setup_logging(log_path)
        
        self.dicom_series_path = dicom_series_path
        self.rtstruct_path = rtstruct_path
        self.output_seg_path = output_seg_path
        self.sitk_image = None
        self.series_files = None
        self.roi_masks = {}
        self.segment_configs = {}


        # Colori predefiniti per le ROI
        self.default_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
                             (255, 255, 0), (255, 0, 255), (0, 255, 255),
                             (128, 128, 128)]
        
        if config_path:
            self.load_segment_config(config_path)
            
    def _setup_logging(self, log_path: Optional[str] = None) -> logging.Logger:
        """
        Configura il sistema di logging
        
        Args:
            log_path: Percorso dove salvare il file di log. Se None, usa la directory corrente
        
        Returns:
            Logger configurato
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Formattazione del log
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Handler per console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler per file
        if log_path is None:
            log_path = os.path.join(os.getcwd(), 'logs')
            os.makedirs(log_path, exist_ok=True)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_path, f'conversion_{timestamp}.log')
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger

    def load_segment_config(self, config_path: str) -> None:
        """
        Carica la configurazione dei segmenti da un file YAML
        
        Args:
            config_path: Percorso del file di configurazione YAML
        """
        self.logger.info(f"Loading configuration File")
        if not Path(config_path).exists():
            self.logger.error(f"Configuration file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        else  : 
            self.logger.info(f"Configuration file found: {config_path}")
            
        with open(config_path, 'r') as f:
            self.logger.info("Configuration file loaded")
            self.segment_configs = yaml.safe_load(f)['segments']
            
    def read_dicom_series(self):
        """Legge la serie DICOM usando SimpleITK"""
        
        self.logger.info("Starting DICOM series reading")
        reader = sitk.ImageSeriesReader()
        series_ids = reader.GetGDCMSeriesIDs(self.dicom_series_path)
        if not series_ids:
            self.logger.error(f"No DICOM series found in {self.dicom_series_path}")
            raise ValueError(f"No DICOM series found in {self.dicom_series_path}")
        
        self.logger.info(f"Found DICOM series with ID: {series_ids[0]}")
        self.series_files = reader.GetGDCMSeriesFileNames(self.dicom_series_path, series_ids[0])
        reader.SetFileNames(self.series_files)
        self.sitk_image = reader.Execute()
        self.logger.info(f"Successfully read {len(self.series_files)} DICOM files")
        return self

    def extract_roi_masks(self):
        """Estrae le maschere ROI dal RTSTRUCT"""
        self.logger.info("Starting ROI mask extraction from RTSTRUCT")
        ds_rt = pydicom.dcmread(self.rtstruct_path)
        size = self.sitk_image.GetSize()
        depth, height, width = size[2], size[1], size[0]
        
        self.logger.info(f"Image dimensions: depth={depth}, height={height}, width={width}")

        # Mapping ROI number -> name
        roi_num_to_name = {
            item.ROINumber: item.ROIName 
            for item in ds_rt.StructureSetROISequence
        } if hasattr(ds_rt, "StructureSetROISequence") else {}

        if not hasattr(ds_rt, "ROIContourSequence"):
            self.logger.error("RTSTRUCT does not contain ROIContourSequence!")
            raise ValueError("RTSTRUCT non contiene ROIContourSequence!")

        self.logger.info(f"Found {len(roi_num_to_name)} ROIs in structure set")

        for roi_item in ds_rt.ROIContourSequence:
            roi_num = roi_item.ReferencedROINumber
            roi_name = roi_num_to_name.get(roi_num, f"ROI_{roi_num}")
            self.logger.info(f"Processing ROI: {roi_name} (number {roi_num})")
            self._process_roi_contours(roi_item, roi_name, depth, height, width)
        
        self.logger.info("ROI mask extraction completed")
        return self

    def _process_roi_contours(self, roi_item, roi_name, depth, height, width):
        """Processa i contorni di una singola ROI"""
        self.logger.info(f"Processing contours for ROI: {roi_name}")
        mask = np.zeros((depth, height, width), dtype=np.uint8)
        
        if hasattr(roi_item, "ContourSequence"):
            contour_count = len(roi_item.ContourSequence)
            self.logger.info(f"Found {contour_count} contours for ROI {roi_name}")
            for i, contour in enumerate(roi_item.ContourSequence):
                if hasattr(contour, "ContourData"):
                    self._rasterize_contour(contour, mask, height, width)
                    self.logger.debug(f"Processed contour {i+1}/{contour_count} for ROI {roi_name}")
                else:
                    self.logger.warning(f"Contour {i+1} in ROI {roi_name} has no ContourData")
        else:
            self.logger.warning(f"No ContourSequence found for ROI {roi_name}")
        
        self.roi_masks[roi_name] = mask
        self.logger.info(f"Completed processing ROI: {roi_name}")



    # def _rasterize_contour(self, contour, mask, height, width):
    #     """Rasterizza un singolo contorno con gestione dei MultiPolygon."""
    #     self.logger.debug("Starting advanced contour rasterization")
    #     try:
    #         # Estrae i dati del contorno e li rimodella in una matrice (N, 3)
    #         data = np.array(contour.ContourData).reshape(-1, 3)
            
    #         # Controlla se il contorno ha almeno 3 punti
    #         if data.shape[0] < 3:
    #             self.logger.warning("Contorno con meno di 3 punti; saltato la rasterizzazione.")
    #             return
            
    #         # Verifica se il contorno è chiuso, altrimenti lo chiude
    #         if not np.allclose(data[0], data[-1]):
    #             self.logger.debug("Contorno non chiuso; chiudo il contorno aggiungendo il primo punto alla fine.")
    #             data = np.vstack([data, data[0]])
            
    #         # Converte i punti fisici in indici pixel
    #         indices = [self.sitk_image.TransformPhysicalPointToIndex(tuple(pt)) for pt in data]
    #         slice_idx = indices[0][2]
    #         poly_cols = [ind[0] for ind in indices]
    #         poly_rows = [ind[1] for ind in indices]
            
    #         self.logger.debug(f"Processing contour in slice {slice_idx} with {len(poly_rows)} points")
            
    #         # Crea il poligono dai punti (coordinate (row, col))
    #         poly = Polygon(zip(poly_rows, poly_cols))
    #         if not poly.is_valid:
    #             self.logger.debug("Poligono non valido, applico buffer(0) per correggere autointersezioni")
    #             poly = poly.buffer(0)
            
    #         # Se il risultato è un MultiPolygon, seleziona il poligono con area maggiore
    #         if poly.geom_type == 'MultiPolygon':
    #             self.logger.debug("Multipolygon trovato, seleziono il poligono più grande per rasterizzazione")
    #             poly = max(poly.geoms, key=lambda p: p.area)
            
    #         if poly.is_empty:
    #             self.logger.warning("Il poligono risulta vuoto dopo la correzione; salto la rasterizzazione.")
    #             return
            
    #         # Estrae le coordinate dal poligono corretto
    #         x, y = poly.exterior.coords.xy
    #         x = list(x)
    #         y = list(y)
            
    #         # Rasterizza il poligono (attento all'ordine: (row, col))
    #         rr, cc = polygon(y, x, shape=(height, width))
    #         mask[slice_idx, rr, cc] = 1
    #         self.logger.debug(f"Successfully rasterized contour in slice {slice_idx}")
            
    #     except Exception as e:
    #         self.logger.error(f"Error during advanced contour rasterization: {str(e)}")
    #         raise


    def _rasterize_contour(self, contour, mask, height, width):
        """Rasterizza un singolo contorno"""
        self.logger.debug("Starting contour rasterization")
        try:
            data = np.array(contour.ContourData).reshape(-1, 3)
            indices = [self.sitk_image.TransformPhysicalPointToIndex(tuple(pt)) for pt in data]
            slice_idx = indices[0][2]
            poly_cols = [ind[0] for ind in indices]
            poly_rows = [ind[1] for ind in indices]
            
            self.logger.debug(f"Processing contour in slice {slice_idx} with {len(poly_rows)} points")
            
            rr, cc = polygon(poly_rows, poly_cols, shape=(height, width))
            mask[slice_idx, rr, cc] = 1
            self.logger.debug(f"Successfully rasterized contour in slice {slice_idx}")
            
        except Exception as e:
            self.logger.error(f"Error during contour rasterization: {str(e)}")
            raise

    def create_dicom_seg(self):
        """Crea il DICOM SEG finale"""
        self.logger.info("Starting DICOM-SEG creation")
        
        if not self.roi_masks:
            self.logger.error("No ROIs extracted. Please run extract_roi_masks() first")
            raise ValueError("Nessuna ROI estratta. Eseguire prima extract_roi_masks()")

        roi_names = list(self.roi_masks.keys())
        self.logger.info(f"Processing {len(roi_names)} ROIs: {', '.join(roi_names)}")
        
        seg_array = np.stack([self.roi_masks[name] for name in roi_names], axis=-1)
        self.logger.info(f"Created segmentation array with shape {seg_array.shape}")
        
        self.logger.info("Creating segment descriptions")
        segment_descriptions = self._create_segment_descriptions(roi_names)
        
        self.logger.info("Reading DICOM datasets")
        dicom_datasets = [pydicom.dcmread(f) for f in self.series_files]
        
        self.logger.info("Creating final DICOM-SEG dataset")
        seg_dataset = self._create_segmentation_dataset(seg_array, segment_descriptions, dicom_datasets)
        
        self.logger.info(f"Saving DICOM-SEG to {self.output_seg_path}")
        pydicom.dcmwrite(self.output_seg_path, seg_dataset)
        
        self.logger.info("DICOM-SEG creation completed successfully")
        return self

    def _create_segment_descriptions(self, roi_names):
        """Crea le descrizioni dei segmenti usando la configurazione se disponibile"""
        self.logger.info("Creating segment descriptions")
        descriptions = []
        
        for i, name in enumerate(roi_names):
            self.logger.info(f"Processing segment description for ROI: {name}")
            
            # Cerca la configurazione per questo segmento
            config = self.segment_configs.get(name.upper(), {})
            
            # Valori predefiniti se non trovati nella configurazione
            default_category = {
                'code': 'T-D0050',
                'scheme': 'SRT',
                'meaning': 'Tissue'  
            }
            default_type = {
                'code': 'M-03000',
                'scheme': 'SRT',
                'meaning': 'Tumor'
            }
            default_color = self.default_colors[i % len(self.default_colors)]
            
            # Usa i valori dalla configurazione o i default
            category = config.get('category', default_category)
            seg_type = config.get('type', default_type)
            color = config.get('color', default_color)
            
            self.logger.debug(f"Using category: {category}, type: {seg_type}, color: {color}")
            
            try:
                description = hd.seg.SegmentDescription(
                    segment_number=i + 1,
                    segment_label=name,
                    segmented_property_category=CodedConcept(
                        category['code'],
                        category['scheme'],
                        category['meaning']
                    ),
                    segmented_property_type=CodedConcept(
                        seg_type['code'],
                        seg_type['scheme'],
                        seg_type['meaning']
                    ),
                    algorithm_type=hd.seg.SegmentAlgorithmTypeValues.MANUAL,
                    # recommended_display_rgb_value=color
                )
                descriptions.append(description)
                self.logger.info(f"Successfully created description for ROI: {name}")
                
            except Exception as e:
                self.logger.error(f"Error creating description for ROI {name}: {str(e)}")
                raise
            
        self.logger.info(f"Created {len(descriptions)} segment descriptions")
        return descriptions
    
    
    def _add_missing_dicom_fields(self, dicom_datasets):
        """Aggiunge campi DICOM mancanti se necessario"""
        self.logger.info("Checking for missing DICOM fields")
        required_fields = [
            'StudyInstanceUID', 'SeriesInstanceUID', 'SOPInstanceUID',
            'PatientName', 'PatientID', 'StudyID', 'SeriesNumber',
            'Modality', 'StudyDate', 'StudyTime', 'AccessionNumber'
        ]
        
        for ds in dicom_datasets:
            for field in required_fields:
                if not hasattr(ds, field):
                    self.logger.warning(f"Missing {field}, adding default value")
                    if field == 'StudyInstanceUID':
                        ds.StudyInstanceUID = hd.UID()
                    elif field == 'SeriesInstanceUID':
                        ds.SeriesInstanceUID = hd.UID()
                    elif field == 'SOPInstanceUID':
                        ds.SOPInstanceUID = hd.UID()
                    elif field == 'PatientName':
                        ds.PatientName = "ANONYMOUS"
                    elif field == 'PatientID':
                        ds.PatientID = "12345"
                    elif field == 'StudyID':
                        ds.StudyID = "1"
                    elif field == 'SeriesNumber':
                        ds.SeriesNumber = "1"
                    elif field == 'Modality':
                        ds.Modality = "CT"
                    elif field == 'StudyDate':
                        ds.StudyDate = datetime.now().strftime('%Y%m%d')
                    elif field == 'StudyTime':
                        ds.StudyTime = datetime.now().strftime('%H%M%S')
                    elif field == 'AccessionNumber':
                        ds.AccessionNumber = "1"

    def _create_segmentation_dataset(self, seg_array, segment_descriptions, dicom_datasets):
        """Crea il dataset di segmentazione"""
        self.logger.info("Creating segmentation dataset")
        self.logger.debug(f"Segmentation array shape: {seg_array.shape}")
        self.logger.debug(f"Number of segment descriptions: {len(segment_descriptions)}")
        self.logger.debug(f"Number of source DICOM datasets: {len(dicom_datasets)}")
        
        try:
            # Aggiunge campi mancanti se necessario
            self._add_missing_dicom_fields(dicom_datasets)
            
            seg_dataset = hd.seg.Segmentation(
                source_images=dicom_datasets,
                pixel_array=seg_array.astype(np.uint8),
                segmentation_type=hd.seg.SegmentationTypeValues.BINARY,
                segment_descriptions=segment_descriptions,
                series_instance_uid=hd.UID(),
                series_number=1,
                instance_number=1,
                sop_instance_uid=hd.UID(),
                manufacturer="",
                manufacturer_model_name="RTSTRUCT to SEG",
                software_versions="1.0",
                series_description="RTSTRUCT to SEG",
                device_serial_number="123456"
            )
            self.logger.info("Successfully created segmentation dataset")
            return seg_dataset
            
        except Exception as e:
            self.logger.error(f"Error creating segmentation dataset: {str(e)}")
            raise

    def convert(self):
        """Metodo principale per eseguire l'intera conversione"""
        return (self
                .read_dicom_series()
                .extract_roi_masks()
                .create_dicom_seg())
        
    