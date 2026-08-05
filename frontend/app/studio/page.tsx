"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppNav } from "@/components/layout/app-nav";
import { ImagePlaceholder } from "@/components/ui/image-placeholder";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Save, RotateCcw } from "lucide-react";
import { useWardrobe } from "@/hooks/use-wardrobe";
import { saveLook } from "@/lib/api/saved-looks";
import { visualizeOutfit } from "@/lib/api/visualization";

type Zone = "top" | "bottom" | "shoes";

export default function StudioPage() {
  const { items, refresh } = useWardrobe();
  const [zone, setZone] = React.useState<Zone>("top");
  
  // Keep track of the currently selected piece for each zone
  const [look, setLook] = React.useState<Record<Zone, string | null>>({
    top: null,
    bottom: null,
    shoes: null,
  });
  
  const [overlayItems, setOverlayItems] = React.useState<any[]>([]);
  const [saved, setSaved] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  const zones: { key: Zone; label: string }[] = [
    { key: "top", label: "TOP" },
    { key: "bottom", label: "BOTTOM" },
    { key: "shoes", label: "SHOES" },
  ];

  // Derive the options for the current zone from the wardrobe items
  const currentOptions = React.useMemo(() => {
    return items.filter((it) => {
      const cat = it.category.toLowerCase();
      const type = (it.type || "").toLowerCase();
      const tagsStr = (it.tags || []).join(" ").toLowerCase();
      const matchStr = `${cat} ${type} ${tagsStr}`;

      if (zone === "top") return matchStr.includes("top") || matchStr.includes("shirt") || matchStr.includes("sweater") || matchStr.includes("outerwear") || matchStr.includes("jacket") || matchStr.includes("dress");
      if (zone === "bottom") return matchStr.includes("bottom") || matchStr.includes("pant") || matchStr.includes("short") || matchStr.includes("skirt") || matchStr.includes("dress");
      if (zone === "shoes") return matchStr.includes("shoe") || matchStr.includes("footwear") || matchStr.includes("boot") || matchStr.includes("sneaker");
      return false;
    });
  }, [items, zone]);

  // When look changes, try to generate a visualization if we have at least one item
  React.useEffect(() => {
    const itemIds = [look.top, look.bottom, look.shoes].filter(Boolean) as string[];
    if (itemIds.length === 0) {
      setOverlayItems([]);
      return;
    }
    
    setLoading(true);
    visualizeOutfit(itemIds, "overlay")
      .then((res) => {
        if (res.items) setOverlayItems(res.items);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [look]);

  function selectPiece(id: string) {
    setLook((l) => ({ ...l, [zone]: id }));
    setSaved(false);
  }

  async function handleSave() {
    const itemIds = [look.top, look.bottom, look.shoes].filter(Boolean) as string[];
    if (itemIds.length === 0) return;
    
    setLoading(true);
    try {
      await saveLook("Studio Look", "CUSTOM", itemIds);
      setSaved(true);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-cream dark:bg-[#161611]">
      <AppNav />
      <div className="relative mx-auto max-w-5xl px-6 pb-24 pt-11 md:px-12">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <span className="font-mono text-[11.5px] font-semibold tracking-wide text-gold">BUILD A LOOK</span>
          <h1 className="mt-2 font-heading text-[clamp(30px,3.6vw,44px)] font-semibold text-ink dark:text-cream">Studio</h1>
          <p className="mb-7 mt-2 font-sans text-[15px] text-ink/60 dark:text-cream/60">
            Mix pieces from your wardrobe into a new look.
          </p>
        </motion.div>

        <div className="relative">
          {/* Focal preview */}
          <div className="relative mx-auto aspect-[3/4] max-w-md overflow-hidden rounded-2xl bg-card shadow-[0_20px_60px_rgba(30,30,30,0.12)] dark:bg-card/50 dark:shadow-[0_20px_60px_rgba(0,0,0,0.4)]">
            <AnimatePresence mode="wait">
              <motion.div
                key={`${look.top}-${look.bottom}-${look.shoes}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: loading ? 0.5 : 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="h-full w-full"
              >
                {overlayItems.length > 0 ? (
                  <div className="relative h-full w-full bg-cream-muted dark:bg-white/5">
                    {overlayItems.map((item, i) => (
                      <div
                        key={i}
                        className="absolute"
                        style={{
                          left: `${item.position?.x}%`,
                          top: `${item.position?.y}%`,
                          width: `${item.position?.width}%`,
                          height: `${item.position?.height}%`,
                          transform: 'translate(-50%, -50%)',
                          zIndex: item.z_index || 1,
                        }}
                      >
                        <img src={item.image_url} className="h-full w-full object-contain" alt="Garment overlay" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex h-full flex-col items-center justify-center p-8 text-center opacity-60">
                    <p className="font-mono text-xs tracking-wide">Select items to preview</p>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>

            {/* Floating control rail */}
            <div className="absolute bottom-4 left-1/2 flex -translate-x-1/2 items-center gap-2 rounded-full border border-white/20 bg-ink/80 px-3 py-2 shadow-xl backdrop-blur-md dark:bg-black/70">
              {zones.map((z) => (
                <button
                  key={z.key}
                  onClick={() => setZone(z.key)}
                  className={cn(
                    "rounded-full px-3 py-1.5 font-mono text-[10px] tracking-wide transition-colors",
                    zone === z.key ? "bg-gold text-ink" : "text-cream/70 hover:text-cream"
                  )}
                >
                  {z.label}
                </button>
              ))}
            </div>
          </div>

          {/* Piece picker — bottom sheet style on mobile */}
          <div className="mt-6 flex gap-3 overflow-x-auto pb-2 scrollbar-none">
            {currentOptions.length === 0 ? (
              <p className="py-4 text-center w-full font-sans text-xs text-ink/40 dark:text-cream/40">
                No items found for this category.
              </p>
            ) : (
              currentOptions.map((p) => (
                <motion.button
                  key={p.id}
                  whileTap={{ scale: 0.96 }}
                  onClick={() => selectPiece(p.id)}
                  className={cn(
                    "flex shrink-0 items-center gap-2.5 rounded-xl border bg-card p-2 shadow-sm transition-colors",
                    look[zone] === p.id
                      ? "border-gold ring-1 ring-gold/30"
                      : "border-ink/5 dark:border-cream/5"
                  )}
                >
                  <div className="h-12 w-12 overflow-hidden rounded-lg bg-cream-muted dark:bg-white/5">
                    {p.imageUrl ? (
                      <img src={p.imageUrl} alt={p.name} className="h-full w-full object-cover" />
                    ) : (
                      <ImagePlaceholder label={p.name.slice(0, 6)} />
                    )}
                  </div>
                  <span className="max-w-[100px] truncate text-left font-sans text-[12px] text-ink dark:text-cream">{p.name}</span>
                </motion.button>
              ))
            )}
          </div>

          {/* Floating actions */}
          <div className="mt-6 flex justify-center gap-3">
            <Button variant="secondary" size="sm" onClick={() => { setLook({ top: null, bottom: null, shoes: null }); setSaved(false); }}>
              <RotateCcw className="h-3.5 w-3.5" /> Reset
            </Button>
            <Button size="sm" onClick={handleSave} disabled={loading || (!look.top && !look.bottom && !look.shoes)}>
              <Save className="h-3.5 w-3.5" /> Save look
            </Button>
          </div>
          <AnimatePresence>
            {saved && (
              <motion.p
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-3 text-center font-sans text-xs text-forest dark:text-[#8fbfa4]"
              >
                Saved to your rail ✓
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
