"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppNav } from "@/components/layout/app-nav";
import { ImagePlaceholder } from "@/components/ui/image-placeholder";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const GARMENTS = ["Clay Linen Shirt", "Cream Silk Blouse", "Waxed Field Jacket", "Charcoal Wool Skirt"];

export default function TryOnPage() {
  const [view, setView] = React.useState<"original" | "styled">("styled");
  const [garment, setGarment] = React.useState(GARMENTS[0]);
  const [loading, setLoading] = React.useState(false);
  const isStyled = view === "styled";

  function swapGarment(g: string) {
    setLoading(true);
    setGarment(g);
    setTimeout(() => setLoading(false), 450);
  }

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

        {/* Focal result with floating toggle */}
        <div className="relative mx-auto max-w-sm">
          <div className="relative aspect-[3/4] overflow-hidden rounded-2xl shadow-[0_20px_60px_rgba(30,30,30,0.12)] dark:shadow-[0_20px_60px_rgba(0,0,0,0.4)]">
            <AnimatePresence mode="wait">
              {loading ? (
                <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                  <Skeleton className="h-full w-full rounded-none" />
                </motion.div>
              ) : (
                <motion.div
                  key={`${view}-${garment}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.35 }}
                  className="h-full"
                >
                  <ImagePlaceholder label={isStyled ? `${garment} — result` : "Your photo"} rounded="rounded-none" />
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
            {isStyled ? `With ${garment} · 96% fit confidence` : "Your original photo"}
          </p>
        </div>

        <p className="mb-3.5 mt-9 font-mono text-[10.5px] tracking-wide text-ink/50 dark:text-cream/50">SWAP GARMENT</p>
        <div className="flex flex-wrap justify-center gap-3.5">
          {GARMENTS.map((g) => (
            <motion.button
              key={g}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => swapGarment(g)}
              className="flex flex-col items-center gap-2"
            >
              <div
                className={cn(
                  "h-16 w-16 overflow-hidden rounded-md border-2 transition-colors",
                  g === garment ? "border-gold shadow-[0_0_12px_rgba(201,164,92,0.3)]" : "border-transparent"
                )}
              >
                <ImagePlaceholder label={g.slice(0, 8)} />
              </div>
              <span className="max-w-[80px] truncate font-sans text-[11px] text-ink dark:text-cream">{g}</span>
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  );
}
