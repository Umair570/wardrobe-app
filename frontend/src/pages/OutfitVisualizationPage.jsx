import BackLink from '../components/BackLink'
import { SLOT_LABELS } from '../utils/outfitSlots'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function getImageUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  const cleanBase = API_BASE.replace(/\/$/, '')
  const cleanPath = url.startsWith('/') ? url : `/${url}`
  return `${cleanBase}${cleanPath}`
}

export default function OutfitVisualizationPage({ outfit, onBack, onChangeClothing, onGenerateAnother }) {
  if (!outfit) return null

  const isOverlay = outfit.mode === 'overlay' && Array.isArray(outfit.items)
  const isOffline = outfit.mode === 'offline'
  const filledSlots = isOverlay ? new Set(outfit.items.map((i) => i.category)) : new Set()
  const missingSlots = ['top', 'bottom', 'shoes'].filter((s) => !filledSlots.has(s))

  return (
    <div className="max-w-5xl mx-auto px-6 py-14">
      <BackLink onClick={onBack} label="Back" />

      <div className="grid md:grid-cols-5 gap-8">
        <div className="md:col-span-3">
          <p className="eyebrow mb-3">Outfit Preview</p>
          <div className="panel p-6 sm:p-8 flex items-center justify-center min-h-[520px]">
            {isOverlay && outfit.items.length > 0 ? (
              <div
                className="relative rounded-3xl overflow-hidden shadow-inner"
                style={{
                  width: '280px',
                  height: '540px',
                  background: 'linear-gradient(180deg, #f5f0eb 0%, #e8dfd6 45%, #ddd4cb 100%)',
                }}
              >
                {/* Human silhouette — subtle guide under garments */}
                <svg
                  viewBox="0 0 100 200"
                  className="absolute inset-0 w-full h-full pointer-events-none select-none"
                  preserveAspectRatio="xMidYMid meet"
                >
                  <defs>
                    <linearGradient id="skinGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#d4c4b0" stopOpacity="0.35" />
                      <stop offset="100%" stopColor="#c9b8a3" stopOpacity="0.2" />
                    </linearGradient>
                  </defs>
                  <ellipse cx="50" cy="14" rx="8" ry="9" fill="url(#skinGrad)" />
                  <rect x="46" y="22" width="8" height="5" rx="2" fill="url(#skinGrad)" />
                  <path
                    d="M 28 28 Q 50 24 72 28 L 66 78 L 34 78 Z"
                    fill="url(#skinGrad)"
                  />
                  <path d="M 27 29 L 18 68 Q 16 72 19 72 L 26 68 L 32 40 Z" fill="url(#skinGrad)" />
                  <path d="M 73 29 L 82 68 Q 84 72 81 72 L 74 68 L 68 40 Z" fill="url(#skinGrad)" />
                  <path d="M 36 79 L 38 168 L 46 168 L 47 79 Z" fill="url(#skinGrad)" />
                  <path d="M 53 79 L 54 168 L 62 168 L 64 79 Z" fill="url(#skinGrad)" />
                </svg>

                {outfit.items
                  .slice()
                  .sort((a, b) => a.z_index - b.z_index)
                  .map((item) => (
                    <img
                      key={item.id}
                      src={getImageUrl(item.image_url)}
                      alt={`${item.category} — ${item.type}`}
                      title={`${item.type} (${item.category})`}
                      draggable={false}
                      style={{
                        position: 'absolute',
                        left: `${item.position.x - item.position.width / 2}%`,
                        top: `${item.position.y - item.position.height / 2}%`,
                        width: `${item.position.width}%`,
                        height: `${item.position.height}%`,
                        zIndex: item.z_index,
                        objectFit: 'contain',
                        objectPosition: 'center',
                        filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.12))',
                        pointerEvents: 'none',
                      }}
                    />
                  ))}

                {missingSlots.length > 0 && (
                  <div className="absolute bottom-3 left-3 right-3 text-center">
                    <p className="text-[10px] text-ink/40 bg-white/60 backdrop-blur-sm rounded-full py-1 px-2 inline-block">
                      Missing: {missingSlots.map((s) => SLOT_LABELS[s]).join(', ')}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="border-2 border-dashed border-ink/30 w-48 py-16 text-center placeholder-box text-sm text-soft">
                {isOffline
                  ? 'Backend offline — start FastAPI to see the overlay.'
                  : 'No items selected for visualization.'}
              </div>
            )}
          </div>
          <p className="eyebrow mt-3">
            {isOverlay && outfit.items.length > 1
              ? `Full outfit — ${outfit.items.length} items layered on mannequin.`
              : isOverlay
                ? 'Select top + bottom + shoes from Wardrobe for a complete outfit.'
                : 'MVP visualization using 2D garment overlay.'}
          </p>
        </div>

        <div className="md:col-span-2 flex flex-col gap-6">
          <div>
            <p className="eyebrow mb-3">Selected Items</p>
            <div className="space-y-2.5">
              {isOverlay && outfit.items.length > 0 ? (
                outfit.items
                  .slice()
                  .sort((a, b) => b.z_index - a.z_index)
                  .map((item) => (
                    <div key={item.id} className="panel p-3 flex items-center gap-3">
                      <div className="w-12 h-12 rounded-lg overflow-hidden bg-gradient-to-b from-neutral-100 to-neutral-200 shrink-0 flex items-center justify-center">
                        <img
                          src={getImageUrl(item.image_url)}
                          alt={item.type}
                          className="w-full h-full object-contain"
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="eyebrow">{SLOT_LABELS[item.category] ?? item.category}</p>
                        <p className="text-sm font-medium truncate">{item.type}</p>
                      </div>
                    </div>
                  ))
              ) : (
                <p className="text-sm text-soft">
                  {isOffline ? outfit.description : 'No items loaded.'}
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-2.5 mt-auto">
            <button onClick={() => onChangeClothing()} className="btn-outline">
              Change Clothing
            </button>
            <button onClick={onGenerateAnother} className="btn-primary">
              Generate Another Outfit
            </button>
            <button onClick={onBack} className="btn-muted">
              Back to Wardrobe
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
