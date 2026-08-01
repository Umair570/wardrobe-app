# AI Wardrobe — Frontend

Started from the 8-screen wireframe-matched build, then restyled with a
modern indigo/slate/amber/coral palette and extended with many features eg authentication, a left sidebar navigation drawer, a "Most Viewed / Most Worn"
stats carousel on Home, and a floating chatbot dock.

## Run it

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production build into dist/
```

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
- Sidebar + bottom nav cover navigation on small screens.
- Chatbot button repositions above the bottom nav on mobile so nothing
  overlaps.
