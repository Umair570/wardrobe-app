// stylistApi.js — AI Stylist + Visualization API (WMVP-20)

import { getItemSlot, groupItemsBySlot } from '../utils/outfitSlots'

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export const SUGGESTED_PROMPTS = [
  'Suggest a complete casual outfit for today.',
  'What matches my blue jeans?',
  'Suggest a formal outfit with jacket.',
]

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Very light keyword matching so the same query words that are visible in
 * the item's name/color/type/tags can influence which items get picked.
 * This is not an LLM call — it's a stand-in so results actually change
 * based on what the user typed instead of always returning the same
 * fixed combo. Replace with a real backend call when the AI stylist
 * endpoint exists.
 */
function scoreItemAgainstQuery(item, queryWords) {
  if (!queryWords.length) return 0
  const haystack = `${item.name || ''} ${item.color || ''} ${item.type || ''} ${item.category || ''} ${item.occasion || ''} ${item.season || ''}`.toLowerCase()
  return queryWords.reduce((score, word) => (haystack.includes(word) ? score + 1 : score), 0)
}

function sortBySlotThenQueryMatch(groups, queryWords) {
  const sorted = {}
  for (const slot of Object.keys(groups)) {
    sorted[slot] = [...groups[slot]].sort(
      (a, b) => scoreItemAgainstQuery(b, queryWords) - scoreItemAgainstQuery(a, queryWords),
    )
  }
  return sorted
}

/**
 * Build outfit combinations from live wardrobe items.
 * @param {object[]} wardrobeItems
 * @param {string} query - the user's typed message, e.g. "What matches my blue jeans?"
 */
export async function generateOutfits(wardrobeItems = [], query = '') {
  await delay(400)

  if (!wardrobeItems.length) return []

  const queryWords = query
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .split(/\s+/)
    .filter((w) => w.length > 2)

  const groups = queryWords.length
    ? sortBySlotThenQueryMatch(groupItemsBySlot(wardrobeItems), queryWords)
    : groupItemsBySlot(wardrobeItems)
  const tops = groups.top
  const bottoms = groups.bottom
  const shoesList = groups.shoes
  const outerwear = groups.outerwear

  const outfits = []
  let n = 0

  const addOutfit = (title, tags, description, picks) => {
    const item_ids = picks.map((i) => i.id).filter(Boolean)
    if (item_ids.length === 0) return
    n += 1
    outfits.push({
      id: `outfit_${n}`,
      number: String(n).padStart(2, '0'),
      title,
      items: picks.map((i) => `${i.name || i.type} — ${i.color || ''}`.trim()),
      item_ids,
      tags,
      description,
    })
  }

  if (tops[0] && bottoms[0] && shoesList[0]) {
    addOutfit(
      'Everyday Casual',
      ['Casual', 'All Season'],
      'A balanced everyday look from your wardrobe.',
      [tops[0], bottoms[0], shoesList[0]],
    )
  }

  if (tops[1] && bottoms[0] && shoesList[0]) {
    addOutfit(
      'Relaxed Weekend',
      ['Casual', 'Weekend'],
      'Comfortable and easy for errands or coffee.',
      [tops[1], bottoms[0], shoesList[0]],
    )
  }

  if (outerwear[0] && tops[0] && bottoms[0]) {
    addOutfit(
      'Smart Layered',
      ['Smart Casual', 'Layered'],
      'Layer outerwear over a top and bottom for cooler days.',
      [outerwear[0], tops[0], bottoms[0], ...(shoesList[0] ? [shoesList[0]] : [])],
    )
  }

  if (tops[0] && bottoms[1] && shoesList[0]) {
    addOutfit(
      'Fresh Combo',
      ['Casual', 'Versatile'],
      'Mix different tops and bottoms for variety.',
      [tops[0], bottoms[1], shoesList[0]],
    )
  }

  // Fallback: any single complete combo we can find
  if (outfits.length === 0) {
    const picks = [tops[0], bottoms[0], shoesList[0], outerwear[0]].filter(Boolean)
    if (picks.length >= 2) {
      addOutfit(
        'Your Wardrobe Pick',
        ['Custom'],
        'Built from items currently in your wardrobe.',
        picks,
      )
    }
  }

  return outfits
}

function toAbsoluteUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  const cleanBase = API_BASE.replace(/\/$/, '')
  return `${cleanBase}${url.startsWith('/') ? '' : '/'}${url}`
}

/**
 * @param {string[]} item_ids
 * @param {string} mode - 'overlay' or 'ai'
 * @param {string|null} userBodyPhoto - required when mode === 'ai'; URL/path of the
 *   user's uploaded body photo, used server-side for the actual image-to-image try-on.
 */
export async function postVisualization(item_ids, mode = 'overlay', userBodyPhoto = null) {
  if (mode === 'ai' && !userBodyPhoto) {
    throw new Error('A body photo is required for AI try-on.')
  }

  const res = await fetch(`${API_BASE}/visualization`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      item_ids,
      mode,
      user_body_photo_url: userBodyPhoto,
    }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    // Surface the real backend error (e.g. AI generation failure) instead of
    // letting the caller assume success just because a response came back.
    throw new Error(err.detail || `Visualization request failed (${res.status})`)
  }

  const data = await res.json()

  data.items = (data.items || []).map((item) => ({
    ...item,
    image_url: toAbsoluteUrl(item.image_url),
  }))

  // ai_image_url was previously left untouched, so a generated image would try
  // to load from the frontend's own origin and 404. Prefix it the same way.
  if (data.ai_image_url) {
    data.ai_image_url = toAbsoluteUrl(data.ai_image_url)
  }

  return data
}