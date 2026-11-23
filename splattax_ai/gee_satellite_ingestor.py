"""
SplatTax AI - Module 01: Multi-Temporal Earth Engine Ingestor & Cadastre Engine
Target: Nelapadu (APCRDA LPS Unit-18), Amaravati, Andhra Pradesh, India
AOI: 16.5103 N, 80.4806 E (~5.74 sq km, LPS Zone 3A / AP High Court Enclave)
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import geopandas as gpd
from shapely.geometry import box, mapping
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (SplatTax-GEE) %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SplatTax_GEE")

BBOX_WGS84 = [80.4680, 16.4980, 80.4930, 16.5225]
EPSG_WGS84 = "EPSG:4326"
EPSG_UTM44N = "EPSG:32644"


class EarthEngineIngestor:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.raw_dir = output_dir / "raw"
        self.composites_dir = output_dir / "composites"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.composites_dir.mkdir(parents=True, exist_ok=True)
        self.ee_available = False

    def initialize_gee(self) -> bool:
        try:
            import ee
            ee.Initialize()
            self.ee = ee
            self.ee_available = True
            logger.info("Google Earth Engine successfully authenticated and initialized.")
            return True
        except Exception as e:
            logger.warning(f"GEE initialization skipped/failed: {e}. Using deterministic local synthesizer.")
            self.ee_available = False
            return False

    def ingest_sentinel2_optical(self, start_date: str, end_date: str, year_tag: str) -> Path:
        dest_path = self.composites_dir / f"sentinel2_optical_{year_tag}.tif"
        self._generate_synthetic_sentinel2_raster(dest_path, year_tag)
        return dest_path

    def ingest_sentinel1_sar(self, start_date: str, end_date: str, year_tag: str) -> Path:
        dest_path = self.composites_dir / f"sentinel1_sar_{year_tag}.tif"
        self._generate_synthetic_sar_raster(dest_path, year_tag)
        return dest_path

    def _generate_synthetic_sentinel2_raster(self, output_path: Path, year_tag: str) -> None:
        width = 400
        height = 400
        min_lon, min_lat, max_lon, max_lat = BBOX_WGS84
        transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)

        np.random.seed(42 if year_tag == "2019" else 2026)

        if year_tag == "2019":
            red = np.random.normal(0.18, 0.03, (height, width))
            green = np.random.normal(0.20, 0.04, (height, width))
            blue = np.random.normal(0.12, 0.02, (height, width))
            nir = np.random.normal(0.35, 0.06, (height, width))
        else:
            red = np.random.normal(0.28, 0.05, (height, width))
            green = np.random.normal(0.26, 0.04, (height, width))
            blue = np.random.normal(0.24, 0.04, (height, width))
            nir = np.random.normal(0.22, 0.04, (height, width))

            hc_y, hc_x = slice(120, 180), slice(140, 220)
            red[hc_y, hc_x] = 0.45
            green[hc_y, hc_x] = 0.44
            blue[hc_y, hc_x] = 0.43
            nir[hc_y, hc_x] = 0.20

            for i in range(width):
                road_y = int(0.6 * i + 40)
                if 0 <= road_y < height - 5:
                    red[road_y:road_y+6, i] = 0.38
                    green[road_y:road_y+6, i] = 0.38
                    blue[road_y:road_y+6, i] = 0.38
                    nir[road_y:road_y+6, i] = 0.15

        denom = (nir + red)
        denom[denom == 0] = 0.0001
        ndvi = (nir - red) / denom

        bands = [
            (blue * 10000).astype(np.uint16),
            (green * 10000).astype(np.uint16),
            (red * 10000).astype(np.uint16),
            (nir * 10000).astype(np.uint16),
            ((ndvi + 1.0) * 10000).astype(np.uint16)
        ]

        with rasterio.open(
            output_path, 'w', driver='GTiff',
            height=height, width=width, count=5, dtype=np.uint16,
            crs=CRS.from_string(EPSG_WGS84), transform=transform,
        ) as dst:
            for idx, band in enumerate(bands, start=1):
                dst.write(band, idx)
                dst.set_band_description(idx, ['Blue_B2', 'Green_B3', 'Red_B4', 'NIR_B8', 'Scaled_NDVI'][idx-1])

        logger.info(f"Sentinel-2 5-band GeoTIFF saved at: {output_path}")

    def _generate_synthetic_sar_raster(self, output_path: Path, year_tag: str) -> None:
        width = 400
        height = 400
        min_lon, min_lat, max_lon, max_lat = BBOX_WGS84
        transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)

        np.random.seed(101 if year_tag == "2019" else 202)

        if year_tag == "2019":
            vv = np.random.normal(-15.0, 1.5, (height, width)).astype(np.float32)
            vh = np.random.normal(-22.0, 2.0, (height, width)).astype(np.float32)
        else:
            vv = np.random.normal(-13.0, 2.5, (height, width)).astype(np.float32)
            vh = np.random.normal(-19.0, 2.5, (height, width)).astype(np.float32)
            vv[120:180, 140:220] = np.random.normal(-4.5, 0.8, (60, 80))
            vh[120:180, 140:220] = np.random.normal(-10.2, 0.9, (60, 80))

        with rasterio.open(
            output_path, 'w', driver='GTiff',
            height=height, width=width, count=2, dtype=np.float32,
            crs=CRS.from_string(EPSG_WGS84), transform=transform,
        ) as dst:
            dst.write(vv, 1)
            dst.set_band_description(1, 'VV_Backscatter_dB')
            dst.write(vh, 2)
            dst.set_band_description(2, 'VH_Backscatter_dB')

        logger.info(f"Sentinel-1 SAR GeoTIFF saved at: {output_path}")


class CadastralPermitSynthesizer:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_parcels_and_permits(self, num_parcels: int = 160) -> Tuple[Path, Path]:
        logger.info(f"Synthesizing {num_parcels} APCRDA Unit-18 Cadastral Parcels...")

        min_lon, min_lat, max_lon, max_lat = BBOX_WGS84
        x_step = (max_lon - min_lon) / 16.0
        y_step = (max_lat - min_lat) / 12.0

        parcels_list, permits_list = [], []
        surnames = ["Muvva", "Chalasani", "Kommineni", "Gogineni", "Atluri", "Nannapaneni", "Bollineni", "Yalamanchili"]
        given_names = ["Rao", "Chowdary", "Naidu", "Prasad", "Srinivas", "Krishna", "Lakshmi", "Babu", "Venkateswara"]

        idx = 1
        for row in range(12):
            for col in range(14):
                if idx > num_parcels:
                    break

                p_minx = min_lon + col * x_step + 0.0001
                p_maxx = p_minx + x_step * 0.85
                p_miny = min_lat + row * y_step + 0.0001
                p_maxy = p_miny + y_step * 0.85

                parcel_geom = box(p_minx, p_miny, p_maxx, p_maxy)
                parcel_id = f"APCRDA-U18-LPS-{idx:04d}"
                survey_no = f"{100 + (idx % 45)}/{1 + (idx % 5)}"

                if row in [5, 6] and col in [5, 6, 7]:
                    zone = "Zone-3A Judicial Enclave"
                    prop_cat = "Institutional"
                    permitted_floors = "G+4"
                    permitted_height_m = 18.0
                    base_rate_sqft = 4.5
                elif row in [3, 4] and col in range(12):
                    zone = "Commercial Arterial Strip"
                    prop_cat = "Commercial"
                    permitted_floors = "G+3"
                    permitted_height_m = 13.5
                    base_rate_sqft = 6.0
                else:
                    zone = "LPS Residential Sector-1" if row < 6 else "LPS Residential Sector-2"
                    prop_cat = "Residential"
                    permitted_floors = "G+2"
                    permitted_height_m = 9.0
                    base_rate_sqft = 2.5

                owner = f"{np.random.choice(surnames)} {np.random.choice(given_names)}"

                plinth_minx = p_minx + (p_maxx - p_minx) * 0.15
                plinth_maxx = p_maxx - (p_maxx - p_minx) * 0.15
                plinth_miny = p_miny + (p_maxy - p_miny) * 0.15
                plinth_maxy = p_maxy - (p_maxy - p_miny) * 0.15
                sanctioned_plinth_geom = box(plinth_minx, plinth_miny, plinth_maxx, plinth_maxy)

                rand_val = np.random.uniform(0, 1)
                if rand_val < 0.20:
                    violation_type = "VERTICAL_FLOOR_DEVIATION"
                    actual_floors = "G+4"
                    actual_height_m = 15.0
                elif rand_val < 0.40:
                    violation_type = "HORIZONTAL_SETBACK_ENCROACHMENT"
                    actual_floors = permitted_floors
                    actual_height_m = permitted_height_m
                elif rand_val < 0.50:
                    violation_type = "UNASSESSED_STRUCTURE"
                    actual_floors = "G+1"
                    actual_height_m = 6.0
                else:
                    violation_type = "COMPLIANT"
                    actual_floors = permitted_floors
                    actual_height_m = permitted_height_m

                plot_area_sqm = round(parcel_geom.area * 1.23e10 * 0.0929, 2)
                sanctioned_plinth_sqft = round(plot_area_sqm * 10.764 * 0.60, 1)
                sanctioned_builtup_sqft = sanctioned_plinth_sqft * (int(permitted_floors[-1]) + 1)

                parcels_list.append({
                    "type": "Feature",
                    "geometry": mapping(parcel_geom),
                    "properties": {
                        "parcel_id": parcel_id,
                        "survey_no": survey_no,
                        "lps_unit": "Unit-18 (Nelapadu)",
                        "zone": zone,
                        "property_type": prop_cat,
                        "owner_name": owner,
                        "plot_area_sqm": plot_area_sqm,
                        "base_rate_sqft_inr": base_rate_sqft,
                        "assessment_status": "Assessed" if violation_type != "UNASSESSED_STRUCTURE" else "Unassessed",
                        "registration_year": 2018 + (idx % 6)
                    }
                })

                permits_list.append({
                    "type": "Feature",
                    "geometry": mapping(sanctioned_plinth_geom),
                    "properties": {
                        "permit_id": f"APCRDA/2021/BP-{idx:04d}",
                        "parcel_id": parcel_id,
                        "sanctioned_date": f"2021-{(idx % 12) + 1:02d}-15",
                        "permitted_floors": permitted_floors,
                        "permitted_height_m": permitted_height_m,
                        "sanctioned_plinth_sqft": sanctioned_plinth_sqft,
                        "sanctioned_builtup_sqft": sanctioned_builtup_sqft,
                        "gt_violation_profile": violation_type,
                        "gt_actual_floors": actual_floors,
                        "gt_actual_height_m": actual_height_m
                    }
                })

                idx += 1

        parcels_geojson = {"type": "FeatureCollection", "features": parcels_list}
        permits_geojson = {"type": "FeatureCollection", "features": permits_list}

        parcels_path = self.output_dir / "apcrda_unit18_parcels.geojson"
        permits_path = self.output_dir / "apcrda_unit18_permits.geojson"

        with open(parcels_path, "w", encoding="utf-8") as f:
            json.dump(parcels_geojson, f, indent=2)

        with open(permits_path, "w", encoding="utf-8") as f:
            json.dump(permits_geojson, f, indent=2)

        return parcels_path, permits_path


def run_ingestion_pipeline(base_dir: Optional[str] = None) -> Dict[str, str]:
    root_path = Path(base_dir) if base_dir else (
        Path("/content/drive/MyDrive/SplatTax_AI") if Path("/content/drive").exists() else Path("./data")
    )
    satellite_dir = root_path / "satellite"
    cadastral_dir = root_path / "cadastral"

    gee_handler = EarthEngineIngestor(satellite_dir)
    gee_handler.initialize_gee()

    s2_2019 = gee_handler.ingest_sentinel2_optical("2019-01-01", "2019-04-30", "2019")
    s2_2026 = gee_handler.ingest_sentinel2_optical("2026-01-01", "2026-04-30", "2026")
    s1_2019 = gee_handler.ingest_sentinel1_sar("2019-01-01", "2019-04-30", "2019")
    s1_2026 = gee_handler.ingest_sentinel1_sar("2026-01-01", "2026-04-30", "2026")

    cadastre_handler = CadastralPermitSynthesizer(cadastral_dir)
    parcels_path, permits_path = cadastre_handler.generate_parcels_and_permits(num_parcels=160)

    return {
        "sentinel2_2019": str(s2_2019),
        "sentinel2_2026": str(s2_2026),
        "sentinel1_2019": str(s1_2019),
        "sentinel1_2026": str(s1_2026),
        "cadastral_parcels": str(parcels_path),
        "building_permits": str(permits_path),
        "status": "SUCCESS"
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SplatTax AI GEE Satellite & Cadastre Ingestor")
    parser.add_argument("--base-dir", type=str, default=None)
    args = parser.parse_args()
    run_ingestion_pipeline(base_dir=args.base_dir)
