"""
SplatTax AI (APCRDA Edition) - Unified Master Execution Pipeline
Integrates:
1. Sentinel-1/2 Satellite Observations
2. 3D Gaussian Splatting (3DGS) Volumetric Metrology
3. APCRDA LPS Layout (Nelapadu_Plot_Numbers00.pdf)
4. MeeBhoomi AP Land Records & Legal Boundaries in Feet
5. Statutory 25% Tax Surcharges & XGBoost Revenue Forecaster (2026-2030)
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from splattax_ai.gee_satellite_ingestor import run_ingestion_pipeline
from splattax_ai.official_cadastre_and_boundaries import build_unified_splattax_dataset
from splattax_ai.tax_engine_and_forecaster import MunicipalRevenueForecaster

if __name__ == "__main__":
    print("\n" + "="*75)
    print("SPLATTAX AI (APCRDA EDITION) — MASTER PIPELINE EXECUTION")
    print("Study Area: Nelapadu (APCRDA LPS Unit-18), Amaravati Capital Region, AP")
    print("="*75)

    print("\n[1/3] Ingesting Sentinel-1/2 Satellite Composites...")
    run_ingestion_pipeline()

    print("\n[2/3] Fusing APCRDA Blueprint, MeeBhoomi Records & Directional Boundaries...")
    parcels_path, blds_path = build_unified_splattax_dataset()

    print("\n[3/3] Training XGBoost Sectoral Municipal Revenue Forecaster (2026-2030)...")
    import geopandas as gpd
    parcels_gdf = gpd.read_file(parcels_path)
    # Filter out lake for ML training
    trainable_gdf = parcels_gdf[parcels_gdf['property_type'] != 'Public Waterbody']
    forecast_df = MunicipalRevenueForecaster.train_and_forecast(trainable_gdf)
    out_csv = BASE_DIR / "data" / "extracted_features" / "revenue_forecast_2026_2030.csv"
    forecast_df.to_csv(out_csv, index=False)

    print("\n" + "="*75)
    print("✓ SPLATTAX AI UNIFIED PLATFORM READY!")
    print("  Launch Executive Dashboard: python -m streamlit run app.py")
    print("="*75)
