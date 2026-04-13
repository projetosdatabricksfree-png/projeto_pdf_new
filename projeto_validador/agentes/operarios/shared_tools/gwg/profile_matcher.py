"""
GWG Profile Matcher - Ghent Workgroup 2015/2022 Specification Constants
Handles different validation thresholds based on the target printing process.
"""

from typing import Dict, Any

# Thresholds baseados na GWG 2015 Specification
GWG_PROFILES = {
    "sheetfed_offset": {
        "name": "GWG 2015 Sheetfed Offset",
        "tac_limit": 300,
        "min_image_resolution": 250,
        "max_image_resolution": 450,
        "allowed_color_spaces": ["CMYK", "Gray", "Spot"],
        "max_spot_colors": 2,
        "require_output_intent": True,
        "allowed_pdf_versions": ["1.3", "1.4", "1.6"]
    },
    "magazine_ads": {
        "name": "GWG 2015 Web Offset (Magazine)",
        "tac_limit": 300,
        "min_image_resolution": 225,
        "max_image_resolution": 450,
        "allowed_color_spaces": ["CMYK", "Gray", "Spot"],
        "max_spot_colors": 0,
        "require_output_intent": True,
        "allowed_pdf_versions": ["1.3", "1.4"]
    },
    "newspaper": {
        "name": "GWG 2015 Newspaper",
        "tac_limit": 240,
        "min_image_resolution": 150,
        "max_image_resolution": 300,
        "allowed_color_spaces": ["CMYK", "Gray"],
        "max_spot_colors": 0,
        "require_output_intent": True,
        "allowed_pdf_versions": ["1.3"]
    },
    "packaging": {
        "name": "GWG 2022 Packaging (Flexo/Offset)",
        "tac_limit": 330,
        "min_image_resolution": 300,
        "max_image_resolution": 600,
        "allowed_color_spaces": ["CMYK", "Gray", "Spot", "DeviceN"],
        "max_spot_colors": 12,
        "require_output_intent": True,
        "allowed_pdf_versions": ["1.4", "1.6", "1.7"]
    }
}

def get_gwg_profile(profile_key: str = "sheetfed_offset") -> Dict[str, Any]:
    """Retorna os parâmetros de validação para um determinado perfil GWG."""
    return GWG_PROFILES.get(profile_key, GWG_PROFILES["sheetfed_offset"])

def identify_profile_by_metadata(metadata: Dict[str, Any]) -> str:
    """
    Tenta identificar o perfil GWG ideal baseado nos metadados do arquivo (Ex: ProductType do Gerente).
    Default: sheetfed_offset
    """
    product = metadata.get("produto", "").lower()
    
    if "jornal" in product or "newspaper" in product:
        return "newspaper"
    if "revista" in product or "magazine" in product:
        return "magazine_ads"
    if "embalagem" in product or "packaging" in product:
        return "packaging"
        
    return "sheetfed_offset"
