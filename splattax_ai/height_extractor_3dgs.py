"""
SplatTax AI - Module 03: 3D Gaussian Splatting (3DGS) Volumetric Height Extractor
Extracts roof elevations, DTM-normalized heights, and vertical floor counts.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import geopandas as gpd
from plyfile import PlyData, PlyElement
import open3d as o3d

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (SplatTax-3DGS) %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SplatTax_3DGS")

EPSG_WGS84 = "EPSG:4326"
EPSG_UTM44N = "EPSG:32644"


class Synthetic3DGSSynthesizer:
    @staticmethod
    def generate_ply(output_ply_path: Path, parcels_path: Path, num_points: int = 120000) -> Path:
        logger.info(f"Generating synthetic 3DGS point cloud: {output_ply_path.name}")
        parcels_gdf = gpd.read_file(parcels_path).to_crs(EPSG_UTM44N)
        minx, miny, maxx, maxy = parcels_gdf.total_bounds

        points, colors, opacities = [], [], []
        n_ground = int(num_points * 0.40)
        gx = np.random.uniform(minx, maxx, n_ground)
        gy = np.random.uniform(miny, maxy, n_ground)
        gz = 18.0 + (gx - minx) * 0.001 + (gy - miny) * 0.0008 + np.random.normal(0, 0.08, n_ground)

        for x, y, z in zip(gx, gy, gz):
            points.append([x, y, z])
            colors.append([0.35, 0.38, 0.25])
            opacities.append(1.5)

        n_bld_pts = int((num_points - n_ground) / len(parcels_gdf))
        for idx, parcel in parcels_gdf.iterrows():
            bx_min, by_min, bx_max, by_max = parcel.geometry.bounds
            b_minx, b_maxx = bx_min + (bx_max - bx_min) * 0.2, bx_max - (bx_max - bx_min) * 0.2
            b_miny, b_maxy = by_min + (by_max - by_min) * 0.2, by_max - (by_max - by_min) * 0.2

            ground_z = 18.0 + (b_minx - minx) * 0.001 + (b_miny - miny) * 0.0008
            bld_h = 15.2 if idx % 5 == 0 else (18.5 if idx % 7 == 0 else (9.1 if idx % 3 == 0 else 6.2))
            roof_z = ground_z + bld_h

            px = np.random.uniform(b_minx, b_maxx, n_bld_pts)
            py = np.random.uniform(b_miny, b_maxy, n_bld_pts)
            pz = np.random.uniform(ground_z, roof_z, n_bld_pts)
            roof_idx = np.random.choice(n_bld_pts, int(n_bld_pts * 0.6), replace=False)
            pz[roof_idx] = np.random.normal(roof_z, 0.12, len(roof_idx))

            for x, y, z in zip(px, py, pz):
                points.append([x, y, z])
                colors.append([0.72, 0.68, 0.65])
                opacities.append(2.0)

        points_arr = np.array(points, dtype=np.float32)
        colors_arr = np.array(colors, dtype=np.float32)

        dtype = [
            ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
            ('f_dc_0', 'f4'), ('f_dc_1', 'f4'), ('f_dc_2', 'f4'),
            ('opacity', 'f4'),
            ('scale_0', 'f4'), ('scale_1', 'f4'), ('scale_2', 'f4')
        ]
        elements = np.empty(len(points_arr), dtype=dtype)
        elements['x'], elements['y'], elements['z'] = points_arr[:, 0], points_arr[:, 1], points_arr[:, 2]
        elements['f_dc_0'], elements['f_dc_1'], elements['f_dc_2'] = colors_arr[:, 0], colors_arr[:, 1], colors_arr[:, 2]
        elements['opacity'] = 2.0
        elements['scale_0'] = elements['scale_1'] = elements['scale_2'] = 0.05

        PlyData([PlyElement.describe(elements, 'vertex')], text=False).write(str(output_ply_path))
        logger.info(f"3DGS point cloud saved: {output_ply_path}")
        return output_ply_path


class GaussianSplatHeightExtractor:
    def __init__(self, ply_path: Path):
        self.ply_path = ply_path

    def process_point_cloud(self, parcels_path: Path, output_features_path: Path) -> gpd.GeoDataFrame:
        plydata = PlyData.read(str(self.ply_path))
        v = plydata['vertex']
        xyz = np.vstack([v['x'], v['y'], v['z']]).T

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(xyz)
        plane_model, _ = pcd.segment_plane(distance_threshold=0.35, ransac_n=3, num_iterations=500)
        a, b, c, d = plane_model

        parcels_gdf = gpd.read_file(parcels_path).to_crs(EPSG_UTM44N)
        results = []

        for idx, parcel in parcels_gdf.iterrows():
            bx_min, by_min, bx_max, by_max = parcel.geometry.bounds
            mask = (
                (xyz[:, 0] >= bx_min) & (xyz[:, 0] <= bx_max) &
                (xyz[:, 1] >= by_min) & (xyz[:, 1] <= by_max)
            )
            pts = xyz[mask]
            if len(pts) < 15:
                results.append({
                    "parcel_id": parcel["parcel_id"],
                    "estimated_height_m": 0.0,
                    "extracted_floors_count": 0,
                    "extracted_floor_label": "G+0 (Vacant)"
                })
                continue

            centroid = parcel.geometry.centroid
            ground_ref_z = -(a * centroid.x + b * centroid.y + d) / c
            relative_z = pts[:, 2] - ground_ref_z
            valid_z = relative_z[relative_z > 1.5]

            bld_h = max(0.0, round(float(np.percentile(valid_z, 95)), 2)) if len(valid_z) > 5 else 0.0
            floors = int(np.round(bld_h / 3.0)) if bld_h >= 2.0 else 0
            label = f"G+{max(0, floors - 1)}" if floors > 0 else "G+0"

            results.append({
                "parcel_id": parcel["parcel_id"],
                "estimated_height_m": bld_h,
                "extracted_floors_count": floors,
                "extracted_floor_label": label
            })

        final_gdf = parcels_gdf.merge(gpd.GeoDataFrame(results), on="parcel_id", how="left").to_crs(EPSG_WGS84)
        final_gdf.to_file(output_features_path, driver="GeoJSON")
        return final_gdf


def run_height_extraction_pipeline(base_dir: Optional[str] = None) -> Path:
    root_path = Path(base_dir) if base_dir else (
        Path("/content/drive/MyDrive/SplatTax_AI") if Path("/content/drive").exists() else Path("./data")
    )
    drone_dir = root_path / "synthetic_drone_3dgs"
    cadastral_dir = root_path / "cadastral"
    extracted_dir = root_path / "extracted_features"

    drone_dir.mkdir(parents=True, exist_ok=True)
    ply_path = drone_dir / "nelapadu_unit18_splatfacto.ply"
    parcels_path = cadastral_dir / "apcrda_unit18_parcels.geojson"
    output_features = extracted_dir / "volumetric_height_features.geojson"

    if not ply_path.exists():
        Synthetic3DGSSynthesizer.generate_ply(ply_path, parcels_path)

    extractor = GaussianSplatHeightExtractor(ply_path)
    return extractor.process_point_cloud(parcels_path, output_features)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SplatTax AI 3DGS Height Extractor")
    parser.add_argument("--base-dir", type=str, default=None)
    args = parser.parse_args()
    run_height_extraction_pipeline(args.base_dir)
