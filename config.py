#!/usr/bin/env python3
"""
Centralized configuration for Kevin's Outfit Finder.
All settings, paths, brand lists, and category definitions in one place.
"""

from pathlib import Path
from typing import Dict, List

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent
TESSERACT_PATH = "/opt/homebrew/bin/tesseract"

# Collection image directories (only 3 actual collections)
COLLECTION_PATHS: Dict[str, Path] = {
    "summer": BASE_DIR / "Kevin_Summer_Looks_Pages",
    "spring": BASE_DIR / "KEVIN_Spring_Looks_Images",
    "fw": BASE_DIR / "Fall_Winter_Looks_Images",
}

# Data file paths (only 3 actual collections - fall/winter are filtered views of fw)
DATA_FILES: Dict[str, Dict[str, Path]] = {
    "summer": {
        "clothing_index": BASE_DIR / "clothing_index.json",
        "page_items": BASE_DIR / "page_items.json",
        "category_stats": BASE_DIR / "category_stats_summer.json",
    },
    "spring": {
        "clothing_index": BASE_DIR / "clothing_index_spring.json",
        "page_items": BASE_DIR / "page_items_spring.json",
        "category_stats": BASE_DIR / "category_stats_spring.json",
    },
    "fw": {
        "clothing_index": BASE_DIR / "clothing_index_fw.json",
        "page_items": BASE_DIR / "page_items_fw.json",
        "category_stats": BASE_DIR / "category_stats_fw.json",
    },
}

# Page seasons files (for seasonal filtering within each collection)
PAGE_SEASONS_FILES: Dict[str, Path] = {
    "summer": BASE_DIR / "page_seasons_summer.json",
    "spring": BASE_DIR / "page_seasons_spring.json",
    "fw": BASE_DIR / "page_seasons_fw.json",
}

# Legacy alias for backward compatibility
PAGE_SEASONS_FILE = PAGE_SEASONS_FILES["fw"]

# Static site output
DIST_DIR = BASE_DIR / "dist"
DIST_IMAGE_FOLDERS: Dict[str, str] = {
    "summer": "images",
    "spring": "spring_images",
    "fw": "fw_images",
}

# =============================================================================
# CLOTHING CATEGORIES
# =============================================================================

# Category keywords for OCR item classification
CATEGORIES: Dict[str, Dict[str, List[str]]] = {
    "summer": {
        "Outerwear": ["jacket", "blazer", "cardigan"],
        "Tops": ["polo", "shirt", "sweater", "tee", "t-shirt", "blouse", "henley"],
        "Bottoms": ["trouser", "pant", "short", "jean", "chino", "khaki", "5-pocket", "5 pocket", "corduroy"],
        "Footwear": ["loafer", "sandal", "espadrille", "shoe", "sneaker", "moccasin"],
        "Accessories": ["belt", "watch", "sunglasses", "hat", "tie"],
    },
    "spring": {
        "Outerwear": ["jacket", "coat", "blazer", "windbreaker", "bomber", "trench", "parka", "vest", "overcoat"],
        "Tops": ["shirt", "polo", "t-shirt", "tee", "blouse", "sweater", "pullover", "hoodie", "cardigan", "knit", "henley", "tank", "turtleneck", "sweatshirt"],
        "Bottoms": ["trouser", "pant", "jean", "chino", "short", "slack", "jogger", "corduroy", "5 pocket", "5-pocket"],
        "Footwear": ["shoe", "sneaker", "loafer", "boot", "sandal", "slipper", "oxford", "derby", "moccasin", "espadrille", "desert boot"],
        "Accessories": ["belt", "watch", "sunglasses", "hat", "cap", "scarf", "tie", "bag", "wallet", "bracelet", "necklace"],
        "Suits": ["suit", "tuxedo"],
        "Activewear": ["tracksuit", "sweatpant", "athletic", "gym", "running", "training"],
    },
    "fw": {
        "Outerwear": ["coat", "jacket", "blazer", "overcoat", "parka", "bomber", "windbreaker", "trench", "peacoat", "duffle", "topcoat", "raincoat", "anorak"],
        "Knitwear": ["sweater", "cardigan", "pullover", "jumper", "knit", "turtleneck", "rollneck", "v-neck", "crewneck", "cable knit", "merino", "cashmere", "wool"],
        "Tops": ["shirt", "polo", "blouse", "t-shirt", "tee", "henley", "oxford", "flannel"],
        "Bottoms": ["trouser", "pant", "jean", "chino", "corduroy", "slack", "wool pant", "flannel trouser", "5 pocket", "5-pocket"],
        "Footwear": ["boot", "shoe", "loafer", "oxford", "derby", "chelsea", "combat boot", "desert boot", "sneaker", "brogue", "monk strap", "chukka"],
        "Accessories": ["scarf", "glove", "hat", "beanie", "cap", "belt", "watch", "bag", "sunglasses", "tie", "pocket square", "muffler"],
        "Suits": ["suit", "tuxedo", "dinner jacket", "formal"],
        "Layering": ["vest", "gilet", "waistcoat", "liner", "thermal"],
    },
}

