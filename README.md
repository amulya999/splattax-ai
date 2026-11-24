# SplatTax AI: 3D Geospatial Revenue & Property Intelligence Platform

SplatTax AI is a geospatial AI platform for urban property-tax assessment, compliance auditing, and municipal revenue forecasting. It combines satellite imagery, building-footprint extraction, 3D Gaussian Splatting-based height analysis, APCRDA property-tax rules, and machine-learning-based revenue forecasting.

## Live App

**Open the SplatTax AI Dashboard:** [Launch App](https://splattax-ai-athg5yk3xjnu7xodevvhun.streamlit.app/)

## Key Features

- **Satellite Data Ingestion:** Uses Sentinel-1 and Sentinel-2 imagery through Google Earth Engine for geospatial analysis.
- **Building Footprint Extraction:** Applies Segment Anything Model (SAM) concepts to identify building footprints and audit horizontal setbacks.
- **3D Height Analysis:** Processes 3D Gaussian Splatting `.ply` point clouds to estimate building roof heights and detect vertical floor deviations.
- **Floor Compliance Audit:** Converts estimated roof height into floor counts using a 3-meter-per-floor assumption, helping identify cases such as a permitted G+2 building being constructed as G+4.
- **APCRDA Property Tax Engine:** Computes base annual property tax according to AP Capital Region norms.
- **Unauthorized Construction Penalty:** Applies a statutory 25% surcharge on unauthorized built-up area under Sections 102/103.
- **Compliance Classification:** Categorizes properties into Red, Yellow, and Green compliance tiers.
- **Audit Demand Notices:** Generates official PDF Audit Demand Notices for non-compliant properties.
- **Revenue Forecasting:** Uses an XGBoost regressor to project municipal revenue across Residential, Commercial, and Institutional sectors from 2026 to 2030.
- **Interactive WebGIS Dashboard:** Provides map-based audit inspection, property intelligence, and revenue simulation using Streamlit, Leafmap, and Plotly.

## Repository Structure

```text
splattax-ai/
├── splattax_ai/
│   ├── __init__.py
│   ├── gee_satellite_ingestor.py      # Sentinel-1/2 ingestion & APCRDA cadastre generator
│   ├── footprint_extractor.py         # SAM 2D footprint & horizontal setback audit
│   ├── height_extractor_3dgs.py       # 3DGS .ply parser, RANSAC DTM & vertical floor audit
│   ├── tax_engine_and_forecaster.py   # APCRDA tax engine, 25% penalties, XGBoost forecaster
│   └── run_pipeline.py                # End-to-end pipeline execution runner
├── app.py                             # Streamlit WebGIS & Executive Dashboard
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Excludes large rasters, point clouds, and outputs
└── README.md                          # Project documentation
```

## Quickstart

### 1. Clone and install dependencies

```bash
git clone [https://github.com/amulya999/splattax-ai.git](https://github.com/amulya999/splattax-ai.git)
cd splattax-ai
pip install -r requirements.txt
```

### 2. Run the processing pipeline

```bash
python splattax_ai/run_pipeline.py
```

### 3. Launch the WebGIS dashboard

```bash
streamlit run app.py
```

The dashboard will open locally at:

```text
http://localhost:8501
```

## Google Colab Execution

To run the project on a free Google Colab NVIDIA T4 instance:

```python
from google.colab import drive
drive.mount('/content/drive')

!git clone [https://github.com/amulya999/splattax-ai.git](https://github.com/amulya999/splattax-ai.git)
%cd splattax-ai

!pip install -q -r requirements.txt
!python splattax_ai/run_pipeline.py

!streamlit run app.py & npx localtunnel --port 8501
```

## Deployment

The Streamlit dashboard is deployed using Streamlit Community Cloud:

**Live Dashboard:** https://splattax-ai-athg5yk3xjnu7xodevvhun.streamlit.app/

## Data and API Keys

Do not upload large satellite rasters, `.ply` point clouds, generated outputs, or API credentials directly to GitHub.

If the application requires Google Earth Engine, Sentinel Hub, or other external-service credentials, store them securely using Streamlit secrets:

```text
Streamlit Cloud → App settings → Secrets
```

## License

Distributed under the Apache 2.0 License. See `LICENSE` for details.
