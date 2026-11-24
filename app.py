"""
SplatTax AI (APCRDA Edition) - Unified 3D Geospatial Revenue & Property Intelligence Platform
Cleaned up warnings; Times New Roman Italic typography for Directional Legal Boundaries.
"""

import math
from pathlib import Path

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium

st.set_page_config(
    page_title="SplatTax AI | APCRDA 3D Geospatial Revenue Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling with Times New Roman Italic for Legal Boundaries
st.markdown("""
<style>
    .main-title { font-size: 26px; font-weight: 800; color: #1E3A8A; margin-bottom: 2px; }
    .sub-title { font-size: 13px; color: #475569; margin-bottom: 16px; }
    .kpi-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; text-align: center; }
    .kpi-val { font-size: 24px; font-weight: bold; color: #0F172A; }
    .kpi-lbl { font-size: 11px; color: #64748B; text-transform: uppercase; font-weight: 600; }
    
    /* Times New Roman Italic Typography for Boundary & Direction Cards */
    .boundary-box {
        font-family: "Times New Roman", Times, serif;
        font-style: italic;
        font-size: 15px;
        line-height: 1.6;
        background-color: #F8FAFC;
        border-left: 5px solid #1E3A8A;
        border-radius: 6px;
        padding: 14px 18px;
        margin-top: 10px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .direction-title {
        font-family: "Times New Roman", Times, serif;
        font-style: normal;
        font-weight: bold;
        color: #1E3A8A;
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data" / "extracted_features"
MASTER_FILE = DATA_DIR / "apcrda_tax_assessment_master.geojson"
BLDS_FILE = DATA_DIR / "real_building_footprints.geojson"
FORECAST_FILE = DATA_DIR / "revenue_forecast_2026_2030.csv"

EPSG_WGS84 = "EPSG:4326"
EPSG_UTM44N = "EPSG:32644"


@st.cache_data
def load_all_data():
    # Always regenerate to ensure columns match latest schema
    from splattax_ai.official_cadastre_and_hadulu import build_unified_splattax_dataset
    build_unified_splattax_dataset()

    parcels_gdf = gpd.read_file(MASTER_FILE)

    # Ensure all required columns exist with safe defaults
    defaults = {
        "vertical_violation_flag": False,
        "unauthorized_builtup_sqft": 0.0,
        "penalty_surcharge_inr": 0.0,
        "total_tax_demand_inr": 0.0,
        "base_tax_inr": 0.0,
        "compliance_tier": "GREEN_COMPLIANT",
        "north_boundary": "N/A",
        "south_boundary": "N/A",
        "east_boundary": "N/A",
        "west_boundary": "N/A",
        "fencing_status": "N/A",
    }
    for col, default in defaults.items():
        if col not in parcels_gdf.columns:
            parcels_gdf[col] = default

    blds_gdf = gpd.read_file(BLDS_FILE) if BLDS_FILE.exists() else None
    forecast_df = pd.read_csv(FORECAST_FILE) if FORECAST_FILE.exists() else None
    return parcels_gdf, blds_gdf, forecast_df


parcels_gdf, blds_gdf, forecast_df = load_all_data()

parcels_utm = parcels_gdf.to_crs(EPSG_UTM44N)
parcels_gdf["computed_sqyds"] = (parcels_utm.geometry.area * 1.19599).round(1)
parcels_gdf["perimeter_ft"] = (parcels_utm.geometry.length * 3.28084).round(1)

# ==============================================================================
# SIDEBAR CONTROLS
# ==============================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Seal_of_Andhra_Pradesh.svg/300px-Seal_of_Andhra_Pradesh.svg.png", width=75)
    st.title("🏛️ SplatTax AI")
    st.caption("APCRDA Unit-18 (Nelapadu), Amaravati")
    st.markdown("---")

    st.subheader("🔍 Search & Filter")
    search_q = st.text_input(
        "Search Plot No, Survey No, or Owner:",
        value="U18-C2-101",
        help="Try: U18-C2-101, U18-3A-101, 448, 112, or Muvva"
    )

    compliance_filter = st.multiselect(
        "Compliance Status",
        options=["RED_CRITICAL_DEVIATION", "YELLOW_MODERATE_DEVIATION", "GREEN_COMPLIANT"],
        default=["RED_CRITICAL_DEVIATION", "YELLOW_MODERATE_DEVIATION", "GREEN_COMPLIANT"]
    )

    zone_filter = st.multiselect(
        "APCRDA Master Plan Zones",
        options=list(parcels_gdf["zone"].unique()),
        default=list(parcels_gdf["zone"].unique())
    )

    st.markdown("---")
    st.markdown("### 🗺️ GIS Layers & Measurements")
    show_satellite = st.checkbox("Google Satellite Hybrid Basemap", value=True)
    show_boundary_labels = st.checkbox("Show Boundary Lengths in Feet (ft)", value=True)
    show_parcels = st.checkbox("Show APCRDA Cadastral Boundaries", value=True)
    show_buildings = st.checkbox("Show 3D Assessed Buildings (3DGS)", value=True)

    st.info("📜 **Legal Foundations**:\n• APCRDA Act 2014 (Sec 102/103)\n• Nelapadu_Plot_Numbers00.pdf\n• MeeBhoomi Revenue Records")

# Filtered set
filtered_parcels = parcels_gdf[
    (parcels_gdf["compliance_tier"].isin(compliance_filter)) &
    (parcels_gdf["zone"].isin(zone_filter))
]

selected = filtered_parcels[
    filtered_parcels["plot_no"].str.contains(search_q, case=False, na=False) |
    filtered_parcels["survey_no"].str.contains(search_q, case=False, na=False) |
    filtered_parcels["owner_name"].str.contains(search_q, case=False, na=False)
]

# ==============================================================================
# MAIN PAGE HEADER & KPI SUMMARY
# ==============================================================================
st.markdown('<div class="main-title">SplatTax AI — 3D Geospatial Revenue & Property Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Pilot: <b>Nelapadu (APCRDA LPS Unit-18), Amaravati</b> | Fusing 3D Gaussian Splatting, MeeBhoomi Records, and Cadastral Boundaries</div>', unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
total_demand = filtered_parcels["total_tax_demand_inr"].sum()
penalties = filtered_parcels["penalty_surcharge_inr"].sum()
red_count = len(filtered_parcels[filtered_parcels["compliance_tier"] == "RED_CRITICAL_DEVIATION"])
comp_rate = (len(filtered_parcels[filtered_parcels["compliance_tier"] == "GREEN_COMPLIANT"]) / max(1, len(filtered_parcels))) * 100

with k1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-val">₹{total_demand/1e5:.2f} L</div><div class="kpi-lbl">Total Assessed Demand</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#DC2626;">₹{penalties/1e5:.2f} L</div><div class="kpi-lbl">Recoverable Surcharges (25%)</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#DC2626;">{red_count}</div><div class="kpi-lbl">Critical Violations</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#16A34A;">{comp_rate:.1f}%</div><div class="kpi-lbl">Cadastral Compliance Rate</div></div>', unsafe_allow_html=True)

# ==============================================================================
# TABS: MAP, INSPECTOR, REVENUE FORECAST, BLUEPRINT MATRIX
# ==============================================================================
tab_map, tab_inspector, tab_forecast, tab_blueprint = st.tabs([
    "🛰️ Google Satellite WebGIS & Boundaries Map",
    "🔍 APCRDA & MeeBhoomi Plot Inspector",
    "📈 5-Year Revenue Forecast (2026-2030)",
    "📜 Official Blueprint & Survey Matrix"
])

# ------------------------------------------------------------------------------
# TAB 1: SATELLITE WEBGIS & BOUNDARIES MAP
# ------------------------------------------------------------------------------
with tab_map:
    col_map_l, col_map_r = st.columns([2.8, 1.2])

    with col_map_l:
        if not selected.empty:
            c_lat = selected.iloc[0].geometry.centroid.y
            c_lon = selected.iloc[0].geometry.centroid.x
            zoom = 18
        else:
            c_lat, c_lon, zoom = 16.5103, 80.4806, 16

        m = folium.Map(location=[c_lat, c_lon], zoom_start=zoom, max_zoom=21, tiles=None)

        if show_satellite:
            folium.TileLayer(
                tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
                attr="Google Satellite Hybrid",
                name="Google Satellite Hybrid",
                overlay=False,
                control=True,
                max_zoom=21
            ).add_to(m)
        else:
            folium.TileLayer("OpenStreetMap").add_to(m)

        if show_parcels:
            for idx, row in filtered_parcels.iterrows():
                if row["parcel_id"] == "APCRDA-NEL-WB-1049":
                    folium.GeoJson(
                        row["geometry"],
                        name="Lake 1049 (P3 Waterbody)",
                        style_function=lambda x: {'fillColor': '#0284C7', 'color': '#0369A1', 'weight': 2, 'fillOpacity': 0.65},
                        tooltip="Protected Waterbody: Lake 1049"
                    ).add_to(m)
                    continue

                is_sel = not selected.empty and row["plot_no"] == selected.iloc[0]["plot_no"]
                tier = row["compliance_tier"]
                c = "#00F5D4" if is_sel else ("#EF4444" if tier == "RED_CRITICAL_DEVIATION" else ("#F59E0B" if tier == "YELLOW_MODERATE_DEVIATION" else "#10B981"))

                n_b = row.get("north_boundary", row.get("north_hadulu", "N/A"))
                s_b = row.get("south_boundary", row.get("south_hadulu", "N/A"))
                e_b = row.get("east_boundary", row.get("east_hadulu", "N/A"))
                w_b = row.get("west_boundary", row.get("west_hadulu", "N/A"))

                popup_content = f"""
                <div style="font-family:'Times New Roman', Times, serif; width:270px; font-size:13px; line-height:1.45;">
                    <h4 style="margin:0; font-family:'Times New Roman', Times, serif; color:#1E3A8A; font-weight:bold;">Plot: {row['plot_no']}</h4>
                    <i><b>Revenue Sy.No:</b> {row['survey_no']} | <b>Khata No:</b> {row['khata_no']}</i><br/>
                    <i><b>Owner:</b> {row['owner_name']}</i><br/>
                    <i><b>Zoning:</b> {row['zone']}</i><br/>
                    <hr style="margin:4px 0; border:0.5px solid #CBD5E1;"/>
                    <i><b>GIS Measured Area:</b> {row['computed_sqyds']} Sq.Yds ({row['perimeter_ft']} ft perimeter)</i><br/>
                    <i><b>Sanctioned:</b> {row['sanctioned_floors']} | <b>Actual (3DGS):</b> {row['actual_floors']}</i><br/>
                    <i><b>Total Tax Demand:</b> ₹{row['total_tax_demand_inr']:,.2f}</i><br/>
                    <hr style="margin:4px 0; border:0.5px solid #CBD5E1;"/>
                    <b style="font-style:normal; color:#1E3A8A;">🧭 Four-Side Legal Boundaries & Directions:</b><br/>
                    <i>• <b>North Direction (N):</b> {n_b}</i><br/>
                    <i>• <b>South Direction (S):</b> {s_b}</i><br/>
                    <i>• <b>East Direction (E):</b> {e_b}</i><br/>
                    <i>• <b>West Direction (W):</b> {w_b}</i>
                </div>
                """

                folium.GeoJson(
                    row["geometry"],
                    name=f"Plot {row['plot_no']}",
                    style_function=lambda x, colr=c, sel=is_sel: {
                        'fillColor': colr,
                        'color': colr,
                        'weight': 3.5 if sel else 1.8,
                        'dashArray': '4, 4',
                        'fillOpacity': 0.25 if sel else 0.12
                    },
                    popup=folium.Popup(popup_content, max_width=320),
                    tooltip=f"Plot {row['plot_no']} | {row['computed_sqyds']} Sq.Yds"
                ).add_to(m)

                if show_boundary_labels:
                    coords = list(row["geometry"].exterior.coords)
                    utm_c = list(parcels_utm.loc[idx, "geometry"].exterior.coords)
                    for e_i in range(len(coords) - 1):
                        mid_x = (coords[e_i][0] + coords[e_i+1][0]) / 2.0
                        mid_y = (coords[e_i][1] + coords[e_i+1][1]) / 2.0
                        edge_ft = math.dist(utm_c[e_i], utm_c[e_i+1]) * 3.28084
                        folium.Marker(
                            [mid_y, mid_x],
                            icon=folium.DivIcon(
                                html=f'<div style="font-family:\'Times New Roman\', Times, serif; font-style:italic; font-size:10px; font-weight:bold; color:#FFFFFF; background:rgba(15,23,42,0.85); padding:1px 4px; border-radius:3px; border:0.5px solid #00F5D4; white-space:nowrap;">{edge_ft:.1f} ft</div>'
                            )
                        ).add_to(m)

        if show_buildings and blds_gdf is not None:
            def b_style(f):
                t = f["properties"].get("compliance_tier", "")
                c = "#EF4444" if t == "RED_CRITICAL_DEVIATION" else ("#F59E0B" if t == "YELLOW_MODERATE_DEVIATION" else "#10B981")
                return {'fillColor': c, 'color': '#FFFFFF', 'weight': 1.2, 'fillOpacity': 0.85}

            folium.GeoJson(
                blds_gdf[blds_gdf["parcel_id"].isin(filtered_parcels["parcel_id"])].__geo_interface__,
                name="3D Building Footprints (3DGS)",
                style_function=b_style
            ).add_to(m)

        folium.LayerControl().add_to(m)
        st.components.v1.html(m._repr_html_(), height=600, scrolling=False)

    with col_map_r:
        st.subheader("Legend & Cadastral Guide")
        st.markdown("""
        * 🔴 **Red (Critical Violation):**
          * Constructed additional floors (e.g., G+4 vs permitted G+2).
          * Physical compound wall encroaches onto road/boundary.
        * 🟡 **Yellow (Moderate Deviation):**
          * Rear or side setback encroachment (excess plinth).
        * 🟢 **Green (Compliant):**
          * Fully conforms to APCRDA bye-laws and registered boundaries.
        * 🔷 **Blue (Lake 1049):**
          * Natural waterbody buffer from official blueprint.
        """)
        st.markdown("---")
        st.markdown("**Location:** Nelapadu, Thullur Mandal, Amaravati")
        st.markdown("**CRS:** EPSG:4326 (WGS84) & EPSG:32644 (UTM 44N)")

# ------------------------------------------------------------------------------
# TAB 2: PLOT INSPECTOR
# ------------------------------------------------------------------------------
with tab_inspector:
    st.subheader("📋 APCRDA & MeeBhoomi Plot Inspector")

    sel_plot_no = st.selectbox("Select Plot to Audit:", options=filtered_parcels["plot_no"].tolist())
    rec = filtered_parcels[filtered_parcels["plot_no"] == sel_plot_no].iloc[0]

    c_i1, c_i2, c_i3 = st.columns(3)

    with c_i1:
        st.markdown("##### 🏛️ Official Land Record")
        st.write(f"**Plot Number:** `{rec['plot_no']}`")
        st.write(f"**Revenue Survey No:** `{rec['survey_no']}` (Nelapadu)")
        st.write(f"**MeeBhoomi Khata No:** `{rec['khata_no']}`")
        st.write(f"**Pattadar / Owner:** **{rec['owner_name']}**")
        st.write(f"**Master Plan Zone:** {rec['zone']}")

    with c_i2:
        st.markdown("##### 🛰️ 2D & 3D Volumetric Metrology")
        st.write(f"**Sanctioned Floors:** {rec['sanctioned_floors']}")
        is_violation = bool(rec.get('vertical_violation_flag', False))
        st.write(f"**Actual Floors (3DGS):** :red[{rec['actual_floors']}]" if is_violation else f"**Actual Floors (3DGS):** {rec['actual_floors']}")
        st.write(f"**Detected Roof Height:** {rec['estimated_height_m']} meters")
        st.write(f"**Permitted Built-up:** {rec['sanctioned_builtup_sqft']:,.1f} sq ft")
        st.write(f"**Actual Built-up:** {rec['actual_builtup_sqft']:,.1f} sq ft")
        st.write(f"**Unauthorized Built-up:** :red[{rec['unauthorized_builtup_sqft']:,.1f} sq ft]")

    with c_i3:
        st.markdown("##### 💰 Statutory Tax & 25% Surcharge")
        st.write(f"**Base Unit Rate:** ₹{rec['base_rate_sqft_inr']} / sq ft")
        st.write(f"**Standard Property Tax:** ₹{rec['base_tax_inr']:,.2f}")
        st.write(f"**25% Violation Surcharge:** :red[₹{rec['penalty_surcharge_inr']:,.2f}]")
        st.write(f"**Total Demand Payable:** :red[**₹{rec['total_tax_demand_inr']:,.2f}**]")
        st.write(f"**Audit Compliance Tier:** `{rec['compliance_tier']}`")

    st.markdown("---")
    st.markdown("##### 🧭 Official Four-Side Legal Boundaries & Directions")
    n_bound = rec.get("north_boundary", rec.get("north_hadulu", "N/A"))
    s_bound = rec.get("south_boundary", rec.get("south_hadulu", "N/A"))
    e_bound = rec.get("east_boundary", rec.get("east_hadulu", "N/A"))
    w_bound = rec.get("west_boundary", rec.get("west_hadulu", "N/A"))

    st.markdown(f"""
    <div class="boundary-box">
        <span class="direction-title">Compass Directional Boundaries:</span><br/>
        <b>⬆️ North Direction [N 0°]:</b> <i>{n_bound}</i><br/>
        <b>⬇️ South Direction [S 180°]:</b> <i>{s_bound}</i><br/>
        <b>➡️ East Direction [E 90°]:</b> <i>{e_bound}</i><br/>
        <b>⬅️ West Direction [W 270°]:</b> <i>{w_bound}</i>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"**Fencing / Boundary Status:** `{rec['fencing_status']}`")

    st.markdown("---")
    btn1, btn2, btn3 = st.columns(3)
    with btn1:
        st.link_button("🌐 Open MeeBhoomi Land Records", "https://meebhoomi.ap.gov.in/VAdangal/Index")
    with btn2:
        st.link_button("🗺️ Open APCRDA LPS GIS Portal", "https://gis.apcrda.org/lps/index.html")
    with btn3:
        pdf_path = ROOT_DIR / "data" / "audit_notices" / f"Notice_{rec['parcel_id']}.pdf"
        if not pdf_path.exists():
            from splattax_ai.tax_engine_and_forecaster import DemandNoticePDFGenerator
            DemandNoticePDFGenerator.generate_notice_pdf(rec.to_dict(), pdf_path)
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label=f"📥 Download Audit Demand Notice PDF ({rec['plot_no']})",
                    data=f,
                    file_name=f"APCRDA_TaxNotice_{rec['plot_no']}.pdf",
                    mime="application/pdf"
                )

