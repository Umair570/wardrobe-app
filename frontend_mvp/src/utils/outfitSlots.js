// Maps ML/backend category values to outfit layout slots (WMVP-20 contract).

export const SLOT_LABELS = {
  top: 'Top',
  bottom: 'Bottom',
  shoes: 'Shoes',
  outerwear: 'Outerwear',
}

/** ML pipeline category → layout slot */
export const CATEGORY_TO_SLOT = {
  shirt: 'top',
  sweater: 'top',
  suit: 'top',
  dress: 'bottom',
  pants: 'bottom',
  shorts: 'bottom',
  skirt: 'bottom',
  shoes: 'shoes',
  jacket: 'outerwear',
  // Frontend mock display names
  top: 'top',
  bottom: 'bottom',
  outerwear: 'outerwear',
}

export function getItemSlot(item) {
  const raw = String(item?.category || '').toLowerCase()
  return CATEGORY_TO_SLOT[raw] || null
}

export function getDisplayCategory(item) {
  const slot = getItemSlot(item)
  return slot ? SLOT_LABELS[slot] : item?.category || 'Other'
}

/** Group wardrobe items by outfit slot for the builder UI. */
export function groupItemsBySlot(items) {
  const groups = { top: [], bottom: [], shoes: [], outerwear: [] }
  for (const item of items) {
    const slot = getItemSlot(item)
    if (slot && groups[slot]) groups[slot].push(item)
  }
  return groups
}
