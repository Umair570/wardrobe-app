"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import type { ClothingItem } from "@/types";
import { ImagePlaceholder } from "@/components/ui/image-placeholder";

interface ItemDetailsModalProps {
  item: ClothingItem | null;
  onClose: () => void;
}

export function ItemDetailsModal({ item, onClose }: ItemDetailsModalProps) {
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!item) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ type: "spring", stiffness: 400, damping: 30 }}
          className="relative w-full max-w-lg overflow-hidden rounded-xl bg-card shadow-2xl dark:border dark:border-white/10"
        >
          <button
            onClick={onClose}
            className="absolute right-4 top-4 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-black/10 text-ink backdrop-blur-md transition-colors hover:bg-black/20 dark:bg-white/10 dark:text-cream dark:hover:bg-white/20"
          >
            <X className="h-4 w-4" />
          </button>

          <div className="flex flex-col md:flex-row">
            <div className="relative aspect-square w-full bg-cream-muted dark:bg-white/5 md:w-1/2">
              {item.imageUrl ? (
                <img src={item.imageUrl} alt={item.name} className="h-full w-full object-cover" />
              ) : (
                <ImagePlaceholder label={item.name} rounded="rounded-none" />
              )}
              {item.colorHex && (
                <div
                  className="absolute bottom-4 right-4 h-6 w-6 rounded-full border-2 border-white shadow-md dark:border-ink"
                  style={{ backgroundColor: item.colorHex }}
                />
              )}
            </div>

            <div className="flex w-full flex-col p-6 md:w-1/2">
              <span className="font-mono text-[10px] font-semibold tracking-widest text-ink/50 dark:text-cream/50">
                {item.category.toUpperCase()}
              </span>
              <h2 className="mt-1 font-heading text-2xl font-semibold text-ink dark:text-cream">{item.name}</h2>

              <div className="mt-6 flex flex-col gap-4">
                <DetailRow label="Style" value={item.style} />
                <DetailRow label="Season" value={item.season} />
                <DetailRow label="Pattern" value={item.pattern} />
                <DetailRow label="Color" value={item.color} />
              </div>

              {item.tags && item.tags.length > 0 && (
                <div className="mt-6">
                  <span className="mb-2 block font-mono text-[10px] font-semibold tracking-widest text-ink/50 dark:text-cream/50">
                    TAGS
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {item.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded bg-ink/5 px-2 py-1 font-mono text-[10px] uppercase text-ink dark:bg-white/10 dark:text-cream"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

function DetailRow({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="flex flex-col">
      <span className="font-mono text-[10px] font-semibold tracking-widest text-ink/50 dark:text-cream/50">
        {label.toUpperCase()}
      </span>
      <span className="font-sans text-[15px] text-ink dark:text-cream">{value}</span>
    </div>
  );
}
