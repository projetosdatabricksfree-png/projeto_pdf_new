"""
GWG Profile Matcher - Ghent Workgroup 2015/2022 Specification Constants
Handles different validation thresholds based on the target printing process.
"""

from typing import Dict, Any

# Thresholds baseados na GWG 2015 Specification (§5.1 - §5.14)
GWG_PROFILES = {
    # 1. MagazineAds (Web Offset)
    "MagazineAds_CMYK": {
        "name": "GWG 2015 Magazine Ads (CMYK)",
        "tac_limit": 305,
        "min_image_resolution": 149,
        "warn_image_resolution": 224,
        "max_spot_colors": 0,
        "allowed_color_spaces": ["CMYK", "Gray"],
        "allow_rgb": False
    },
    "MagazineAds_CMYK+RGB": {
        "name": "GWG 2015 Magazine Ads (CMYK+RGB)",
        "tac_limit": 305,
        "min_image_resolution": 149,
        "warn_image_resolution": 224,
        "max_spot_colors": 0,
        "allowed_color_spaces": ["CMYK", "Gray", "RGB", "ICCBased"],
        "allow_rgb": True
    },
    # 2. NewspaperAds
    "NewspaperAds_CMYK": {
        "name": "GWG 2015 Newspaper Ads (CMYK)",
        "tac_limit": 245,
        "min_image_resolution": 99,
        "warn_image_resolution": 149,
        "max_spot_colors": 1,
        "allowed_color_spaces": ["CMYK", "Gray", "Spot"],
        "allow_rgb": False
    },
    "NewspaperAds_CMYK+RGB": {
        "name": "GWG 2015 Newspaper Ads (CMYK+RGB)",
        "tac_limit": 245,
        "min_image_resolution": 99,
        "warn_image_resolution": 149,
        "max_spot_colors": 1,
        "allowed_color_spaces": ["CMYK", "Gray", "RGB", "Spot"],
        "allow_rgb": True
    },
    # 3. Sheetfed Offset
    "SheetCmyk_CMYK": {
        "name": "GWG 2015 Sheetfed Offset (CMYK)",
        "tac_limit": 320,
        "min_image_resolution": 149,
        "warn_image_resolution": 224,
        "max_spot_colors": 0,
        "allowed_color_spaces": ["CMYK", "Gray"],
        "allow_rgb": False
    },
    "SheetCmyk_CMYK+RGB": {
        "name": "GWG 2015 Sheetfed Offset (CMYK+RGB)",
        "tac_limit": 320,
        "min_image_resolution": 149,
        "warn_image_resolution": 224,
        "max_spot_colors": 0,
        "allowed_color_spaces": ["CMYK", "Gray", "RGB"],
        "allow_rgb": True
    },
    "SheetSpot_CMYK": {
        "name": "GWG 2015 Sheetfed Offset Spot (CMYK)",
        "tac_limit": 320,
        "min_image_resolution": 149,
        "warn_image_resolution": 224,
        "max_spot_colors": 2,
        "allowed_color_spaces": ["CMYK", "Gray", "Spot"],
        "allow_rgb": False
    },
    "SheetSpot_CMYK+RGB": {
        "name": "GWG 2015 Sheetfed Offset Spot (CMYK+RGB)",
        "tac_limit": 320,
        "min_image_resolution": 149,
        "warn_image_resolution": 224,
        "max_spot_colors": 2,
        "allowed_color_spaces": ["CMYK", "Gray", "RGB", "Spot"],
        "allow_rgb": True
    },
    # 4. Web Offset (Heatset)
    "WebCmyk_CMYK": {
        "name": "GWG 2015 Web Offset (CMYK)",
        "tac_limit": 300,
        "min_image_resolution": 149,
        "warn_image_resolution": 224,
        "max_spot_colors": 0,
        "allowed_color_spaces": ["CMYK", "Gray"],
        "allow_rgb": False
    },
    "WebCmyk_CMYK+RGB": {
        "name": "GWG 2015 Web Offset (CMYK+RGB)",
        "tac_limit": 300,
        "min_image_resolution": 149,
        "warn_image_resolution": 224,
        "max_spot_colors": 0,
        "allowed_color_spaces": ["CMYK", "Gray", "RGB"],
        "allow_rgb": True
    },
    # 5. Web Cmyk News (Coldset)
    "WebCmykNews_CMYK": {
        "name": "GWG 2015 Web Offset News (CMYK)",
        "tac_limit": 245,
        "min_image_resolution": 99,
        "warn_image_resolution": 149,
        "max_spot_colors": 0,
        "allowed_color_spaces": ["CMYK", "Gray"],
        "allow_rgb": False
    },
    "WebCmykNews_CMYK+RGB": {
        "name": "GWG 2015 Web Offset News (CMYK+RGB)",
        "tac_limit": 245,
        "min_image_resolution": 99,
        "warn_image_resolution": 149,
        "max_spot_colors": 0,
        "allowed_color_spaces": ["CMYK", "Gray", "RGB"],
        "allow_rgb": True
    },
    # 6. Web Spot (Heatset)
    "WebSpot_CMYK": {
        "name": "GWG 2015 Web Offset Spot (CMYK)",
        "tac_limit": 300,
        "min_image_resolution": 149,
        "warn_image_resolution": 224,
        "max_spot_colors": 2,
        "allowed_color_spaces": ["CMYK", "Gray", "Spot"],
        "allow_rgb": False
    },
    "WebSpot_CMYK+RGB": {
        "name": "GWG 2015 Web Offset Spot (CMYK+RGB)",
        "tac_limit": 300,
        "min_image_resolution": 149,
        "warn_image_resolution": 224,
        "max_spot_colors": 2,
        "allowed_color_spaces": ["CMYK", "Gray", "RGB", "Spot"],
        "allow_rgb": True
    },
    # Default Fallback
    "default": {
        "name": "GWG 2015 Default (Generic)",
        "tac_limit": 300,
        "min_image_resolution": 150,
        "warn_image_resolution": 225,
        "max_spot_colors": 2,
        "allowed_color_spaces": ["CMYK", "Gray", "Spot"],
        "allow_rgb": False
    }
}

def get_gwg_profile(profile_key: str = "default") -> Dict[str, Any]:
    """Retorna os parâmetros de validação para um determinado perfil GWG."""
    return GWG_PROFILES.get(profile_key, GWG_PROFILES["default"])

def identify_profile_by_metadata(metadata: Dict[str, Any]) -> str:
    """
    Tenta identificar o perfil GWG ideal baseado nos metadados do arquivo.
    """
    product = metadata.get("produto", "").lower()
    
    # Newspaper
    if any(k in product for k in ["jornal", "newspaper", "news"]):
        return "NewspaperAds_CMYK"
    
    # Web Spot (Heatset with spots)
    if any(k in product for k in ["web spot", "rotativa spot"]):
        return "WebSpot_CMYK"

    # Web/Commercial (Heatset)
    if any(k in product for k in ["web offset", "rotativa commercial", "web cmyk"]):
        return "WebCmyk_CMYK"
        
    return "default"
