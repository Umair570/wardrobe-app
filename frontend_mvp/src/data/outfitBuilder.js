const SLOT_FOR_CATEGORY = {
  Top: 'Top',
  Outerwear: 'Top',
  Bottom: 'Bottom',
  Shoes: 'Shoes',
}

function findByCategory(items, categoryRole, excludeId) {
  return items.find((i) => SLOT_FOR_CATEGORY[i.category] === categoryRole && i.id !== excludeId)
}

export function buildOutfitFromItem(focusItem, allItems) {
  const roles = ['Top', 'Bottom', 'Shoes']
  const focusRole = SLOT_FOR_CATEGORY[focusItem.category] || 'Top'

  const slots = roles.map((role) => ({
    role,
    item: role === focusRole ? focusItem : findByCategory(allItems, role, focusItem.id),
  }))

  return {
    slots,
    tags: [focusItem.occasion.split(' / ')[0], focusItem.season.split(' / ')[0]],
    description: `A look built around the ${focusItem.color.toLowerCase()} ${focusItem.name.toLowerCase()}.`,
  }
}

export function buildOutfitFromRecommendation(outfit, allItems) {
  const roles = ['Top', 'Bottom', 'Shoes']
  const parsed = outfit.items.map((entry) => {
    const [name, color] = entry.split(' — ')
    return allItems.find((i) => i.name === name && i.color === color)
  })

  const slots = roles.map((role) => ({
    role,
    item: parsed.find((i) => i && SLOT_FOR_CATEGORY[i.category] === role) || null,
  }))

  return { slots, tags: outfit.tags, description: outfit.description }
}
