"""
SplatTax AI - Complete Pipeline Orchestrator
Executes data ingestion, footprint extraction, 3DGS height parsing, and tax assessment.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from splattax_ai.gee_satellite_ingestor import run_ingestion_pipeline
from splattax_ai.footprint_extractor import run_footprint_pipeline
from splattax_ai.height_extractor_3dgs import run_height_extraction_pipeline
from splattax_ai.tax_engine_and_forecaster import run_tax_engine_pipeline

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SPLATTAX AI: EXECUTING END-TO-END PIPELINE")
    print("Target: Nelapadu (APCRDA LPS Unit-18), Amaravati, AP, India")
    print("="*70)

    print("\n[1/4] Running Satellite & Cadastral Ingestion...")
    run_ingestion_pipeline()

    print("\n[2/4] Running Footprint Extraction & Setback Audit...")
    run_footprint_pipeline()

    print("\n[3/4] Running 3DGS Volumetric Height Extraction...")
    run_height_extraction_pipeline()

    print("\n[4/4] Running APCRDA Tax Assessment & Revenue Forecaster...")
    run_tax_engine_pipeline()

    print("\n" + "="*70)
    print("SPLATTAX AI PIPELINE COMPLETE! Launch dashboard via: streamlit run app.py")
    print("="*70)
