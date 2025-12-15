/* Kevin's Outfit Finder - Main Application JavaScript */

// State
let currentCollection = 'summer';
let currentClothingIndex = null;
let currentPageItems = null;
let currentCategory = 'all';

// Data will be injected by template
// const summerClothingIndex, summerPageItems, etc.

// =============================================================================
// Edit/Delete Functions
// =============================================================================

// Map UI collection names to backend keys
function mapCollectionToKey(collection) {
    const map = {
        'Summer': 'summer',
        'Spring': 'spring',
        'Fall': 'fw',
        'Winter': 'fw',
        'summer': 'summer',
        'spring': 'spring',
        'fall': 'fw',
        'winter': 'fw'
    };
    return map[collection] || collection.toLowerCase();
}

// Show toast notification
function showToast(message, type = 'success') {
    // Remove existing toast
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Edit item name
async function editItem(event, itemName, collection) {
    event.stopPropagation();

    const newName = prompt('Enter new name:', itemName);
    if (!newName || newName === itemName) return;

    const collectionKey = mapCollectionToKey(collection);

    try {
        const response = await fetch('/api/item/rename', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                collection: collectionKey,
                old_name: itemName,
                new_name: newName
            })
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message || `Renamed "${itemName}" to "${newName}"`);
            // Reload but stay on current collection and category
            window.location.hash = `${currentCollection}/${currentCategory}`;
            window.location.reload();
        } else {
            showToast(result.error || 'Failed to rename item', 'error');
        }
    } catch (err) {
        showToast('Failed to rename item: ' + err.message, 'error');
    }
}

// Change item category
async function changeCategory(event, itemName, collection, currentCategory) {
    event.stopPropagation();

    const categories = ['Bottoms', 'Tops', 'Footwear', 'Outerwear', 'Knitwear', 'Suits', 'Accessories'];

    // Create a simple selection prompt
    const categoryOptions = categories.map((cat, i) => `${i + 1}. ${cat}${cat === currentCategory ? ' (current)' : ''}`).join('\n');
    const choice = prompt(`Select new category for:\n"${itemName}"\n\n${categoryOptions}\n\nEnter number (1-${categories.length}):`);

    if (!choice) return;

    const index = parseInt(choice) - 1;
    if (isNaN(index) || index < 0 || index >= categories.length) {
        showToast('Invalid selection', 'error');
        return;
    }

    const newCategory = categories[index];
    if (newCategory === currentCategory) {
        showToast('Category unchanged', 'error');
        return;
    }

    const collectionKey = mapCollectionToKey(collection);

    try {
        const response = await fetch('/api/item/category', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                collection: collectionKey,
                item_name: itemName,
                new_category: newCategory
            })
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message || `Changed to ${newCategory}`);
            // Reload but stay on current collection and category
            window.location.hash = `${currentCollection}/${currentCategory}`;
            window.location.reload();
        } else {
            showToast(result.error || 'Failed to change category', 'error');
        }
    } catch (err) {
        showToast('Failed to change category: ' + err.message, 'error');
    }
}

// Change season for all pages of an item
async function changeSeason(event, itemName, collection) {
    event.stopPropagation();

    // Define season options based on collection
    let seasons, icons;
    const collectionLower = collection.toLowerCase();

    if (collectionLower === 'fall' || collectionLower === 'winter') {
        seasons = ['fall', 'winter', 'both'];
        icons = {'fall': '🍂', 'winter': '❄️', 'both': '🍂❄️'};
    } else if (collectionLower === 'summer') {
        seasons = ['summer', 'spring', 'both'];
        icons = {'summer': '☀️', 'spring': '🌸', 'both': '☀️🌸'};
    } else if (collectionLower === 'spring') {
        seasons = ['spring', 'summer', 'fall', 'all'];
        icons = {'spring': '🌸', 'summer': '☀️', 'fall': '🍂', 'all': '🌸☀️🍂'};
    } else {
        showToast('Unknown collection', 'error');
        return;
    }

    const options = seasons.map((s, i) => `${i + 1}. ${icons[s]} ${s.charAt(0).toUpperCase() + s.slice(1)}`).join('\n');
    const choice = prompt(`Change season for all pages of:\n"${itemName}"\n\n${options}\n\nEnter number (1-${seasons.length}):`);

    if (!choice) return;

    const index = parseInt(choice) - 1;
    if (isNaN(index) || index < 0 || index >= seasons.length) {
        showToast('Invalid selection', 'error');
        return;
    }

    const newSeason = seasons[index];
    const collectionKey = mapCollectionToKey(collection);

    try {
        const response = await fetch('/api/item/season', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                collection: collectionKey,
                item_name: itemName,
                new_season: newSeason
            })
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message || `Changed to ${newSeason}`);
            window.location.hash = `${currentCollection}/${currentCategory}`;
            window.location.reload();
        } else {
            showToast(result.error || 'Failed to change season', 'error');
        }
    } catch (err) {
        showToast('Failed to change season: ' + err.message, 'error');
    }
}

