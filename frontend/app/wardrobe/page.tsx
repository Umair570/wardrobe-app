"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ChevronDown } from "lucide-react";
import { AppNav } from "@/components/layout/app-nav";
import { ClothingCard } from "@/components/wardrobe/clothing-card";
import { ItemDetailsModal } from "@/components/wardrobe/item-details-modal";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useWardrobe } from "@/hooks/use-wardrobe";
import { cn } from "@/lib/utils";

export default function WardrobePage() {
  const { items, favorites, toggleFavorite, removeItem, loading } = useWardrobe();
  const [search, setSearch] = React.useState("");
  const [selectedItem, setSelectedItem] = React.useState<any>(null);
  const [filtersOpen, setFiltersOpen] = React.useState(false);
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => setMounted(true), []);

  const filtered = items.filter((it) => it.name.toLowerCase().includes(search.toLowerCase()));
  const showSkeleton = !mounted || loading;

  return (
    <div className="min-h-screen bg-cream dark:bg-[#161611]">
      <AppNav />
      <div className="mx-auto max-w-6xl px-6 pb-24 pt-11 md:px-12">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <span className="font-mono text-[11.5px] font-semibold tracking-wide text-gold">
            {items.length} PIECES ON THE RAIL
          </span>
          <h1 className="mt-2 font-heading text-[clamp(30px,3.6vw,44px)] font-semibold text-ink dark:text-cream">
            My Wardrobe
          </h1>
          <p className="mt-2 font-sans text-[15px] text-ink/60 dark:text-cream/60">
            Tap a card to unclip it from the rail and start a look.
          </p>
        </motion.div>

        <div className="relative mt-7">
          <Search className="pointer-events-none absolute left-5 top-1/2 h-[15px] w-[15px] -translate-y-1/2 text-ink/40" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="SEARCH GARMENTS"
            className="h-auto rounded-md py-3.5 pl-11 font-mono text-xs uppercase tracking-wide shadow-[0_4px_16px_rgba(30,30,30,0.05)]"
          />
        </div>

        <div className="mt-3.5">
          <button
            onClick={() => setFiltersOpen((o) => !o)}
            className="mb-2 flex items-center gap-1 font-mono text-[11px] tracking-wide text-ink/50 dark:text-cream/50"
          >
            FILTERS <ChevronDown className={cn("h-3 w-3 transition-transform", filtersOpen && "rotate-180")} />
          </button>
          <AnimatePresence>
            {filtersOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                className="overflow-hidden"
              >
                <div className="flex flex-wrap gap-3 pb-2">
                  {["CATEGORY", "COLOR", "SEASON"].map((label) => (
                    <Button key={label} variant="secondary" size="sm" className="font-mono text-[11.5px] tracking-wide">
                      {label} <ChevronDown className="h-3 w-3" />
                    </Button>
                  ))}
                  <Button size="sm" className="ml-auto font-mono text-[11.5px] tracking-wide">
                    SORT: NEWEST <ChevronDown className="h-3 w-3" />
                  </Button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="relative my-9 h-0.5 bg-[repeating-linear-gradient(90deg,rgba(30,30,30,0.22)_0_6px,transparent_6px_14px)] dark:bg-[repeating-linear-gradient(90deg,rgba(248,247,244,0.15)_0_6px,transparent_6px_14px)]">
          <span className="absolute -top-1 left-0 h-2.5 w-2.5 bg-gold" />
          <span className="absolute -top-1 right-0 h-2.5 w-2.5 bg-gold" />
        </div>

        <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
          {showSkeleton
            ? Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="space-y-3">
                  <Skeleton className="aspect-[3/4] w-full rounded-lg" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              ))
            : filtered.map((item, i) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 12, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ delay: i * 0.04, type: "spring", stiffness: 280, damping: 26 }}
                >
                  <ClothingCard
                    item={item}
                    favorited={!!favorites[item.id]}
                    onToggleFavorite={() => toggleFavorite(item.id)}
                    onDelete={() => removeItem(item.id)}
                    onClick={() => setSelectedItem(item)}
                    showColorDot
                  />
                </motion.div>
              ))}
        </div>

        <ItemDetailsModal item={selectedItem} onClose={() => setSelectedItem(null)} />
      </div>
    </div>
  );
}
