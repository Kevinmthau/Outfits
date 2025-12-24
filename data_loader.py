#!/usr/bin/env python3
"""
Data loader with validation for Kevin's Outfit Finder.
Loads JSON data and validates using Pydantic models.
Centralized data operations used by app.py and static site generator.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from pydantic import ValidationError

from config import DATA_FILES, PAGE_SEASONS_FILE, PAGE_SEASONS_FILES, CATEGORY_ORDER
from models import ClothingItem, CollectionData


def load_json(file_path: Path) -> Dict:
    """Load JSON file with error handling."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_collection(collection: str, validate: bool = True) -> CollectionData:
    """
    Load and optionally validate a collection's data.

    Args:
        collection: Collection name ('summer', 'spring', or 'fw')
        validate: Whether to validate data against models

    Returns:
        CollectionData object with all collection data

    Raises:
        FileNotFoundError: If data files don't exist
        ValidationError: If validation fails (when validate=True)
    """
    files = DATA_FILES.get(collection)
    if not files:
        raise ValueError(f"Unknown collection: {collection}")

    # Load raw data
    clothing_index = {}
    page_items = {}
    category_stats = None

    if files.get("clothing_index") and files["clothing_index"].exists():
        clothing_index = load_json(files["clothing_index"])

    if files.get("page_items") and files["page_items"].exists():
        page_items = load_json(files["page_items"])

    if files.get("category_stats") and files["category_stats"].exists():
        category_stats = load_json(files["category_stats"])

    if validate:
        # Validate using Pydantic model
        return CollectionData(
            name=collection,
            clothing_index=clothing_index,
            page_items=page_items,
            category_stats=category_stats,
        )
    else:
        # Return without validation (for legacy code compatibility)
        return CollectionData.model_construct(
            name=collection,
            clothing_index=clothing_index,
            page_items=page_items,
            category_stats=category_stats,
        )


def load_collection_raw(collection: str) -> Tuple[Dict, Dict, Optional[Dict]]:
    """
    Load collection data as raw dictionaries (legacy interface).

    This maintains backward compatibility with existing code.

    Returns:
        Tuple of (clothing_index, page_items, category_stats)
    """
    data = load_collection(collection, validate=False)
    return data.clothing_index, dict(data.page_items), data.category_stats


def load_page_seasons() -> Dict[str, str]:
    """Load the page seasons mapping."""
    if PAGE_SEASONS_FILE.exists():
        return load_json(PAGE_SEASONS_FILE)
    return {}


def validate_collection(collection: str) -> List[str]:
    """
    Validate a collection and return list of issues found.

    Returns:
        List of issue descriptions (empty if valid)
    """
    issues = []

    try:
        data = load_collection(collection, validate=True)
    except FileNotFoundError as e:
        return [str(e)]
    except ValidationError as e:
        return [f"Validation error: {err['msg']}" for err in e.errors()]

    # Additional semantic validation
    index_items = set(data.clothing_index.keys())
    page_item_names = set()

    for page, items in data.page_items.items():
        for item in items:
            if isinstance(item, ClothingItem):
                page_item_names.add(item.name)

    # Check for items in index but not in page_items
    orphan_index = index_items - page_item_names
    if orphan_index and len(orphan_index) < 10:
        issues.append(f"Items in index but not in page_items: {orphan_index}")

    # Check for items in page_items but not in index
    orphan_pages = page_item_names - index_items
    if orphan_pages and len(orphan_pages) < 10:
        issues.append(f"Items in page_items but not in index: {orphan_pages}")

    return issues


def validate_all_collections() -> Dict[str, List[str]]:
    """Validate all collections and return issues by collection."""
    results = {}
    for collection in DATA_FILES.keys():
        issues = validate_collection(collection)
        if issues:
            results[collection] = issues
        else:
            results[collection] = ["OK"]
    return results


# =============================================================================
# Shared utility functions (used by app.py and generate_static_site_all_collections.py)
# =============================================================================


def load_page_seasons_for_collection(collection: str = "fw") -> Dict[str, str]:
    """Load page seasons mapping for a specific collection."""
    seasons_file = PAGE_SEASONS_FILES.get(collection, PAGE_SEASONS_FILE)
    if seasons_file.exists():
        return load_json(seasons_file)
    return {}


