"""
SplatTax AI - Official Cadastre & Legal Boundaries Engine (APCRDA Nelapadu Unit-18 Edition)
Standardized English nomenclature with Compass Directional Boundaries and Times New Roman Italic styling.
"""

from splattax_ai.official_cadastre_and_hadulu import (
    build_unified_splattax_dataset,
    BASE_DIR,
    DATA_DIR,
    EPSG_WGS84,
    EPSG_UTM44N,
    CENTER_LAT,
    CENTER_LON,
)

if __name__ == "__main__":
    build_unified_splattax_dataset()
