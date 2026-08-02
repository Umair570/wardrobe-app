import { getItemSlot, groupItemsBySlot } from '../utils/outfitSlots'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function itemLabel(item) {
  const color = item.color?.trim()
  const type = item.type || item.name || 'item'
  if (color && color.toLowerCase() !== 'unknown') {
    return `${color} ${type}`.replace(/\b\w/g, (c) => c.toUpperCase())
  }
  return type.charAt(0).toUpperCase() + type.slice(1)
}

function pickLocalOutfit(wardrobeItems, message = '') {
  if (!wardrobeItems?.length) {
    return { reply: 'Your wardrobe is empty. Upload clothing first!', recommendedItems: [] }
  }

  const msg = message.toLowerCase()
  const groups = groupItemsBySlot(wardrobeItems)
  const picks = []

  if (msg.includes('formal') || msg.includes('jacket')) {
    if (groups.outerwear[0]) picks.push(groups.outerwear[0])
  }
  if (groups.top[0]) picks.push(groups.top[0])
  if (groups.bottom[0]) picks.push(groups.bottom[0])
  if (groups.shoes[0]) picks.push(groups.shoes[0])

  const unique = []
  const seen = new Set()
  for (const item of picks) {
    const slot = getItemSlot(item)
    if (slot && !seen.has(slot)) {
      seen.add(slot)
      unique.push(item)
    }
  }

  const finalPicks = unique.length ? unique : wardrobeItems.slice(0, 3)
  const labels = finalPicks.map(itemLabel)

  let reply
  if (labels.length === 1) {
    reply = `I'd suggest your ${labels[0]}. Tap Visualize to preview it.`
  } else {
    reply = `Here's a look from your wardrobe: ${labels.join(', ')}. Visualize each item or the full outfit.`
  }

  return {
    reply,
    recommendedItems: finalPicks.map((item) => ({
      id: item.id,
      label: itemLabel(item),
      category: item.category,
      slot: getItemSlot(item) || 'other',
      color: item.color || '',
      type: item.type || item.name || '',
    })),
  }
}

/**
 * @returns {{ reply: string, recommendedItems: Array }}
 */
export async function sendMessage(message, { wardrobeItems = [] } = {}) {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        user_id: 'default_user',
      }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Chat request failed (${res.status})`)
    }

    const data = await res.json()
    return {
      reply: data.reply,
      recommendedItems: data.recommended_items || [],
    }
  } catch (error) {
    console.warn('[chatbotApi] Backend unavailable, using local outfit picker:', error.message)
    return pickLocalOutfit(wardrobeItems, message)
  }
}

export { pickLocalOutfit, itemLabel }