// Delete page
async function deletePage(event, pageName, collection) {
    event.stopPropagation();

    // Validate inputs
    if (!pageName || typeof pageName !== 'string') {
        showToast('Invalid page name', 'error');
        console.error('deletePage: invalid pageName', pageName);
        return;
    }
    if (!collection || typeof collection !== 'string') {
        showToast('Invalid collection', 'error');
        console.error('deletePage: invalid collection', collection);
        return;
    }

    if (!confirm(`Delete ${pageName.replace('page_', 'Page ')}? This cannot be undone.`)) return;

    const collectionKey = mapCollectionToKey(collection);
    const url = `/api/page/${encodeURIComponent(collectionKey)}/${encodeURIComponent(pageName)}`;

    try {
        const response = await fetch(url, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message || `Deleted ${pageName}`);
            // Refresh the page to reload data
            window.location.reload();
        } else {
            showToast(result.error || 'Failed to delete page', 'error');
        }
    } catch (err) {
        console.error('deletePage error:', err, 'URL:', url);
        showToast('Failed to delete page: ' + err.message, 'error');
    }
}

// Fuzzy Search Implementation
function levenshteinDistance(str1, str2) {
    const m = str1.length;
    const n = str2.length;
    const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (str1[i - 1] === str2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
            }
        }
    }
    return dp[m][n];
}

function fuzzyMatch(search, target) {
    const searchLower = search.toLowerCase();
    const targetLower = target.toLowerCase();

    // Exact substring match
    if (targetLower.includes(searchLower)) {
        return true;
    }

    // Word-by-word fuzzy matching
    const searchWords = searchLower.split(/\s+/);
    const targetWords = targetLower.split(/\s+/);

    return searchWords.every(searchWord => {
        return targetWords.some(targetWord => {
            // Check for partial match or small edit distance
            if (targetWord.includes(searchWord) || searchWord.includes(targetWord)) {
                return true;
            }
            // Allow 1-2 character mistakes for words > 3 chars
            if (searchWord.length > 3) {
                const maxDistance = searchWord.length > 5 ? 2 : 1;
                return levenshteinDistance(searchWord, targetWord) <= maxDistance;
            }
            return false;
        });
    });
}

// Image source helper
function getImageSrc(folder, page) {
    return folder + '/' + page + '.png';
}

// Modal functions
function openModal(imageSrc, caption) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const modalCaption = document.getElementById('modalCaption');

    modal.style.display = 'block';
    modalImg.src = imageSrc;
    modalCaption.innerHTML = caption;

    // Close on click outside
    modal.onclick = function(event) {
        if (event.target === modal || event.target === modalImg) {
            closeModal();
        }
    };

    // Close on Escape key
    document.onkeydown = function(event) {
        if (event.key === 'Escape') {
            closeModal();
        }
    };
}

function closeModal() {
    document.getElementById('imageModal').style.display = 'none';
}

