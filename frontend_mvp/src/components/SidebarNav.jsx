import { useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const LINKS = [
  { key: 'home', label: 'Home' },
  { key: 'upload', label: 'Upload Item' },
  { key: 'wardrobe', label: 'View Wardrobe' },
  { key: 'stylist', label: 'AI Stylist' },
  { key: 'recommended', label: 'Recommended Outfits' },
]

export default function SidebarNav({ open, page, onNavigate, onClose }) {
  const { logout } = useAuth()

  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  const go = (key) => {
    onNavigate(key)
    onClose()
  }

  return (
    <>
      <div
        className={`fixed inset-0 z-40 bg-ink/40 backdrop-blur-[1px] transition-opacity duration-200
          ${open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}
        `}
        onClick={onClose}
        aria-hidden="true"
      />

      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-white shadow-pop transition-transform duration-[250ms] ease-out
          ${open ? 'translate-x-0' : '-translate-x-full'}
        `}
        role="dialog"
        aria-label="Navigation"
      >
        <div className="h-16 flex items-center justify-between px-5 border-b border-ink/8">
          <span className="font-display font-semibold tracking-tight">Menu</span>
          <button onClick={onClose} aria-label="Close menu" className="text-ink/40 hover:text-ink text-xl leading-none">
            ×
          </button>
        </div>

        <nav className="p-3">
          {LINKS.map((link) => (
            <button
              key={link.key}
              onClick={() => go(link.key)}
              className={`w-full text-left px-3 py-3 rounded-lg text-sm font-medium transition-colors flex items-center justify-between
                ${page === link.key ? 'bg-indigo/10 text-indigo' : 'text-ink/70 hover:bg-panel hover:text-ink'}
              `}
            >
              {link.label}
              {page === link.key && <span className="w-1.5 h-1.5 rounded-full bg-indigo" />}
            </button>
          ))}

          <div className="my-3 border-t border-ink/8" />

          <button
            onClick={() => {
              logout()
              onClose()
            }}
            className="w-full text-left px-3 py-3 rounded-lg text-sm font-medium text-coral hover:bg-coral/5 transition-colors"
          >
            Log Out
          </button>
        </nav>
      </aside>
    </>
  )
}
