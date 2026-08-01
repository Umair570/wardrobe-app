// chatbotApi.js
//
// TODO(partner): replace this mock implementation with the real chatbot
// logic/backend call. ChatbotDock only imports `sendMessage` below — do
// not change its name or signature without updating ChatbotDock.jsx.
//
// Signature: sendMessage(message, { history, wardrobeItems }) -> Promise<string>
//   message        - the user's latest message text
//   history        - array of { role: 'user' | 'ai', text } for the session so far
//   wardrobeItems  - the person's current wardrobe items, for grounding responses
//
// The mock below reuses the same simple rule-based responder built for the
// full AI Stylist page (src/api/stylistApi.js) so both surfaces feel
// consistent until real logic lands here.

import { askStylist } from './stylistApi'

export async function sendMessage(message, { history = [], wardrobeItems = [] } = {}) {
  return askStylist(message, wardrobeItems)
}
