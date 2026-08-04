const ITEMS = [
  { key: 'home', label: 'Home' },
  { key: 'wardrobe', label: 'Wardrobe' },
]

export default function BottomNav({ page, onNavigate, onAdd, onOpenSidebar }) {
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-30 bg-white border-t border-ink/10 pb-[env(safe-area-inset-bottom)]">
      <div className="flex items-center justify-around h-16">
        {ITEMS.map((item) => (
          <button
            key={item.key}
            onClick={() => onNavigate(item.key)}
            className={`flex flex-col items-center gap-1 flex-1 h-full justify-center ${
              page === item.key ? 'text-indigo' : 'text-ink/45'
            }`}
          >
            <span className="text-[11px] font-medium">{item.label}</span>
          </button>
        ))}

        <button
          onClick={onAdd}
          className="w-12 h-12 -mt-6 rounded-full bg-indigo text-white flex items-center justify-center shadow-pop active:scale-95 transition-transform"
          aria-label="Add item"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M9 1v16M1 9h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </button>

        <button onClick={onOpenSidebar} className="flex flex-col items-center gap-1 flex-1 h-full justify-center text-ink/45">
          <span className="text-[11px] font-medium">Menu</span>
        </button>
      </div>
    </nav>
  )
}
