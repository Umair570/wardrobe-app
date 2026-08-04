import { useEffect, useState } from 'react'
import { generateOutfits } from '../api/stylistApi'
import BackLink from '../components/BackLink'
import { useToast } from '../components/ToastProvider'

export default function RecommendedOutfitsPage({ items, onBack, onVisualize }) {
  const notify = useToast()
  const [outfits, setOutfits] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    generateOutfits(items).then((data) => {
      setOutfits(data)
      setLoading(false)
    })
  }

  useEffect(load, [items])

  return (
    <div className="max-w-6xl mx-auto px-6 py-14">
      <BackLink onClick={onBack} />

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold mb-1">Recommended Outfits</h1>
          <p className="text-sm text-soft">Built from your actual wardrobe items</p>
        </div>
        <button onClick={load} className="btn-primary">
          Generate Again
        </button>
      </div>

      {loading ? (
        <p className="eyebrow text-center py-16">Generating outfits...</p>
      ) : outfits.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-ink/15">
          <p className="text-soft mb-2">Upload at least a top, bottom, and shoes to get outfit suggestions.</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {outfits.map((outfit) => (
            <div key={outfit.id} className="panel p-5">
              <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
                {outfit.item_ids?.slice(0, 4).map((id) => {
                  const item = items.find((i) => i.id === id)
                  return item?.image_url ? (
                    <div
                      key={id}
                      className="w-16 h-16 shrink-0 rounded-lg overflow-hidden bg-gradient-to-b from-neutral-100 to-neutral-200 flex items-center justify-center"
                    >
                      <img src={item.image_url} alt={item.name} className="w-full h-full object-contain" />
                    </div>
                  ) : null
                })}
              </div>
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold">{outfit.title}</h3>
                <span className="eyebrow">#{outfit.number}</span>
              </div>
              <p className="eyebrow mb-1.5">Items Included ({outfit.item_ids?.length || 0})</p>
              <ul className="text-sm text-soft mb-3 space-y-0.5">
                {outfit.items.map((item) => (
                  <li key={item}>• {item}</li>
                ))}
              </ul>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {outfit.tags.map((tag) => (
                  <span key={tag} className="tag">
                    {tag}
                  </span>
                ))}
              </div>
              <p className="text-sm text-soft mb-4">{outfit.description}</p>
              <div className="flex gap-2.5">
                <button onClick={() => onVisualize(outfit)} className="btn-primary flex-1">
                  Visualize Outfit
                </button>
                <button onClick={() => notify(`"${outfit.title}" saved to your outfits`)} className="btn-outline flex-1">
                  Save Outfit
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
