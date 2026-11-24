# SplatTax AI: Complete System Engineering & Operational Documentation

## 1. System Overview & Executive Summary

**SplatTax AI** is an enterprise-grade 3D Geospatial Revenue Intelligence Platform designed for greenfield capital city development. It bridges the gap between administrative cadastral records, high-resolution satellite remote sensing, and 3D radiance field photogrammetry.

### 1.1 The Urban Governance Problem in Greenfield Capitals
In rapidly developing urban regions such as Amaravati (Andhra Pradesh, India), municipal authorities encounter severe revenue leakage and urban planning non-compliance:
* **Unassessed horizontal plinth coverage:** Property owners expand footprints into mandated setback zones.
* **Unauthorized vertical floor construction:** Buildings permitted for G+2 floors are constructed up to G+4 or G+5 without structural or municipal approval.
* **Airspace & operational constraints:** Drone operations in sensitive government zones (e.g., High Court of Andhra Pradesh, State Secretariats) face strict DGCA airspace clearance restrictions.

SplatTax AI automates the detection of these discrepancies and calculates statutory property tax demand, including statutory 25% non-compliance surcharges under Sections 102/103 of the APCRDA Act.

---

## 2. System Architecture & Repository Layout

```
splattax-ai/
├── splattax_ai/
│   ├── __init__.py                     # Package initialization
│   ├── gee_satellite_ingestor.py       # Module 01: EO Ingestion & Cadastral Synthesizer
│   ├── footprint_extractor.py          # Module 02: SAM 2D Footprint Segmentation
│   ├── height_extractor_3dgs.py        # Module 03: 3DGS Volumetric Height Extractor
│   ├── tax_engine_and_forecaster.py    # Module 04: APCRDA Tax, Surcharges & XGBoost Forecast
│   └── run_pipeline.py                 # End-to-end headless pipeline orchestrator
├── docs/
│   ├── RESEARCH_PAPER.md               # Full academic publication paper
│   ├── SYSTEM_DOCUMENTATION.md         # Exhaustive engineering specification
│   └── generate_pdf.py                 # Multi-page ReportLab PDF documentation compiler
├── data/
│   ├── satellite/                      # Raw & composite Sentinel-1/2 rasters
│   ├── cadastral/                      # APCRDA Unit-18 LPS Parcels & Permits GeoJSONs
│   ├── synthetic_drone_3dgs/           # Nerfstudio splatfacto .ply point clouds
│   ├── extracted_features/             # Vectorized footprints, heights, & tax ledgers
│   └── audit_notices/                  # Generated official demand notice PDFs
├── app.py                              # Interactive Streamlit WebGIS Dashboard
├── requirements.txt                    # PyTorch, GeoPandas, Rasterio, Open3D, Leafmap stack
├── .gitignore                          # High-volume binary exclusions
└── README.md                           # GitHub repository front-page
```

---

## 3. Coordinate Reference Systems (CRS) & Spatial Alignment

Precision municipal taxation requires transitioning between geographic and projected metric coordinate reference systems:

* **WGS 84 (`EPSG:4326`):**
  * Expressed in decimal degrees (longitude, latitude).
  * Used for Earth Engine satellite tile streaming, Leafmap WebGIS visualization, and GeoJSON interchange.
  * Spatial bounds for Nelapadu pilot: `[80.4680° E, 16.4980° N]` to `[80.4930° E, 16.5225° N]`.
* **UTM Zone 44N (`EPSG:32644`):**
  * Projected conformal metric coordinate system for Andhra Pradesh.
  * Used for all physical geometric operations: polygon buffer calculations, square-foot plinth conversions ($1\text{ m}^2 = 10.7639\text{ sq ft}$), and 3D point cloud spatial KDTree indexing.

---

## 4. Module-by-Module Technical Specification

### Module 01: `gee_satellite_ingestor.py`
* **Functionality:**
  * Connects to Google Earth Engine via `earthengine-api`.
  * Queries `COPERNICUS/S2_SR_HARMONIZED` (Sentinel-2 L2A) and filters for dry-season, low-cloud composites (2019 baseline vs 2026 present).
  * Queries `COPERNICUS/S1_GRD` (Sentinel-1 SAR C-Band in IW mode) to detect structural double-bounce backscatter transitions.
  * **Deterministic Offline Fallback:** If Earth Engine API authentication is pending, it synthesizes calibrated 5-band GeoTIFFs (Blue, Green, Red, NIR, NDVI) with affine transformations matching the Nelapadu geographic bounding box.
  * **Cadastral Synthesizer:** Generates 160 realistic APCRDA Land Pooling Scheme (LPS) Unit-18 parcels and building permits with landowner attributes, survey numbers, permitted setback limits, and ground-truth deviation labels.