// Navigation
function showCollection(collection) {
    currentCollection = collection;

    // Hide all views
    document.getElementById('summer-view').classList.add('hidden');
    document.getElementById('spring-view').classList.add('hidden');
    document.getElementById('fall-view').classList.add('hidden');
    document.getElementById('winter-view').classList.add('hidden');
    document.getElementById('item-view').classList.add('hidden');
    document.getElementById('page-view').classList.add('hidden');

    // Show selected collection
    document.getElementById(collection + '-view').classList.remove('hidden');

    // Update navigation
    document.querySelectorAll('.nav button').forEach(btn => btn.classList.remove('active'));
    document.getElementById('nav-' + collection).classList.add('active');

    // Update current data
    if (collection === 'summer') {
        currentClothingIndex = summerClothingIndex;
        currentPageItems = summerPageItems;
    } else if (collection === 'spring') {
        currentClothingIndex = springClothingIndex;
        currentPageItems = springPageItems;
    } else if (collection === 'fall') {
        currentClothingIndex = fallClothingIndex;
        currentPageItems = fallPageItems;
    } else if (collection === 'winter') {
        currentClothingIndex = winterClothingIndex;
        currentPageItems = winterPageItems;
    }

    // Update browser title
    document.title = "Kevin's Outfit Finder";
}

function backToCollection() {
    showCollection(currentCollection);
}

// Category filter functionality
function filterByCategory(category) {
    currentCategory = category;

    // Update active tab
    document.querySelectorAll('.category-tabs button').forEach(btn => btn.classList.remove('active'));
    document.getElementById('cat-' + category).classList.add('active');

    // Filter all collection views
    ['summer', 'spring', 'fall', 'winter'].forEach(collection => {
        const container = document.getElementById(collection + '-items-grid');
        if (!container) return;

        const sections = container.querySelectorAll('.category-section');
        sections.forEach(section => {
            const header = section.querySelector('.category-header h2');
            if (!header) return;

            const sectionCategory = header.textContent.split(' ').slice(1).join(' ');

            if (category === 'all') {
                section.classList.remove('hidden');
            } else if (sectionCategory === category) {
                section.classList.remove('hidden');
            } else {
                section.classList.add('hidden');
            }
        });
    });
}

// Search functionality with fuzzy matching
function filterItems(collection) {
    const search = document.getElementById(collection + 'SearchInput').value.trim();
    const container = document.getElementById(collection + '-items-grid');
    const items = container.querySelectorAll('.item-card');
    const noResults = document.getElementById(collection + '-no-results');

    let visibleCount = 0;

    items.forEach(item => {
        const itemName = item.querySelector('.item-name').textContent;

        if (search === '' || fuzzyMatch(search, itemName)) {
            item.classList.remove('hidden');
            visibleCount++;
        } else {
            item.classList.add('hidden');
        }
    });

    // Show/hide category sections based on visible items
    const sections = container.querySelectorAll('.category-section');
    sections.forEach(section => {
        const visibleItems = section.querySelectorAll('.item-card:not(.hidden)');
        section.style.display = visibleItems.length > 0 ? 'block' : 'none';
    });

    // Show no results message if needed
    if (visibleCount === 0 && search !== '') {
        noResults.classList.remove('hidden');
    } else {
        noResults.classList.add('hidden');
    }
}

