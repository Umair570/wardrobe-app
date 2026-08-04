import React, { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { RefreshCw, Sparkles, Move, Palette, Camera, AlertTriangle } from 'lucide-react'
import BackLink from '../components/BackLink'
import UserBodyPhotoUpload from '../components/UserBodyPhotoUpload'
import { SLOT_LABELS } from '../utils/outfitSlots'
import { postVisualization } from '../api/stylistApi'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function getImageUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  const cleanBase = API_BASE.replace(/\/$/, '')
  const cleanPath = url.startsWith('/') ? url : `/${url}`
  return `${cleanBase}${cleanPath}`
}

// Color-name → CSS color mapping
const COLOR_SWATCH = {
  black: '#1a1a1a', white: '#f8f8f8', red: '#e74c3c', blue: '#3498db',
  navy: '#1a2d5a', 'navy blue': '#1a3a6e', green: '#27ae60', olive: '#7a8c45',
  'olive green': '#6b7a3d', yellow: '#f1c40f', orange: '#e67e22', pink: '#e91e8c',
  purple: '#9b59b6', grey: '#95a5a6', gray: '#95a5a6', charcoal: '#36454f',
  'charcoal grey': '#36454f', brown: '#795548', beige: '#f5deb3', cream: '#fffdd0',
  teal: '#009688', maroon: '#800000',
}

function getColorSwatch(colorName) {
  if (!colorName) return null
  return COLOR_SWATCH[colorName.toLowerCase().trim()] || null
}

// ─── Single item card (draggable) ─────────────────────────────────────────────
function ItemCard({ item, index }) {
  const [imgFailed, setImgFailed] = useState(false)
  const imgSrc = getImageUrl(item.image_url)
  const swatch = getColorSwatch(item.color)

  return (
    <motion.div
      drag
      dragConstraints={{ left: -140, right: 140, top: -120, bottom: 120 }}
      whileHover={{ scale: 1.04, cursor: 'grab', zIndex: 50 }}
      whileTap={{ scale: 0.97, cursor: 'grabbing' }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 }}
      className="relative bg-white/95 backdrop-blur-sm border border-black/10 rounded-2xl shadow-lg overflow-hidden select-none"
      style={{ zIndex: (item.z_index || 1) + 10 }}
    >
      <div className="w-36 h-44 relative">
        {imgSrc && !imgFailed ? (
          <img
            src={imgSrc}
            alt={item.type}
            className="w-full h-full object-contain p-2"
            onError={() => setImgFailed(true)}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-2 bg-gradient-to-b from-neutral-50 to-neutral-100">
            {swatch && (
              <div className="w-12 h-12 rounded-full border border-black/10 shadow-inner" style={{ backgroundColor: swatch }} />
            )}
            <span className="text-[11px] text-black/50 font-semibold capitalize">{item.type}</span>
          </div>
        )}
        <span className="absolute top-1.5 left-1.5 px-1.5 py-0.5 bg-black/70 text-white rounded-full text-[9px] font-bold uppercase tracking-wider">
          {item.category}
        </span>
      </div>
      <div className="px-2 pb-2 pt-0.5 border-t border-black/5">
        <p className="text-[11px] font-bold text-black/80 capitalize truncate">{item.color} {item.type}</p>
      </div>
    </motion.div>
  )
}

// ─── Positionally-placed garment image ───────────────────────────────────────
function PositionedItem({ item }) {
  const [imgFailed, setImgFailed] = useState(false)
  const imgSrc = getImageUrl(item.image_url)
  const swatch = getColorSwatch(item.color)

  return (
    <motion.div
      drag
      dragConstraints={{ left: -100, right: 100, top: -100, bottom: 100 }}
      whileHover={{ scale: 1.05, cursor: 'grab' }}
      whileTap={{ scale: 0.98, cursor: 'grabbing' }}
      style={{
        position: 'absolute',
        left: `${item.position.x - item.position.width / 2}%`,
        top: `${item.position.y - item.position.height / 2}%`,
        width: `${item.position.width}%`,
        height: `${item.position.height}%`,
        zIndex: item.z_index,
      }}
    >
      {imgSrc && !imgFailed ? (
        <img
          src={imgSrc}
          alt={item.type}
          className="w-full h-full object-contain"
          style={{ filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.2))' }}
          onError={() => setImgFailed(true)}
        />
      ) : (
        <div
          className="w-full h-full rounded-xl flex items-center justify-center border border-black/10"
          style={{ backgroundColor: swatch || '#e5e7eb' }}
        >
          <span className="text-[10px] text-white font-bold drop-shadow capitalize">{item.type}</span>
        </div>
      )}
    </motion.div>
  )
}

