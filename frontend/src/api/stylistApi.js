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

/** Build outfit combinations from live wardrobe items. */
export async function generateOutfits(wardrobeItems = []) {
  await delay(400)

  if (!wardrobeItems.length) return []

  const groups = groupItemsBySlot(wardrobeItems)
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

export async function postVisualization(item_ids) {
  const res = await fetch(`${API_BASE}/visualization`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_ids, mode: 'overlay' }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Visualization request failed (${res.status})`)
  }

  const data = await res.json()
  const cleanBase = API_BASE.replace(/\/$/, '')
  data.items = (data.items || []).map((item) => ({
    ...item,
    image_url: item.image_url
      ? (item.image_url.startsWith('http') ? item.image_url : `${cleanBase}${item.image_url.startsWith('/') ? '' : '/'}${item.image_url}`)
      : '',
  }))
  return data
}