### Module 02: `footprint_extractor.py`
* **Functionality:**
  * Ingests the 2026 optical composite raster.
  * Computes morphological built-up indices (NDBI) and prompts the **Segment Anything Model (SAM / SamGeo ViT-H)** to delineate discrete building footprint boundaries.
  * Normalizes polygon topologies, eliminating slivers and self-intersections using $\text{buffer}(0)$.
  * Intersects extracted footprints with cadastral parcel boundaries in metric UTM 44N.
  * Computes plinth discrepancy ($\Delta \text{Plinth} = \text{Actual} - \text{Sanctioned}$) and flags properties exceeding the 5% allowable setback threshold.

### Module 03: `height_extractor_3dgs.py`
* **Functionality:**
  * Ingests Nerfstudio `splatfacto` 3D Gaussian Splat point cloud (`.ply`).
  * If drone imagery is restricted, generates a calibrated synthetic 3DGS point cloud representing the High Court and surrounding residential/commercial sectors.
  * Fits a global Digital Terrain Model (DTM) ground plane using **RANSAC plane segmentation** ($ax + by + cz + d = 0$).
  * Partitions point cloud coordinates per cadastral parcel using spatial bounding queries.
  * Determines building height $H$ by evaluating the 95th-percentile elevation of non-ground points ($z > 1.5\text{ m}$).
  * Infers discrete floor counts using the standard APCRDA slab height coefficient ($\lambda = 3.0\text{ m}$):
    $$\text{Floors} = \left\lfloor \frac{H}{3.0} + 0.5 \right\rfloor$$

### Module 04: `tax_engine_and_forecaster.py`
* **Functionality:**
  * Fuses horizontal plinth areas and vertical floor heights into an auditable master assessment table.
  * Computes base property tax:
    $$\text{Base Tax} = \min(A_{\text{actual}}, A_{\text{permitted}}) \times R_{\text{base}}$$
  * Levies the statutory 25% non-compliance surcharge on unauthorized built-up area under APCRDA Sections 102/103:
    $$\text{Surcharge} = A_{\text{unauthorized}} \times R_{\text{base}} \times 1.25$$
  * Categorizes compliance into **Red** (critical deviation $>20\%$ or $\ge 2$ unpermitted floors), **Yellow** (minor deviation $<20\%$), and **Green** (compliant).
  * Trains an **XGBoost Regressor** on spatial features to forecast municipal revenue streams from 2026 to 2030.
  * Generates official, publication-ready PDF Audit Demand Notices via ReportLab.

### Module 05: `app.py` (WebGIS Executive Dashboard)
* **Functionality:**
  * Interactive dual-layer WebGIS rendered using **Streamlit** and **Leafmap (Folium)**.
  * Real-time filtering by compliance tier (Red / Yellow / Green) and LPS zoning sectors.
  * KPI summary cards tracking total assessed tax, recoverable penalty surcharges, and compliance rates.
  * Property-level inspector tab with one-click official PDF demand notice downloads.
  * Interactive Plotly charts visualizing 2026–2030 sectoral revenue forecasts.

---

## 5. Execution & Deployment Guide

### Running in Google Colab (Free T4 GPU)
```bash
# 1. Clone repository
git clone https://github.com/<your-username>/splattax-ai.git
cd splattax-ai

# 2. Install dependencies
pip install -q -r requirements.txt

# 3. Execute end-to-end pipeline
python splattax_ai/run_pipeline.py

# 4. Launch interactive dashboard
streamlit run app.py & npx localtunnel --port 8501
```

### Running Locally (Windows / Linux / macOS)
```powershell
cd C:\Users\HP\.gemini\antigravity\scratch\splattax-ai
pip install -r requirements.txt
python splattax_ai\run_pipeline.py
streamlit run app.py
```
Open `http://localhost:8501` in your web browser.