# ------------------------------------------------------------------------------
# TAB 3: 5-YEAR REVENUE FORECAST (2026-2030)
# ------------------------------------------------------------------------------
with tab_forecast:
    st.subheader("📈 Municipal Revenue Forecast (2026–2030)")
    st.caption("Powered by XGBoost Machine Learning trained on Nelapadu zoning codes, built-up areas, and compliance enforcement rates.")

    if forecast_df is not None:
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            fig_bar = px.bar(
                forecast_df, x="Year",
                y=["Residential_Revenue_INR", "Commercial_Revenue_INR", "Institutional_Revenue_INR"],
                title="Sector-Wise Revenue Projections (INR)",
                labels={"value": "Projected Collection (₹)", "variable": "Sector"},
                barmode="stack",
                color_discrete_sequence=["#3B82F6", "#F59E0B", "#10B981"]
            )
            st.plotly_chart(fig_bar)

        with c_f2:
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=forecast_df["Year"], y=forecast_df["Total_Municipal_Revenue_INR"], mode="lines+markers", name="Total Demand", line=dict(color="#1E3A8A", width=3)))
            fig_line.add_trace(go.Scatter(x=forecast_df["Year"], y=forecast_df["Recoverable_Penalties_INR"], mode="lines+markers", name="Recoverable 25% Surcharges", line=dict(color="#DC2626", width=2, dash="dot")))
            fig_line.update_layout(title="Total Revenue vs. Recoverable Surcharges", xaxis_title="Year", yaxis_title="INR (₹)")
            st.plotly_chart(fig_line)

        st.dataframe(forecast_df)

# ------------------------------------------------------------------------------
# TAB 4: OFFICIAL BLUEPRINT MATRIX
# ------------------------------------------------------------------------------
with tab_blueprint:
    st.subheader("📜 Official APCRDA Blueprint & Survey Matrix")
    st.markdown("Mapping reconstituted plots from **Nelapadu_Plot_Numbers00.pdf** to **MeeBhoomi Revenue Survey Numbers**:")

    matrix_df = parcels_gdf[[
        "plot_no", "survey_no", "khata_no", "block_no", "owner_name", "zone",
        "registered_sqyds", "computed_sqyds", "sanctioned_floors", "actual_floors", "compliance_tier"
    ]].copy()
    st.dataframe(matrix_df)
