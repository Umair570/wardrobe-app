import { useEffect, useRef, useState } from 'react'

function buildSlides(items) {
  const byViews = [...items].sort((a, b) => b.viewCount - a.viewCount).slice(0, 4)
  const byWears = [...items].sort((a, b) => b.wearCount - a.wearCount).slice(0, 4)
  const recent = [...items].slice(0, 4)

  return [
    { key: 'viewed', label: 'Most Viewed', unit: 'views', items: byViews, stat: (i) => i.viewCount },
    { key: 'worn', label: 'Most Worn', unit: 'wears', items: byWears, stat: (i) => i.wearCount },
    { key: 'recent', label: 'Recently Added', unit: '', items: recent, stat: (i) => i.addedDate },
  ]
}

export default function StatsCarousel({ items }) {
  const slides = buildSlides(items)
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)
  const prefersReducedMotion = useRef(
    typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  ).current

  useEffect(() => {
    if (paused || prefersReducedMotion) return
    const id = setInterval(() => setIndex((i) => (i + 1) % slides.length), 4500)
    return () => clearInterval(id)
  }, [paused, slides.length, prefersReducedMotion])

  if (items.length === 0) return null

  const slide = slides[index]

  return (
    <div
      className="panel p-5 mb-10"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <div className="flex items-center justify-between mb-4">
        <p className="eyebrow">{slide.label}</p>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIndex((i) => (i - 1 + slides.length) % slides.length)}
            aria-label="Previous"
            className="w-6 h-6 rounded-full border border-ink/15 flex items-center justify-center hover:border-indigo hover:text-indigo text-xs"
          >
            ‹
          </button>
          <button
            onClick={() => setIndex((i) => (i + 1) % slides.length)}
            aria-label="Next"
            className="w-6 h-6 rounded-full border border-ink/15 flex items-center justify-center hover:border-indigo hover:text-indigo text-xs"
          >
            ›
          </button>
        </div>
      </div>

      <div key={slide.key} className={prefersReducedMotion ? '' : 'animate-fade-slide-in'}>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {slide.items.map((item) => (
            <div key={item.id} className="flex items-center gap-2.5">
              {item.image_url ? (
                <img src={item.image_url} alt={item.name || item.type} className="w-10 h-10 object-cover rounded border border-ink/10 shrink-0" />
              ) : (
                <div className="placeholder-box w-10 h-10 shrink-0 text-[9px]">{item.category}</div>
              )}
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{item.name || item.type || 'Item'}</p>
                <p className="text-xs text-soft">
                  {slide.key === 'recent'
                    ? (item.addedDate || 'Recent')
                    : `${slide.stat(item) ?? 0} ${slide.unit}`}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>


      <div className="flex items-center justify-center gap-1.5 mt-4">
        {slides.map((s, i) => (
          <button
            key={s.key}
            onClick={() => setIndex(i)}
            aria-label={`Show ${s.label}`}
            className={`h-1.5 rounded-full transition-all ${i === index ? 'w-5 bg-indigo' : 'w-1.5 bg-ink/15'}`}
          />
        ))}
      </div>
    </div>
  )
}
