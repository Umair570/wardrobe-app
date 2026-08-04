"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Heart } from "lucide-react";
import { AppNav } from "@/components/layout/app-nav";
import { ImagePlaceholder } from "@/components/ui/image-placeholder";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getSavedLooks } from "@/lib/api/wardrobe";
import type { SavedLook } from "@/types";

export default function SavedPage() {
  const [looks, setLooks] = React.useState<SavedLook[]>([]);
  const [favorites, setFavorites] = React.useState<Record<string, boolean>>({});
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    getSavedLooks().then((data) => {
      setLooks(data);
      setFavorites(Object.fromEntries(data.filter((l) => l.favorited).map((l) => [l.id, true])));
      setLoading(false);
    });
  }, []);

  return (
    <div className="min-h-screen bg-cream dark:bg-[#161611]">
      <AppNav />
      <div className="mx-auto max-w-6xl px-6 pb-24 pt-11 md:px-12">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <span className="font-mono text-[11.5px] font-semibold tracking-wide text-gold">YOUR RAIL, CURATED</span>
          <h1 className="mt-2 font-heading text-[clamp(30px,3.6vw,44px)] font-semibold text-ink dark:text-cream">
            Saved Looks
          </h1>
          <p className="mb-8 mt-2 font-sans text-[15px] text-ink/60 dark:text-cream/60">
            Outfits you&apos;ve kept for later.
          </p>
        </motion.div>

        {loading ? (
          <div className="columns-1 gap-5 sm:columns-2 lg:columns-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="mb-5 aspect-[4/5] w-full break-inside-avoid rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="columns-1 gap-5 sm:columns-2 lg:columns-3">
            {looks.map((look, i) => (
              <motion.article
                key={look.id}
                initial={{ opacity: 0, y: 16, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ delay: i * 0.06, type: "spring", stiffness: 280, damping: 26 }}
                whileHover={{ y: -4 }}
                className="group mb-5 break-inside-avoid overflow-hidden rounded-lg bg-card shadow-[0_4px_16px_rgba(30,30,30,0.06)] transition-shadow hover:shadow-[0_12px_40px_rgba(30,30,30,0.1)] dark:hover:shadow-[0_12px_40px_rgba(0,0,0,0.3)]"
                style={{ marginBottom: i % 3 === 1 ? "2rem" : undefined }}
              >
                <div className="relative mb-3 p-4 pb-0">
                  <div
                    className={`grid gap-1.5 ${i % 3 === 0 ? "grid-cols-2 grid-rows-2" : i % 3 === 1 ? "grid-cols-1" : "grid-cols-3"}`}
                  >
                    {i % 3 === 0 ? (
                      <>
                        <div className="row-span-2 aspect-square overflow-hidden rounded-md">
                          <ImagePlaceholder />
                        </div>
                        <div className="aspect-[1.6/1] overflow-hidden rounded-md">
                          <ImagePlaceholder />
                        </div>
                        <div className="aspect-[1.6/1] overflow-hidden rounded-md">
                          <ImagePlaceholder />
                        </div>
                      </>
                    ) : i % 3 === 1 ? (
                      <div className="aspect-[4/5] overflow-hidden rounded-md">
                        <ImagePlaceholder label={look.name} />
                      </div>
                    ) : (
                      <>
                        <div className="col-span-2 aspect-[2/1] overflow-hidden rounded-md">
                          <ImagePlaceholder />
                        </div>
                        <div className="aspect-square overflow-hidden rounded-md">
                          <ImagePlaceholder />
                        </div>
                        <div className="aspect-square overflow-hidden rounded-md">
                          <ImagePlaceholder />
                        </div>
                      </>
                    )}
                  </div>

                  <div className="absolute inset-x-4 bottom-0 flex justify-end gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                    <span className="rounded-full bg-forest/90 px-3 py-1 font-sans text-[11px] font-semibold text-white">
                      Try on
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between px-4 pb-4">
                  <div>
                    <Badge variant="accent">{look.tag}</Badge>
                    <p className="mt-2 font-sans text-[14.5px] font-semibold text-ink dark:text-cream">{look.name}</p>
                  </div>
                  <button
                    onClick={() => setFavorites((f) => ({ ...f, [look.id]: !f[look.id] }))}
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cream-muted dark:bg-white/10"
                  >
                    <motion.span
                      key={favorites[look.id] ? "on" : "off"}
                      initial={{ scale: 0.5 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 500, damping: 15 }}
                    >
                      <Heart
                        className="h-[15px] w-[15px]"
                        fill={favorites[look.id] ? "#C9A45C" : "none"}
                        stroke={favorites[look.id] ? "#C9A45C" : "#1E1E1E"}
                        strokeWidth={1.6}
                      />
                    </motion.span>
                  </button>
                </div>
              </motion.article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
