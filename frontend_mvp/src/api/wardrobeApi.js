// wardrobeApi.js
//
// Mock implementation of the contract agreed with Mahad (Backend):
//   POST /api/upload   -> { id, image_url, segmented_url, category, color, ... }
//   GET  /api/wardrobe -> Item[]
//
// Set VITE_API_BASE_URL to point this at the real FastAPI backend once it's
// live -- component code never changes, it only imports the named exports
// below (uploadItem / fetchWardrobe / removeItem).

import { SEED_ITEMS } from '../data/mockData'
import { getDisplayCategory } from '../utils/outfitSlots'

const USE_MOCK = !import.meta.env.VITE_API_BASE_URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const STORAGE_KEY = 'wardrobe:items'

const CATEGORY_POOL = [
  ['T-Shirt', 'Top'],
  ['Jeans', 'Bottom'],
  ['Jacket', 'Outerwear'],
  ['Sneakers', 'Shoes'],
  ['Dress', 'Top'],
  ['Hoodie', 'Outerwear'],
]
const COLOR_POOL = ['Navy Blue', 'Black', 'White', 'Olive Green', 'Charcoal Grey', 'Dark Blue', 'Cream']
const SEASON_POOL = ['All Season', 'Spring / Summer', 'Autumn / Winter']
const OCCASION_POOL = ['Casual', 'Formal / Business']

export const PROCESSING_STEPS = [
  'Upload Complete',
  'Removing Background',
  'Detecting Clothing',
  'Classifying Item',
  'Saving to Wardrobe',
]

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function readStore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : [...SEED_ITEMS]
  } catch {
    return [...SEED_ITEMS]
  }
}

function writeStore(items) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {
    // storage full/unavailable -- in-memory state for this session still works
  }
}

let idCounter = readStore().length

function pick(pool) {
  return pool[Math.floor(Math.random() * pool.length)]
}

/**
 * Mock implementation of POST /api/upload. Walks through the same five
 * processing steps shown in the wireframe's "Activity Log" (page 3),
 * calling onStep(index) as each completes, then resolves with the full
 * detected item -- or rejects for the FR-8 error-state path.
 */
async function mockUploadItem(file, { onStep } = {}) {
  if (!file || !file.type.startsWith('image/')) {
    await delay(500)
    throw { code: 'ERR_002', message: 'Unsupported image format.' }
  }

  const stepDelays = [400, 700, 900, 700, 500]
  for (let i = 0; i < PROCESSING_STEPS.length; i += 1) {
    await delay(stepDelays[i])
    onStep?.(i)
  }

  // ~8% simulated failure so the error page is easy to demo
  if (Math.random() < 0.08) {
    throw { code: 'ERR_001', message: 'The AI could not find a clothing item in the uploaded image.' }
  }

  const [name, category] = pick(CATEGORY_POOL)
  idCounter += 1
  const item = {
    id: `item_${idCounter}`,
    name,
    category,
    color: pick(COLOR_POOL),
    material: pick(['Cotton', 'Denim', 'Wool Blend', 'Leather', 'Polyester']),
    season: pick(SEASON_POOL),
    occasion: pick(OCCASION_POOL),
    confidence: Math.round((88 + Math.random() * 9) * 10) / 10,
    addedDate: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    image_url: URL.createObjectURL(file),
  }

  const items = readStore()
  items.unshift(item)
  writeStore(items)
  return item
}

async function mockFetchWardrobe() {
  await delay(300)
  return readStore()
}

async function mockRemoveItem(id) {
  await delay(200)
  const items = readStore().filter((item) => item.id !== id)
  writeStore(items)
  return { ok: true }
}

export function normalizeItem(item) {
  if (!item) return item
  const rawId = item.id || item._id || 'unknown'
  const id = String(rawId)
  const category = item.category || 'Clothing'
  const type = item.type || category
  const color = item.color || ''
  
  // Construct clean display name
  let name = item.name
  if (!name || name === 'undefined') {
    name = color ? `${color} ${type}` : type
    name = name.charAt(0).toUpperCase() + name.slice(1)
  }

  // Construct valid image_url for browser
  let image_url = item.image_url
  if (!image_url) {
    const rawPath = item.segmentation_path || item.source_image || ''
    if (rawPath) {
      const norm = rawPath.replace(/\\/g, '/')
      const idxUploads = norm.toLowerCase().indexOf('uploads/')
      const idxMl = norm.toLowerCase().indexOf('ml/outputs/')
      if (idxUploads !== -1) {
        image_url = `${API_BASE_URL}/${norm.substring(idxUploads)}`
      } else if (idxMl !== -1) {
        image_url = `${API_BASE_URL}/${norm.substring(idxMl)}`
      } else {
        image_url = norm.startsWith('http') ? norm : `${API_BASE_URL}/${norm.replace(/^\//, '')}`
      }
    }
  }

  const addedDate = item.addedDate || (item.uploaded_at ? new Date(item.uploaded_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Recently')

  return {
    ...item,
    id,
    name,
    category,
    displayCategory: getDisplayCategory({ ...item, category }),
    type,
    color,
    material: item.material || item.pattern || 'Cotton',
    season: item.season || 'All Season',
    occasion: item.occasion || item.style || 'Casual',
    viewCount: item.viewCount ?? 0,
    wearCount: item.wearCount ?? 0,
    addedDate,
    confidence: item.confidence || (item.confidence_scores?.category ? Math.round(item.confidence_scores.category * 100) : 90),
    image_url: image_url || '/placeholder.png',
  }
}

async function realUploadItem(file, { onStep } = {}) {
  const form = new FormData()
  form.append('file', file)
  onStep?.(0)
  const res = await fetch(`${API_BASE_URL}/upload/`, { method: 'POST', body: form })
  if (!res.ok) throw { code: 'ERR_001', message: 'The AI could not find a clothing item in the uploaded image.' }
  onStep?.(PROCESSING_STEPS.length - 1)
  const data = await res.json()
  return Array.isArray(data) ? data.map(normalizeItem)[0] : normalizeItem(data)
}

async function realFetchWardrobe() {
  const res = await fetch(`${API_BASE_URL}/wardrobe/`)
  if (!res.ok) throw new Error('Could not load your wardrobe.')
  const data = await res.json()
  return data.map(normalizeItem)
}

async function realRemoveItem(id) {
  const res = await fetch(`${API_BASE_URL}/wardrobe/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Could not remove this item.')
  return res.json()
}

export const uploadItem = USE_MOCK ? mockUploadItem : realUploadItem
export const fetchWardrobe = USE_MOCK ? mockFetchWardrobe : realFetchWardrobe
export const removeItem = USE_MOCK ? mockRemoveItem : realRemoveItem
export const isMock = USE_MOCK

