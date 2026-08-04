import { createFileRoute } from "@tanstack/react-router";
import { AnimatePresence } from "motion/react";
import { useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { ItemCard } from "@/components/wardrobe/ItemCard";
import { ItemDetailPanel } from "@/components/wardrobe/ItemDetailPanel";
import { UploadModal } from "@/components/wardrobe/UploadModal";
import { useWardrobe } from "@/hooks/useWardrobe";
import type { WardrobeItem } from "@/lib/types";

export const Route = createFileRoute("/wardrobe")({
  head: () => ({
    meta: [
      { title: "My Wardrobe — Atelier" },
      { name: "description", content: "Browse, filter and search every garment in your digital wardrobe as floating cutout images." },
      { property: "og:title", content: "My Wardrobe — Atelier" },
      { property: "og:description", content: "Every garment you own, catalogued and searchable." },
    ],
  }),
  component: WardrobePage,
});

const filters = ["all", "top", "bottom", "shoes", "outerwear"] as const;
const labels: Record<(typeof filters)[number], string> = {
  all: "All",
  top: "Tops",
  bottom: "Bottoms",
  shoes: "Shoes",
  outerwear: "Outerwear",
};

function WardrobePage() {
  const { data: items = [] } = useWardrobe();
  const [filter, setFilter] = useState<(typeof filters)[number]>("all");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<WardrobeItem | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);

  const visible = useMemo(
    () =>
      items.filter(
        (i) =>
          (filter === "all" || i.category === filter) &&
          (i.name + i.color + i.tags.join(" ")).toLowerCase().includes(query.toLowerCase()),
      ),
    [items, filter, query],
  );

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-6 py-12">
        <PageHeader subtitle={`${items.length} pieces catalogued`} title="My Wardrobe" />

        <div className="mt-9 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-2">
            {filters.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`rounded-full px-5 py-2.5 text-[0.62rem] font-bold uppercase tracking-[0.2em] transition-all duration-300 ${
                  filter === f
                    ? "bg-ink text-beige shadow-soft"
                    : "border border-border text-muted-foreground hover:border-forest hover:text-forest"
                }`}
              >
                {labels[f]}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-3 rounded-full border border-border bg-card px-5 py-2.5 transition-colors focus-within:border-forest lg:w-72">
            <Search className="h-4 w-4 text-muted-foreground" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search your closet"
              className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
          </div>
        </div>

        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence mode="popLayout">
            {visible.map((item, i) => (
              <ItemCard key={item.id} item={item} index={i} onClick={() => setSelected(item)} />
            ))}
          </AnimatePresence>
        </div>

        {visible.length === 0 && (
          <p className="mt-16 text-center text-sm text-muted-foreground">
            Nothing matches that search yet.
          </p>
        )}
      </div>

      <button
        onClick={() => setUploadOpen(true)}
        className="fixed bottom-24 right-6 z-30 inline-flex items-center gap-2 rounded-full bg-ink px-6 py-4 text-[0.62rem] font-bold uppercase tracking-[0.2em] text-beige shadow-luxe transition-transform hover:scale-105 md:bottom-8"
      >
        <Plus className="h-4 w-4" /> Add items
      </button>

      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
      <ItemDetailPanel item={selected} onClose={() => setSelected(null)} />
    </AppShell>
  );
}