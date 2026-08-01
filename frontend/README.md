# AI Wardrobe — Frontend (wireframe pages + auth, sidebar nav, stats, chatbot)

Started from the 8-screen wireframe-matched build, then restyled with a
modern indigo/slate/amber/coral palette and extended with four features:
authentication, a left sidebar navigation drawer, a "Most Viewed / Most Worn"
stats carousel on Home, and a floating chatbot dock.

## Run it

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production build into dist/
```

## What changed from the wireframe-only version

### Design system restyle
- `tailwind.config.js` / `src/index.css` — same class names as before
  (`ink`, `soft`, `panel`, `.eyebrow`, `.tag`, `.btn-primary`, `.field`,
  etc.) now resolve to the modern palette instead of pure monochrome:
  - Slate `#1E293B` (primary text/dark surfaces)
  - Indigo `#3B82F6` (primary actions/links)
  - Amber `#F59E0B` (secondary accent, `.btn-accent`)
  - Coral `#EF4444` (destructive actions/errors)
  - Canvas `#F8FAFC` (background)
  - Type: Space Grotesk (headings), Inter (body), IBM Plex Mono (data labels)
  - Rounded corners, shadows, and hover/active micro-interactions added
    throughout (cards lift on hover, buttons press on click, etc.)
- Because pages used semantic class names rather than raw colors, this
  restyle didn't require editing every page individually — just the design
  tokens and shared component classes.

### Feature 1 — Authentication
- `src/api/authApi.js` — mock signup/login/session, **plaintext,
  localStorage-only, explicitly not production-safe** (flagged in the file).
- `src/context/AuthContext.jsx` — `useAuth()` hook.
- `src/pages/AuthPage.jsx` — Login/Sign Up tab toggle, Remember Me,
  Terms & Conditions checkbox gating signup.
- `src/App.jsx` gates the whole app behind this — no session, no wardrobe.

### Feature 2 — Sidebar navigation
- `src/components/SidebarNav.jsx` — slide-in drawer (Home, Upload Item,
  View Wardrobe, AI Stylist, Recommended Outfits, Log Out), triggered by a
  menu icon in `src/components/Nav.jsx` (now a slim top bar instead of
  horizontal tabs).
- `src/components/BottomNav.jsx` — mobile-only fixed bottom bar (Home,
  Wardrobe, floating "+" add button, Menu) per the mobile responsiveness
  requirement; desktop uses the sidebar only.

### Feature 3 — Stats carousel
- `src/data/mockData.js` — every item now has `viewCount` / `wearCount`.
- `src/components/StatsCarousel.jsx` — auto-advancing banner on Home
  (Most Viewed / Most Worn / Recently Added), manual prev/next + dot
  indicators, pauses on hover/focus, **respects `prefers-reduced-motion`**.

### Feature 4 — Chatbot dock
- `src/components/ChatbotDock.jsx` — floating button, bottom-right (raised
  above the mobile bottom nav on small screens), opens a chat panel.
- `src/api/chatbotApi.js` — the **only file your partner needs to edit**.
  `sendMessage(message, { history, wardrobeItems })` is currently a mock
  that delegates to the same rule-based responder as the full AI Stylist
  page; swap its body for the real backend call.
- Decision made explicitly (see comment in `App.jsx`): the full "AI Stylist"
  page was **kept**, reachable from the sidebar and via the dock's "Expand"
  button — not removed — since Recommended Outfits and Outfit Visualization
  both link through it.

### Toast notifications
- `src/components/ToastProvider.jsx` — `useToast()` hook, wired into item
  upload ("Item added successfully"), item removal, and outfit save.

## Mobile responsiveness
- Sidebar + bottom nav cover navigation on small screens; horizontal tabs
  removed entirely.
- Wardrobe grid: 2 columns on mobile → 3 on tablet → 4 on desktop.
- Chatbot button repositions above the bottom nav on mobile so nothing
  overlaps.

## Known gaps / honest notes
- Auth is a mock. Do not ship it as-is — see the comment block at the top
  of `authApi.js`.
- The chatbot dock's replies are a placeholder rule-based mock, same as the
  existing AI Stylist page — not real AI.