// ─── Sidebar item row ─────────────────────────────────────────────────────────
function SidebarItem({ item }) {
  const [imgFailed, setImgFailed] = useState(false)
  const imgSrc = getImageUrl(item.image_url)
  const swatch = getColorSwatch(item.color)

  return (
    <div className="flex items-center gap-3">
      <div className="w-12 h-12 rounded-xl border border-black/10 bg-neutral-50 overflow-hidden flex items-center justify-center shrink-0">
        {imgSrc && !imgFailed ? (
          <img src={imgSrc} alt={item.type} className="w-full h-full object-contain" onError={() => setImgFailed(true)} />
        ) : swatch ? (
          <div className="w-full h-full" style={{ backgroundColor: swatch }} />
        ) : (
          <span className="text-[10px] text-black/40 font-semibold capitalize">{(item.category || 'X')[0]}</span>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold text-black capitalize truncate">{item.color} {item.type}</p>
        <p className="text-[10px] text-black/50 capitalize">{item.category}</p>
      </div>
      <span className="text-[9px] bg-black/5 border border-black/10 rounded-full px-2 py-0.5 font-bold uppercase shrink-0">
        {item.category}
      </span>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function OutfitVisualizationPage({
  outfit,
  userBodyPhoto,
  onSaveUserBodyPhoto,
  onBack,
  onChangeClothing,
  onGenerateAnother,
}) {
  const [showPhotoModal, setShowPhotoModal] = useState(false)
  // modes: 'overlay' (positional 2D), 'cards' (draggable card grid), 'ai' (IDM-VTON)
  const [activeMode, setActiveMode] = useState('overlay')
  const [aiLoading, setAiLoading] = useState(false)
  const [aiImage, setAiImage] = useState(outfit?.ai_image_url || '')
  const [aiError, setAiError] = useState('')
  const [resetKey, setResetKey] = useState(0)

  const isOverlay = outfit?.mode === 'overlay' && Array.isArray(outfit.items)
  const isOffline = outfit?.mode === 'offline'

  useEffect(() => {
    if (outfit?.ai_image_url) setAiImage(outfit.ai_image_url)
  }, [outfit])

  if (!outfit) return null

  const { slots = [], tags = [], description = '' } = outfit
  const filledSlots = isOverlay ? new Set(outfit.items.map((i) => i.category)) : new Set()
  const missingSlots = ['top', 'bottom', 'shoes'].filter((s) => !filledSlots.has(s))
  const detectedColors = isOverlay
    ? outfit.items.map((item) => item.color || item.type).filter(Boolean)
    : slots.filter((s) => s.item?.color).map((s) => s.item.color)

  const runAiGeneration = async () => {
    if (!isOverlay || outfit.items.length === 0) return
    if (!userBodyPhoto) { setShowPhotoModal(true); return }
    setAiError('')
    setAiLoading(true)
    try {
      const itemIds = outfit.items.map((i) => i.id)
      const res = await postVisualization(itemIds, 'ai', userBodyPhoto)
      if (res.ai_image_url) setAiImage(res.ai_image_url)
    } catch (err) {
      console.error('IDM-VTON generation error:', err)
      setAiError(err?.message || 'IDM-VTON generation failed. Please try again.')
    } finally {
      setAiLoading(false)
    }
  }

  const handleSwitchMode = async (mode) => {
    setActiveMode(mode)
    if (mode === 'ai' && !aiImage) await runAiGeneration()
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
      {/* Photo Upload Modal */}
      {showPhotoModal && (
        <UserBodyPhotoUpload
          currentPhoto={userBodyPhoto}
          onSavePhoto={(photo) => { onSaveUserBodyPhoto?.(photo); setShowPhotoModal(false) }}
          onClose={() => setShowPhotoModal(false)}
        />
      )}

      {/* Top bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <BackLink onClick={onBack} label="Back to Wardrobe" />
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setShowPhotoModal(true)}
            className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border text-xs font-semibold shadow-sm transition-all ${
              userBodyPhoto ? 'border-emerald-500 bg-emerald-50 text-emerald-800' : 'border-black/15 bg-white text-black hover:bg-black/5'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            {userBodyPhoto ? '📸 My Body Photo (Active)' : '📸 Upload My Body Photo'}
          </button>
          <button
            onClick={() => setResetKey((p) => p + 1)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-black/15 bg-white text-xs font-semibold text-black shadow-sm hover:bg-black/5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Reset Layout
          </button>
          <button
            onClick={onGenerateAnother}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-black text-xs font-semibold text-white shadow-md hover:bg-black/80 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Generate Another
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-5 gap-8 items-start">
        {/* ── STAGE ── */}
        <div className="lg:col-span-3 space-y-4">
          {/* Mode tabs */}
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex bg-black/5 p-1 rounded-xl border border-black/10">
              {[
                { id: 'overlay', label: '📸 2D Overlay' },
                { id: 'cards', label: '🗂 Item Cards' },
                { id: 'ai', label: '✨ IDM-VTON Try-On', icon: true },
              ].map(({ id, label, icon }) => (
                <button
                  key={id}
                  onClick={() => handleSwitchMode(id)}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
                    activeMode === id
                      ? id === 'ai' ? 'bg-black text-white shadow-sm' : 'bg-white text-black shadow-sm'
                      : 'text-black/60 hover:text-black'
                  }`}
                >
                  {icon && <Sparkles className="w-3 h-3 text-amber-400" />}
                  {label}
                </button>
              ))}
            </div>
            <span className="text-[11px] font-medium text-black/50 flex items-center gap-1">
              <Move className="w-3 h-3" /> Drag items to test fit
            </span>
          </div>

          {/* Canvas */}
          <div
            key={resetKey}
            className="relative w-full h-[540px] rounded-3xl border border-black/15 bg-gradient-to-b from-gray-50 to-gray-100/60 shadow-inner overflow-hidden flex items-center justify-center p-6"
          >
            {/* ── IDM-VTON mode ── */}
            {activeMode === 'ai' && (
              <div className="relative w-full h-full flex flex-col items-center justify-center">
                {aiLoading ? (
                  <div className="text-center space-y-4">
                    <div className="relative mx-auto w-16 h-16">
                      <Sparkles className="absolute inset-0 w-16 h-16 text-amber-400/30" />
                      <Sparkles className="absolute inset-0 w-16 h-16 text-amber-500 animate-spin" style={{ animationDuration: '2s' }} />
                    </div>
                    <p className="text-sm font-extrabold text-black">IDM-VTON is generating your try-on...</p>
                    <p className="text-[11px] text-black/50">Connecting to HuggingFace — this may take 30–90 sec</p>
                    <div className="flex gap-1 justify-center">
                      {[0, 1, 2].map((i) => (
                        <span key={i} className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                      ))}
                    </div>
                  </div>
                ) : aiImage ? (
                  <div className="relative w-full h-full">
                    <img src={getImageUrl(aiImage)} alt="IDM-VTON try-on" className="w-full h-full object-contain rounded-2xl shadow-md" />
                    <div className="absolute top-3 right-3 bg-black/70 text-white text-[10px] font-bold px-2 py-1 rounded-full flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-amber-400" /> IDM-VTON
                    </div>
                    <button
                      onClick={() => { setAiImage(''); runAiGeneration() }}
                      className="absolute bottom-3 right-3 px-3 py-1.5 bg-black text-white text-xs font-bold rounded-xl shadow hover:bg-black/80"
                    >
                      ↺ Regenerate
                    </button>
                  </div>
                ) : aiError ? (
                  <div className="text-center space-y-3 max-w-xs">
                    <AlertTriangle className="w-8 h-8 text-red-500 mx-auto" />
                    <p className="text-xs font-extrabold text-black">Couldn't generate the IDM-VTON try-on</p>
                    <p className="text-[11px] text-black/60">{aiError}</p>
                    <button onClick={runAiGeneration} className="px-4 py-2 bg-black text-white text-xs font-bold rounded-xl shadow">
                      Try Again
                    </button>
                  </div>
                ) : (
                  <div className="text-center space-y-3 max-w-xs">
                    <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-amber-100 to-amber-200 flex items-center justify-center">
                      <Sparkles className="w-8 h-8 text-amber-500" />
                    </div>
                    <p className="text-sm font-bold text-black">IDM-VTON Virtual Try-On</p>
                    <p className="text-[11px] text-black/60 leading-relaxed">
                      {userBodyPhoto
                        ? 'Ready! Click below to generate a photorealistic try-on.'
                        : 'Upload your body photo first, then generate with IDM-VTON.'}
                    </p>
                    <button onClick={runAiGeneration} className="px-5 py-2 bg-black text-white text-xs font-bold rounded-xl shadow hover:bg-black/80 transition-colors">
                      {userBodyPhoto ? '✨ Generate IDM-VTON Try-On' : '📸 Add Body Photo to Continue'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* ── Item Cards mode ── */}
            {activeMode === 'cards' && (
              <>
                {userBodyPhoto && (
                  <img
                    src={userBodyPhoto}
                    alt="Body reference"
                    className="absolute inset-0 w-full h-full object-contain pointer-events-none opacity-25 select-none p-4"
                  />
                )}
                {isOverlay && outfit.items.length > 0 ? (
                  <div className="relative flex flex-wrap gap-4 items-center justify-center w-full h-full p-4">
                    {outfit.items.map((item, idx) => (
                      <ItemCard key={item.id} item={item} index={idx} />
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-xs text-black/40">No items loaded.</div>
                )}
              </>
            )}

            {/* ── 2D Positional Overlay mode ── */}
            {activeMode === 'overlay' && (
              <>
                {userBodyPhoto ? (
                  <img
                    src={userBodyPhoto}
                    alt="User body photo"
                    className="absolute inset-0 w-full h-full object-contain pointer-events-none opacity-90 select-none p-2"
                  />
                ) : (
                  <>
                    <svg
                      viewBox="0 0 100 200"
                      className="absolute inset-0 w-full h-full pointer-events-none select-none opacity-15"
                      preserveAspectRatio="xMidYMid meet"
                    >
                      <ellipse cx="50" cy="14" rx="8" ry="9" fill="#000" />
                      <rect x="46" y="22" width="8" height="5" rx="2" fill="#000" />
                      <path d="M 28 28 Q 50 24 72 28 L 66 78 L 34 78 Z" fill="#000" />
                      <path d="M 27 29 L 18 68 Q 16 72 19 72 L 26 68 L 32 40 Z" fill="#000" />
                      <path d="M 73 29 L 82 68 Q 84 72 81 72 L 74 68 L 68 40 Z" fill="#000" />
                      <path d="M 36 79 L 38 168 L 46 168 L 47 79 Z" fill="#000" />
                      <path d="M 53 79 L 54 168 L 62 168 L 64 79 Z" fill="#000" />
                    </svg>
                    <button
                      onClick={() => setShowPhotoModal(true)}
                      className="absolute top-3 right-3 z-10 px-2.5 py-1 bg-white/90 backdrop-blur-sm border border-black/10 rounded-full text-[10px] font-bold text-black/70 hover:text-black hover:bg-white shadow-sm transition-all flex items-center gap-1"
                    >
                      <Camera className="w-3 h-3" /> Try on your own photo
                    </button>
                  </>
                )}

                {isOverlay && outfit.items.length > 0 ? (
                  <div className="relative w-[300px] h-[500px]">
                    {outfit.items
                      .slice()
                      .sort((a, b) => a.z_index - b.z_index)
                      .map((item) => (
                        <PositionedItem key={item.id} item={item} />
                      ))}
                  </div>
                ) : slots.length > 0 ? (
                  <div className="flex flex-col items-center gap-4">
                    {slots.map((slot) => (
                      <motion.div
                        key={slot.role}
                        drag
                        dragConstraints={{ left: -120, right: 120, top: -80, bottom: 80 }}
                        whileHover={{ scale: 1.04, cursor: 'grab' }}
                        whileTap={{ scale: 0.98, cursor: 'grabbing' }}
                        className="bg-white border border-black/15 p-3 rounded-2xl shadow-md w-64 flex items-center gap-3"
                      >
                        <div className="w-10 h-10 rounded-xl bg-black/5 flex items-center justify-center shrink-0">
                          {slot.item?.imageUrl || slot.item?.image
                            ? <img src={slot.item.imageUrl || slot.item.image} alt={slot.item.name} className="w-full h-full object-contain" />
                            : <span className="font-bold text-xs">{slot.role[0]}</span>}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-[10px] font-bold text-black/40 uppercase">{slot.role}</p>
                          <p className="text-xs font-bold text-black truncate">{slot.item ? slot.item.name : 'Empty'}</p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-xs text-black/40">
                    {isOffline ? 'Backend offline — start FastAPI to view generated items.' : 'No items loaded for visualization.'}
                  </div>
                )}
              </>
            )}

            {missingSlots.length > 0 && (
              <div className="absolute bottom-3 left-3 right-3 text-center pointer-events-none">
                <p className="text-[10px] text-black/60 bg-white/80 backdrop-blur-sm rounded-full py-1 px-3 inline-block border border-black/10">
                  Missing: {missingSlots.map((s) => SLOT_LABELS[s] || s).join(', ')}
                </p>
              </div>
            )}
          </div>

          {/* Color Palette Bar */}
          {detectedColors.length > 0 && (
            <div className="bg-white/90 border border-black/15 rounded-2xl p-4 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-black flex items-center gap-1.5">
                  <Palette className="w-3.5 h-3.5" /> Outfit Color Harmony
                </span>
                <span className="text-[11px] font-medium text-black/50">{detectedColors.length} Tones Detected</span>
              </div>
              <div className="flex gap-2 flex-wrap">
                {detectedColors.map((col, i) => {
                  const sw = getColorSwatch(col)
                  return (
                    <div key={i} className="flex-1 min-w-[80px] py-1.5 px-3 rounded-lg border border-black/10 bg-black/5 text-center flex items-center gap-1.5 justify-center">
                      {sw && <span className="w-3 h-3 rounded-full border border-black/10 shrink-0" style={{ backgroundColor: sw }} />}
                      <span className="text-[11px] font-bold text-black capitalize truncate">{col}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* ── SIDEBAR ── */}
        <div className="lg:col-span-2 space-y-5">
          {/* Items from DB */}
          {isOverlay && outfit.items.length > 0 && (
            <div className="bg-white/90 border border-black/15 rounded-3xl p-5 shadow-sm space-y-3">
              <h3 className="text-xs font-extrabold text-black uppercase tracking-wider border-b border-black/10 pb-2">
                Outfit Items ({outfit.items.length})
              </h3>
              {outfit.items.map((item) => (
                <SidebarItem key={item.id} item={item} />
              ))}
            </div>
          )}

          {/* Stylist Analysis */}
          <div className="bg-white/90 border border-black/15 rounded-3xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-extrabold text-black uppercase tracking-wider border-b border-black/10 pb-3">
              Stylist Analysis
            </h3>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {tags.map((tag) => (
                  <span key={tag} className="px-2.5 py-1 bg-black/5 border border-black/10 rounded-full text-xs font-bold text-black">
                    #{tag}
                  </span>
                ))}
              </div>
            )}
            <p className="text-xs text-black/80 leading-relaxed font-medium">
              {description || 'Custom layered combination tailored for your selected style and weather.'}
            </p>
          </div>

          {/* IDM-VTON Quick Launch */}
          <div className="bg-gradient-to-br from-amber-50 to-amber-100/60 border border-amber-200 rounded-2xl p-4 space-y-2">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-600" />
              <span className="text-xs font-extrabold text-amber-900">IDM-VTON Try-On</span>
            </div>
            <p className="text-[11px] text-amber-800/80 leading-relaxed">
              Generate a photorealistic virtual try-on using IDM-VTON via HuggingFace. Upload your body photo first.
            </p>
            <button
              onClick={() => handleSwitchMode('ai')}
              className="w-full py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-xl text-xs font-bold transition-colors shadow"
            >
              ✨ Open IDM-VTON Mode
            </button>
          </div>

          {/* Actions */}
          <div className="space-y-2.5">
            <button
              onClick={() => onChangeClothing?.()}
              className="w-full py-2.5 border border-black rounded-xl font-semibold text-xs hover:bg-black/5 transition-colors"
            >
              Change Clothing
            </button>
            <button
              onClick={onGenerateAnother}
              className="w-full py-2.5 bg-black text-white rounded-xl font-semibold text-xs hover:bg-black/80 transition-colors"
            >
              Generate Another Outfit
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}