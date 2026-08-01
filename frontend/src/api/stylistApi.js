// stylistApi.js
//
// Placeholder for Abdulrehman's real AI Stylist. Everything here is a
// simple rule-based mock so the Stylist and Recommended Outfits screens
// are fully clickable in the demo. Swap `askStylist` for a real API call
// once his chatbot backend is ready -- StylistPage only imports this
// function, so nothing else needs to change.

import { RECOMMENDED_OUTFITS } from '../data/mockData'

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function askStylist(message, wardrobeContext = []) {
  await delay(600)
  const lower = message.toLowerCase()

  if (lower.includes('jean')) {
    return "Your blue jeans pair well with: the charcoal blazer for a smart look, the grey hoodie for a relaxed fit, or white sneakers as a shoe option."
  }
  if (lower.includes('formal')) {
    return 'For a formal occasion, try the charcoal blazer with dark jeans and white sneakers swapped for loafers if you have them.'
  }
  if (lower.includes('wear today') || lower.includes('today')) {
    return "Based on your wardrobe and today's casual occasion, I'd suggest your navy t-shirt with dark jeans and white sneakers. It's a clean, versatile look."
  }
  if (wardrobeContext.length > 0) {
    const sample = wardrobeContext.slice(0, 2).map((i) => `${i.name} (${i.color})`).join(' and ')
    return `Based on what's in your wardrobe right now, ${sample} would make a solid starting point. Want me to build a full outfit around it?`
  }
  return "Add a few items to your wardrobe and I'll be able to give you more specific outfit ideas."
}

export async function generateOutfits() {
  await delay(500)
  return RECOMMENDED_OUTFITS
}

export const SUGGESTED_PROMPTS = [
  'What should I wear today?',
  'What matches my blue jeans?',
  'Suggest a formal outfit.',
]
