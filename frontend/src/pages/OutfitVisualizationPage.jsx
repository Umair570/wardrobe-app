import BackLink from '../components/BackLink'

const SLOT_LETTER = { Top: 'T', Bottom: 'B', Shoes: 'S' }

export default function OutfitVisualizationPage({ outfit, onBack, onChangeClothing, onGenerateAnother }) {
  if (!outfit) return null
  const { slots, tags, description } = outfit

  return (
    <div className="max-w-5xl mx-auto px-6 py-14">
      <BackLink onClick={onBack} label="Back" />

      <div className="grid md:grid-cols-5 gap-8">
        <div className="md:col-span-3">
          <p className="eyebrow mb-3">Body Visualization</p>
          <div className="panel p-8 flex items-center justify-center min-h-[400px]">
            <div className="border-2 border-dashed border-ink/30 w-48 py-16 text-center placeholder-box">
              Clothing Overlay
              <br />
              Body Template
              <br />
              Placeholder
            </div>
          </div>
          <p className="eyebrow mt-3">MVP visualization using simplified overlay.</p>
        </div>

        <div className="md:col-span-2 flex flex-col gap-6">
          <div>
            <p className="eyebrow mb-3">Selected Items</p>
            <div className="space-y-2.5">
              {slots.map((slot) => (
                <div key={slot.role} className="panel p-3 flex items-center gap-3">
                  <span className="w-8 h-8 border border-ink/25 flex items-center justify-center font-mono text-sm shrink-0">
                    {SLOT_LETTER[slot.role]}
                  </span>
                  <div className="flex-1">
                    <p className="eyebrow">{slot.role}</p>
                    <p className="text-sm font-medium">
                      {slot.item ? `${slot.item.name} — ${slot.item.color}` : 'Not selected'}
                    </p>
                  </div>
                  <button onClick={() => onChangeClothing(slot.role)} className="text-xs text-soft hover:text-ink underline">
                    Change
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="panel p-4">
            <p className="eyebrow mb-3">Outfit Details</p>
            <div className="flex flex-wrap gap-1.5 mb-3">
              {tags.map((tag) => (
                <span key={tag} className="tag">
                  {tag}
                </span>
              ))}
            </div>
            <p className="text-sm text-soft">{description}</p>
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
