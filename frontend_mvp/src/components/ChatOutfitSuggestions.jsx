import { SLOT_LABELS } from '../utils/outfitSlots'

export default function ChatOutfitSuggestions({
  recommendedItems = [],
  wardrobeItems = [],
  onVisualizeItem,
  onVisualizeOutfit,
  compact = false,
}) {
  if (!recommendedItems.length) return null

  const findThumb = (id) => wardrobeItems.find((i) => String(i.id) === String(id) || String(i._id) === String(id))?.image_url

  return (
    <div className={`mt-2.5 space-y-2 ${compact ? '' : 'max-w-sm'}`}>
      <p className="text-[10px] uppercase tracking-wide text-ink/50 font-medium">
        Suggested from your wardrobe
      </p>

      {recommendedItems.map((rec) => (
        <div
          key={rec.id}
          className="flex items-center gap-2 bg-white/80 border border-ink/10 rounded-lg p-2"
        >
          <div className="w-10 h-10 shrink-0 rounded-md overflow-hidden bg-gradient-to-b from-neutral-100 to-neutral-200 flex items-center justify-center">
            {findThumb(rec.id) ? (
              <img src={findThumb(rec.id)} alt={rec.label} className="w-full h-full object-contain" />
            ) : (
              <span className="text-[9px] text-soft uppercase">{rec.slot?.slice(0, 2)}</span>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] text-soft uppercase">{SLOT_LABELS[rec.slot] || rec.category}</p>
            <p className="text-xs font-medium truncate">{rec.label}</p>
          </div>
          <button
            type="button"
            onClick={() => onVisualizeItem?.(rec.id)}
            className="shrink-0 text-[11px] font-semibold bg-black hover:bg-black/80 text-white px-2.5 py-1 rounded-md transition-colors"
          >
            Visualize
          </button>
        </div>
      ))}

      {recommendedItems.length > 1 && onVisualizeOutfit && (
        <button
          type="button"
          onClick={() => onVisualizeOutfit(recommendedItems.map((r) => r.id))}
          className="w-full text-xs font-semibold border border-ink/20 hover:bg-ink/5 py-1.5 rounded-lg transition-colors"
        >
          Visualize full outfit ({recommendedItems.length} items)
        </button>
      )}
    </div>
  )
}
