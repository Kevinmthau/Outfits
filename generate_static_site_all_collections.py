#!/usr/bin/env python3
"""
Generate a static version of the outfit finder with four collections.
Features:
- Lazy loading for images
- WebP support with PNG fallback
- Fuzzy search
- Unified categorized data format
- Separate Fall and Winter tabs (using page_seasons_fw.json)
- Templates loaded from external files
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from config import (
    DATA_FILES,
    COLLECTION_PATHS,
    DIST_DIR,
    DIST_IMAGE_FOLDERS,
    CATEGORY_ORDER,
    CATEGORY_ICONS,
    PAGE_SEASONS_FILE,
)

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"


def load_template(name: str) -> str:
    """Load a template file."""
    template_path = TEMPLATE_DIR / name
    if template_path.exists():
        return template_path.read_text(encoding='utf-8')
    raise FileNotFoundError(f"Template not found: {template_path}")


def load_page_seasons() -> Dict[str, str]:
    """Load the page seasons mapping (page -> 'fall' or 'winter')."""
    if PAGE_SEASONS_FILE.exists():
        with open(PAGE_SEASONS_FILE, 'r') as f:
            return json.load(f)
    return {}


def load_collection_data(collection: str) -> Tuple[Dict, Dict, Optional[Dict]]:
    """Load clothing data for a specific collection."""
    files = DATA_FILES.get(collection, {})

    clothing_index = {}
    page_items = {}
    category_stats = None

    if "clothing_index" in files and files["clothing_index"].exists():
        with open(files["clothing_index"], 'r') as f:
            clothing_index = json.load(f)

    if "page_items" in files and files["page_items"].exists():
        with open(files["page_items"], 'r') as f:
            page_items = json.load(f)

    if "category_stats" in files and files["category_stats"].exists():
        with open(files["category_stats"], 'r') as f:
            category_stats = json.load(f)

    return clothing_index, page_items, category_stats


def filter_by_season(clothing_index: Dict, page_items: Dict, season: str, page_seasons: Dict[str, str]) -> Tuple[Dict, Dict]:
    """Filter clothing index and page items to only include pages for the given season."""
    season_pages: Set[str] = set()
    for page, page_season in page_seasons.items():
        if page_season == season:
            season_pages.add(page)

    filtered_page_items = {
        page: items for page, items in page_items.items()
        if page in season_pages
    }

    # Filter clothing index - pages may be integers or "page_X" strings
    filtered_clothing_index = {}
    for item, pages in clothing_index.items():
        filtered_pages = []
        for p in pages:
            # Handle both integer and string formats
            page_key = p if isinstance(p, str) and p.startswith("page_") else f"page_{p}"
            if page_key in season_pages:
                filtered_pages.append(page_key)
        if filtered_pages:
            filtered_clothing_index[item] = filtered_pages

    return filtered_clothing_index, filtered_page_items


def categorize_items(clothing_index: Dict[str, List], collection: str, page_items: Dict = None) -> Dict[str, List[Tuple[str, List, str]]]:
    """Categorize items using category data from the item names or page_items."""
    categories = CATEGORY_ORDER.get(collection, CATEGORY_ORDER["summer"])
    categorized: Dict[str, List[Tuple[str, List, str]]] = {cat: [] for cat in categories}

    # Build item->category lookup from page_items if available
    item_category_lookup = {}
    if page_items:
        for page, items in page_items.items():
            for item_data in items:
                if isinstance(item_data, dict) and 'name' in item_data and 'category' in item_data:
                    item_category_lookup[item_data['name']] = item_data['category']

    for item, pages in clothing_index.items():
        if item in item_category_lookup:
            item_name = item
            category = item_category_lookup[item]
        elif '(' in item and ')' in item:
            category = item[item.rfind('(')+1:item.rfind(')')]
            item_name = item[:item.rfind('(')].strip()
        else:
            item_name = item
            category = "Other"

        if category in categorized:
            categorized[category].append((item_name, pages, category))
        else:
            categorized["Other"].append((item_name, pages, "Other"))

    for category in categorized:
        categorized[category].sort(key=lambda x: len(x[1]), reverse=True)

    return categorized


def generate_collection_html(collection_name: str, clothing_index: Dict, page_items: Dict, image_folder: str) -> str:
    """Generate HTML for a specific collection."""
    collection_key = collection_name.lower().replace("/", "")
    if collection_key == "fallwinter":
        collection_key = "fw"

    categorized_items = categorize_items(clothing_index, collection_key, page_items)
    category_order = CATEGORY_ORDER.get(collection_key, CATEGORY_ORDER["summer"])

    category_sections = []
    for category in category_order:
        if category not in categorized_items or not categorized_items[category]:
            continue

        items = categorized_items[category]
        icon = CATEGORY_ICONS.get(category, '📦')

        section_html = f"""
                    <div class="category-section">
                        <div class="category-header">
                            <h2>{icon} {category}</h2>
                            <p class="category-description">{len(items)} items in this category</p>
                        </div>
                        <div class="item-grid">"""

        for item_name, pages, _ in items:
            escaped_item = item_name.replace("'", "\\'").replace('"', '\\"')
            section_html += f"""
                            <div class="item-card" data-item-name="{item_name}" onclick="showItemDetail('{escaped_item}', '{collection_name}', '{image_folder}')">
                                <div class="item-name">{item_name}</div>
                                <div class="item-count">
                                    Appears on {len(pages)} page{'s' if len(pages) > 1 else ''}
                                </div>
                                <button class="edit-btn" onclick="editItem(event, '{escaped_item}', '{collection_name}')" title="Edit item name">&#9998;</button>
                            </div>"""

        section_html += """
                        </div>
                    </div>"""

        category_sections.append(section_html)

    return ''.join(category_sections)


def create_all_collections_html() -> str:
    """Create the main static HTML file with four collections."""

    # Load all collections
    summer_index, summer_items, _ = load_collection_data('summer')
    spring_index, spring_items, _ = load_collection_data('spring')
    fw_index, fw_items, _ = load_collection_data('fw')

    # Load page seasons and filter Fall/Winter into separate collections
    page_seasons = load_page_seasons()
    fall_index, fall_items = filter_by_season(fw_index, fw_items, 'fall', page_seasons)
    winter_index, winter_items = filter_by_season(fw_index, fw_items, 'winter', page_seasons)

    # Generate HTML for each collection
    summer_html = generate_collection_html('Summer', summer_index, summer_items, 'images')
    spring_html = generate_collection_html('Spring', spring_index, spring_items, 'spring_images')
    fall_html = generate_collection_html('Fall', fall_index, fall_items, 'fw_images')
    winter_html = generate_collection_html('Winter', winter_index, winter_items, 'fw_images')

    # Load templates
    css_content = load_template("css/styles.css")
    js_content = load_template("js/app.js")
    html_template = load_template("index.html")

    # Render template with data
    html_content = html_template
    html_content = html_content.replace("{{ css_content }}", css_content)
    html_content = html_content.replace("{{ js_content }}", js_content)
    html_content = html_content.replace("{{ summer_html }}", summer_html)
    html_content = html_content.replace("{{ spring_html }}", spring_html)
    html_content = html_content.replace("{{ fall_html }}", fall_html)
    html_content = html_content.replace("{{ winter_html }}", winter_html)
    html_content = html_content.replace("{{ summer_index_json }}", json.dumps(summer_index))
    html_content = html_content.replace("{{ summer_items_json }}", json.dumps(summer_items))
    html_content = html_content.replace("{{ spring_index_json }}", json.dumps(spring_index))
    html_content = html_content.replace("{{ spring_items_json }}", json.dumps(spring_items))
    html_content = html_content.replace("{{ fall_index_json }}", json.dumps(fall_index))
    html_content = html_content.replace("{{ fall_items_json }}", json.dumps(fall_items))
    html_content = html_content.replace("{{ winter_index_json }}", json.dumps(winter_index))
    html_content = html_content.replace("{{ winter_items_json }}", json.dumps(winter_items))

    return html_content


def create_netlify_files_all_collections() -> None:
    """Create necessary files for Netlify deployment with all collections."""

    # Create dist directory
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()

    # Create images directories and copy images
    for collection, source_dir in COLLECTION_PATHS.items():
        output_folder = DIST_IMAGE_FOLDERS[collection]
        output_dir = DIST_DIR / output_folder
        output_dir.mkdir()

        if source_dir.exists():
            count = 0
            for img_file in source_dir.glob('*.png'):
                shutil.copy2(img_file, output_dir)
                count += 1
            print(f"✅ Copied {count} {collection} images")

    # Generate and write main HTML file
    html_content = create_all_collections_html()
    with open(DIST_DIR / 'index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("✅ Generated index.html with all three collections")

    # Create _redirects file in dist
    with open(DIST_DIR / '_redirects', 'w') as f:
        f.write("/*    /index.html   200\n")
    print("✅ Created _redirects")

    # Copy all data files to dist for reference
    for collection, files in DATA_FILES.items():
        for file_type, file_path in files.items():
            if file_path.exists():
                shutil.copy2(file_path, DIST_DIR)
    print("✅ Copied all data files")

    # Copy favicon files
    favicon_files = ['favicon.png', 'favicon.ico']
    for favicon in favicon_files:
        favicon_path = Path(favicon)
        if favicon_path.exists():
            shutil.copy2(favicon_path, DIST_DIR)
    print("✅ Copied favicon files")

    print(f"\n🎉 Static site with all three collections ready for deployment!")
    print(f"📁 Files created in: {DIST_DIR.absolute()}")
    print(f"📊 Total files: {len(list(DIST_DIR.rglob('*')))}")


def main() -> None:
    """Main function."""
    print("🚀 Generating static site with Summer, Spring & Fall/Winter collections...")
    print("   Features: Lazy loading, WebP support, Fuzzy search")
    create_netlify_files_all_collections()

    print(f"\n📱 Ready for mobile-friendly deployment with all collections!")
    print(f"\n📋 Next steps:")
    print(f"   1. (Optional) Run: python optimize_images.py all")
    print(f"      This converts images to WebP for ~30-50% smaller files")
    print(f"   2. Deploy to Netlify using: netlify deploy --prod --dir=dist")
    print(f"   3. Or drag and drop the 'dist' folder to Netlify")


if __name__ == "__main__":
    main()
