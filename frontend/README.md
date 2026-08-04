# Wardrobe.AI — Next.js frontend

Production-ready Next.js 15 (App Router) frontend for the Wardrobe.AI product, matching the HTML design references built earlier in this project.

## Stack
- Next.js 15 · React 19 · TypeScript
- Tailwind CSS (custom cream/charcoal/forest/gold palette, dark mode via `class` strategy)
- shadcn/ui-style primitives (hand-rolled, no CLI dependency): Button, Card, Input, Badge, Avatar, Switch, Separator
- Framer Motion for entrance/hover/page transitions
- Lucide React icons
- React Context for theme + wardrobe state; a thin `lib/api` layer with mock fallbacks

## Getting started
```bash
npm install
npm run dev
```
Visit `http://localhost:3000`.

## Folder structure
```
app/
  layout.tsx            root layout: fonts, ThemeProvider, WardrobeProvider
  page.tsx               /  — marketing landing page
  dashboard/page.tsx      /dashboard
  wardrobe/page.tsx       /wardrobe — closet grid
  upload/page.tsx         /upload
  stylist/page.tsx        /stylist — AI stylist chat
  studio/page.tsx         /studio — outfit builder
  try-on/page.tsx         /try-on
  saved/page.tsx          /saved
  profile/page.tsx        /profile
  auth/page.tsx           /auth — login/register toggle
components/
  ui/                    shadcn-style primitives + ImagePlaceholder
  layout/                AppNav, SiteNav, Footer, ThemeToggle
  wardrobe/               ClothingCard
  dashboard/              AiSearchBar, RecommendationCard, ActivityTimeline
  stylist/                ChatBubble, TypingIndicator
context/
  theme-provider.tsx      light/dark theme context, persisted to localStorage
  wardrobe-provider.tsx   closet items + favorites context
hooks/
  use-wardrobe.ts, use-media-query.ts, use-local-storage.ts
lib/
  api/                   client.ts (fetch wrapper), wardrobe.ts, stylist.ts — all fall back
                         to mock data until NEXT_PUBLIC_API_BASE_URL is set
  utils.ts               cn() class merge helper
types/
  index.ts               shared domain types
```

## Connecting a real backend
Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local`. Every function in `lib/api/*` calls
that base URL once set; until then the app runs entirely on local mock data, so the
UI is fully explorable standalone.

## Design tokens
- `cream` #F8F7F4 / `cream-muted` #EFE9DF — light backgrounds
- `ink` #1E1E1E — text / dark-mode surface base
- `forest` #2F4F3F — primary actions, active states
- `gold` #C9A45C — highlights, active nav indicator, kickers
- Fonts: Cormorant Garamond (display/headings), Manrope (body/UI), JetBrains Mono (labels/meta)

## Notes
- `ImagePlaceholder` stands in for garment photography / user photos everywhere;
  swap in `next/image` once real assets are available.
- Mock data lives next to each `lib/api/*` module — replace with real fetches once
  the backend is live; component code doesn't need to change.