// Show item detail
function showItemDetail(itemName, collection, imageFolder) {
    // Determine which index to use based on collection name
    let clothingIndex, pageItems;
    if (collection === 'Summer') {
        clothingIndex = summerClothingIndex;
        pageItems = summerPageItems;
    } else if (collection === 'Spring') {
        clothingIndex = springClothingIndex;
        pageItems = springPageItems;
    } else if (collection === 'Fall') {
        clothingIndex = fallClothingIndex;
        pageItems = fallPageItems;
    } else if (collection === 'Winter') {
        clothingIndex = winterClothingIndex;
        pageItems = winterPageItems;
    }

    // Try to find the item with or without category suffix
    let pages = null;
    for (let key in clothingIndex) {
        if (key.startsWith(itemName)) {
            pages = clothingIndex[key];
            break;
        }
    }

    if (!pages) {
        console.log('No pages found for:', itemName);
        return;
    }

    // Hide other views
    document.getElementById('summer-view').classList.add('hidden');
    document.getElementById('spring-view').classList.add('hidden');
    document.getElementById('fall-view').classList.add('hidden');
    document.getElementById('winter-view').classList.add('hidden');
    document.getElementById('page-view').classList.add('hidden');
    document.getElementById('item-view').classList.remove('hidden');

    document.title = itemName + ' - ' + collection + ' Collection';

    const content = document.getElementById('item-detail-content');

    content.innerHTML = `
        <div class="page-images">
            ${pages.map(page => {
                return `
                <div class="page-card">
                    <img src="${imageFolder}/${page}.png"
                         alt="${page}"
                         class="clickable-image"
                         loading="lazy"
                         onclick="openModal('${imageFolder}/${page}.png', '${page.replace('page_', 'Page ')} - ${itemName}')"
                         onerror="this.parentElement.style.display='none';">
                    <div class="page-title" onclick="showPageDetail('${page}', '${collection}', '${imageFolder}')" style="cursor: pointer;">
                        ${page.replace('page_', 'Page ')}
                    </div>
                    <button class="delete-btn" onclick="deletePage(event, '${page}', '${collection}')" title="Delete page">
                        &#128465;
                    </button>
                </div>
            `}).join('')}
        </div>
    `;
}

// Show page detail
function showPageDetail(pageName, collection, imageFolder) {
    let pageItems;
    if (collection === 'Summer') {
        pageItems = summerPageItems;
    } else if (collection === 'Spring') {
        pageItems = springPageItems;
    } else if (collection === 'Fall') {
        pageItems = fallPageItems;
    } else if (collection === 'Winter') {
        pageItems = winterPageItems;
    }

    if (!pageItems[pageName]) return;

    const items = pageItems[pageName];

    // Hide other views
    document.getElementById('summer-view').classList.add('hidden');
    document.getElementById('spring-view').classList.add('hidden');
    document.getElementById('fall-view').classList.add('hidden');
    document.getElementById('winter-view').classList.add('hidden');
    document.getElementById('item-view').classList.add('hidden');
    document.getElementById('page-view').classList.remove('hidden');

    document.title = pageName.replace('page_', 'Page ') + ' - ' + collection + ' Collection';

    const content = document.getElementById('page-detail-content');

    // Handle different data formats (objects with name/category)
    let itemsList = '';
    if (Array.isArray(items)) {
        if (items.length > 0 && typeof items[0] === 'object') {
            // Categorized format (array of objects with name and category)
            itemsList = items.map(item => `
                <a onclick="showItemDetail('${item.name.replace(/'/g, "\\'")}', '${collection}', '${imageFolder}')" class="item-link">
                    ${item.name} <span style="color: #7f8c8d; font-size: 0.9em;">[${item.category}]</span>
                </a>
            `).join('');
        } else {
            // Legacy simple array format
            itemsList = items.map(item => `
                <a onclick="showItemDetail('${item.replace(/'/g, "\\'")}', '${collection}', '${imageFolder}')" class="item-link">
                    ${item}
                </a>
            `).join('');
        }
    }

    content.innerHTML = `
        <div class="page-detail">
            <div class="page-image">
                <img src="${imageFolder}/${pageName}.png" alt="${pageName}"
                     class="clickable-image"
                     loading="lazy"
                     style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);"
                     onclick="openModal('${imageFolder}/${pageName}.png', '${pageName.replace('page_', 'Page ')} - ${collection} Collection')">
            </div>
            <div class="page-items">
                <h3>Clothing items on this page:</h3>
                <div class="item-list">
                    ${itemsList}
                </div>
            </div>
        </div>
    `;
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Check for saved state in URL hash (e.g., #fall/Suits)
    const hash = window.location.hash.slice(1);
    if (hash) {
        const [collection, category] = hash.split('/');
        if (collection) {
            showCollection(collection);
        }
        if (category && category !== 'all') {
            setTimeout(() => filterByCategory(category), 100);
        }
    } else {
        showCollection('summer');
    }
});
