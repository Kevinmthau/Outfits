#!/usr/bin/env python3
"""
Outfit Manager - Web UI for managing outfit data.

Features:
- Delete pages from collections
- Rename clothing items
- Re-categorize pages by season (fall/winter/both)
- Change item categories

Usage:
    python outfit_manager.py
    Visit http://localhost:5002
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, send_from_directory

from config import DATA_FILES, BASE_DIR, PAGE_SEASONS_FILE, CATEGORY_ORDER, COLLECTION_PATHS

app = Flask(__name__)

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
        page_num = page.replace("page_", "") if page.startswith("page_") else page
        for item_data in items:
            if isinstance(item_data, dict):
                name = item_data.get("name", "")
            else:
                name = item_data

            if name:
                if name not in index:
                    index[name] = []
                # Store as integer for fw, string for others
                index[name].append(page)

    # Sort pages for each item
    for name in index:
        index[name] = sorted(set(index[name]), key=lambda x: int(x.replace("page_", "")) if "page_" in str(x) else int(x))

    return index


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Outfit Manager</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0; padding: 20px;
            background: #f5f5f5;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab {
            padding: 10px 20px; background: #ddd; border: none;
            cursor: pointer; border-radius: 5px; font-size: 1rem;
        }
        .tab.active { background: #3498db; color: white; }
        .panel { display: none; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .panel.active { display: block; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: 600; }
        input, select, textarea {
            width: 100%; padding: 10px; border: 1px solid #ddd;
            border-radius: 5px; font-size: 1rem;
        }
        button {
            padding: 10px 20px; background: #3498db; color: white;
            border: none; border-radius: 5px; cursor: pointer; font-size: 1rem;
        }
        button:hover { background: #2980b9; }
        button.danger { background: #e74c3c; }
        button.danger:hover { background: #c0392b; }
        .success { color: #27ae60; padding: 10px; background: #d4edda; border-radius: 5px; margin-bottom: 15px; }
        .error { color: #c0392b; padding: 10px; background: #f8d7da; border-radius: 5px; margin-bottom: 15px; }
        .item-list { max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; }
        .item { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; }
        .item:hover { background: #f0f0f0; }
        .item.selected { background: #e3f2fd; }
        .page-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 10px; margin-top: 10px; }
        .page-grid.with-images { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
        .page-item {
            padding: 10px; background: #f0f0f0; border-radius: 5px;
            text-align: center; cursor: pointer; border: 2px solid transparent;
        }
        .page-item:hover { background: #e0e0e0; }
        .page-item.selected { border-color: #e74c3c; background: #fdecea; }
        .page-item img { width: 100%; height: auto; border-radius: 4px; margin-bottom: 5px; }
        .page-item .page-label { font-size: 0.85rem; color: #333; }
        .page-item.fall { border-left: 4px solid #e67e22; }
        .page-item.winter { border-left: 4px solid #3498db; }
        .page-item.both { border-left: 4px solid #9b59b6; }
        .season-legend { display: flex; gap: 20px; margin-bottom: 15px; }
        .legend-item { display: flex; align-items: center; gap: 5px; }
        .legend-color { width: 20px; height: 20px; border-radius: 3px; }
        .search-box { margin-bottom: 15px; }
        .checkbox-group { display: flex; gap: 20px; margin-top: 10px; }
        .checkbox-group label { display: flex; align-items: center; gap: 5px; font-weight: normal; }
        .actions { display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Outfit Manager</h1>

        {% if message %}
        <div class="{{ 'success' if success else 'error' }}">{{ message }}</div>
        {% endif %}

        <div class="tabs">
            <button class="tab active" onclick="showPanel('rename')">Rename Items</button>
            <button class="tab" onclick="showPanel('delete')">Delete Pages</button>
            <button class="tab" onclick="showPanel('seasons')">Manage Seasons</button>
            <button class="tab" onclick="showPanel('category')">Change Category</button>
        </div>

        <!-- Rename Items Panel -->
        <div id="rename" class="panel active">
            <h2>Rename Clothing Items</h2>
            <form method="POST" action="/rename">
                <div class="form-group">
                    <label>Collection</label>
                    <select name="collection" id="rename-collection" onchange="loadItems('rename')">
                        <option value="summer">Summer</option>
                        <option value="spring">Spring</option>
                        <option value="fw">Fall/Winter</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Search Items</label>
                    <input type="text" id="rename-search" placeholder="Type to filter..." onkeyup="filterItems('rename')">
                </div>
                <div class="form-group">
                    <label>Select Item</label>
                    <div class="item-list" id="rename-items"></div>
                    <input type="hidden" name="old_name" id="rename-old-name">
                </div>
                <div class="form-group">
                    <label>New Name</label>
                    <input type="text" name="new_name" id="rename-new-name" required>
                </div>
                <button type="submit">Rename Item</button>
            </form>
        </div>

        <!-- Delete Pages Panel -->
        <div id="delete" class="panel">
            <h2>Delete Pages</h2>
            <form method="POST" action="/delete-page">
                <div class="form-group">
                    <label>Collection</label>
                    <select name="collection" id="delete-collection" onchange="loadPagesWithImages()">
                        <option value="summer">Summer</option>
                        <option value="spring">Spring</option>
                        <option value="fw">Fall/Winter</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Select Pages to Delete (click to toggle) - <span id="delete-count">0</span> selected</label>
                    <div class="page-grid with-images" id="delete-pages"></div>
                    <input type="hidden" name="pages" id="delete-selected-pages">
                </div>
                <button type="submit" class="danger">Delete Selected Pages</button>
            </form>
        </div>

        <!-- Manage Seasons Panel -->
        <div id="seasons" class="panel">
            <h2>Manage Page Seasons (Fall/Winter)</h2>
            <div class="season-legend">
                <div class="legend-item"><div class="legend-color" style="background: #e67e22;"></div> Fall</div>
                <div class="legend-item"><div class="legend-color" style="background: #3498db;"></div> Winter</div>
                <div class="legend-item"><div class="legend-color" style="background: #9b59b6;"></div> Both</div>
                <div class="legend-item"><div class="legend-color" style="background: #95a5a6;"></div> Unassigned</div>
            </div>
            <form method="POST" action="/update-seasons">
                <div class="form-group">
                    <label>Select Pages (click to toggle selection) - <span id="season-count">0</span> selected</label>
                    <div class="page-grid with-images" id="season-pages"></div>
                    <input type="hidden" name="pages" id="season-selected-pages">
                </div>
                <div class="form-group">
                    <label>Set Season For Selected Pages</label>
                    <div class="checkbox-group">
                        <label><input type="checkbox" name="fall" value="1"> Fall</label>
                        <label><input type="checkbox" name="winter" value="1"> Winter</label>
                    </div>
                </div>
                <div class="actions">
                    <button type="submit">Update Seasons</button>
                    <button type="button" onclick="selectAllPages()">Select All</button>
                    <button type="button" onclick="clearSelection()">Clear Selection</button>
                </div>
            </form>
        </div>

        <!-- Change Category Panel -->
        <div id="category" class="panel">
            <h2>Change Item Category</h2>
            <form method="POST" action="/change-category">
                <div class="form-group">
                    <label>Collection</label>
                    <select name="collection" id="category-collection" onchange="loadItems('category')">
                        <option value="summer">Summer</option>
                        <option value="spring">Spring</option>
                        <option value="fw">Fall/Winter</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Search Items</label>
                    <input type="text" id="category-search" placeholder="Type to filter..." onkeyup="filterItems('category')">
                </div>
                <div class="form-group">
                    <label>Select Item</label>
                    <div class="item-list" id="category-items"></div>
                    <input type="hidden" name="item_name" id="category-item-name">
                </div>
                <div class="form-group">
                    <label>New Category</label>
                    <select name="new_category" id="category-select">
                        <option value="Bottoms">Bottoms</option>
                        <option value="Tops">Tops</option>
                        <option value="Footwear">Footwear</option>
                        <option value="Outerwear">Outerwear</option>
                        <option value="Knitwear">Knitwear</option>
                        <option value="Accessories">Accessories</option>
                        <option value="Suits">Suits</option>
                        <option value="Layering">Layering</option>
                        <option value="Other">Other</option>
                    </select>
                </div>
                <button type="submit">Change Category</button>
            </form>
        </div>
    </div>

    <script>
        let itemsData = {};
        let pagesData = {};
        let seasonsData = {};
        let selectedPages = new Set();

        function showPanel(id) {
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.target.classList.add('active');

            if (id === 'rename' || id === 'category') loadItems(id);
            if (id === 'delete') loadPagesWithImages();
            if (id === 'seasons') loadSeasonPages();
        }

        async function loadItems(panel) {
            const collection = document.getElementById(panel + '-collection').value;
            const response = await fetch('/api/items/' + collection);
            itemsData[panel] = await response.json();
            renderItems(panel);
        }

        function renderItems(panel) {
            const container = document.getElementById(panel + '-items');
            const search = document.getElementById(panel + '-search').value.toLowerCase();
            const items = itemsData[panel] || [];

            const filtered = items.filter(item => item.name.toLowerCase().includes(search));
            container.innerHTML = filtered.map(item =>
                `<div class="item" onclick="selectItem('${panel}', '${item.name.replace(/'/g, "\\'")}', '${item.category}')">${item.name} <small style="color:#888">[${item.category}]</small></div>`
            ).join('');
        }

        function filterItems(panel) {
            renderItems(panel);
        }

        function selectItem(panel, name, category) {
            document.querySelectorAll('#' + panel + '-items .item').forEach(el => el.classList.remove('selected'));
            event.target.classList.add('selected');

            if (panel === 'rename') {
                document.getElementById('rename-old-name').value = name;
                document.getElementById('rename-new-name').value = name;
            } else if (panel === 'category') {
                document.getElementById('category-item-name').value = name;
                document.getElementById('category-select').value = category;
            }
        }

        async function loadPages(panel) {
            const collection = document.getElementById(panel + '-collection').value;
            const response = await fetch('/api/pages/' + collection);
            pagesData[panel] = await response.json();
            renderPages(panel);
        }

        function renderPages(panel) {
            const container = document.getElementById(panel + '-pages');
            const pages = pagesData[panel] || [];
            selectedPages = new Set();

            container.innerHTML = pages.map(page =>
                `<div class="page-item" onclick="togglePage('${panel}', '${page}')" id="${panel}-${page}">${page.replace('page_', 'P')}</div>`
            ).join('');
            updateSelectedPages(panel);
        }

        async function loadPagesWithImages() {
            const collection = document.getElementById('delete-collection').value;
            const response = await fetch('/api/pages/' + collection);
            pagesData['delete'] = await response.json();
            renderPagesWithImages();
        }

        function renderPagesWithImages() {
            const container = document.getElementById('delete-pages');
            const pages = pagesData['delete'] || [];
            const collection = document.getElementById('delete-collection').value;
            selectedPages = new Set();

            container.innerHTML = pages.map(page => {
                const pageNum = page.replace('page_', '');
                const imgSrc = `/images/${collection}/page_${pageNum}.png`;
                return `<div class="page-item" onclick="togglePage('delete', '${page}')" id="delete-${page}">
                    <img src="${imgSrc}" alt="Page ${pageNum}" loading="lazy" onerror="this.style.display='none'">
                    <div class="page-label">Page ${pageNum}</div>
                </div>`;
            }).join('');
            updateSelectedPages('delete');
            updateDeleteCount();
        }

        function updateDeleteCount() {
            document.getElementById('delete-count').textContent = selectedPages.size;
        }

        function togglePage(panel, page) {
            if (selectedPages.has(page)) {
                selectedPages.delete(page);
            } else {
                selectedPages.add(page);
            }
            document.getElementById(panel + '-' + page).classList.toggle('selected');
            updateSelectedPages(panel);
            if (panel === 'delete') updateDeleteCount();
            if (panel === 'seasons') updateSeasonCount();
        }

        function updateSelectedPages(panel) {
            const input = document.getElementById(panel === 'seasons' ? 'season-selected-pages' : 'delete-selected-pages');
            input.value = Array.from(selectedPages).join(',');
        }

        async function loadSeasonPages() {
            const response = await fetch('/api/seasons');
            const data = await response.json();
            seasonsData = data.seasons;
            const pages = data.pages;
            selectedPages = new Set();

            const container = document.getElementById('season-pages');
            container.innerHTML = pages.map(page => {
                const season = seasonsData[page];
                let cls = '';
                if (season === 'fall') cls = 'fall';
                else if (season === 'winter') cls = 'winter';
                else if (season === 'both') cls = 'both';
                const pageNum = page.replace('page_', '');
                const imgSrc = `/images/fw/page_${pageNum}.png`;
                return `<div class="page-item ${cls}" onclick="togglePage('seasons', '${page}')" id="seasons-${page}">
                    <img src="${imgSrc}" alt="Page ${pageNum}" loading="lazy" onerror="this.style.display='none'">
                    <div class="page-label">Page ${pageNum}</div>
                </div>`;
            }).join('');
            updateSeasonCount();
        }

        function updateSeasonCount() {
            document.getElementById('season-count').textContent = selectedPages.size;
        }

        function selectAllPages() {
            document.querySelectorAll('#season-pages .page-item').forEach(el => {
                const page = el.id.replace('seasons-', '');
                selectedPages.add(page);
                el.classList.add('selected');
            });
            updateSelectedPages('seasons');
            updateSeasonCount();
        }

        function clearSelection() {
            selectedPages = new Set();
            document.querySelectorAll('#season-pages .page-item').forEach(el => el.classList.remove('selected'));
            updateSelectedPages('seasons');
            updateSeasonCount();
        }

        // Initialize
        loadItems('rename');
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    message = request.args.get('message')
    success = request.args.get('success', 'true') == 'true'
    return render_template_string(HTML_TEMPLATE, message=message, success=success)


@app.route('/api/items/<collection>')
def api_items(collection):
    """Get all items for a collection."""
    index, page_items = load_collection_data(collection)

    # Build item list with categories
    items = []
    seen = set()
    for page, page_item_list in page_items.items():
        for item_data in page_item_list:
            if isinstance(item_data, dict):
                name = item_data.get('name', '')
                category = item_data.get('category', 'Other')
            else:
                name = item_data
                category = 'Other'

            if name and name not in seen:
                seen.add(name)
                items.append({'name': name, 'category': category})

    items.sort(key=lambda x: x['name'].lower())
    return jsonify(items)


@app.route('/api/pages/<collection>')
def api_pages(collection):
    """Get all pages for a collection."""
    _, page_items = load_collection_data(collection)
    pages = sorted(page_items.keys(), key=lambda x: int(x.replace('page_', '')) if 'page_' in x else int(x))
    return jsonify(pages)


@app.route('/api/seasons')
def api_seasons():
    """Get page seasons data."""
    seasons = load_json(PAGE_SEASONS_FILE)
    _, page_items = load_collection_data('fw')
    pages = sorted(page_items.keys(), key=lambda x: int(x.replace('page_', '')) if 'page_' in x else int(x))
    return jsonify({'seasons': seasons, 'pages': pages})


@app.route('/images/<collection>/<filename>')
def serve_image(collection, filename):
    """Serve images from collection folders."""
    if collection not in COLLECTION_PATHS:
        return "Collection not found", 404
    image_dir = COLLECTION_PATHS[collection]
    return send_from_directory(image_dir, filename)


@app.route('/rename', methods=['POST'])
def rename_item():
    """Rename a clothing item."""
    collection = request.form['collection']
    old_name = request.form['old_name']
    new_name = request.form['new_name'].strip()

    if not old_name or not new_name:
        return redirect(url_for('index', message='Please select an item and enter a new name', success='false'))

    if old_name == new_name:
        return redirect(url_for('index', message='New name is the same as old name', success='false'))

    index, page_items = load_collection_data(collection)

    # Update page_items
    for page, items in page_items.items():
        for i, item_data in enumerate(items):
            if isinstance(item_data, dict) and item_data.get('name') == old_name:
                items[i]['name'] = new_name
            elif isinstance(item_data, str) and item_data == old_name:
                items[i] = new_name

    # Rebuild index
    index = rebuild_index(page_items)

    save_collection_data(collection, index, page_items)

    return redirect(url_for('index', message=f'Renamed "{old_name}" to "{new_name}"', success='true'))


@app.route('/delete-page', methods=['POST'])
def delete_page():
    """Delete pages from a collection."""
    collection = request.form['collection']
    pages_str = request.form.get('pages', '')

    if not pages_str:
        return redirect(url_for('index', message='Please select pages to delete', success='false'))

    pages_to_delete = set(pages_str.split(','))

    index, page_items = load_collection_data(collection)

    # Remove pages
    for page in pages_to_delete:
        if page in page_items:
            del page_items[page]

    # Rebuild index
    index = rebuild_index(page_items)

    save_collection_data(collection, index, page_items)

    # Also remove from seasons if fw collection
    if collection == 'fw':
        seasons = load_json(PAGE_SEASONS_FILE)
        for page in pages_to_delete:
            if page in seasons:
                del seasons[page]
        save_json(PAGE_SEASONS_FILE, seasons)

    return redirect(url_for('index', message=f'Deleted {len(pages_to_delete)} pages', success='true'))


@app.route('/update-seasons', methods=['POST'])
def update_seasons():
    """Update page seasons."""
    pages_str = request.form.get('pages', '')
    fall = request.form.get('fall') == '1'
    winter = request.form.get('winter') == '1'

    if not pages_str:
        return redirect(url_for('index', message='Please select pages to update', success='false'))

    if not fall and not winter:
        return redirect(url_for('index', message='Please select at least one season', success='false'))

    pages_to_update = pages_str.split(',')
    seasons = load_json(PAGE_SEASONS_FILE)

    # Determine season value
    if fall and winter:
        season = 'both'
    elif fall:
        season = 'fall'
    else:
        season = 'winter'

    # Update seasons
    for page in pages_to_update:
        seasons[page] = season

    save_json(PAGE_SEASONS_FILE, seasons)

    return redirect(url_for('index', message=f'Updated {len(pages_to_update)} pages to {season}', success='true'))


@app.route('/change-category', methods=['POST'])
def change_category():
    """Change item category."""
    collection = request.form['collection']
    item_name = request.form['item_name']
    new_category = request.form['new_category']

    if not item_name:
        return redirect(url_for('index', message='Please select an item', success='false'))

    index, page_items = load_collection_data(collection)

    # Update category in page_items
    updated = 0
    for page, items in page_items.items():
        for i, item_data in enumerate(items):
            if isinstance(item_data, dict) and item_data.get('name') == item_name:
                items[i]['category'] = new_category
                updated += 1
            elif isinstance(item_data, str) and item_data == item_name:
                items[i] = {'name': item_name, 'category': new_category}
                updated += 1

    save_collection_data(collection, index, page_items)

    return redirect(url_for('index', message=f'Changed category of "{item_name}" to {new_category} ({updated} occurrences)', success='true'))


if __name__ == '__main__':
    print("Starting Outfit Manager...")
    print("Visit http://localhost:5002")
    app.run(port=5002, debug=True)
