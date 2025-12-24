# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kevin's Outfit Finder is a mobile-first web application for browsing and discovering clothing combinations from curated seasonal wardrobe collections (Summer, Spring, and Fall/Winter). The project uses OCR to extract clothing items from outfit images and provides a visual discovery interface with image modal/lightbox functionality.

## Architecture

### Dual Development Approach
- **Development Mode**: Flask web application (`app.py`) for local development and testing
- **Production Mode**: Static site generation (`generate_static_site_all_collections.py`) for Netlify deployment

### Data Architecture
The application maintains separate datasets for each collection with bidirectional mapping:

**Summer Collection:**
- `clothing_index.json`: Maps clothing items → pages where they appear
- `page_items.json`: Maps outfit pages → clothing items they contain
- Images in `Kevin_Summer_Looks_Pages/` (90 pages)

**Spring Collection:**
- `clothing_index_spring.json`: Categorized items with format "Item Name (Category)"
- `page_items_spring.json`: Includes category metadata for each item
- `category_stats_spring.json`: Category statistics
- Images in `KEVIN_Spring_Looks_Images/` (109 pages)

**Fall/Winter Collection:**
- `clothing_index_fw.json`: Categorized items for cold weather
- `page_items_fw.json`: Includes seasonal category metadata
- `category_stats_fw.json`: Category statistics
- Images in `Fall_Winter_Looks_Images/` (80 pages)

## Essential Commands

### Local Development
```bash
# Start Flask development server (all collections)
python3 app.py
# Visit http://localhost:5001

# Start outfit manager for data editing (delete, rename, recategorize)
python3 outfit_manager.py
# Visit http://localhost:5002

# Test static site locally
cd dist && python3 -m http.server 8080
# Visit http://localhost:8080
```

### OCR Processing
```bash
# Extract Summer collection items
export PATH="/opt/homebrew/bin:$PATH"  # Ensure Tesseract is available
python3 extract_clothing_items.py

# Extract Spring collection with improved separation and categorization
python3 extract_spring_clothing_improved.py

# Extract Fall/Winter collection with seasonal categories
python3 extract_fall_winter_clothing.py
```

### Data Management
```bash
# Use outfit manager for interactive data editing
python3 outfit_manager.py

# Rebuild clothing index after manual edits to page_items.json
python3 rebuild_index.py

# Analyze data for cleaning opportunities
python3 analyze_data.py
```

### Static Site Generation
```bash
# Generate static site with ALL three collections (REQUIRED for production)
python3 generate_static_site_all_collections.py

# Legacy generators (do not use for production)
python3 generate_static_site_with_collections.py  # Summer + Spring only
python3 generate_static_site.py                    # Summer only
```

### Deployment
```bash
# Netlify will automatically build using the command in netlify.toml
# Manual deployment if needed:
netlify deploy --prod --dir=dist
```

## Key Technical Details

### OCR Configuration
- Tesseract path: `/opt/homebrew/bin/tesseract` (macOS Homebrew)
- Each collection extractor includes:
  - Automatic item separation for combined entries
  - Category detection appropriate to season
  - Brand recognition for 30+ luxury brands
  - Artifact cleaning (removes OCR noise)

### Static Site Features
- **Three Collection Support**: Tab navigation (Summer, Spring, Fall/Winter)
- **Image Modal**: Click any outfit image for full-screen lightbox view
- **Categorized Display**: Items grouped by type with seasonal categories
- **Search**: Real-time filtering within each collection
- **Mobile Optimized**: Touch-friendly with responsive grid layouts
- **Favicon**: Wardrobe-themed icon for browser tabs

### Collection Categories
**Summer/Spring Categories:**
- Outerwear, Tops, Bottoms, Footwear, Accessories, Other

**Fall/Winter Categories:**
- Outerwear, Knitwear, Tops, Bottoms, Footwear, Accessories, Suits, Layering, Other

### Build Configuration
- **netlify.toml**: Specifies build command `python3 generate_static_site_all_collections.py`
- **package.json**: Build script points to all collections generator
- Output directory: `dist/`

## Data Structure Notes

### Image Naming Convention
- Summer: `Kevin_Summer_Looks_Pages/page_1.png` through `page_90.png`
- Spring: `KEVIN_Spring_Looks_Images/page_1.png` through `page_109.png`
- Fall/Winter: `Fall_Winter_Looks_Images/page_1.png` through `page_80.png`
- Static site copies to: `dist/images/`, `dist/spring_images/`, `dist/fw_images/`

### JSON Data Formats
**Summer format (simple):**
```json
{
  "page_1": ["Saint Laurent ivory trouser", "The Row brown tassel loafer"]
}
```

**Spring/Fall-Winter format (categorized):**
```json
{
  "page_1": [
    {"name": "Saint Laurent blush sweater", "category": "Tops"},
    {"name": "The Row brown tassel loafer", "category": "Footwear"}
  ]
}
```

## Common Data Cleaning Tasks

### OCR Artifacts
- Problem: Items like "i The Row brown tassel loafer" or "of The Row"
- Solution: Use `outfit_manager.py` to rename items, or edit JSON directly

### Combined Items
- Problem: "Caruso camel blazer Drake's ivory corduroy" as single item
- Solution: Use improved extractors that automatically separate

### Duplicate/Variant Items
- Problem: Case variations, typos, or mislabeled items
- Solution: Use `outfit_manager.py` to merge/rename items

### Workflow for Data Updates
1. Extract with OCR: `python3 extract_[collection]_clothing.py`
2. Manual review/edit: Use `python3 outfit_manager.py` or edit JSON directly
3. Rebuild index: `python3 rebuild_index.py`
4. Generate site: `python3 generate_static_site_all_collections.py`
5. Commit and push (Netlify auto-deploys)