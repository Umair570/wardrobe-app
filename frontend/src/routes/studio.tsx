import { createFileRoute } from "@tanstack/react-router";
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { MessageSquare, Send, Sparkles, X } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/LuxButton";
import { Eyebrow } from "@/components/ui/Surface";
import { useWardrobe } from "@/hooks/useWardrobe";
import { askStylist } from "@/lib/api";
import type { Category, ChatMessage, OutfitSelection } from "@/lib/types";

export const Route = createFileRoute("/studio")({
  validateSearch: (search: Record<string, unknown>) => ({
    q: typeof search['q'] === "string" ? search['q'] : "",
  }),
  head: () => ({
    meta: [
      { title: "Outfit Studio — Atelier" },
      { name: "description", content: "Stack your garments on a visual canvas, swap pieces per slot and let the AI stylist build the look." },
      { property: "og:title", content: "Outfit Studio — Atelier" },
      { property: "og:description", content: "A visual workspace for assembling outfits with AI." },
    ],
  }),
  component: Studio,
});

const slots: { key: keyof OutfitSelection; category: Category; label: string }[] = [
  { key: "outerwear_id", category: "outerwear", label: "Outerwear" },
  { key: "top_id", category: "top", label: "Top" },
  { key: "bottom_id", category: "bottom", label: "Bottom" },
  { key: "shoes_id", category: "shoes", label: "Shoes" },
];

