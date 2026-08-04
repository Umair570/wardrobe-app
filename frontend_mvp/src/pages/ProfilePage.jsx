// src/pages/ProfilePage.jsx
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/ToastProvider'
import { supabase } from '../lib/supabase'

export default function ProfilePage({ onBack }) {
  const { user } = useAuth()
  const notify = useToast()

  const [avatarUrl, setAvatarUrl] = useState(
    user?.user_metadata?.avatar_url || null
  )
  const [fullName, setFullName] = useState(
    user?.user_metadata?.full_name || ''
  )
  const [avatarFile, setAvatarFile] = useState(null)
  const [saving, setSaving] = useState(false)

  const handleAvatarChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setAvatarFile(file)
      // Local preview
      setAvatarUrl(URL.createObjectURL(file))
    }
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)

    try {
      let finalAvatarUrl = avatarUrl

      // 1. Upload new picture to Supabase storage if selected
      if (avatarFile) {
        const fileExt = avatarFile.name.split('.').pop()
        const filePath = `avatars/${user.id}-${Date.now()}.${fileExt}`

        const { error: uploadError } = await supabase.storage
          .from('avatars')
          .upload(filePath, avatarFile, { upsert: true })

        if (uploadError) {
          // If bucket doesn't exist yet, fallback to base64 encoding for prototype persistence
          const reader = new FileReader()
          finalAvatarUrl = await new Promise((resolve) => {
            reader.onloadend = () => resolve(reader.result)
            reader.readAsDataURL(avatarFile)
          })
        } else {
          const { data: publicUrlData } = supabase.storage
            .from('avatars')
            .getPublicUrl(filePath)
          finalAvatarUrl = publicUrlData.publicUrl
        }
      }

      // 2. Persist metadata (Full Name & Avatar URL) in Supabase Auth User Metadata
      const { error: updateError } = await supabase.auth.updateUser({
        data: {
          full_name: fullName,
          avatar_url: finalAvatarUrl,
        },
      })

      if (updateError) throw updateError

      notify('Profile updated successfully!')
    } catch (err) {
      console.error('Failed to update profile:', err)
      notify(err.message || 'Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-black">User Profile</h1>
          <p className="text-sm text-black/60">Manage your personal info and avatar</p>
        </div>
        <button
          onClick={onBack}
          className="px-4 py-2 border border-black/15 text-black rounded-xl hover:bg-black/5 transition-colors text-sm font-medium"
        >
          ← Back to App
        </button>
      </div>

      <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-black/10 space-y-8">
        {/* Avatar Upload Section */}
        <div className="flex items-center gap-6 pb-6 border-b border-black/10">
          <div className="relative w-20 h-20 rounded-full overflow-hidden bg-black/10 flex items-center justify-center text-black font-bold text-2xl border border-black/15">
            {avatarUrl ? (
              <img src={avatarUrl} alt="User Avatar" className="w-full h-full object-cover" />
            ) : (
              user?.email?.[0]?.toUpperCase() || 'U'
            )}
          </div>

          <div>
            <label className="cursor-pointer inline-flex items-center px-4 py-2 bg-black text-white text-sm font-medium rounded-xl hover:bg-black/80 transition-colors shadow-sm">
              <span>Upload New Picture</span>
              <input type="file" accept="image/*" onChange={handleAvatarChange} className="hidden" />
            </label>
            <p className="text-xs text-black/50 mt-1">JPG, PNG or WEBP (max. 5MB)</p>
          </div>
        </div>

        {/* Profile Details Form */}
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-black/70 mb-1">Email Address</label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              className="w-full p-3 border border-black/10 rounded-xl bg-black/5 text-black/60 text-sm cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-black/70 mb-1">Full Name</label>
            <input
              type="text"
              placeholder="Your Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full p-3 border border-black/15 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-black text-sm"
            />
          </div>

          <div className="pt-4 flex items-center justify-end border-t border-black/10">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 bg-black text-white font-medium text-sm rounded-xl hover:bg-black/80 transition-colors shadow-sm disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}