import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { motion } from "motion/react";
import { useState } from "react";
import { ArrowUpRight, Send, Sparkles } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { Surface, Eyebrow } from "@/components/ui/Surface";
import { Button } from "@/components/ui/LuxButton";
import { ItemCard } from "@/components/wardrobe/ItemCard";
import { useWardrobe } from "@/hooks/useWardrobe";
import type { Category } from "@/lib/types";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — Atelier AI Wardrobe" },
      { name: "description", content: "Your daily outfit recommendation, wardrobe highlights and a direct line to the assistant." },
      { property: "og:title", content: "Dashboard — Atelier AI Wardrobe" },
      { property: "og:description", content: "Daily outfit recommendation and wardrobe highlights." },
    ],
  }),
  component: Dashboard,
});

const groups: { label: string; category: Category }[] = [
  { label: "Tops", category: "top" },
  { label: "Bottoms", category: "bottom" },
  { label: "Shoes", category: "shoes" },
];

function Dashboard() {
  const { data: items = [] } = useWardrobe();
  const [prompt, setPrompt] = useState("");
  const navigate = useNavigate();

  const daily = {
    top: items.find((i) => i.category === "top"),
    bottom: items.find((i) => i.category === "bottom"),
    outerwear: items.find((i) => i.category === "outerwear"),
    shoes: items.find((i) => i.category === "shoes"),
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-6 py-12">
        <PageHeader subtitle="Good evening" title="What are you wearing today?" />

        <motion.form
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          onSubmit={(e) => {
            e.preventDefault();
            navigate({ to: "/studio", search: { q: prompt } });
          }}
          className="mt-9 flex items-center gap-3 rounded-full border border-border bg-card px-5 py-3 shadow-soft transition-colors focus-within:border-forest"
        >
          <Sparkles className="h-4 w-4 shrink-0 text-forest" />
          <input
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Dinner outdoors, slightly cold…"
            className="w-full bg-transparent py-2 text-sm outline-none placeholder:text-muted-foreground"
          />
          <button
            type="submit"
            aria-label="Ask the assistant"
            className="rounded-full bg-ink p-2.5 text-beige transition-transform hover:scale-105"
          >
            <Send className="h-4 w-4" />
          </button>
        </motion.form>

        <motion.div
          initial={{ opacity: 0, y: 26 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15 }}
          className="gradient-hero mt-8 overflow-hidden rounded-[2rem] p-8 shadow-luxe"
        >
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div>
              <Eyebrow className="text-beige/60">Daily recommendation</Eyebrow>
              <h2 className="mt-3 max-w-xs text-3xl uppercase text-beige display-xl">
                Soft knit, sharp tailoring
              </h2>
              <Link to="/studio" search={{ q: "" }} className="mt-6 inline-block">
                <Button variant="glow" size="sm">
                  Open in studio <ArrowUpRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
            <div className="flex items-end gap-2">
              {[daily.outerwear, daily.top, daily.bottom, daily.shoes]
                .filter(Boolean)
                .map((it, i) => (
                  <img
                    key={it!.id}
                    src={it!.cutout_url}
                    alt={it!.name}
                    width={768}
                    height={768}
                    loading="lazy"
                    className="h-24 w-24 object-contain animate-float-slow sm:h-28 sm:w-28"
                    style={{ animationDelay: `${i * 0.5}s` }}
                  />
                ))}
            </div>
          </div>
        </motion.div>

        {groups.map(({ label, category }) => {
          const list = items.filter((i) => i.category === category);
          if (!list.length) return null;
          return (
            <section key={category} className="mt-14">
              <div className="flex items-end justify-between">
                <h2 className="text-2xl uppercase display-xl">{label}</h2>
                <Link
                  to="/wardrobe"
                  className="text-[0.6rem] font-bold uppercase tracking-[0.22em] text-muted-foreground transition-colors hover:text-forest"
                >
                  View all
                </Link>
              </div>
              <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {list.slice(0, 3).map((item, i) => (
                  <ItemCard key={item.id} item={item} index={i} />
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </AppShell>
  );
}