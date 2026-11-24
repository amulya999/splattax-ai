"""
SplatTax AI - Official Cadastre & Legal Boundaries Engine (APCRDA Nelapadu Unit-18 Edition)
Standardized English nomenclature with Compass Directional Boundaries and Times New Roman Italic styling.
"""

import math
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon, box

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "extracted_features"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EPSG_WGS84 = "EPSG:4326"
EPSG_UTM44N = "EPSG:32644"

CENTER_LAT = 16.5103
CENTER_LON = 80.4806


def build_unified_splattax_dataset():
    parcels = []
    buildings = []

    surnames = ["Muvva", "Chalasani", "Kommineni", "Gogineni", "Atluri", "Nannapaneni", "Bollineni", "Yalamanchili"]
    given_names = ["Venkateswara Rao", "Krishna Murthy", "Srinivasa Rao", "Lakshmi Prasanna", "Babu Naidu", "Sambasiva Rao"]

    # Lake 1049 (P3 Protected Waterbody)
    lake_coords = [
        (80.4840, 16.5135), (80.4855, 16.5150), (80.4868, 16.5142),
        (80.4872, 16.5115), (80.4860, 16.5085), (80.4845, 16.5070),
        (80.4835, 16.5090), (80.4840, 16.5135)
    ]
    lake_poly = Polygon(lake_coords)
    lake_rec = {
        "parcel_id": "APCRDA-NEL-WB-1049",
        "plot_no": "LAKE-1049",
        "survey_no": "469/P3",
        "khata_no": "GOVT-01",
        "block_no": "Block-1049",
        "owner_name": "Govt of Andhra Pradesh (APCRDA Water Resources)",
        "zone": "P3 - Waterbody (Lake 1049)",
        "property_type": "Public Waterbody",
        "registered_sqyds": 14250.0,
        "base_rate_sqft_inr": 0.0,
        "sanctioned_floors": "N/A",
        "actual_floors": "G+0",
        "estimated_height_m": 0.0,
        "sanctioned_plinth_sqft": 0.0,
        "actual_plinth_sqft": 0.0,
        "sanctioned_builtup_sqft": 0.0,
        "actual_builtup_sqft": 0.0,
        "unauthorized_builtup_sqft": 0.0,
        "vertical_violation_flag": False,
        "base_tax_inr": 0.0,
        "penalty_surcharge_inr": 0.0,
        "total_tax_demand_inr": 0.0,
        "compliance_tier": "GREEN_COMPLIANT",
        "fencing_status": "Protected Natural Waterbody (Lake Buffer Active)",
        "north_boundary": "North [N 0°]: Rayapudi Sector Road",
        "south_boundary": "South [S 180°]: Lakefront Promenade",
        "east_boundary": "East [E 90°]: R3 Lakefront Residential Blocks (1050-1052)",
        "west_boundary": "West [W 270°]: APCRDA Green Buffer",
        "north_hadulu": "North [N 0°]: Rayapudi Sector Road",
        "south_hadulu": "South [S 180°]: Lakefront Promenade",
        "east_hadulu": "East [E 90°]: R3 Lakefront Residential Blocks (1050-1052)",
        "west_hadulu": "West [W 270°]: APCRDA Green Buffer",
        "geometry": lake_poly
    }
    parcels.append(lake_rec)

    sectors = [
        {"prefix": "U18-C2", "blk": "1042", "sy": "448/2A", "zone": "C2 - Commercial Returnable", "rate": 6.5, "w": 45.0, "d": 65.0, "p_floors": "G+3", "lat": 16.5125, "lon": 80.4735, "n": 8},
        {"prefix": "U18-R3", "blk": "1051", "sy": "469/1B", "zone": "R3 - Lakefront Residential", "rate": 3.5, "w": 42.0, "d": 70.0, "p_floors": "G+2", "lat": 16.5130, "lon": 80.4875, "n": 8},
        {"prefix": "U18-K29", "blk": "1114", "sy": "572/3", "zone": "R3 - Southern LPS (K29)", "rate": 3.0, "w": 38.0, "d": 60.0, "p_floors": "G+2", "lat": 16.5065, "lon": 80.4795, "n": 8},
        {"prefix": "U18-3A", "blk": "100", "sy": "112/2A", "zone": "Zone-3A Judicial Enclave", "rate": 4.5, "w": 40.0, "d": 60.0, "p_floors": "G+2", "lat": 16.5095, "lon": 80.4760, "n": 8}
    ]

    total_idx = 1
    for sec in sectors:
        w_deg = sec["w"] * 0.3048 / 111320.0
        d_deg = sec["d"] * 0.3048 / 110540.0

        for i in range(sec["n"]):
            col = i % 4
            row = i // 4

            px1 = sec["lon"] + (col * (w_deg * 1.35))
            px2 = px1 + w_deg
            py1 = sec["lat"] - (row * (d_deg * 1.35))
            py2 = py1 + d_deg

            parcel_poly = box(px1, py1, px2, py2)
            plot_no = f"{sec['prefix']}-{i+101:03d}"
            survey_no = f"{sec['sy']}"
            khata_no = f"{300 + (total_idx % 180)}"
            owner = f"{surnames[total_idx % len(surnames)]} {given_names[total_idx % len(given_names)]}"

            reg_sqyds = round((sec["w"] * sec["d"]) / 9.0, 1)

            # Four-Side Legal Boundaries with Cardinal Directions
            north_adj = "40 ft Master Plan Road" if row == 0 else f"Plot No. {sec['prefix']}-{i+101-4:03d}"
            south_adj = "30 ft Internal Colony Road" if row > 0 else f"Plot No. {sec['prefix']}-{i+101+4:03d}"
            east_adj = f"Plot No. {sec['prefix']}-{i+102:03d}" if col < 3 else "Green Buffer / Utility Corridor"
            west_adj = f"Plot No. {sec['prefix']}-{i+100:03d}" if col > 0 else "60 ft Arterial Sector Road"

            north_b = f"North Direction [N 0°]: {north_adj} (Width: {sec['w']:.1f} ft)"
            south_b = f"South Direction [S 180°]: {south_adj} (Width: {sec['w']:.1f} ft)"
            east_b = f"East Direction [E 90°]: {east_adj} (Depth: {sec['d']:.1f} ft)"
            west_b = f"West Direction [W 270°]: {west_adj} (Depth: {sec['d']:.1f} ft)"

            p_floors_int = int(sec["p_floors"][-1]) + 1
            if total_idx in [2, 7, 14, 21]:
                tier = "RED_CRITICAL_DEVIATION"
                actual_fl = "G+4"
                actual_h = 15.2
                is_vert = True
                fencing = f"Encroachment Detected (South boundary [S 180°] exceeded by 4.8 ft onto road & +2 unauthorized floors)"
                unauth_builtup = 1100.0
                b_poly = box(px1 + (w_deg * 0.08), py1 - (d_deg * 0.08), px2 - (w_deg * 0.08), py2 - (d_deg * 0.12))
            elif total_idx in [4, 11, 18]:
                tier = "YELLOW_MODERATE_DEVIATION"
                actual_fl = sec["p_floors"]
                actual_h = 9.2 if sec["p_floors"] == "G+2" else 13.5
                is_vert = False
                fencing = f"Minor Setback Encroachment (Shed inside rear North boundary [N 0°] buffer)"
                unauth_builtup = 250.0
                b_poly = box(px1 + (w_deg * 0.08), py1 + (d_deg * 0.12), px2 - (w_deg * 0.04), py2 - (d_deg * 0.12))
            else:
                tier = "GREEN_COMPLIANT"
                actual_fl = sec["p_floors"]
                actual_h = 9.0 if sec["p_floors"] == "G+2" else 13.5
                is_vert = False
                fencing = "Compliant (Structure and compound wall strictly within registered directional boundaries)"
                unauth_builtup = 0.0
                b_poly = box(px1 + (w_deg * 0.12), py1 + (d_deg * 0.15), px2 - (w_deg * 0.12), py2 - (d_deg * 0.15))

            sanctioned_plinth = round(reg_sqyds * 9.0 * 0.60, 1)
            actual_plinth = sanctioned_plinth + (200.0 if tier != "GREEN_COMPLIANT" else 0.0)
            sanctioned_builtup = sanctioned_plinth * p_floors_int
            actual_builtup = sanctioned_builtup + unauth_builtup

            base_rate = sec["rate"]
            base_tax = round(sanctioned_builtup * base_rate, 2)
            penalty = round(unauth_builtup * base_rate * 1.25, 2)
            total_demand = round(base_tax + penalty, 2)

            rec = {
                "parcel_id": plot_no,
                "plot_no": plot_no,
                "survey_no": survey_no,
                "khata_no": khata_no,
                "block_no": sec["blk"],
                "owner_name": owner,
                "zone": sec["zone"],
                "property_type": "Commercial" if "Commercial" in sec["zone"] else "Residential",
                "registered_sqyds": reg_sqyds,
                "base_rate_sqft_inr": base_rate,
                "sanctioned_floors": sec["p_floors"],
                "actual_floors": actual_fl,
                "estimated_height_m": actual_h,
                "sanctioned_plinth_sqft": sanctioned_plinth,
                "actual_plinth_sqft": actual_plinth,
                "sanctioned_builtup_sqft": sanctioned_builtup,
                "actual_builtup_sqft": actual_builtup,
                "unauthorized_builtup_sqft": unauth_builtup,
                "vertical_violation_flag": is_vert,
                "base_tax_inr": base_tax,
                "penalty_surcharge_inr": penalty,
                "total_tax_demand_inr": total_demand,
                "compliance_tier": tier,
                "fencing_status": fencing,
                "north_boundary": north_b,
                "south_boundary": south_b,
                "east_boundary": east_b,
                "west_boundary": west_b,
                # Backward compatibility
                "north_hadulu": north_b,
                "south_hadulu": south_b,
                "east_hadulu": east_b,
                "west_hadulu": west_b
            }

            p_rec = rec.copy()
            p_rec["geometry"] = parcel_poly
            parcels.append(p_rec)

            b_rec = rec.copy()
            b_rec["geometry"] = b_poly
            buildings.append(b_rec)

            total_idx += 1

    parcels_gdf = gpd.GeoDataFrame(parcels, crs=EPSG_WGS84)
    parcels_utm = parcels_gdf.to_crs(EPSG_UTM44N)
    parcels_gdf["computed_sqyds"] = (parcels_utm.geometry.area * 1.19599).round(1)
    parcels_gdf["perimeter_ft"] = (parcels_utm.geometry.length * 3.28084).round(1)

    buildings_gdf = gpd.GeoDataFrame(buildings, crs=EPSG_WGS84)

    parcels_path = DATA_DIR / "apcrda_tax_assessment_master.geojson"
    blds_path = DATA_DIR / "real_building_footprints.geojson"
    boundaries_path = DATA_DIR / "nelapadu_real_plots.geojson"

    parcels_gdf.to_file(parcels_path, driver="GeoJSON")
    parcels_gdf.to_file(boundaries_path, driver="GeoJSON")
    buildings_gdf.to_file(blds_path, driver="GeoJSON")

    print(f"✓ Cadastral Legal Boundaries Dataset Ready: {len(parcels_gdf)} parcels & {len(buildings_gdf)} 3D footprints.")
    return parcels_path, blds_path


if __name__ == "__main__":
    build_unified_splattax_dataset()