def filter_by_season(
    clothing_index: Dict[str, List],
    page_items: Dict,
    season: str,
    page_seasons: Dict[str, str]
) -> Tuple[Dict[str, List], Dict]:
    """
    Filter clothing index and page items for a specific season.

    Args:
        clothing_index: Map of item names to list of pages
        page_items: Map of pages to list of items
        season: Season to filter for ('fall', 'winter', 'both', etc.)
        page_seasons: Map of pages to their assigned season

    Returns:
        Tuple of (filtered_clothing_index, filtered_page_items)
    """
    # Build set of pages for this season
    season_pages: Set[str] = set()
    for page, page_season in page_seasons.items():
        if page_season == season or page_season == 'both':
            season_pages.add(page)

    # Filter page_items
    filtered_page_items = {
        page: items for page, items in page_items.items()
        if page in season_pages
    }

    # Filter clothing_index - handle both integer and string page formats
    filtered_clothing_index = {}
    for item, pages in clothing_index.items():
        filtered_pages = []
        for p in pages:
            # Normalize page key format
            page_key = p if isinstance(p, str) and p.startswith("page_") else f"page_{p}"
            if page_key in season_pages:
                filtered_pages.append(page_key)
        if filtered_pages:
            filtered_clothing_index[item] = filtered_pages

    return filtered_clothing_index, filtered_page_items


def rebuild_index(page_items: Dict) -> Dict[str, List[str]]:
    """
    Rebuild clothing index from page_items.

    Args:
        page_items: Map of pages to list of items

    Returns:
        Rebuilt clothing index mapping item names to list of pages
    """
    index: Dict[str, List[str]] = {}
    for page, items in page_items.items():
        for item_data in items:
            if isinstance(item_data, dict):
                name = item_data.get("name", "")
            else:
                name = item_data

            if name:
                if name not in index:
                    index[name] = []
                index[name].append(page)

    # Sort pages for each item numerically
    for name in index:
        index[name] = sorted(
            set(index[name]),
            key=lambda x: int(x.replace("page_", "")) if "page_" in str(x) else int(x)
        )

    return index


def categorize_items(
    clothing_index: Dict[str, List],
    collection: str,
    page_items: Dict = None
) -> Dict[str, List[Tuple[str, List, str]]]:
    """
    Categorize items by their category.

    Args:
        clothing_index: Map of item names to list of pages
        collection: Collection name for category order lookup
        page_items: Optional page items for category lookup

    Returns:
        Dict mapping category names to list of (item_name, pages, category) tuples
    """
    categories = CATEGORY_ORDER.get(collection, CATEGORY_ORDER.get("summer", []))
    categorized: Dict[str, List[Tuple[str, List, str]]] = {cat: [] for cat in categories}

    # Build item->category lookup from page_items
    item_category_lookup = {}
    if page_items:
        for page, items in page_items.items():
            for item_data in items:
                if isinstance(item_data, dict):
                    name = item_data.get("name", "")
                    category = item_data.get("category", "")
                    if name and category and name not in item_category_lookup:
                        item_category_lookup[name] = category

    for item_name, pages in clothing_index.items():
        # Check if item name has category suffix like "Item Name (Category)"
        category = None
        display_name = item_name

        if ' (' in item_name and item_name.endswith(')'):
            # Extract category from name like "The Row loafer (Footwear)"
            base_name = item_name.rsplit(' (', 1)[0]
            cat_from_name = item_name.rsplit(' (', 1)[1].rstrip(')')
            if cat_from_name in categorized:
                category = cat_from_name
                display_name = base_name

        # If no category from name, try lookup
        if not category:
            category = item_category_lookup.get(item_name)
            if not category and ' (' in item_name:
                base_name = item_name.rsplit(' (', 1)[0]
                category = item_category_lookup.get(base_name)

        # Default to Other if still no category
        if not category or category not in categorized:
            category = "Other"
            if "Other" not in categorized:
                categorized["Other"] = []

        categorized[category].append((display_name, pages, category))

    # Sort items within each category by page count (descending), then name
    for category in categorized:
        categorized[category].sort(key=lambda x: (-len(x[1]), x[0].lower()))

    return categorized


def save_json(file_path: Path, data: Dict, create_backup: bool = False) -> None:
    """
    Save data to JSON file.

    Args:
        file_path: Path to save to
        data: Data to save
        create_backup: If True, create timestamped backup first (requires backup_file function)
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # When run directly, validate all collections
    print("Validating all collections...\n")

    results = validate_all_collections()

    for collection, issues in results.items():
        status = "✅" if issues == ["OK"] else "⚠️"
        print(f"{status} {collection}:")
        for issue in issues:
            print(f"   {issue}")
        print()
