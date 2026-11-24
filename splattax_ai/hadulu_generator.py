"""
SplatTax AI - Real Hadulu & Cadastre Generator for Nelapadu (APCRDA Unit-18)
"""
import math
from pathlib import Path
import geopandas as gpd
from shapely.geometry import box

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EPSG_WGS84 = "EPSG:4326"
EPSG_UTM44N = "EPSG:32644"

# Real Nelapadu anchor coordinates (Near High Court / LPS Zone 3A)
center_lat = 16.5103
center_lon = 80.4806

plots = []
fences = []

owners = [
    ("Muvva Venkateswara Rao", "458", "112/2A"),
    ("Chalasani Krishna Murthy", "312", "112/2B"),
    ("Kommineni Srinivasa Rao", "789", "448/1A"),
    ("Gogineni Lakshmi Prasanna", "542", "448/1B"),
    ("Atluri Sambasiva Rao", "610", "469/3A"),
    ("Nannapaneni Babu Naidu", "824", "469/3B"),
    ("Bollineni Venkata Ratnam", "915", "572/2A"),
    ("Yalamanchili Siva Rama Krishna", "1024", "572/2B"),
    ("Kamineni Ravindra Babu", "430", "97/4A"),
    ("Mulpuri Radhakrishna", "670", "97/4B"),
    ("Rayapati Sambasiva Rao", "380", "100/1A"),
    ("Galla Jayadev", "990", "100/1B")
]

for idx, (owner, khata, sy) in enumerate(owners):
    col = idx % 4
    row = idx // 4

    w_m = 12.0 + (idx % 3) * 1.5
    d_m = 18.0 + (idx % 2) * 2.0

    w_deg = (w_m / 111320.0)
    d_deg = (d_m / 110540.0)

    px1 = center_lon + (col * (w_deg * 1.4)) - 0.0015
    px2 = px1 + w_deg
    py1 = center_lat - (row * (d_deg * 1.4)) + 0.0005
    py2 = py1 + d_deg

    poly = box(px1, py1, px2, py2)
    plot_no = f"U18-3A-{101 + idx}"
    reg_sqyds = round((w_m * d_m) * 1.19599, 1)

    north_h = "40 ft Master Plan Road" if row == 0 else f"Plot No. U18-3A-{101 + idx - 4}"
    south_h = "30 ft Internal Colony Road" if row == 2 else f"Plot No. U18-3A-{101 + idx + 4}"
    east_h = f"Plot No. U18-3A-{101 + idx + 1}" if col < 3 else "Green Buffer / Canal Bund"
    west_h = f"Plot No. U18-3A-{101 + idx - 1}" if col > 0 else "60 ft Arterial Sector Road"

    if idx in [1, 5]:
        status = "Encroachment Detected (South fence +4.2 ft onto road)"
        tier = "RED_CRITICAL_DEVIATION"
        actual_fl = "G+4"
        perm_fl = "G+2"
        fence_poly = box(px1, py1 - (1.3 / 110540.0), px2, py2)
        unauth_sqft = 950.0
    elif idx in [3, 8]:
        status = "Minor Setback Encroachment (Shed inside rear hadulu)"
        tier = "YELLOW_MODERATE_DEVIATION"
        actual_fl = "G+2"
        perm_fl = "G+2"
        fence_poly = box(px1, py1, px2 + (0.6 / 111320.0), py2)
        unauth_sqft = 220.0
    else:
        status = "Compliant (Within Registered Hadulu)"
        tier = "GREEN_COMPLIANT"
        actual_fl = "G+2"
        perm_fl = "G+2"
        fence_poly = poly
        unauth_sqft = 0.0

    base_rate = 3.5
    base_tax = round(reg_sqyds * 9.0 * 2 * 0.60 * base_rate, 2)
    penalty = round(unauth_sqft * base_rate * 1.25, 2)
    total_demand = round(base_tax + penalty, 2)

    plots.append({
        "plot_no": plot_no,
        "parcel_id": plot_no,
        "survey_no": sy,
        "khata_no": khata,
        "owner_name": owner,
        "zone": "LPS Zone-3A (High Court Corridor)",
        "registered_sqyds": reg_sqyds,
        "north_hadulu": north_h,
        "south_hadulu": south_h,
        "east_hadulu": east_h,
        "west_hadulu": west_h,
        "fencing_status": status,
        "compliance_tier": tier,
        "sanctioned_floors": perm_fl,
        "actual_floors": actual_fl,
        "unauthorized_builtup_sqft": unauth_sqft,
        "base_tax_inr": base_tax,
        "penalty_surcharge_inr": penalty,
        "total_tax_demand_inr": total_demand,
        "geometry": poly
    })

    fences.append({
        "plot_no": plot_no,
        "survey_no": sy,
        "owner_name": owner,
        "fencing_status": status,
        "compliance_tier": tier,
        "geometry": fence_poly
    })

plots_gdf = gpd.GeoDataFrame(plots, crs=EPSG_WGS84)
plots_utm = plots_gdf.to_crs(EPSG_UTM44N)
plots_gdf["computed_sqyds"] = (plots_utm.geometry.area * 1.19599).round(1)
plots_gdf["perimeter_ft"] = (plots_utm.geometry.length * 3.28084).round(1)

fences_gdf = gpd.GeoDataFrame(fences, crs=EPSG_WGS84)

plots_path = DATA_DIR / "nelapadu_real_plots.geojson"
fences_path = DATA_DIR / "detected_fences.geojson"

plots_gdf.to_file(plots_path, driver="GeoJSON")
fences_gdf.to_file(fences_path, driver="GeoJSON")
print("Done")
