import React, { useState } from 'react'
import { Camera, Upload, X, Check } from 'lucide-react'

export default function UserBodyPhotoUpload({ currentPhoto, onSavePhoto, onClose }) {
  const [preview, setPreview] = useState(currentPhoto || '')

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      setPreview(reader.result)
    }
    reader.readAsDataURL(file)
  }

  const handleSave = () => {
    onSavePhoto(preview)
    onClose()
  }

  const handleClear = () => {
    setPreview('')
    onSavePhoto('')
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-5 animate-fade-slide-in">
        <div className="flex items-center justify-between border-b border-black/10 pb-3">
          <div className="flex items-center gap-2">
            <Camera className="w-5 h-5 text-black" />
            <h3 className="font-extrabold text-base text-black">My Body Photo Template</h3>
          </div>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-black/5 text-black/60 hover:text-black">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-black/70 leading-relaxed">
          Upload a full-body photo of yourself. Your clothes will be overlaid directly onto your photo so you can preview outfits on your real body!
        </p>

        {/* Photo Preview Box */}
        <div className="relative w-full aspect-[3/4] max-h-72 rounded-2xl border-2 border-dashed border-black/20 bg-black/5 flex flex-col items-center justify-center overflow-hidden">
          {preview ? (
            <img src={preview} alt="User body preview" className="w-full h-full object-contain" />
          ) : (
            <div className="text-center p-6 space-y-2">
              <Upload className="w-8 h-8 text-black/40 mx-auto" />
              <p className="text-xs font-semibold text-black/60">Click below to upload your photo</p>
              <p className="text-[10px] text-black/40">PNG, JPG, or JPEG (Full-body preferred)</p>
            </div>
          )}
        </div>

        {/* Upload Button */}
        <label className="w-full py-2.5 px-4 bg-black/5 hover:bg-black/10 border border-black/15 rounded-xl font-bold text-xs text-black flex items-center justify-center gap-2 cursor-pointer transition-colors">
          <Upload className="w-4 h-4" />
          {preview ? 'Change Selected Photo' : 'Choose Photo File'}
          <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
        </label>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          {preview && (
            <button
              onClick={handleClear}
              className="py-2.5 px-4 border border-red-200 text-red-600 rounded-xl font-semibold text-xs hover:bg-red-50 transition-colors"
            >
              Remove Photo
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={!preview && !currentPhoto}
            className="flex-1 py-2.5 px-4 bg-black hover:bg-black/80 disabled:opacity-40 text-white rounded-xl font-bold text-xs shadow-md flex items-center justify-center gap-1.5 transition-colors"
          >
            <Check className="w-4 h-4" />
            Use for Visualization
          </button>
        </div>
      </div>
    </div>
  )
}
