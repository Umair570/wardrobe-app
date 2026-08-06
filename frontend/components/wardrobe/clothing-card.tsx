"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Heart, Trash2 } from "lucide-react";
import Link from "next/link";
import type { ClothingItem } from "@/types";
import { ImagePlaceholder } from "@/components/ui/image-placeholder";
import { cn } from "@/lib/utils";

interface ClothingCardProps {
  item: ClothingItem;
  favorited?: boolean;
  onToggleFavorite?: () => void;
  onDelete?: () => void;
  showColorDot?: boolean;
  className?: string;
  onClick?: () => void;
}

export function ClothingCard({ item, favorited, onToggleFavorite, onDelete, showColorDot, className, onClick }: ClothingCardProps) {
  return (
    <motion.article
      onClick={onClick}
      whileHover={{ y: -4, scale: 1.015 }}
      whileTap={{ scale: 0.985 }}
      transition={{ type: "spring", stiffness: 420, damping: 26 }}
      className={cn(
        "group overflow-hidden rounded-lg bg-card shadow-[0_8px_32px_rgba(2,6,23,0.08)] transition-shadow duration-300 cursor-pointer",
        "hover:shadow-[0_16px_48px_rgba(2,6,23,0.14)] dark:hover:shadow-[0_16px_48px_rgba(0,0,0,0.35)]",
        className
      )}
      style={{ willChange: "transform" }}
    >
      <div className="relative aspect-[3/4] w-full overflow-hidden bg-cream-muted dark:bg-white/5">
        <motion.div
          className="h-full w-full"
          whileHover={{ scale: 1.06 }}
          transition={{ type: "spring", stiffness: 300, damping: 22 }}
        >
          {item.imageUrl ? (
            <img src={item.imageUrl} alt={item.name} className="h-full w-full object-cover" />
          ) : (
            <ImagePlaceholder label={item.name} rounded="rounded-none" />
          )}
        </motion.div>

        <span className="absolute left-3 top-3 rounded-full bg-white/85 px-2.5 py-1 font-mono text-[10px] font-semibold tracking-wide text-ink backdrop-blur dark:bg-ink/80 dark:text-cream">
          {item.category.toUpperCase()}
        </span>

        {showColorDot && (
          <span
            className="absolute right-3 top-3 h-2.5 w-2.5 rounded-full border border-ink/15 dark:border-cream/20"
            style={{ backgroundColor: item.colorHex }}
          />
        )}

        <div className="absolute right-3 top-3 flex flex-col gap-2">
          {onToggleFavorite && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleFavorite();
              }}
              aria-label="Toggle favorite"
              className="flex h-8 w-8 items-center justify-center rounded-full bg-white/90 shadow-sm ring-1 ring-white/6 dark:bg-ink/80 opacity-0 group-hover:opacity-100 transition-opacity md:opacity-100"
            >
              <motion.span
                key={favorited ? "on" : "off"}
                initial={{ scale: 0.5 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 500, damping: 15 }}
              >
                <Heart
                  className="h-4 w-4"
                  fill={favorited ? "#C9A45C" : "none"}
                  stroke={favorited ? "#C9A45C" : "#1E1E1E"}
                  strokeWidth={1.6}
                />
              </motion.span>
            </button>
          )}

          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (window.confirm("Are you sure you want to delete this item?")) {
                  onDelete();
                }
              }}
              aria-label="Delete item"
              className="flex h-8 w-8 items-center justify-center rounded-full bg-white/90 shadow-sm ring-1 ring-white/6 dark:bg-ink/80 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <Trash2 className="h-4 w-4 text-red-500" strokeWidth={1.6} />
            </button>
          )}
        </div>

        <div className="absolute inset-x-0 bottom-0 flex gap-2 bg-gradient-to-t from-black/45 to-transparent p-3 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
          <Link
            href={`/try-on?item_id=${item.id}`}
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1 rounded-full bg-forest/90 px-3 py-1.5 font-sans text-[11.5px] font-semibold text-white backdrop-blur-sm hover:bg-forest transition-colors"
          >
            Try it on
          </Link>
        </div>
      </div>

      <div className="p-4">
        <p className="font-sans text-[14.5px] font-semibold text-ink dark:text-cream">{item.name}</p>
        <p className="mt-0.5 font-mono text-[10.5px] tracking-wide text-ink/50 dark:text-cream/50">{item.meta}</p>
      </div>
    </motion.article>
  );
}
