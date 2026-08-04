// src/components/Nav.jsx
import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Nav({ onOpenSidebar, onNavigate }) {
  const { user, logout } = useAuth()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const menuRef = useRef(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const initial = user?.email?.[0]?.toUpperCase() || 'U'

  return (
    <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-ink/10 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenSidebar}
          className="p-2 rounded-lg hover:bg-ink/5 text-ink/70 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <span className="font-bold text-ink">AI Wardrobe</span>
      </div>

      {/* User Avatar & Dropdown */}
<div className="relative" ref={menuRef}>
  <button
    onClick={() => setDropdownOpen((prev) => !prev)}
    className="w-9 h-9 rounded-full bg-blue-100 text-blue-600 font-bold text-sm flex items-center justify-center border border-blue-200 hover:ring-2 hover:ring-blue-400 transition-all overflow-hidden"
  >
    {user?.user_metadata?.avatar_url ? (
      <img 
        src={user.user_metadata.avatar_url} 
        alt="Profile" 
        className="w-full h-full object-cover" 
      />
    ) : (
      initial
    )}
  </button>

        {dropdownOpen && (
          <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-ink/10 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
            <div className="px-4 py-2 border-b border-ink/10">
              <p className="text-xs text-ink/50 font-medium">Signed in as</p>
              <p className="text-sm font-semibold text-ink truncate">{user?.email}</p>
            </div>

            <div className="py-1">
              <button
                onClick={() => {
                  setDropdownOpen(false)
                  onNavigate('profile')
                }}
                className="w-full text-left px-4 py-2 text-sm text-ink/80 hover:bg-ink/5 flex items-center gap-2 transition-colors"
              >
                <span>👤</span> View & Edit Profile
              </button>
              
              <button
                onClick={() => {
                  setDropdownOpen(false)
                  onNavigate('wardrobe')
                }}
                className="w-full text-left px-4 py-2 text-sm text-ink/80 hover:bg-ink/5 flex items-center gap-2 transition-colors"
              >
                <span>👗</span> My Wardrobe
              </button>
            </div>

            <div className="border-t border-ink/10 pt-1">
              <button
                onClick={() => {
                  setDropdownOpen(false)
                  logout()
                }}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 transition-colors font-medium"
              >
                <span>🚪</span> Sign Out
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}