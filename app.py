#!/usr/bin/env python3
"""
Flask web application for browsing clothing items and outfits.
Supports all collections (Summer, Spring, Fall/Winter) with inline edit/delete.
"""

from flask import Flask, render_template_string, jsonify, send_from_directory, request
import json
import shutil
from datetime import datetime
from pathlib import Path

from config import DATA_FILES, COLLECTION_PATHS, PAGE_SEASONS_FILE, BASE_DIR, CATEGORY_ORDER, CATEGORY_ICONS

app = Flask(__name__)

# Template directory
TEMPLATE_DIR = BASE_DIR / "templates"

# Backup directory
BACKUP_DIR = BASE_DIR / "backups"


def backup_file(file_path: Path) -> Path:
    """Create a timestamped backup of a file."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{file_path.stem}_{timestamp}{file_path.suffix}"
    shutil.copy2(file_path, backup_path)
    return backup_path


def load_json(path: Path) -> dict:
    """Load JSON file."""
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}


def save_json(path: Path, data: dict) -> None:
    """Save JSON file with backup."""
    backup_file(path)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_collection_data(collection: str) -> tuple:
    """Load all data for a collection."""
    files = DATA_FILES.get(collection, {})
    index = load_json(files.get("clothing_index", Path()))
    page_items = load_json(files.get("page_items", Path()))
    return index, page_items


def save_collection_data(collection: str, index: dict, page_items: dict) -> None:
    """Save all data for a collection."""
    files = DATA_FILES.get(collection, {})
    if "clothing_index" in files:
        save_json(files["clothing_index"], index)
    if "page_items" in files:
        save_json(files["page_items"], page_items)


def rebuild_index(page_items: dict) -> dict:
    """Rebuild clothing index from page_items."""
    index = {}
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

    # Sort pages for each item
    for name in index:
        index[name] = sorted(set(index[name]), key=lambda x: int(x.replace("page_", "")) if "page_" in str(x) else int(x))

    return index


# Load clothing data (legacy - for Summer only routes)
def load_data():
    """Load clothing index and page items from JSON files"""
    try:
        with open('clothing_index.json', 'r') as f:
            clothing_index = json.load(f)
        with open('page_items.json', 'r') as f:
            page_items = json.load(f)
        return clothing_index, page_items
    except FileNotFoundError:
        return {}, {}


def load_page_seasons():
    """Load the page seasons mapping."""
    if PAGE_SEASONS_FILE.exists():
        with open(PAGE_SEASONS_FILE, 'r') as f:
            return json.load(f)
    return {}


def filter_by_season(clothing_index, page_items, season, page_seasons):
    """Filter clothing index and page items for a specific season."""
    season_pages = set()
    for page, page_season in page_seasons.items():
        if page_season == season or page_season == 'both':
            season_pages.add(page)

    filtered_page_items = {
        page: items for page, items in page_items.items()
        if page in season_pages
    }

    filtered_clothing_index = {}
    for item, pages in clothing_index.items():
        filtered_pages = [p if isinstance(p, str) else f"page_{p}" for p in pages]
        filtered_pages = [p for p in filtered_pages if p in season_pages]
        if filtered_pages:
            filtered_clothing_index[item] = filtered_pages

    return filtered_clothing_index, filtered_page_items


def categorize_items(clothing_index, collection, page_items=None):
    """Categorize items by their category."""
    categories = CATEGORY_ORDER.get(collection, CATEGORY_ORDER.get("summer", []))
    # Remove "Other" from categories - we don't want it
    categories = [c for c in categories if c != "Other"]
    categorized = {cat: [] for cat in categories}

    # Build item->category lookup from page_items
    item_category_lookup = {}
    if page_items:
        for page, items in page_items.items():
            for item_data in items:
                if isinstance(item_data, dict):
                    name = item_data.get("name", "")
                    category = item_data.get("category", "Accessories")
                    if name and name not in item_category_lookup:
                        item_category_lookup[name] = category

    for item_name, pages in clothing_index.items():
        # Check if item name has category suffix like "Item Name (Category)"
        # This is common in Summer collection
        category = None
        display_name = item_name

        if ' (' in item_name and item_name.endswith(')'):
            # Extract category from name like "The Row loafer (Footwear)"
            base_name = item_name.rsplit(' (', 1)[0]
            cat_from_name = item_name.rsplit(' (', 1)[1].rstrip(')')
            if cat_from_name in categories:
                category = cat_from_name
                display_name = base_name

        # If no category from name, try lookup
        if not category:
            # Try exact match first
            category = item_category_lookup.get(item_name)
            # Try without category suffix
            if not category and ' (' in item_name:
                base_name = item_name.rsplit(' (', 1)[0]
                category = item_category_lookup.get(base_name)

        # Default to Accessories if still no category
        if not category or category not in categorized:
            category = "Accessories"

        categorized[category].append((display_name, pages, category))

    # Sort items within each category
    for category in categorized:
        categorized[category].sort(key=lambda x: (-len(x[1]), x[0].lower()))

    return categorized


def generate_collection_html(categorized_items, collection_name, image_folder, clothing_index=None):
    """Generate HTML for a collection's item cards."""
    category_sections = []

    # Build reverse lookup: display_name -> full index name
    full_name_lookup = {}
    if clothing_index:
        for full_name in clothing_index.keys():
            if ' (' in full_name and full_name.endswith(')'):
                base_name = full_name.rsplit(' (', 1)[0]
                full_name_lookup[base_name] = full_name
            else:
                full_name_lookup[full_name] = full_name

    # Use lowercase key for CATEGORY_ORDER lookup
    order_key = collection_name.lower()
    for category in CATEGORY_ORDER.get(order_key, CATEGORY_ORDER.get("summer", [])):
        items = categorized_items.get(category, [])
        if not items:
            continue

        icon = CATEGORY_ICONS.get(category, "")
        section_html = f'''
                    <div class="category-section">
                        <div class="category-header">
                            <h2>{icon} {category}</h2>
                            <p class="category-description">{len(items)} items in this category</p>
                        </div>
                        <div class="item-grid">'''

        # Check if this is a Fall/Winter collection (show season button)
        is_fw_collection = collection_name.lower() in ['fall', 'winter']

        for display_name, pages, item_category in items:
            # Get full name for JS functions (may have category suffix)
            full_name = full_name_lookup.get(display_name, display_name)
            escaped_full = full_name.replace("'", "\\'").replace('"', '\\"')
            escaped_display = display_name.replace("'", "\\'").replace('"', '\\"')

            # Season button only for Fall/Winter collections
            season_btn = ''
            if is_fw_collection:
                season_btn = f'''<button class="season-btn" onclick="changeSeason(event, '{escaped_full}', '{collection_name}')" title="Change season">🍂❄️</button>'''

            section_html += f'''
                            <div class="item-card" data-item-name="{display_name}" onclick="showItemDetail('{escaped_display}', '{collection_name}', '{image_folder}')">
                                <div class="item-name">{display_name}</div>
                                <div class="item-count">
                                    Appears on {len(pages)} page{'s' if len(pages) > 1 else ''}
                                </div>
                                {season_btn}
                                <button class="category-btn" onclick="changeCategory(event, '{escaped_full}', '{collection_name}', '{item_category}')" title="Change category">&#128193;</button>
                                <button class="edit-btn" onclick="editItem(event, '{escaped_full}', '{collection_name}')" title="Edit item name">&#9998;</button>
                            </div>'''

        section_html += '''
                        </div>
                    </div>'''
        category_sections.append(section_html)

    return ''.join(category_sections)

