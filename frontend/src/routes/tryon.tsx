import { createFileRoute, Link } from "@tanstack/react-router";
import { motion, AnimatePresence } from "motion/react";
import { useState, useRef, useEffect } from "react";
import { ArrowLeft, Upload, Wand2, Sparkles, User, Camera, Plus, Check } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { useProfile, useUploadBodyPhoto } from "@/hooks/useProfile";
import { useWardrobe } from "@/hooks/useWardrobe";
import { generateTryOn } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { WardrobeItem } from "@/lib/types";

export const Route = createFileRoute("/tryon")({
  head: () => ({
    meta: [
      { title: "Virtual Try-On — Atelier" },
      { name: "description", content: "Mix and match outfits. Upload your photo and let the AI dress you." },
    ],
  }),
  component: TryOnPage,
});

const LAY_MAP: Record<string, string> = {
  shirt: "top", sweater: "top", suit: "top", pants: "bottom",
  shorts: "bottom", skirt: "bottom", dress: "dress", shoes: "shoes", jacket: "outerwear"
};

function TryOnPage() {
  const { data: profile } = useProfile();
  const { data: items = [] } = useWardrobe();
  const uploadMutation = useUploadBodyPhoto();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [resultImage, setResultImage] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const hasBodyPhoto = Boolean(profile?.body_photo_url);

  // Auto-pick an initial outfit once items load (only if none selected)
  useEffect(() => {
    if (items.length > 0 && selectedIds.size === 0) {
      const newSelection = new Set<string>();
      const seenSlots = new Set<string>();

      for (const item of items) {
        if (!item.category) continue;
        const cat = item.category.toLowerCase();
        const slot = LAY_MAP[cat] || cat;

        if (!seenSlots.has(slot) && slot !== "bag" && slot !== "accessory" && newSelection.size < 4) {
          if (slot === "dress" && (seenSlots.has("top") || seenSlots.has("bottom"))) continue;
          if ((slot === "top" || slot === "bottom") && seenSlots.has("dress")) continue;
          seenSlots.add(slot);
          newSelection.add(item.id);
        }
      }
      setSelectedIds(newSelection);
    }
  }, [items, selectedIds.size]);

  const toggleItem = (item: WardrobeItem) => {
    const next = new Set(selectedIds);
    if (next.has(item.id)) {
      next.delete(item.id);
    } else {
      // Auto-deselect conflicting items in the same slot
      const cat = item.category?.toLowerCase() || "";
      const slot = LAY_MAP[cat] || cat;

      // Clear items sharing the same slot
      for (const id of Array.from(next)) {
        const existing = items.find(i => i.id === id);
        if (existing) {
          const eCat = existing.category?.toLowerCase() || "";
          const eSlot = LAY_MAP[eCat] || eCat;
          if (eSlot === slot) next.delete(id);
          // Handle Top/Bottom vs Dress conflicts
          if (slot === "dress" && (eSlot === "top" || eSlot === "bottom")) next.delete(id);
          if ((slot === "top" || slot === "bottom") && eSlot === "dress") next.delete(id);
        }
      }
      next.add(item.id);
    }
    setSelectedIds(next);
  };

  const previewItems = items.filter(i => selectedIds.has(i.id));

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  }

  async function handleGenerate() {
    if (!hasBodyPhoto || previewItems.length === 0) return;
    setGenerating(true);
    setResultImage(null);
    try {
      const res = await generateTryOn(Array.from(selectedIds), profile!.body_photo_url!);
      if (res.ai_image_url) {
        setResultImage(res.ai_image_url);
      }
    } catch (err: any) {
      console.error(err);
      alert(err.message || "Failed to generate try-on.");
    } finally {
      setGenerating(false);
      setGenerated(true);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="flex items-center gap-4">
          <Link
            to="/wardrobe"
            className="flex items-center gap-2 rounded-full border border-border px-4 py-2 text-xs font-bold uppercase tracking-wider text-muted-foreground transition-colors hover:border-forest hover:text-forest"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Wardrobe
          </Link>
        </div>
        <div className="mt-6">
          <PageHeader subtitle="Mix and match your digital garments" title="Virtual Try-On" />
        </div>

        <div className="mt-10 grid gap-10 lg:grid-cols-2">
          {/* ── Left: Body Photo ── */}
          <div className="flex flex-col gap-6">
            <div>
              <p className="mb-4 text-[0.62rem] font-bold uppercase tracking-[0.28em] text-muted-foreground">
                Your Avatar Photo
              </p>
              {hasBodyPhoto ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="relative overflow-hidden rounded-[2rem] border border-border shadow-luxe bg-secondary/10"
                >
                  <img
                    src={profile!.body_photo_url!}
                    alt="Your avatar"
                    className="w-full object-contain"
                    style={{ maxHeight: "600px" }}
                  />
                  <div className="absolute bottom-4 right-4 flex gap-2">
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="flex items-center gap-2 rounded-full bg-ink/80 px-4 py-2 text-xs font-bold uppercase tracking-wider text-beige backdrop-blur-sm transition-colors hover:bg-ink"
                    >
                      <Camera className="h-3.5 w-3.5" /> Change Photo
                    </button>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  onClick={() => fileInputRef.current?.click()}
                  className="flex min-h-[400px] cursor-pointer flex-col items-center justify-center gap-5 rounded-[2rem] border-2 border-dashed border-border transition-all hover:border-forest/50 hover:bg-secondary/20"
                >
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-secondary">
                    {uploadMutation.isPending ? (
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-forest border-t-transparent" />
                    ) : (
                      <User className="h-7 w-7 text-muted-foreground" />
                    )}
                  </div>
                  <div className="text-center">
                    <p className="font-semibold text-foreground">
                      {uploadMutation.isPending ? "Uploading…" : "Upload clear body photo"}
                    </p>
                    <div className="mt-3 flex items-center justify-center gap-2">
                      <Upload className="h-3.5 w-3.5 text-forest" />
                      <span className="text-xs font-bold uppercase tracking-wider text-forest">Click here</span>
                    </div>
                  </div>
                </motion.div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>
          </div>

          {/* ── Right: Outfit Selector + Visualizer ── */}
          <div className="space-y-10">
            {/* Build your outfit */}
            <div>
              <p className="mb-4 flex items-center gap-2 text-[0.62rem] font-bold uppercase tracking-[0.28em] text-muted-foreground">
                Build your Outfit
              </p>

              <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-none w-full">
                {items.length === 0 && (
                  <div className="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-border p-8 text-sm text-muted-foreground">
                    Your wardrobe is empty. Go add some clothes!
                  </div>
                )}

                {items.map(item => {
                  const selected = selectedIds.has(item.id);
                  return (
                    <button
                      key={item.id}
                      onClick={() => toggleItem(item)}
                      className={cn(
                        "group relative flex min-w-[120px] flex-col items-center gap-3 rounded-2xl border p-4 transition-all hover:shadow-soft",
                        selected ? "border-forest bg-forest/5 shadow-soft" : "border-border glass"
                      )}
                    >
                      <div className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full border">
                        {selected ? <Check className="h-3 w-3 text-forest" /> : <Plus className="h-3 w-3 text-muted-foreground opacity-50" />}
                      </div>
                      <img src={item.cutout_url} alt={item.name} className="h-20 w-20 object-contain drop-shadow" />
                      <div className="text-center">
                        <p className="text-[0.55rem] font-bold uppercase tracking-wider text-muted-foreground truncate w-full max-w-[100px]">{item.category}</p>
                        <p className="text-xs font-bold truncate w-full max-w-[100px]">{item.name}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-4">
              <motion.button
                onClick={handleGenerate}
                disabled={!hasBodyPhoto || generating || selectedIds.size === 0}
                whileHover={hasBodyPhoto && !generating ? { scale: 1.02 } : {}}
                className={cn(
                  "flex w-full items-center justify-center gap-3 rounded-full py-5 text-sm font-bold uppercase tracking-[0.2em] shadow-luxe transition-all",
                  hasBodyPhoto && !generating && selectedIds.size > 0
                    ? "bg-ink text-beige hover:bg-ink/90"
                    : "cursor-not-allowed bg-secondary text-muted-foreground",
                )}
              >
                {generating ? (
                  <>
                    <div className="h-4 w-4" /> Rendering try-on…
                  </>
                ) : (
                  <>
                    <Wand2 className="h-4 w-4" /> Finalize Outfit
                  </>
                )}
              </motion.button>

              {!hasBodyPhoto && (
                <p className="text-center text-xs text-muted-foreground">Upload your body photo first.</p>
              )}
            </div>

            {/* OOTDiffusion / IDM-VTON Results */}
            <AnimatePresence>
              {generated && resultImage && !generating && (
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="overflow-hidden rounded-[2rem] border border-border bg-secondary/10 shadow-luxe"
                >
                  <img src={resultImage} alt="Virtual Try-On Result" className="w-full object-contain max-h-[600px]" />
                </motion.div>
              )}

              {generating && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex h-[400px] w-full flex-col items-center justify-center gap-4 rounded-[2rem] border border-border bg-secondary/20 shadow-inner"
                >
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-forest border-t-transparent opacity-80" />
                  <p className="text-sm font-bold uppercase tracking-wider text-forest/80 animate-pulse">
                    Rendering Outfit...
                  </p>
                </motion.div>
              )}

              {generated && !resultImage && !generating && (
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass rounded-[2rem] p-8 text-center shadow-luxe"
                >
                  <div className="flex items-center justify-center gap-2 mb-3">
                    <Sparkles className="h-5 w-5 text-forest" />
                    <span className="text-sm font-bold uppercase tracking-wider text-forest">Generation Failed</span>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    The visualization backend was unable to process the selected combination. Check the backend logs.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
