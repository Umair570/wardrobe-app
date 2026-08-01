// src/pages/StylistPage.jsx
import { useState, useRef, useEffect } from 'react'
import { askStylist, SUGGESTED_PROMPTS } from '../api/stylistApi'

export default function StylistPage({ items, onViewRecommended }) {
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      text: "Hello! I'm your AI Stylist. Ask me anything about what to wear or select wardrobe items on the right for personalized suggestions!",
    },
  ])
  const [input, setInput] = useState('')
  const [checked, setChecked] = useState(() => new Set(items.map((i) => i.id)))
  const [sending, setSending] = useState(false)
  const chatEndRef = useRef(null)

  const contextItems = items.filter((i) => checked.has(i.id))
  const outfitsSuggested = messages.filter((m) => m.role === 'ai').length - 1

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  const send = async (text) => {
    const trimmed = text.trim()
    if (!trimmed || sending) return
    setMessages((prev) => [...prev, { role: 'user', text: trimmed }])
    setInput('')
    setSending(true)

    const reply = await askStylist(trimmed, contextItems)
    setMessages((prev) => [...prev, { role: 'ai', text: reply }])
    setSending(false)
  }

  const toggleItem = (id) => {
    setChecked((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 panel flex flex-col h-[600px]">
          <div className="px-5 py-4 border-b border-ink/10 flex items-center justify-between">
            <div>
              <h1 className="font-semibold">AI Stylist</h1>
              <p className="eyebrow mt-0.5">Online · Powered by AI</p>
            </div>
            <button onClick={onViewRecommended} className="btn-outline !py-1.5 !px-3 text-xs">
              Recommended Outfits
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-5 space-y-3">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[80%] text-sm px-4 py-2.5 rounded-2xl ${
                    m.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-ink/5 border border-ink/10 rounded-bl-none text-ink'
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))}
            {sending && <p className="eyebrow text-xs text-ink/50 animate-pulse">Stylist is thinking...</p>}
            <div ref={chatEndRef} />
          </div>

          <div className="px-5 py-4 border-t border-ink/10">
            <p className="eyebrow mb-2">Suggested Prompts</p>
            <div className="flex flex-wrap gap-2 mb-3">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => send(prompt)}
                  disabled={sending}
                  className="tag hover:bg-ink hover:text-white transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && send(input)}
                placeholder="Ask your AI stylist..."
                disabled={sending}
                className="field flex-1"
              />
              <button onClick={() => send(input)} disabled={sending || !input.trim()} className="btn-primary">
                Send
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-6">
          <div className="panel p-4">
            <p className="eyebrow mb-3">Wardrobe Context</p>
            <p className="text-xs text-soft mb-3">Items sent to AI assistant:</p>
            <div className="space-y-2 max-h-56 overflow-y-auto">
              {items.map((item) => (
                <label key={item.id} className="flex items-center gap-2.5 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checked.has(item.id)}
                    onChange={() => toggleItem(item.id)}
                  />
                  {item.name} {item.color ? `(${item.color})` : ''}
                </label>
              ))}
            </div>
          </div>

          <div className="panel p-4">
            <p className="eyebrow mb-3">Session Info</p>
            <div className="flex justify-between text-sm py-1.5 border-t border-ink/10">
              <span className="text-soft">Messages</span>
              <span className="font-medium">{messages.length}</span>
            </div>
            <div className="flex justify-between text-sm py-1.5 border-t border-ink/10">
              <span className="text-soft">Outfits suggested</span>
              <span className="font-medium">{Math.max(0, outfitsSuggested)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}