@app.route('/')
def index():
    """Main page showing all clothing items from all collections."""
    # Load all collections
    summer_index, summer_items = load_collection_data('summer')
    spring_index, spring_items = load_collection_data('spring')
    fw_index, fw_items = load_collection_data('fw')

    # Load page seasons and filter Fall/Winter
    page_seasons = load_page_seasons()
    fall_index, fall_items = filter_by_season(fw_index, fw_items, 'fall', page_seasons)
    winter_index, winter_items = filter_by_season(fw_index, fw_items, 'winter', page_seasons)

    # Categorize items (use lowercase keys for CATEGORY_ORDER)
    summer_categorized = categorize_items(summer_index, 'summer', summer_items)
    spring_categorized = categorize_items(spring_index, 'spring', spring_items)
    fall_categorized = categorize_items(fall_index, 'fall', fall_items)
    winter_categorized = categorize_items(winter_index, 'winter', winter_items)

    # Generate HTML for each collection
    summer_html = generate_collection_html(summer_categorized, 'Summer', '/collection-images/summer', summer_index)
    spring_html = generate_collection_html(spring_categorized, 'Spring', '/collection-images/spring', spring_index)
    fall_html = generate_collection_html(fall_categorized, 'Fall', '/collection-images/fw', fall_index)
    winter_html = generate_collection_html(winter_categorized, 'Winter', '/collection-images/fw', winter_index)

    # Load CSS and JS
    css_content = (TEMPLATE_DIR / "css" / "styles.css").read_text()
    js_content = (TEMPLATE_DIR / "js" / "app.js").read_text()

    # Load template
    template = (TEMPLATE_DIR / "index.html").read_text()

    # Render template with all data
    html = template.replace('{{ css_content }}', css_content)
    html = html.replace('{{ js_content }}', js_content)
    html = html.replace('{{ summer_html }}', summer_html)
    html = html.replace('{{ spring_html }}', spring_html)
    html = html.replace('{{ fall_html }}', fall_html)
    html = html.replace('{{ winter_html }}', winter_html)
    html = html.replace('{{ summer_index_json }}', json.dumps(summer_index))
    html = html.replace('{{ summer_items_json }}', json.dumps(summer_items))
    html = html.replace('{{ spring_index_json }}', json.dumps(spring_index))
    html = html.replace('{{ spring_items_json }}', json.dumps(spring_items))
    html = html.replace('{{ fall_index_json }}', json.dumps(fall_index))
    html = html.replace('{{ fall_items_json }}', json.dumps(fall_items))
    html = html.replace('{{ winter_index_json }}', json.dumps(winter_index))
    html = html.replace('{{ winter_items_json }}', json.dumps(winter_items))
    html = html.replace('{{ page_seasons_json }}', json.dumps(page_seasons))

    return html

