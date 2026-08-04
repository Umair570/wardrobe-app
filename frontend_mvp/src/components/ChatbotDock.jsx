import { useEffect, useRef, useState } from 'react'
import { sendMessage } from '../api/chatbotApi'
import ChatOutfitSuggestions from './ChatOutfitSuggestions'

const WELCOME = {
  role: 'ai',
  text: "Hi! I'm your AI Stylist. Ask what to wear today — I'll suggest a complete outfit from your wardrobe with visualize options for each piece.",
  recommendedItems: [],
}

export default function ChatbotDock({ items, onExpand, onVisualizeItem, onVisualizeOutfit }) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && setOpen(false)
    if (open) window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, open])

  const submit = async (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return
    setMessages((prev) => [...prev, { role: 'user', text }])
    setInput('')
    setSending(true)

    const { reply, recommendedItems } = await sendMessage(text, { wardrobeItems: items })
    setMessages((prev) => [...prev, { role: 'ai', text: reply, recommendedItems }])
    setSending(false)
  }

  const handleVisualizeItem = (id) => {
    onVisualizeItem?.(id)
    setOpen(false)
  }

  const handleVisualizeOutfit = (ids) => {
    onVisualizeOutfit?.(ids)
    setOpen(false)
  }

  return (
    <>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Open AI Stylist chat'}
        className="fixed bottom-24 md:bottom-6 right-5 md:right-6 z-40 w-14 h-14 rounded-full bg-indigo text-white shadow-pop
                   flex items-center justify-center hover:bg-indigo-dark active:scale-95 transition-all"
      >
        {open ? (
          <span className="text-xl leading-none">×</span>
        ) : (
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <path
              d="M3 5.5C3 4.1 4.1 3 5.5 3h11C17.9 3 19 4.1 19 5.5v7c0 1.4-1.1 2.5-2.5 2.5H9l-4.5 4v-4H5.5C4.1 15 3 13.9 3 12.5v-7Z"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </button>

      {open && (
        <div className="fixed bottom-[168px] md:bottom-24 right-5 md:right-6 z-40 w-[calc(100%-2.5rem)] sm:w-full max-w-sm h-[520px] max-h-[70vh] panel flex flex-col overflow-hidden animate-fade-slide-in">
          <div className="px-4 py-3.5 border-b border-ink/8 flex items-center justify-between">
            <div>
              <p className="font-semibold text-sm">AI Stylist</p>
              <p className="eyebrow mt-0.5">Wardrobe-aware</p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={onExpand} className="text-xs text-indigo font-medium hover:text-indigo-dark">
                Expand
              </button>
              <button onClick={() => setOpen(false)} aria-label="Close" className="text-ink/40 hover:text-ink text-lg leading-none">
                ×
              </button>
            </div>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-2.5">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[92%] text-sm px-3.5 py-2 rounded-lg ${
                    m.role === 'user' ? 'bg-indigo text-white' : 'bg-panel text-ink border border-ink/8'
                  }`}
                >
                  <p>{m.text}</p>
                  {m.role === 'ai' && m.recommendedItems?.length > 0 && (
                    <ChatOutfitSuggestions
                      recommendedItems={m.recommendedItems}
                      wardrobeItems={items}
                      onVisualizeItem={handleVisualizeItem}
                      onVisualizeOutfit={handleVisualizeOutfit}
                      compact
                    />
                  )}
                </div>
              </div>
            ))}
            {sending && <p className="eyebrow">Building outfit from your wardrobe...</p>}
          </div>

          <form onSubmit={submit} className="px-3 py-3 border-t border-ink/8 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="What should I wear today?"
              className="field flex-1"
            />
            <button type="submit" className="btn-primary !px-4">
              Send
            </button>
          </form>
        </div>
      )}
    </>
  )
}
