# Kevin's Outfit Finder

A mobile-first web application to browse and discover clothing combinations from curated seasonal wardrobe collections.

## Features

- **Three Collections**: Summer, Spring, and Fall/Winter wardrobes
- **Visual Discovery**: Click any item to see all outfits featuring it
- **Categorized Display**: Items grouped by type (Outerwear, Tops, Bottoms, etc.)
- **Search**: Real-time filtering within each collection
- **Mobile Optimized**: Touch-friendly, responsive design
- **Image Lightbox**: Full-screen outfit viewing

## Live Demo

Visit: [kevins-outfit-finder.netlify.app](https://kevins-outfit-finder.netlify.app)

## Quick Start

### Local Development
```bash
# Start Flask development server
python3 app.py
# Visit http://localhost:5001

# Start outfit manager for data editing
python3 outfit_manager.py
# Visit http://localhost:5002
```

### Static Site Generation
```bash
python3 generate_static_site_all_collections.py
# Files created in 'dist' directory
```

## Data Overview

| Collection | Items | Pages |
|------------|-------|-------|
| Summer | ~76 | 90 |
| Spring | ~100+ | 109 |
| Fall/Winter | ~80+ | 80 |

Featuring luxury brands: Saint Laurent, The Row, Loro Piana, Brunello Cucinelli, Boglioli, Lardini, and more.

## Technology Stack

- **Backend**: Python Flask (development)
- **Frontend**: Vanilla JavaScript, CSS Grid/Flexbox
- **Data Processing**: OCR with Tesseract, manual curation
- **Deployment**: Static site on Netlify
- **Validation**: Pydantic models

## Project Structure

```
├── app.py                              # Flask dev server
├── outfit_manager.py                   # Data editing UI
├── generate_static_site_all_collections.py  # Static site builder
├── config.py                           # Centralized configuration
├── data_loader.py                      # Shared data utilities
├── clothing_index*.json                # Item → pages mappings
├── page_items*.json                    # Page → items mappings
├── templates/                          # HTML/CSS/JS templates
└── dist/                               # Generated static site
```

## Deployment

Netlify auto-deploys on push. Manual deployment:
```bash
netlify deploy --prod --dir=dist
```

---

Built for style discovery and mobile browsing.