function Studio() {
  const { q } = Route.useSearch();
  const { data: items = [] } = useWardrobe();
  const [outfit, setOutfit] = useState<OutfitSelection>({
    top_id: null,
    bottom_id: null,
    outerwear_id: null,
    shoes_id: null,
  });
  const [activeSlot, setActiveSlot] = useState<keyof OutfitSelection | null>(null);
  const [chatOpen, setChatOpen] = useState(Boolean(q));
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState(q);
  const [thinking, setThinking] = useState(false);
  const [tryOn, setTryOn] = useState<"idle" | "loading" | "soon">("idle");

  const byId = (id: string | null) => items.find((i) => i.id === id) ?? null;

  async function send(text: string) {
    if (!text.trim()) return;
    setInput("");
    setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", content: text }]);
    setThinking(true);
    const res = await askStylist(text, items);
    setThinking(false);
    setMessages((m) => [...m, { id: crypto.randomUUID(), role: "assistant", content: res.reply }]);
    setOutfit(res.outfit);
  }

  function runTryOn() {
    setTryOn("loading");
    setTimeout(() => setTryOn("soon"), 1800);
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <PageHeader subtitle="Outfit studio" title="Build the look" />
          <Button variant="outline" size="sm" onClick={() => setChatOpen(true)}>
            <MessageSquare className="h-3.5 w-3.5" /> Stylist
          </Button>
        </div>

        <div className="mt-9 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="glass relative flex min-h-[460px] items-center justify-center rounded-[2rem] p-8 shadow-luxe">
            <div className="absolute inset-x-10 top-10 h-64 rounded-full bg-forest/5 blur-3xl" />
            <div className="relative flex flex-col items-center gap-1">
              <AnimatePresence mode="popLayout">
                {slots.map(({ key }) => {
                  const item = byId(outfit[key]);
                  if (!item) return null;
                  return (
                    <motion.img
                      key={item.id + key}
                      src={item.cutout_url}
                      alt={item.name}
                      width={768}
                      height={768}
                      initial={{ opacity: 0, y: -24, scale: 0.9 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ type: "spring", stiffness: 220, damping: 24 }}
                      className="h-36 w-36 object-contain drop-shadow-xl sm:h-44 sm:w-44"
                    />
                  );
                })}
              </AnimatePresence>
              {!Object.values(outfit).some(Boolean) && (
                <p className="max-w-[16rem] text-center text-sm text-muted-foreground">
                  Pick pieces from the slots, or ask the stylist to compose a look for you.
                </p>
              )}
            </div>
          </div>

          <div>
            <div className="space-y-3">
              {slots.map(({ key, label, category }) => {
                const item = byId(outfit[key]);
                const open = activeSlot === key;
                return (
                  <div key={key} className="glass rounded-3xl p-4 shadow-soft">
                    <button
                      onClick={() => setActiveSlot(open ? null : key)}
                      className="flex w-full items-center gap-4"
                    >
                      <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-secondary/70">
                        {item ? (
                          <img
                            src={item.cutout_url}
                            alt={item.name}
                            width={768}
                            height={768}
                            className="h-12 w-12 object-contain"
                          />
                        ) : (
                          <span className="text-lg text-muted-foreground">+</span>
                        )}
                      </div>
                      <div className="text-left">
                        <p className="text-[0.58rem] font-bold uppercase tracking-[0.24em] text-muted-foreground">
                          {label}
                        </p>
                        <p className="mt-1 text-sm font-bold">{item ? item.name : "Empty slot"}</p>
                      </div>
                    </button>

                    <AnimatePresence>
                      {open && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-4 flex gap-3 overflow-x-auto pb-1">
                            {items
                              .filter((i) => i.category === category)
                              .map((i) => (
                                <button
                                  key={i.id}
                                  onClick={() => {
                                    setOutfit((o) => ({ ...o, [key]: i.id }));
                                    setActiveSlot(null);
                                  }}
                                  className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl border border-border bg-card transition-colors hover:border-forest"
                                >
                                  <img
                                    src={i.cutout_url}
                                    alt={i.name}
                                    width={768}
                                    height={768}
                                    className="h-14 w-14 object-contain"
                                  />
                                </button>
                              ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>

            <Button variant="glow" size="lg" className="mt-6 w-full" onClick={runTryOn}>
              <Sparkles className="h-4 w-4" />
              {tryOn === "loading" ? "Rendering…" : "Generate AI try-on"}
            </Button>
            {tryOn === "soon" && (
              <p className="mt-3 text-center text-xs text-muted-foreground">
                Virtual try-on rendering lands in the next phase.
              </p>
            )}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {chatOpen && (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-ink/40 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setChatOpen(false)}
            />
            <motion.aside
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", stiffness: 280, damping: 32 }}
              className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-border bg-card"
            >
              <div className="flex items-center justify-between border-b border-border px-6 py-5">
                <div>
                  <Eyebrow>AI Stylist</Eyebrow>
                  <h2 className="mt-2 text-2xl uppercase display-xl">Talk it through</h2>
                </div>
                <button
                  onClick={() => setChatOpen(false)}
                  aria-label="Close stylist"
                  className="rounded-full p-2 text-muted-foreground hover:bg-secondary"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
                {messages.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    Try: "I need an outfit for a summer party" — the studio canvas fills in with the
                    stylist's picks.
                  </p>
                )}
                {messages.map((m) => (
                  <motion.div
                    key={m.id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`max-w-[85%] rounded-3xl px-5 py-3.5 text-sm leading-relaxed ${
                      m.role === "user"
                        ? "ml-auto bg-ink text-beige"
                        : "bg-secondary text-foreground"
                    }`}
                  >
                    {m.content}
                  </motion.div>
                ))}
                {thinking && (
                  <div className="flex gap-1.5 px-2">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="h-2 w-2 animate-bounce rounded-full bg-forest"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                )}
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void send(input);
                }}
                className="flex items-center gap-3 border-t border-border px-5 py-4"
              >
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask your stylist…"
                  className="w-full rounded-full border border-border bg-background px-5 py-3 text-sm outline-none transition-colors focus:border-forest"
                />
                <button
                  type="submit"
                  aria-label="Send"
                  className="rounded-full bg-ink p-3 text-beige transition-transform hover:scale-105"
                >
                  <Send className="h-4 w-4" />
                </button>
              </form>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </AppShell>
  );
}