@app.route('/item/<path:item_name>')
def item_detail(item_name):
    """Show pages where a specific item appears"""
    clothing_index, page_items = load_data()
    
    if item_name in clothing_index:
        pages = clothing_index[item_name]
        # Sort pages numerically
        pages.sort(key=lambda x: int(x.split('_')[1]) if '_' in x else int(x))
        return render_template('item_detail.html', 
                             item_name=item_name,
                             pages=pages)
    else:
        return "Item not found", 404

@app.route('/page/<page_name>')
def page_detail(page_name):
    """Show all items on a specific page"""
    clothing_index, page_items = load_data()
    
    if page_name in page_items:
        items = page_items[page_name]
        return render_template('page_detail.html',
                             page_name=page_name,
                             items=items)
    else:
        return "Page not found", 404

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the Kevin_Summer_Looks_Pages directory"""
    return send_from_directory('Kevin_Summer_Looks_Pages', filename)

@app.route('/api/search/<query>')
def search_items(query):
    """API endpoint to search for clothing items"""
    clothing_index, page_items = load_data()

    query_lower = query.lower()
    matching_items = {}

    for item, pages in clothing_index.items():
        if query_lower in item.lower():
            matching_items[item] = pages

    return jsonify(matching_items)


# =============================================================================
# Multi-collection image serving
# =============================================================================

@app.route('/collection-images/<collection>/<path:filename>')
def serve_collection_image(collection, filename):
    """Serve images from any collection folder."""
    if collection not in COLLECTION_PATHS:
        return "Collection not found", 404
    image_dir = COLLECTION_PATHS[collection]
    return send_from_directory(image_dir, filename)


# =============================================================================
# API Endpoints for Edit/Delete
# =============================================================================

@app.route('/api/item/rename', methods=['PUT'])
def api_rename_item():
    """Rename a clothing item across all occurrences."""
    try:
        data = request.get_json()
        collection = data.get('collection')
        old_name = data.get('old_name')
        new_name = data.get('new_name', '').strip()

        if not collection or not old_name or not new_name:
            return jsonify({'error': 'Missing required fields'}), 400

        if old_name == new_name:
            return jsonify({'error': 'New name is the same as old name'}), 400

        index, page_items = load_collection_data(collection)

        # Update page_items
        updated_count = 0
        for page, items in page_items.items():
            for i, item_data in enumerate(items):
                if isinstance(item_data, dict) and item_data.get('name') == old_name:
                    items[i]['name'] = new_name
                    updated_count += 1
                elif isinstance(item_data, str) and item_data == old_name:
                    items[i] = new_name
                    updated_count += 1

        if updated_count == 0:
            return jsonify({'error': f'Item "{old_name}" not found'}), 404

        # Rebuild index
        index = rebuild_index(page_items)

        # Save data
        save_collection_data(collection, index, page_items)

        return jsonify({'success': True, 'message': f'Renamed "{old_name}" to "{new_name}" ({updated_count} occurrences)'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/page/<collection>/<page_name>', methods=['DELETE'])
def api_delete_page(collection, page_name):
    """Delete a page from a collection."""
    try:
        if collection not in DATA_FILES:
            return jsonify({'error': 'Invalid collection'}), 400

        index, page_items = load_collection_data(collection)

        if page_name not in page_items:
            return jsonify({'error': f'Page "{page_name}" not found'}), 404

        # Remove page
        del page_items[page_name]

        # Rebuild index
        index = rebuild_index(page_items)

        # Save data
        save_collection_data(collection, index, page_items)

        # Also remove from seasons if fw collection
        if collection == 'fw':
            seasons = load_json(PAGE_SEASONS_FILE)
            if page_name in seasons:
                del seasons[page_name]
                save_json(PAGE_SEASONS_FILE, seasons)

        return jsonify({'success': True, 'message': f'Deleted {page_name}'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/item/category', methods=['PUT'])
def api_change_category():
    """Change category for a clothing item across all occurrences."""
    try:
        data = request.get_json()
        collection = data.get('collection')
        item_name = data.get('item_name')
        new_category = data.get('new_category')

        if not collection or not item_name or not new_category:
            return jsonify({'error': 'Missing required fields'}), 400

        index, page_items = load_collection_data(collection)

        # Update category in page_items
        updated_count = 0
        for page, items in page_items.items():
            for i, item_data in enumerate(items):
                if isinstance(item_data, dict) and item_data.get('name') == item_name:
                    items[i]['category'] = new_category
                    updated_count += 1
                elif isinstance(item_data, str) and item_data == item_name:
                    items[i] = {'name': item_name, 'category': new_category}
                    updated_count += 1

        if updated_count == 0:
            return jsonify({'error': f'Item "{item_name}" not found'}), 404

        # Save data (index doesn't change for category updates)
        save_collection_data(collection, index, page_items)

        return jsonify({'success': True, 'message': f'Changed "{item_name}" to {new_category} ({updated_count} occurrences)'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/item/season', methods=['PUT'])
def api_change_item_season():
    """Change season for all pages of an item (fall/winter/both)."""
    try:
        data = request.get_json()
        item_name = data.get('item_name')
        new_season = data.get('new_season')

        if not item_name or not new_season:
            return jsonify({'error': 'Missing required fields'}), 400

        if new_season not in ['fall', 'winter', 'both']:
            return jsonify({'error': 'Invalid season. Must be fall, winter, or both'}), 400

        # Load fw clothing index to find all pages for this item
        fw_index, _ = load_collection_data('fw')

        # Find pages for this item
        pages = fw_index.get(item_name, [])
        if not pages:
            return jsonify({'error': f'Item "{item_name}" not found'}), 404

        # Load and update seasons for all pages
        seasons = load_json(PAGE_SEASONS_FILE)
        for page in pages:
            page_key = f"page_{page}" if isinstance(page, int) else page
            seasons[page_key] = new_season
        save_json(PAGE_SEASONS_FILE, seasons)

        return jsonify({'success': True, 'message': f'Changed {len(pages)} pages to {new_season}'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/<collection>')
def api_get_collection_data(collection):
    """Get fresh data for a collection (used after edit/delete)."""
    if collection not in DATA_FILES:
        return jsonify({'error': 'Invalid collection'}), 400

    index, page_items = load_collection_data(collection)

    # For fw collection, also return seasons data
    if collection == 'fw':
        seasons = load_json(PAGE_SEASONS_FILE)
        return jsonify({
            'clothing_index': index,
            'page_items': page_items,
            'seasons': seasons
        })

    return jsonify({
        'clothing_index': index,
        'page_items': page_items
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)