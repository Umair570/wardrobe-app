// Seed data so the Wardrobe, Details, Visualization, Stylist and
// Recommended Outfits screens all have something real to point at,
// matching the sample items shown in the wireframes (T-Shirt, Jeans,
// Blazer, Sneakers, Dress, Hoodie...).

const BASE_ITEMS = [
  {
    name: 'T-Shirt',
    category: 'Top',
    color: 'Navy Blue',
    material: 'Cotton',
    season: 'All Season',
    occasion: 'Casual',
    confidence: 94.2,
    addedDate: 'Jul 28, 2026',
    viewCount: 128,
    wearCount: 34,
  },
  {
    name: 'Jeans',
    category: 'Bottom',
    color: 'Dark Blue',
    material: 'Denim',
    season: 'All Season',
    occasion: 'Casual',
    confidence: 92.8,
    addedDate: 'Jul 27, 2026',
    viewCount: 96,
    wearCount: 41,
  },
  {
    name: 'Blazer',
    category: 'Outerwear',
    color: 'Charcoal Grey',
    material: 'Wool Blend',
    season: 'Autumn / Winter',
    occasion: 'Formal / Business',
    confidence: 96.1,
    addedDate: 'Jul 28, 2026',
    viewCount: 152,
    wearCount: 12,
  },
  {
    name: 'Sneakers',
    category: 'Shoes',
    color: 'White',
    material: 'Canvas',
    season: 'All Season',
    occasion: 'Casual',
    confidence: 91.4,
    addedDate: 'Jul 26, 2026',
    viewCount: 203,
    wearCount: 58,
  },
  {
    name: 'Dress',
    category: 'Top',
    color: 'Olive Green',
    material: 'Linen',
    season: 'Spring / Summer',
    occasion: 'Casual',
    confidence: 93.5,
    addedDate: 'Jul 25, 2026',
    viewCount: 74,
    wearCount: 9,
  },
  {
    name: 'Hoodie',
    category: 'Outerwear',
    color: 'Grey',
    material: 'Fleece',
    season: 'Autumn / Winter',
    occasion: 'Casual',
    confidence: 90.7,
    addedDate: 'Jul 24, 2026',
    viewCount: 110,
    wearCount: 27,
  },
]

// Repeat with slight variation so pagination (3 pages / 6 per page, as in
// the wireframe) has enough rows to actually page through.
const FILLER_NAMES = [
  ['Shirt', 'Top', 'Light Blue', 'Cotton', 'All Season', 'Formal / Business'],
  ['Shorts', 'Bottom', 'Beige', 'Cotton', 'Spring / Summer', 'Casual'],
  ['Jacket', 'Outerwear', 'Black', 'Leather', 'Autumn / Winter', 'Casual'],
  ['Boots', 'Shoes', 'Brown', 'Leather', 'Autumn / Winter', 'Casual'],
  ['Sweater', 'Top', 'Cream', 'Wool', 'Autumn / Winter', 'Casual'],
  ['Skirt', 'Bottom', 'Black', 'Polyester', 'All Season', 'Formal / Business'],
  ['Loafers', 'Shoes', 'Tan', 'Leather', 'All Season', 'Formal / Business'],
  ['Cardigan', 'Top', 'Mustard', 'Cotton Blend', 'Autumn / Winter', 'Casual'],
]

function buildItems() {
  const items = BASE_ITEMS.map((item, i) => ({ ...item, id: `item_${i + 1}` }))
  FILLER_NAMES.forEach(([name, category, color, material, season, occasion], i) => {
    items.push({
      id: `item_${BASE_ITEMS.length + i + 1}`,
      name,
      category,
      color,
      material,
      season,
      occasion,
      confidence: 88 + Math.round(Math.random() * 9 * 10) / 10,
      addedDate: 'Jul 20, 2026',
      viewCount: 10 + Math.round(Math.random() * 60),
      wearCount: 1 + Math.round(Math.random() * 20),
    })
  })
  return items
}

export const SEED_ITEMS = buildItems()

export const CATEGORIES = ['All', 'Top', 'Bottom', 'Outerwear', 'Shoes']
export const SEASONS = ['All', 'All Season', 'Spring / Summer', 'Autumn / Winter']
export const SORT_OPTIONS = ['Newest first', 'Oldest first', 'Name A–Z', 'Name Z–A']

export const RECOMMENDED_OUTFITS = [
  {
    id: 'outfit_1',
    number: '01',
    title: 'Smart Casual',
    items: ['Blazer — Charcoal Grey', 'Jeans — Dark Blue', 'Sneakers — White'],
    tags: ['Casual', 'Business'],
    description: 'A versatile look for both office and weekend errands.',
  },
  {
    id: 'outfit_2',
    number: '02',
    title: 'Weekend Relax',
    items: ['Hoodie — Grey', 'Jeans — Dark Blue', 'Sneakers — White'],
    tags: ['Casual', 'Autumn'],
    description: 'A comfortable, relaxed outfit for casual outings.',
  },
  {
    id: 'outfit_3',
    number: '03',
    title: 'Minimalist Day',
    items: ['T-Shirt — Navy Blue', 'Jeans — Dark Blue', 'Sneakers — White'],
    tags: ['Casual', 'Everyday'],
    description: 'A clean, no-fuss outfit that works for most of the day.',
  },
  {
    id: 'outfit_4',
    number: '04',
    title: 'Evening Smart',
    items: ['Blazer — Charcoal Grey', 'T-Shirt — Navy Blue', 'Jeans — Dark Blue'],
    tags: ['Smart Casual', 'Evening'],
    description: 'Dresses down the blazer for a relaxed evening look.',
  },
]
