# SplatTax AI: 3D Geospatial Revenue & Property Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31%2B-FF4B4B.svg)](https://streamlit.io/)
[![Platform](https://img.shields.io/badge/Platform-Google_Colab_%7C_Local-orange.svg)](#quickstart)

An end-to-end **3D Geospatial Revenue & Property Intelligence Platform** designed for greenfield capital city development, piloted over **Nelapadu (APCRDA LPS Unit-18), Amaravati Capital Region, Andhra Pradesh, India** (16.5103° N, 80.4806° E).

---

## Key Capabilities

1. **Multi-Temporal Earth Observation (Sentinel-1/2 + SAM)**:
   - Ingests cloud-free Sentinel-2 optical and Sentinel-1 SAR imagery (2019 baseline vs. 2026 present).
   - Detects 2D horizontal building footprint expansions and plinth setback violations.
2. **3D Gaussian Splatting (3DGS) Volumetric Extraction**:
   - Parses Nerfstudio `splatfacto` 3DGS `.ply` point clouds.
   - Normalizes terrain using RANSAC Digital Terrain Modeling (DTM).
   - Derives accurate building roof heights and converts them into floor counts (3m per slab) to catch vertical floor deviations (e.g. G+2 permitted vs G+4 built).
3. **Statutory APCRDA Property Tax & Penalty Engine**:
   - Computes base annual property tax according to AP Capital Region norms.
   - Automatically levies a statutory 25% surcharge on unauthorized built-up area under Sections 102/103.
   - Classifies properties into Red, Yellow, and Green compliance tiers.
   - Generates official PDF Audit Demand Notices.
4. **Sectoral Machine Learning Revenue Forecaster**:
   - Trains an XGBoost regressor to project municipal revenue across Residential, Commercial, and Institutional sectors from 2026 to 2030.
5. **Interactive WebGIS Dashboard (`app.py`)**:
   - Built with Streamlit, Leafmap, and Plotly for map-based audit inspections and revenue simulation.

---

## Repository Structure

```
splattax-ai/
├── splattax_ai/
│   ├── __init__.py
│   ├── gee_satellite_ingestor.py     # Sentinel-1/2 ingestion & APCRDA cadastre generator
│   ├── footprint_extractor.py        # SAM 2D footprint & horizontal setback audit
│   ├── height_extractor_3dgs.py      # 3DGS .ply parser, RANSAC DTM & vertical floor audit
│   ├── tax_engine_and_forecaster.py  # APCRDA tax engine, 25% penalties, XGBoost forecaster
│   └── run_pipeline.py               # End-to-end pipeline execution runner
├── app.py                            # Streamlit WebGIS & Executive Dashboard
├── requirements.txt                  # Python dependencies (Colab T4 compatible)
├── .gitignore                        # Git exclusion rules for large rasters and point clouds
└── README.md                         # Project documentation
```

---

## Quickstart

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/<your-username>/splattax-ai.git
cd splattax-ai
pip install -r requirements.txt
```

### 2. Run the Processing Pipeline
```bash
python splattax_ai/run_pipeline.py
```

### 3. Launch the WebGIS Dashboard
```bash
streamlit run app.py
```

---

## Google Colab Execution

To run directly on a free Google Colab NVIDIA T4 instance:
```python
# Mount Drive & clone repository
from google.colab import drive
drive.mount('/content/drive')

!git clone https://github.com/<your-username>/splattax-ai.git
%cd splattax-ai
!pip install -q -r requirements.txt
!python splattax_ai/run_pipeline.py
!streamlit run app.py & npx localtunnel --port 8501
```

---

## License

Distributed under the Apache 2.0 License. See `LICENSE` for details.