# Aliases for category lookup
SUMMER_CATEGORIES = CATEGORIES["summer"]
SPRING_CATEGORIES = CATEGORIES["spring"]
FW_CATEGORIES = CATEGORIES["fw"]

# Category display order for each collection
CATEGORY_ORDER: Dict[str, List[str]] = {
    "summer": ["Bottoms", "Tops", "Footwear", "Outerwear", "Accessories", "Other"],
    "spring": ["Bottoms", "Tops", "Footwear", "Outerwear", "Accessories", "Suits", "Activewear", "Other"],
    "fw": ["Bottoms", "Tops", "Footwear", "Outerwear", "Knitwear", "Suits", "Layering", "Accessories", "Other"],
    # Fall/Winter use the same order as fw (they're filtered views)
    "fall": ["Bottoms", "Tops", "Footwear", "Outerwear", "Knitwear", "Suits", "Layering", "Accessories", "Other"],
    "winter": ["Bottoms", "Tops", "Footwear", "Outerwear", "Knitwear", "Suits", "Layering", "Accessories", "Other"],
}

# Category icons for display
CATEGORY_ICONS: Dict[str, str] = {
    "Outerwear": "🧥",
    "Knitwear": "🧶",
    "Tops": "👔",
    "Bottoms": "👖",
    "Footwear": "👞",
    "Accessories": "🧣",
    "Suits": "🤵",
    "Layering": "🦺",
    "Activewear": "🏃",
    "Other": "📦",
}

# =============================================================================
# BRAND LIST (Consolidated)
# =============================================================================

# All recognized luxury/designer brands
BRANDS: List[str] = [
    # Core luxury
    "Saint Laurent", "The Row", "Prada", "Tom Ford", "Brunello Cucinelli",
    "Loro Piana", "Zegna", "Hermès", "Hermes", "Bottega Veneta", "Gucci",
    "Valentino", "Burberry", "Ralph Lauren", "Polo Ralph Lauren",
    # Italian tailoring
    "Boglioli", "Lardini", "Caruso", "Canali", "Kiton", "Isaia", "Brioni",
    "De Petrillo", "Ring Jacket",
    # European designer
    "Celine", "Dior", "Balenciaga", "Acne Studios", "Thom Browne",
    "Maison Margiela", "Lanvin", "Dries Van Noten", "Dries", "Jil Sander",
    "Marni", "Lemaire", "Margaret Howell", "Loewe",
    # British
    "Drake's", "Drakes", "Anderson & Sheppard", "Sunspel", "John Smedley",
    "Private White V.C.", "SEH Kelly", "Clarks", "Dunhill",
    # Contemporary/Streetwear
    "Stone Island", "Moncler", "Off-White", "Fear of God", "Rick Owens",
    "Common Projects", "A.P.C.", "APC", "Norse Projects", "Our Legacy", "Auralee",
    # Knitwear specialists
    "Iris Von Arnim", "Le Kasha", "Fedeli", "Gran Sasso", "Zanone",
    "The Elder Statesman",
    # Other notable
    "Altea", "Officine Generale", "Beams", "Lacoste", "Frame", "Frankie Shop",
    "Massimo Alba", "Berg & Berg", "Saman Amel", "Stoffa", "Canada Goose",
    "Derek Rose", "Castaner", "Ikiji", "Barena", "Umit Benan", "Cesare Attolini",
    "Luca Museo", "Rubinacci", "Mr P", "Mr. P", "The Armoury", "Armory",
    "Kenji Kaga", "J Mueser", "Sid Mashburn",
]

# Aliases for backward compatibility
ALL_BRANDS = BRANDS
SUMMER_BRANDS = BRANDS
SPRING_BRANDS = BRANDS
FW_BRANDS = BRANDS

# =============================================================================
# OCR SETTINGS
# =============================================================================

MAX_ITEM_LENGTH = 50  # Max length before considering it multiple items
MIN_ITEM_LENGTH = 3   # Min length to be considered valid

OCR_ARTIFACTS = [
    r"^i\s+",      # Leading "i "
    r"^of\s+",    # Leading "of "
    r"^\d+\s+",   # Leading numbers
    r"^[^\w]+",   # Leading non-word characters
]

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================

COLLECTION_DISPLAY_NAMES: Dict[str, str] = {
    "summer": "Summer",
    "spring": "Spring",
    "fw": "Fall/Winter",
    "fall": "Fall",
    "winter": "Winter",
}

COLLECTION_ICONS: Dict[str, str] = {
    "summer": "☀️",
    "spring": "🌸",
    "fw": "❄️",
    "fall": "🍂",
    "winter": "❄️",
}

DEFAULT_COLLECTION = "summer"
FUZZY_SEARCH_THRESHOLD = 0.6
