import { useEffect, useMemo, useState } from 'react'
import { CATEGORIES, SEASONS, SORT_OPTIONS } from '../data/mockData'
import { getDisplayCategory, getItemSlot, SLOT_LABELS } from '../utils/outfitSlots'

const PAGE_SIZE = 6
const OUTFIT_SLOTS = ['top', 'bottom', 'shoes', 'outerwear']

function ItemThumbnail({ item }) {
  const [failed, setFailed] = useState(false)

  if (!item.image_url || failed) {
    return (
      <span className="text-xs text-soft text-center px-2">
        {failed ? 'Image unavailable' : item.category}
      </span>
    )
  }

  return (
    <img
      src={item.image_url}
      alt={item.name}
      className="w-full h-full object-contain drop-shadow-sm"
      onError={() => {
        // Previously a failed load just rendered as an empty box with no
        // signal at all. Now it falls back to a visible placeholder and
        // logs the bad URL so it's actually diagnosable from the console.
        console.warn(`[WardrobePage] Failed to load image for "${item.name}" (${item.id}):`, item.image_url)
        setFailed(true)
      }}
    />
  )
}

export default function WardrobePage({ items, loading, onOpenItem, onGoToUpload, onVisualizeMultiple }) {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [color, setColor] = useState('All')
  const [season, setSeason] = useState('All')
  const [sort, setSort] = useState(SORT_OPTIONS[0])
  const [page, setPage] = useState(1)
  const [selectedBySlot, setSelectedBySlot] = useState({})

  const colors = useMemo(() => ['All', ...new Set(items.map((i) => i.color))], [items])

  const selectedIds = useMemo(
    () => Object.values(selectedBySlot).filter(Boolean),
    [selectedBySlot],
  )

  const toggleSelect = (item) => {
    const slot = getItemSlot(item)
    if (!slot) return

    setSelectedBySlot((prev) => {
      const next = { ...prev }
      if (next[slot] === item.id) {
        delete next[slot]
      } else {
        next[slot] = item.id
      }
      return next
    })
  }

  const handleVisualizeSelected = () => {
    if (selectedIds.length === 0) return
    onVisualizeMultiple(selectedIds)
  }

  const filtered = useMemo(() => {
    let list = items.filter((item) => {
      const matchesQuery = query.trim() === '' || item.name.toLowerCase().includes(query.trim().toLowerCase())
      const displayCat = getDisplayCategory(item)
      const matchesCategory = category === 'All' || displayCat === category
      const matchesColor = color === 'All' || item.color === color
      const matchesSeason = season === 'All' || item.season === season
      return matchesQuery && matchesCategory && matchesColor && matchesSeason
    })

    if (sort === 'Name A–Z') list = [...list].sort((a, b) => a.name.localeCompare(b.name))
    if (sort === 'Name Z–A') list = [...list].sort((a, b) => b.name.localeCompare(a.name))
    if (sort === 'Oldest first') list = [...list].reverse()

    return list
  }, [items, query, category, color, season, sort])

  useEffect(() => setPage(1), [query, category, color, season, sort])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const pageItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <div className="max-w-6xl mx-auto px-6 py-14 pb-32">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">My Wardrobe</h1>
        <p className="text-sm text-soft hidden sm:block">Select one item per slot to build an outfit</p>
      </div>

      <div className="flex flex-wrap gap-3 mb-8">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search clothing..."
          className="field flex-1 min-w-[200px]"
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)} className="field">
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              Category: {c}
            </option>
          ))}
        </select>
        <select value={color} onChange={(e) => setColor(e.target.value)} className="field">
          {colors.map((c) => (
            <option key={c} value={c}>
              Color: {c}
            </option>
          ))}
        </select>
        <select value={season} onChange={(e) => setSeason(e.target.value)} className="field">
          {SEASONS.map((s) => (
            <option key={s} value={s}>
              Season: {s}
            </option>
          ))}
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value)} className="field">
          {SORT_OPTIONS.map((s) => (
            <option key={s} value={s}>
              Sort: {s}
            </option>
          ))}
        </select>
      </div>

      {loading && <p className="eyebrow text-center py-16">Fetching your wardrobe...</p>}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-16 border border-dashed border-ink/15">
          <p className="text-soft mb-4">Nothing matches those filters yet.</p>
          <button onClick={onGoToUpload} className="btn-primary">
            Upload an item
          </button>
        </div>
      )}

      {!loading && pageItems.length > 0 && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-5 mb-8">
            {pageItems.map((item) => {
              const slot = getItemSlot(item)
              const isSelected = slot ? selectedBySlot[slot] === item.id : false
              const slotTaken = slot && selectedBySlot[slot] && selectedBySlot[slot] !== item.id

              return (
                <div
                  key={item.id}
                  className={`panel p-4 flex flex-col transition-all relative ${
                    isSelected ? 'ring-2 ring-black border-black bg-black/5' : ''
                  } ${!slot ? 'opacity-60' : ''}`}
                >
                  {slot && (
                    <div className="absolute top-3 left-3 z-10">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        disabled={slotTaken}
                        onChange={() => toggleSelect(item)}
                        className="w-4 h-4 cursor-pointer accent-black disabled:opacity-40"
                      />
                    </div>
                  )}

                  <div className="absolute top-3 right-3 z-10">
                    <span className="tag text-[10px]">{getDisplayCategory(item)}</span>
                  </div>

                  <div className="aspect-square w-full mb-4 rounded-xl overflow-hidden bg-gradient-to-b from-neutral-100 to-neutral-200 border border-ink/10 flex items-center justify-center p-2 relative">
                    <ItemThumbnail item={item} />
                  </div>
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-sm truncate">{item.name}</h3>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    <span className="tag">{item.color}</span>
                    <span className="tag">{item.occasion}</span>
                  </div>
                  <div className="flex gap-2 mt-auto">
                    {slot ? (
                      <button
                        onClick={() => toggleSelect(item)}
                        disabled={slotTaken}
                        className={`btn-outline flex-1 text-xs !py-1.5 ${
                          isSelected ? 'bg-black text-white' : slotTaken ? 'opacity-40 cursor-not-allowed' : ''
                        }`}
                      >
                        {isSelected ? '✓ Selected' : slotTaken ? 'Slot taken' : '+ Add to outfit'}
                      </button>
                    ) : (
                      <span className="text-xs text-soft flex-1 text-center py-1.5">Not visualizable</span>
                    )}
                    <button onClick={() => onOpenItem(item)} className="btn-muted text-xs !py-1.5 !px-2">
                      Details
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="flex items-center justify-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="w-8 h-8 border border-ink/20 flex items-center justify-center disabled:opacity-30"
            >
              ←
            </button>
            {Array.from({ length: totalPages }).map((_, i) => (
              <button
                key={i}
                onClick={() => setPage(i + 1)}
                className={`w-8 h-8 border flex items-center justify-center text-sm ${
                  page === i + 1 ? 'bg-ink text-white border-ink' : 'border-ink/20 text-soft hover:text-ink'
                }`}
              >
                {i + 1}
              </button>
            ))}
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="w-8 h-8 border border-ink/20 flex items-center justify-center disabled:opacity-30"
            >
              →
            </button>
          </div>
        </>
      )}

      {/* Floating outfit builder bar */}
      {selectedIds.length > 0 && (
        <div className="fixed bottom-20 md:bottom-6 left-1/2 -translate-x-1/2 z-30 w-[calc(100%-2rem)] max-w-2xl">
          <div className="panel p-4 shadow-pop border border-ink/15 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
            <div className="flex-1">
              <p className="eyebrow mb-2">Outfit Builder ({selectedIds.length}/4)</p>
              <div className="flex flex-wrap gap-2">
                {OUTFIT_SLOTS.map((slot) => {
                  const id = selectedBySlot[slot]
                  const item = id ? items.find((i) => i.id === id) : null
                  return (
                    <div
                      key={slot}
                      className={`text-xs px-2.5 py-1.5 rounded-lg border ${
                        item ? 'bg-black/5 border-black/20' : 'border-dashed border-ink/20 text-soft'
                      }`}
                    >
                      {SLOT_LABELS[slot]}: {item ? item.name : '—'}
                    </div>
                  )
                })}
              </div>
            </div>
            <div className="flex gap-2 shrink-0">
              <button
                onClick={() => setSelectedBySlot({})}
                className="btn-muted text-sm !py-2"
              >
                Clear
              </button>
              <button onClick={handleVisualizeSelected} className="btn-primary text-sm !py-2 !px-5">
                Visualize Outfit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}