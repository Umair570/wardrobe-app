"use client";

import * as React from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { AppNav } from "@/components/layout/app-nav";
import { AiSearchBar } from "@/components/dashboard/ai-search-bar";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import { ClothingCard } from "@/components/wardrobe/clothing-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useWardrobe } from "@/hooks/use-wardrobe";
import { useAuth } from "@/context/auth-provider";
import { getRecommendations, getActivity } from "@/lib/api/wardrobe";
import type { OutfitRecommendation, ActivityEvent } from "@/types";
import { ChevronRight } from "lucide-react";

const bentoItem = {
  hidden: { opacity: 0, y: 12, scale: 0.97 },
  show: { opacity: 1, y: 0, scale: 1, transition: { type: "spring", stiffness: 280, damping: 26 } },
};

function RecSkeleton() {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-ink/5 bg-card/60 p-4 dark:border-cream/5">
      <Skeleton className="h-14 w-14 shrink-0 rounded-xl" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}

function ActivitySkeleton() {
  return (
    <div className="space-y-3 p-3">
      {[1, 2].map((i) => (
        <div key={i} className="flex items-start gap-3">
          <Skeleton className="mt-1 h-2.5 w-2.5 rounded-full" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-3.5 w-full" />
            <Skeleton className="h-3 w-16" />
          </div>
        </div>
      ))}
    </div>
  );
}

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export default function DashboardPage() {
  const { items, favorites, toggleFavorite } = useWardrobe();
  const { user, loading } = useAuth();
  const [query, setQuery] = React.useState("");
  const [recs, setRecs] = React.useState<OutfitRecommendation[]>([]);
  const [activity, setActivity] = React.useState<ActivityEvent[]>([]);
  const [loadingRecs, setLoadingRecs] = React.useState(true);
  const [loadingActivity, setLoadingActivity] = React.useState(true);

  const rawName = user?.user_metadata?.display_name || user?.email?.split("@")[0] || "there";
  const displayName = rawName.charAt(0).toUpperCase() + rawName.slice(1);

  const router = useRouter();

  React.useEffect(() => {
    if (!loading && !user) {
      router.replace("/auth");
    }
  }, [user, loading, router]);

  React.useEffect(() => {
    getRecommendations()
      .then((data) => setRecs(data))
      .catch(() => setRecs([]))
      .finally(() => setLoadingRecs(false));

    getActivity()
      .then((data) => setActivity(data))
      .catch(() => setActivity([]))
      .finally(() => setLoadingActivity(false));
  }, []);

  const handleSearchSubmit = () => {
    if (query.trim()) {
      router.push(`/stylist?q=${encodeURIComponent(query)}`);
    } else {
      router.push('/stylist');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-cream/80 to-cream dark:from-[#0b0b0b] dark:to-[#0b0b0b]">
      <AppNav />
      <div className="mx-auto max-w-6xl px-6 pb-24 pt-11 md:px-12">
        <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.07 } } }}>
          {/* Header */}
          <motion.div variants={bentoItem} className="mb-6">
            <span className="font-sans text-[13px] text-ink/45 dark:text-cream/45">
              {new Date().toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" })}
            </span>
            <h1 className="mt-1 font-heading text-[clamp(26px,3.2vw,36px)] font-semibold text-ink dark:text-cream">
              {getGreeting()}, {displayName}
            </h1>
          </motion.div>

          {/* Primary action — full width hero */}
          <motion.div variants={bentoItem} className="mb-8">
            <AiSearchBar value={query} onChange={setQuery} onSubmit={handleSearchSubmit} />
          </motion.div>

          {/* Bento grid */}
          <div className="grid gap-4 md:grid-cols-12 md:grid-rows-[auto_auto]">
            {/* Wardrobe summary */}
            <motion.div variants={bentoItem} className="md:col-span-5">
              <div className="flex h-full items-center justify-between rounded-2xl border border-ink/5 bg-card/70 p-4 shadow-sm backdrop-blur-sm dark:border-cream/5 dark:bg-card/40">
                <div>
                  <div className="text-xs text-ink/45 dark:text-cream/45">Your wardrobe</div>
                  <div className="text-sm font-semibold text-ink dark:text-cream">
                    {items.length} {items.length === 1 ? "piece" : "pieces"} on the rail
                  </div>
                </div>
                <Link
                  href="/upload"
                  className="rounded-full bg-forest px-4 py-2 font-sans text-xs font-semibold text-cream transition-colors hover:bg-forest/90 dark:bg-[#3d6b54]"
                >
                  Upload
                </Link>
              </div>
            </motion.div>

            <motion.div variants={bentoItem} className="md:col-span-7">
              <div className="rounded-2xl border border-ink/5 bg-card/50 p-4 dark:border-cream/5 dark:bg-card/30">
                <div className="mb-3 flex items-baseline justify-between">
                  <h2 className="text-sm font-semibold text-ink/70 dark:text-cream/70">AI recommendations</h2>
                  <span className="font-mono text-[10px] tracking-wide text-gold">FOR YOU</span>
                </div>
                <div className="space-y-2">
                  {loadingRecs
                    ? [1, 2].map((i) => <RecSkeleton key={i} />)
                    : recs.length > 0
                      ? recs.slice(0, 2).map((rec) => <RecommendationCard key={rec.id} rec={rec} />)
                      : (
                        <p className="py-4 text-center font-sans text-xs text-ink/40 dark:text-cream/40">
                          Upload garments to get recommendations
                        </p>
                      )}
                </div>
              </div>
            </motion.div>

            {/* Recently added — horizontal scroll rail */}
            <motion.div variants={bentoItem} className="md:col-span-8">
              <div className="mb-3 flex items-baseline justify-between">
                <h2 className="text-sm font-semibold text-ink/70 dark:text-cream/70">Recently added</h2>
                <Link href="/wardrobe" className="flex items-center gap-0.5 font-sans text-xs text-ink/45 hover:text-forest dark:text-cream/45 dark:hover:text-[#8fbfa4]">
                  View all <ChevronRight className="h-3 w-3" />
                </Link>
              </div>
              {items.length > 0 ? (
                <div className="-mx-1 flex gap-3 overflow-x-auto px-1 pb-2 scrollbar-none">
                  {items.slice(0, 6).map((item) => (
                    <div key={item.id} className="w-[140px] shrink-0 md:w-[160px]">
                      <ClothingCard
                        item={item}
                        favorited={!!favorites[item.id]}
                        onToggleFavorite={() => toggleFavorite(item.id)}
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-2xl border border-dashed border-ink/10 p-8 text-center dark:border-cream/10">
                  <p className="font-sans text-xs text-ink/40 dark:text-cream/40">
                    Your wardrobe is empty. <Link href="/upload" className="text-forest hover:underline dark:text-[#8fbfa4]">Upload your first garment</Link>
                  </p>
                </div>
              )}
            </motion.div>

            {/* Compact activity */}
            <motion.div variants={bentoItem} className="md:col-span-4">
              <div className="rounded-2xl border border-ink/5 bg-card/50 p-4 dark:border-cream/5 dark:bg-card/30">
                <div className="mb-3 flex items-baseline justify-between">
                  <h2 className="text-sm font-semibold text-ink/70 dark:text-cream/70">Recent activity</h2>
                </div>
                {loadingActivity ? (
                  <ActivitySkeleton />
                ) : activity.length > 0 ? (
                  <div className="space-y-3">
                    {activity.slice(0, 3).map((event) => (
                      <div key={event.id} className="flex items-start gap-2.5">
                        <span
                          className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                            event.kind === "add"
                              ? "bg-forest"
                              : event.kind === "query"
                                ? "bg-gold"
                                : "bg-ink/25 dark:bg-cream/25"
                          }`}
                        />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-xs text-ink/75 dark:text-cream/75">{event.label.replace(/\*\*/g, "")}</p>
                          <p className="text-[10px] text-ink/40 dark:text-cream/40">{event.timestamp}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="py-4 text-center font-sans text-xs text-ink/40 dark:text-cream/40">
                    No activity yet
                  </p>
                )}
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
