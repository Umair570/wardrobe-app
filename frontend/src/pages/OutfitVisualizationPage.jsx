import React from 'react'
import BackLink from '../components/BackLink'

const SLOT_LETTER = { Top: 'T', Bottom: 'B', Shoes: 'S' }

export default function OutfitVisualizationPage({ outfit, onBack, onChangeClothing, onGenerateAnother }) {
  if (!outfit) return null

  // Provide fallback defaults to avoid undefined map errors
  const { slots = [], tags = [], description = '' } = outfit

  return (
    <div className="max-w-5xl mx-auto px-6 py-14">
      <BackLink onClick={onBack} label="Back" />

      <div className="grid md:grid-cols-5 gap-8 mt-6">
        {/* Visual Canvas Area */}
        <div className="md:col-span-3">
          <p className="eyebrow mb-3">Body Visualization</p>
          <div className="panel p-8 flex flex-col items-center justify-center min-h-[420px] bg-black/5 rounded-2xl border border-black/10">
            
            {/* Simple Mannequin / Item Stacking Stage */}
            <div className="w-52 flex flex-col gap-3 items-center py-6">
              {slots.map((slot) => (
                <div key={slot.role} className="w-full text-center">
                  {slot.item ? (
                    <div className="p-3 bg-white border border-black/15 rounded-xl shadow-sm flex items-center justify-between">
                      {slot.item.imageUrl || slot.item.image ? (
                        <img 
                          src={slot.item.imageUrl || slot.item.image} 
                          alt={slot.item.name} 
                          className="w-10 h-10 object-contain rounded-md" 
                        />
                      ) : (
                        <span className="w-8 h-8 rounded-lg bg-black/10 font-bold text-xs flex items-center justify-center">
                          {SLOT_LETTER[slot.role] || '•'}
                        </span>
                      )}
                      <div className="text-right">
                        <p className="text-xs font-bold text-black">{slot.item.name}</p>
                        <p className="text-[10px] text-black/60">{slot.item.color}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 border-2 border-dashed border-black/20 rounded-xl text-xs text-black/40">
                      Empty {slot.role} Slot
                    </div>
                  )}
                </div>
              ))}
            </div>

          </div>
          <p className="eyebrow mt-3 text-black/50 text-xs">MVP visualization using item layer stack.</p>
        </div>

        {/* Selected Items & Details */}
        <div className="md:col-span-2 flex flex-col gap-6">
          <div>
            <p className="eyebrow mb-3">Selected Items</p>
            <div className="space-y-2.5">
              {slots.map((slot) => (
                <div key={slot.role} className="panel p-3 border border-black/10 rounded-xl flex items-center gap-3">
                  <span className="w-8 h-8 border border-black/20 rounded-lg flex items-center justify-center font-mono text-xs font-bold shrink-0">
                    {SLOT_LETTER[slot.role] || '?'}
                  </span>
                  <div className="flex-1">
                    <p className="text-[10px] uppercase font-bold text-black/50">{slot.role}</p>
                    <p className="text-sm font-medium text-black">
                      {slot.item ? `${slot.item.name} — ${slot.item.color}` : 'Not selected'}
                    </p>
                  </div>
                  <button 
                    onClick={() => onChangeClothing && onChangeClothing(slot.role)} 
                    className="text-xs text-black/70 hover:text-black underline font-medium"
                  >
                    Change
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="panel p-4 border border-black/10 rounded-xl space-y-3">
            <p className="eyebrow">Outfit Details</p>
            <div className="flex flex-wrap gap-1.5">
              {tags.map((tag) => (
                <span key={tag} className="px-2.5 py-1 bg-black/5 border border-black/10 rounded-full text-xs font-semibold text-black">
                  #{tag}
                </span>
              ))}
            </div>
            <p className="text-sm text-black/70 leading-relaxed">{description}</p>
          </div>

          <div className="flex flex-col gap-2.5 mt-auto pt-4">
            <button onClick={() => onChangeClothing && onChangeClothing()} className="w-full py-2.5 border border-black rounded-xl font-medium text-sm hover:bg-black/5 transition-colors">
              Change Clothing
            </button>
            <button onClick={onGenerateAnother} className="w-full py-2.5 bg-black text-white rounded-xl font-medium text-sm hover:bg-black/80 transition-colors">
              Generate Another Outfit
            </button>
            <button onClick={onBack} className="w-full py-2 text-xs text-black/60 hover:text-black font-medium">
              Back to Wardrobe
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}