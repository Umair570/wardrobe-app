import { useEffect, useMemo, useState } from 'react'
import { CATEGORIES, SEASONS, SORT_OPTIONS } from '../data/mockData'

const PAGE_SIZE = 6

export default function WardrobePage({ items, loading, onOpenItem, onGoToUpload }) {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [color, setColor] = useState('All')
  const [season, setSeason] = useState('All')
  const [sort, setSort] = useState(SORT_OPTIONS[0])
  const [page, setPage] = useState(1)

  const colors = useMemo(() => ['All', ...new Set(items.map((i) => i.color))], [items])

  const filtered = useMemo(() => {
    let list = items.filter((item) => {
      const matchesQuery = query.trim() === '' || item.name.toLowerCase().includes(query.trim().toLowerCase())
      const matchesCategory = category === 'All' || item.category === category
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
    <div className="max-w-6xl mx-auto px-6 py-14">
      <h1 className="text-2xl font-bold mb-6">My Wardrobe</h1>

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
            {pageItems.map((item) => (
              <div key={item.id} className="panel p-4 flex flex-col">
                <div className="placeholder-box aspect-square w-full mb-4">
                  Clothing
                  <br />
                  Image
                </div>
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold">{item.name}</h3>
                  <button className="text-faint hover:text-ink" aria-label="Favorite">
                    ♡
                  </button>
                </div>
                <div className="flex gap-1.5 mb-4">
                  <span className="tag">{item.color}</span>
                  <span className="tag">{item.occasion.split(' / ')[0]}</span>
                </div>
                <button onClick={() => onOpenItem(item)} className="btn-outline mt-auto">
                  View Details
                </button>
              </div>
            ))}
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
    </div>
  )
}
