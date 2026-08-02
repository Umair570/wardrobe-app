import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Layers, RefreshCw, Sparkles, Move, Palette, Camera, Image as ImageIcon } from 'lucide-react'
import BackLink from '../components/BackLink'
import UserBodyPhotoUpload from '../components/UserBodyPhotoUpload'
import { SLOT_LABELS } from '../utils/outfitSlots'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function getImageUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  const cleanBase = API_BASE.replace(/\/$/, '')
  const cleanPath = url.startsWith('/') ? url : `/${url}`
  return `${cleanBase}${cleanPath}`
}

export default function OutfitVisualizationPage({
  outfit,
  userBodyPhoto,
  onSaveUserBodyPhoto,
  onBack,
  onChangeClothing,
  onGenerateAnother,
}) {
  const [showPhotoModal, setShowPhotoModal] = useState(false)
  const [activeMode, setActiveMode] = useState('overlay') // 'overlay' | 'ai'
  const [aiLoading, setAiLoading] = useState(false)
  const [aiImage, setAiImage] = useState(outfit?.ai_image_url || '')

  if (!outfit) return null

  // Backend Overlay state detection
  const isOverlay = outfit.mode === 'overlay' && Array.isArray(outfit.items)
  const isOffline = outfit.mode === 'offline'
  
  // Slot tracking
  const { slots = [], tags = [], description = '' } = outfit
  const filledSlots = isOverlay ? new Set(outfit.items.map((i) => i.category)) : new Set()
  const missingSlots = ['top', 'bottom', 'shoes'].filter((s) => !filledSlots.has(s))

  // Interactive Canvas Reset Key
  const [resetKey, setResetKey] = useState(0)

  // Color harmony detection
  const detectedColors = isOverlay
    ? outfit.items.map((item) => item.color || item.type).filter(Boolean)
    : slots.filter((s) => s.item?.color).map((s) => s.item.color)

  const handleResetCanvas = () => setResetKey((prev) => prev + 1)

  const handleSwitchMode = async (mode) => {
    setActiveMode(mode)
    if (mode === 'ai' && !aiImage && isOverlay && outfit.items.length > 0) {
      setAiLoading(true)
      try {
        const itemIds = outfit.items.map((i) => i.id)
        const res = await postVisualization(itemIds, 'ai')
        if (res.ai_image_url) {
          setAiImage(res.ai_image_url)
        }
      } catch (err) {
        console.error('Gemini AI generation error:', err)
      } finally {
        setAiLoading(false)
      }
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
      {/* Photo Upload Modal */}
      {showPhotoModal && (
        <UserBodyPhotoUpload
          currentPhoto={userBodyPhoto}
          onSavePhoto={onSaveUserBodyPhoto}
          onClose={() => setShowPhotoModal(false)}
        />
      )}

      {/* Top Navigation & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <BackLink onClick={onBack} label="Back to Wardrobe" />
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setShowPhotoModal(true)}
            className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border text-xs font-semibold shadow-sm transition-all ${
              userBodyPhoto
                ? 'border-emerald-500 bg-emerald-50 text-emerald-800'
                : 'border-black/15 bg-white text-black hover:bg-black/5'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            {userBodyPhoto ? '📸 My Body Photo (Active)' : '📸 Upload My Body Photo'}
          </button>

          <button
            onClick={handleResetCanvas}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-black/15 bg-white text-xs font-semibold text-black shadow-sm hover:bg-black/5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5 text-black" />
            Reset Layout
          </button>
          <button
            onClick={onGenerateAnother}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-black text-xs font-semibold text-white shadow-md hover:bg-black/80 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            Generate Another
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-5 gap-8 items-start">
        {/* ======================================================== */}
        {/* LEFT/CENTER: YOUR INTERACTIVE STAGE (3 Cols)              */}
        {/* ======================================================== */}
        <div className="lg:col-span-3 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex bg-black/5 p-1 rounded-xl border border-black/10">
              <button
                onClick={() => handleSwitchMode('overlay')}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                  activeMode === 'overlay' ? 'bg-white text-black shadow-sm' : 'text-black/60 hover:text-black'
                }`}
              >
                📸 2D Canvas Overlay
              </button>
              <button
                onClick={() => handleSwitchMode('ai')}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
                  activeMode === 'ai' ? 'bg-black text-white shadow-sm' : 'text-black/60 hover:text-black'
                }`}
              >
                <Sparkles className="w-3 h-3 text-amber-400" />
                ✨ Gemini AI Model Try-On
              </button>
            </div>
            <span className="text-[11px] font-medium text-black/50 flex items-center gap-1">
              <Move className="w-3 h-3" /> Drag items to test fit
            </span>
          </div>

          {/* Canvas Box */}
          <div
            key={resetKey}
            className="relative w-full h-[520px] rounded-3xl border border-black/15 bg-gradient-to-b from-gray-50 to-gray-100/60 shadow-inner overflow-hidden flex items-center justify-center p-6"
          >
            {activeMode === 'ai' ? (
              <div className="relative w-full h-full flex flex-col items-center justify-center">
                {aiLoading ? (
                  <div className="text-center space-y-3">
                    <Sparkles className="w-8 h-8 text-amber-500 animate-spin mx-auto" />
                    <p className="text-xs font-extrabold text-black">Gemini AI is generating your photorealistic try-on...</p>
                    <p className="text-[10px] text-black/50">Synthesizing lighting, texture, and model fit</p>
                  </div>
                ) : aiImage ? (
                  <img src={aiImage} alt="Gemini AI generated outfit try-on" className="w-full h-full object-contain rounded-2xl shadow-md" />
                ) : (
                  <div className="text-center space-y-2">
                    <Sparkles className="w-8 h-8 text-black/30 mx-auto" />
                    <p className="text-xs font-semibold text-black/60">Click below to generate with Gemini AI</p>
                    <button
                      onClick={() => handleSwitchMode('ai')}
                      className="px-4 py-2 bg-black text-white text-xs font-bold rounded-xl shadow"
                    >
                      ✨ Generate Gemini AI Try-On
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                {/* Backdrop: User's Body Photo OR Vector Mannequin Guide */}
                {userBodyPhoto ? (
                  <img
                    src={userBodyPhoto}
                    alt="User Body Photo Template"
                    className="absolute inset-0 w-full h-full object-contain pointer-events-none opacity-90 select-none p-2"
                  />
                ) : (
                  <>
                    <svg
                      viewBox="0 0 100 200"
                      className="absolute inset-0 w-full h-full pointer-events-none select-none opacity-20"
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
                      <Camera className="w-3 h-3 text-black" />
                      Try on your own photo
                    </button>
                  </>
                )}

                {/* Render Backend Overlay Items if present */}
                {isOverlay && outfit.items.length > 0 ? (
                  <div className="relative w-[280px] h-[500px]">
                    {outfit.items
                      .slice()
                      .sort((a, b) => a.z_index - b.z_index)
                      .map((item) => (
                        <motion.img
                          key={item.id}
                          drag
                          dragConstraints={{ left: -100, right: 100, top: -100, bottom: 100 }}
                          whileHover={{ scale: 1.05, cursor: 'grab' }}
                          whileTap={{ scale: 0.98, cursor: 'grabbing' }}
                          src={getImageUrl(item.image_url)}
                          alt={item.type}
                          style={{
                            position: 'absolute',
                            left: `${item.position.x - item.position.width / 2}%`,
                            top: `${item.position.y - item.position.height / 2}%`,
                            width: `${item.position.width}%`,
                            height: `${item.position.height}%`,
                            zIndex: item.z_index,
                            objectFit: 'contain',
                            filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.15))',
                          }}
                        />
                      ))}
                  </div>
                ) : slots.length > 0 ? (
                  /* Fallback slot drag items */
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
                          {slot.item?.imageUrl || slot.item?.image ? (
                            <img src={slot.item.imageUrl || slot.item.image} alt={slot.item.name} className="w-full h-full object-contain" />
                          ) : (
                            <span className="font-bold text-xs">{slot.role[0]}</span>
                          )}
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
              <div className="absolute bottom-3 left-3 right-3 text-center">
                <p className="text-[10px] text-black/60 bg-white/80 backdrop-blur-sm rounded-full py-1 px-3 inline-block border border-black/10">
                  Missing: {missingSlots.map((s) => SLOT_LABELS[s] || s).join(', ')}
                </p>
              </div>
            )}
          </div>

          {/* Color Palette Harmony Bar */}
          {detectedColors.length > 0 && (
            <div className="bg-white/90 border border-black/15 rounded-2xl p-4 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-black flex items-center gap-1.5">
                  <Palette className="w-3.5 h-3.5" /> Outfit Color Harmony
                </span>
                <span className="text-[11px] font-medium text-black/50">
                  {detectedColors.length} Tones Detected
                </span>
              </div>
              <div className="flex gap-2">
                {detectedColors.map((col, i) => (
                  <div key={i} className="flex-1 py-1.5 px-3 rounded-lg border border-black/10 bg-black/5 text-center">
                    <span className="text-[11px] font-bold text-black capitalize block truncate">{col}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ======================================================== */}
        {/* RIGHT: DETAILS & CONTROLS (2 Columns)                   */}
        {/* ======================================================== */}
        <div className="lg:col-span-2 space-y-6">
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

          <div className="space-y-2.5">
            <button onClick={() => onChangeClothing && onChangeClothing()} className="w-full py-2.5 border border-black rounded-xl font-semibold text-xs hover:bg-black/5 transition-colors">
              Change Clothing
            </button>
            <button onClick={onGenerateAnother} className="w-full py-2.5 bg-black text-white rounded-xl font-semibold text-xs hover:bg-black/80 transition-colors">
              Generate Another Outfit
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}