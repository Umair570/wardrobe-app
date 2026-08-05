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
import { Upload, User, Image as ImageIcon } from "lucide-react";

export default function TryOnPage() {
  const { items, loading: wardrobeLoading } = useWardrobe();
  const [view, setView] = React.useState<"original" | "styled">("styled");
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
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

  const selectedItem = items.find((i) => i.id === selectedId) || items[0];

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

  async function swapGarment(id: string) {
    setSelectedId(id);
    setLoading(true);
    setError(null);
    setResultImageUrl(null);

    try {
      const activePhoto = useProfilePhoto ? profileBodyUrl : tempBodyPhotoBase64;
      if (!activePhoto) {
        throw new Error("Please select or upload a body photo first.");
      }
      
      const result = await visualizeOutfit([id], "ai", activePhoto);
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

  // Display items (first 8 from wardrobe)
  const garmentList = items.slice(0, 8);

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
          <>
            {/* Body Photo Selection */}
            <div className="mx-auto max-w-sm mb-6 rounded-lg bg-card p-4 shadow-sm border border-ink/5 dark:border-cream/5">
              <p className="mb-3 font-mono text-[10px] tracking-wide text-ink/50 dark:text-cream/50">YOUR TRY-ON MODEL</p>
              
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

            {/* Focal result with floating toggle */}
            <div className="relative mx-auto max-w-sm">
              <div className="relative aspect-[3/4] overflow-hidden rounded-2xl shadow-[0_20px_60px_rgba(30,30,30,0.12)] dark:shadow-[0_20px_60px_rgba(0,0,0,0.4)]">
                <AnimatePresence mode="wait">
                  {loading ? (
                    <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                      <Skeleton className="h-full w-full rounded-none" />
                    </motion.div>
                  ) : resultImageUrl && isStyled ? (
                    <motion.div
                      key={`result-${selectedId}`}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.35 }}
                      className="h-full"
                    >
                      <img src={resultImageUrl} alt="Try-on result" className="h-full w-full object-cover" />
                    </motion.div>
                  ) : selectedItem?.imageUrl ? (
                    <motion.div
                      key={`original-${selectedId}`}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.35 }}
                      className="h-full"
                    >
                      <img src={selectedItem.imageUrl} alt={selectedItem.name} className="h-full w-full object-cover" />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="placeholder"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="h-full"
                    >
                      <ImagePlaceholder label={selectedItem?.name || "Select a garment"} rounded="rounded-none" />
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

              <p className="mt-4 text-center font-sans text-[13px] text-ink/55 dark:text-cream/55">
                {selectedItem ? (isStyled ? `With ${selectedItem.name}` : "Original garment photo") : "Select a garment below"}
              </p>
              {error && (
                <p className="mt-2 text-center font-sans text-xs text-[#B5502F]">{error}</p>
              )}
            </div>

            <p className="mb-3.5 mt-9 font-mono text-[10.5px] tracking-wide text-ink/50 dark:text-cream/50">SWAP GARMENT</p>
            <div className="flex flex-wrap justify-center gap-3.5">
              {garmentList.map((item) => (
                <motion.button
                  key={item.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => swapGarment(item.id)}
                  className="flex flex-col items-center gap-2"
                >
                  <div
                    className={cn(
                      "h-16 w-16 overflow-hidden rounded-md border-2 transition-colors",
                      item.id === (selectedId || items[0]?.id) ? "border-gold shadow-[0_0_12px_rgba(201,164,92,0.3)]" : "border-transparent"
                    )}
                  >
                    {item.imageUrl ? (
                      <img src={item.imageUrl} alt={item.name} className="h-full w-full object-cover" />
                    ) : (
                      <ImagePlaceholder label={item.name.slice(0, 8)} />
                    )}
                  </div>
                  <span className="max-w-[80px] truncate font-sans text-[11px] text-ink dark:text-cream">{item.name}</span>
                </motion.button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
