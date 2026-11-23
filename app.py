"""
SplatTax AI - Interactive WebGIS & Executive Property Tax Dashboard
Built with Streamlit, Leafmap, and Plotly.
"""

import os
import sys
from pathlib import Path

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import leafmap.foliumap as leafmap

st.set_page_config(
    page_title="SplatTax AI | APCRDA 3D Geospatial Revenue Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
EXTRACTED_DIR = DATA_DIR / "extracted_features"
NOTICES_DIR = DATA_DIR / "audit_notices"

st.markdown("""
<style>
    .main-header { font-size: 24px; font-weight: 700; color: #1E3A8A; margin-bottom: 4px; }
    .sub-header { font-size: 13px; color: #4B5563; margin-bottom: 16px; }
    .kpi-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; text-align: center; }
    .kpi-val { font-size: 24px; font-weight: bold; color: #0F172A; }
    .kpi-lbl { font-size: 11px; color: #64748B; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    tax_file = EXTRACTED_DIR / "apcrda_tax_assessment_master.geojson"
    forecast_file = EXTRACTED_DIR / "revenue_forecast_2026_2030.csv"

    if not tax_file.exists():
        st.warning(f"Assessment data not detected at {tax_file}. Run 'python splattax_ai/run_pipeline.py' to generate.")
        return None, None

    gdf = gpd.read_file(tax_file)
    f_df = pd.read_csv(forecast_file) if forecast_file.exists() else None
    return gdf, f_df


tax_gdf, forecast_df = load_data()

with st.sidebar:
    st.title("🏛️ SplatTax AI")
    st.caption("Nelapadu (APCRDA Unit-18), Amaravati")
    st.markdown("---")

    if tax_gdf is not None:
        compliance_filter = st.multiselect(
            "Filter by Compliance Tier",
            options=["RED_CRITICAL_DEVIATION", "YELLOW_MODERATE_DEVIATION", "GREEN_COMPLIANT"],
            default=["RED_CRITICAL_DEVIATION", "YELLOW_MODERATE_DEVIATION", "GREEN_COMPLIANT"]
        )
        zone_filter = st.multiselect(
            "Filter by LPS Zone",
            options=list(tax_gdf['zone'].unique()),
            default=list(tax_gdf['zone'].unique())
        )
    else:
        compliance_filter, zone_filter = [], []

st.markdown('<div class="main-header">SplatTax AI — 3D Geospatial Revenue Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-Temporal Satellite (SAM) & 3D Gaussian Splatting Cadastral Audit | AP High Court Enclave</div>', unsafe_allow_html=True)

if tax_gdf is not None and len(compliance_filter) > 0 and len(zone_filter) > 0:
    filtered_gdf = tax_gdf[
        (tax_gdf['compliance_tier'].isin(compliance_filter)) &
        (tax_gdf['zone'].isin(zone_filter))
    ]

    k1, k2, k3, k4 = st.columns(4)
    total_demand = filtered_gdf['total_tax_demand_inr'].sum()
    penalties = filtered_gdf['penalty_surcharge_inr'].sum()
    red_count = len(filtered_gdf[filtered_gdf['compliance_tier'] == 'RED_CRITICAL_DEVIATION'])
    comp_rate = (len(filtered_gdf[filtered_gdf['compliance_tier'] == 'GREEN_COMPLIANT']) / max(1, len(filtered_gdf))) * 100

    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-val">₹{total_demand/1e5:.2f} L</div><div class="kpi-lbl">Total Assessed Demand</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#DC2626;">₹{penalties/1e5:.2f} L</div><div class="kpi-lbl">Violation Surcharges</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#DC2626;">{red_count}</div><div class="kpi-lbl">Critical Violations</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#16A34A;">{comp_rate:.1f}%</div><div class="kpi-lbl">Compliance Rate</div></div>', unsafe_allow_html=True)

    tab_map, tab_inspector, tab_forecast = st.tabs(["🗺️ Interactive Cadastral WebGIS", "🔍 Property Inspector", "📈 Revenue Projections (2026-2030)"])

    with tab_map:
        m = leafmap.Map(center=[16.5103, 80.4806], zoom=15)
        def style_callback(feature):
            tier = feature['properties'].get('compliance_tier', '')
            color = '#EF4444' if tier == 'RED_CRITICAL_DEVIATION' else ('#F59E0B' if tier == 'YELLOW_MODERATE_DEVIATION' else '#10B981')
            return {'fillColor': color, 'color': '#0F172A', 'weight': 1, 'fillOpacity': 0.65}
        m.add_gdf(filtered_gdf, layer_name="APCRDA Cadastre", style_callback=style_callback, info_mode="on_click")
        m.to_streamlit(height=520)

    with tab_inspector:
        sel_id = st.selectbox("Select Parcel to Inspect:", options=filtered_gdf['parcel_id'].tolist())
        row = filtered_gdf[filtered_gdf['parcel_id'] == sel_id].iloc[0]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**Owner:** {row['owner_name']}")
            st.write(f"**Zone:** {row['zone']}")
            st.write(f"**Category:** {row['property_type']}")
        with c2:
            st.write(f"**Permitted Floors:** {row['sanctioned_floors']}")
            st.write(f"**Actual Floors (3DGS):** {row['actual_floors']}")
            st.write(f"**Unauthorized Built-up:** {row['unauthorized_builtup_sqft']:,.1f} sq ft")
        with c3:
            st.write(f"**Base Tax:** ₹{row['base_tax_inr']:,.2f}")
            st.write(f"**25% Surcharge:** ₹{row['penalty_surcharge_inr']:,.2f}")
            st.write(f"**Total Demand:** ₹{row['total_tax_demand_inr']:,.2f}")

    with tab_forecast:
        if forecast_df is not None:
            fig = px.bar(
                forecast_df, x="Year",
                y=["Residential_Revenue_INR", "Commercial_Revenue_INR", "Institutional_Revenue_INR"],
                title="Projected Municipal Revenue by Sector (2026-2030)",
                labels={"value": "Revenue (INR)", "variable": "Sector"}
            )
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Execute 'python splattax_ai/run_pipeline.py' to generate initial data layers.")
