"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppNav } from "@/components/layout/app-nav";
import { ImagePlaceholder } from "@/components/ui/image-placeholder";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useWardrobe } from "@/hooks/use-wardrobe";
import { visualizeOutfit } from "@/lib/api/visualization";
import { getProfile } from "@/lib/api/profile";
import { Upload, User, Image as ImageIcon, Sparkles } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";

function TryOnContent() {
  const { items, loading: wardrobeLoading } = useWardrobe();
  const searchParams = useSearchParams();
  const initialIds = searchParams.get("item_ids")?.split(",").filter(Boolean) || [];
  
  const [view, setView] = React.useState<"original" | "styled">("styled");
  const [selectedIds, setSelectedIds] = React.useState<string[]>(initialIds);
  const [resultImageUrl, setResultImageUrl] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [profileBodyUrl, setProfileBodyUrl] = React.useState<string | null>(null);
  const [tempBodyPhotoBase64, setTempBodyPhotoBase64] = React.useState<string | null>(null);
  const [useProfilePhoto, setUseProfilePhoto] = React.useState(true);
  const isStyled = view === "styled";

  React.useEffect(() => {
    getProfile()
      .then((profile) => {
        if (profile.body_photo_url) {
          setProfileBodyUrl(profile.body_photo_url);
        } else {
          setUseProfilePhoto(false);
        }
      })
      .catch(() => {});
  }, []);

  function handleTempPhotoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      setTempBodyPhotoBase64(event.target?.result as string);
      setUseProfilePhoto(false);
    };
    reader.readAsDataURL(file);
  }

  function toggleGarment(id: string) {
    setSelectedIds((prev) => 
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  }

  async function handleGenerate() {
    if (selectedIds.length === 0) return;
    setLoading(true);
    setError(null);
    setResultImageUrl(null);
    setView("styled");

    try {
      const activePhoto = useProfilePhoto ? profileBodyUrl : tempBodyPhotoBase64;
      if (!activePhoto) {
        throw new Error("Please select or upload a body photo first.");
      }
      
      const result = await visualizeOutfit(selectedIds, "ai", activePhoto);
      if (result.ai_image_url) {
        setResultImageUrl(result.ai_image_url);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Visualization failed";
      console.warn("[try-on]", message);
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  const garmentList = items.slice(0, 16); // Show a few more items for outfits

  return (
    <div className="min-h-screen bg-cream dark:bg-[#161611]">
      <AppNav />
      <div className="mx-auto max-w-3xl px-6 pb-24 pt-11 md:px-12">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <span className="font-mono text-[11.5px] font-semibold tracking-wide text-gold">SEE IT ON YOU</span>
          <h1 className="mt-2 font-heading text-[clamp(30px,3.6vw,44px)] font-semibold text-ink dark:text-cream">Try-On</h1>
          <p className="mb-7 mt-2 font-sans text-[15px] text-ink/60 dark:text-cream/60">
            Instant visualization, before you wear it.
          </p>
        </motion.div>

        {wardrobeLoading ? (
          <div className="mx-auto max-w-sm">
            <Skeleton className="aspect-[3/4] w-full rounded-2xl" />
          </div>
        ) : items.length === 0 ? (
          <div className="py-16 text-center">
            <p className="font-sans text-sm text-ink/50 dark:text-cream/50">
              Upload some garments first to try them on.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-8 md:flex-row md:items-start md:gap-12">
            
            {/* Left Column: Try-On Settings & Action */}
            <div className="flex-1 space-y-6">
              {/* Body Photo Selection */}
              <div className="rounded-lg bg-card p-4 shadow-sm border border-ink/5 dark:border-cream/5">
                <p className="mb-3 font-mono text-[10px] tracking-wide text-ink/50 dark:text-cream/50">1. YOUR TRY-ON MODEL</p>
                
                <div className="flex flex-col gap-2">
                  {profileBodyUrl && (
                    <button
                      onClick={() => setUseProfilePhoto(true)}
                      className={cn(
                        "flex items-center gap-3 rounded-md px-3 py-2 text-left font-sans text-[13px] transition-colors",
                        useProfilePhoto ? "bg-forest/10 text-forest font-semibold dark:bg-[#8fbfa4]/10 dark:text-[#8fbfa4]" : "hover:bg-cream-muted dark:hover:bg-white/5"
                      )}
                    >
                      <User className="h-4 w-4" />
                      Use saved profile photo
                    </button>
                  )}
                  
                  <div className="relative">
                    <button
                      onClick={() => setUseProfilePhoto(false)}
                      className={cn(
                        "flex w-full items-center gap-3 rounded-md px-3 py-2 text-left font-sans text-[13px] transition-colors",
                        !useProfilePhoto && tempBodyPhotoBase64 ? "bg-forest/10 text-forest font-semibold dark:bg-[#8fbfa4]/10 dark:text-[#8fbfa4]" : "hover:bg-cream-muted dark:hover:bg-white/5"
                      )}
                    >
                      <ImageIcon className="h-4 w-4" />
                      {tempBodyPhotoBase64 ? "Using uploaded photo" : "Upload a temporary photo"}
                    </button>
                    <input
                      type="file"
                      accept="image/jpeg, image/png, image/webp"
                      className="absolute inset-0 cursor-pointer opacity-0"
                      onChange={handleTempPhotoUpload}
                      title="Upload temporary photo"
                    />
                  </div>
                </div>
              </div>

              {/* Garment Selection Grid */}
              <div className="rounded-lg bg-card p-4 shadow-sm border border-ink/5 dark:border-cream/5">
                <p className="mb-3 font-mono text-[10px] tracking-wide text-ink/50 dark:text-cream/50">2. SELECT GARMENTS</p>
                <div className="flex flex-wrap gap-2.5 max-h-[300px] overflow-y-auto">
                  {garmentList.map((item) => {
                    const isSelected = selectedIds.includes(item.id);
                    return (
                      <motion.button
                        key={item.id}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => toggleGarment(item.id)}
                        className="flex flex-col items-center gap-1.5"
                      >
                        <div
                          className={cn(
                            "h-[72px] w-[72px] overflow-hidden rounded-md border-2 transition-colors bg-cream-muted dark:bg-white/5 relative",
                            isSelected ? "border-gold shadow-[0_0_12px_rgba(201,164,92,0.3)]" : "border-transparent"
                          )}
                        >
                          {item.imageUrl ? (
                            <img src={item.imageUrl} alt={item.name} className="h-full w-full object-cover" />
                          ) : (
                            <ImagePlaceholder label={item.name.slice(0, 8)} />
                          )}
                          {isSelected && (
                            <div className="absolute inset-0 bg-gold/10" />
                          )}
                        </div>
                      </motion.button>
                    );
                  })}
                </div>
              </div>

              <Button
                onClick={handleGenerate}
                disabled={loading || selectedIds.length === 0}
                className="w-full font-semibold"
                size="lg"
              >
                {loading ? "Visualizing..." : `Try On ${selectedIds.length} Item${selectedIds.length === 1 ? '' : 's'}`}
                {!loading && <Sparkles className="ml-2 h-4 w-4" />}
              </Button>
            </div>

            {/* Right Column: Focal Result */}
            <div className="relative mx-auto w-full max-w-sm shrink-0 md:sticky md:top-24">
              <div className="relative aspect-[3/4] overflow-hidden rounded-2xl shadow-[0_20px_60px_rgba(30,30,30,0.12)] dark:shadow-[0_20px_60px_rgba(0,0,0,0.4)]">
                <AnimatePresence mode="wait">
                  {loading ? (
                    <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                      <Skeleton className="h-full w-full rounded-none" />
                    </motion.div>
                  ) : resultImageUrl && isStyled ? (
                    <motion.div
                      key={resultImageUrl}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.35 }}
                      className="h-full"
                    >
                      <img src={resultImageUrl} alt="Try-on result" className="h-full w-full object-cover" />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="placeholder"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex h-full flex-col items-center justify-center p-6 text-center text-ink/40 dark:text-cream/40"
                    >
                      <Sparkles className="mb-3 h-8 w-8 opacity-20" />
                      <p className="font-mono text-xs tracking-wide">Ready to visualize</p>
                      <p className="mt-2 font-sans text-xs">Select garments and click Try On</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="absolute left-1/2 top-4 flex -translate-x-1/2 gap-1 rounded-full border border-white/20 bg-ink/80 p-1 backdrop-blur-md dark:bg-black/70">
                  <button
                    onClick={() => setView("original")}
                    className={cn(
                      "rounded-full px-4 py-1.5 font-sans text-[12px] font-semibold transition-colors",
                      !isStyled ? "bg-cream text-ink" : "text-cream/70"
                    )}
                  >
                    Original
                  </button>
                  <button
                    onClick={() => setView("styled")}
                    className={cn(
                      "rounded-full px-4 py-1.5 font-sans text-[12px] font-semibold transition-colors",
                      isStyled ? "bg-cream text-ink" : "text-cream/70"
                    )}
                  >
                    Styled
                  </button>
                </div>
              </div>


              {error && (
                <p className="mt-4 text-center font-sans text-xs text-[#B5502F]">{error}</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function TryOnPage() {
  return (
    <React.Suspense fallback={
      <div className="min-h-screen bg-cream dark:bg-[#161611] flex items-center justify-center">
        <div className="font-mono text-xs text-gold animate-pulse">Loading Try-On...</div>
      </div>
    }>
      <TryOnContent />
    </React.Suspense>
  );
}
