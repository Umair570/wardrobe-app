import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AnimatePresence, motion } from "motion/react";
import { useRef, useState } from "react";
import { Send, Sparkles, Wand2, Zap, Database } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { useWardrobe } from "@/hooks/useWardrobe";
import { askStylist } from "@/lib/api";
import type { ChatMessage, WardrobeItem } from "@/lib/types";

export const Route = createFileRoute("/stylist")({
  head: () => ({
    meta: [
      { title: "AI Stylist — Atelier" },
      {
        name: "description",
        content:
          "Have a conversation with your personal AI stylist. It retrieves your wardrobe items using vector search and builds the perfect outfit for any occasion.",
      },
    ],
  }),
  component: StylistPage,
});

interface ExtendedChatResponse {
  reply: string;
  outfit: {
    top_id: string | null;
    bottom_id: string | null;
    outerwear_id: string | null;
    shoes_id: string | null;
  };
  retrieval_source?: string;
  items_retrieved?: number;
}

function StylistPage() {
  const { data: items = [] } = useWardrobe();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [lastResponse, setLastResponse] = useState<ExtendedChatResponse | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const byId = (id: string | null): WardrobeItem | null =>
    items.find((i) => i.id === id) ?? null;

  const suggestedItems = lastResponse
    ? [
        byId(lastResponse.outfit.outerwear_id),
        byId(lastResponse.outfit.top_id),
        byId(lastResponse.outfit.bottom_id),
        byId(lastResponse.outfit.shoes_id),
      ].filter(Boolean) as WardrobeItem[]
    : [];

  async function send(text: string) {
    if (!text.trim()) return;
    setInput("");
    setMessages((m) => [
      ...m,
      { id: crypto.randomUUID(), role: "user", content: text },
    ]);
    setThinking(true);

    const res = await askStylist(text, items) as ExtendedChatResponse;
    setThinking(false);
    setLastResponse(res);
    setMessages((m) => [
      ...m,
      { id: crypto.randomUUID(), role: "assistant", content: res.reply },
    ]);

    setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <PageHeader subtitle="Powered by vector search" title="AI Stylist" />
          {lastResponse?.retrieval_source && (
            <div className="flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-[0.6rem] font-bold uppercase tracking-wider text-muted-foreground">
              <Database className="h-3 w-3" />
              {lastResponse.retrieval_source === "qdrant_vector"
                ? `Qdrant · ${lastResponse.items_retrieved} items`
                : "MongoDB fallback"}
            </div>
          )}
        </div>

        <div className="mt-9 grid gap-6 lg:grid-cols-[1fr_380px]">
          {/* ── Chat panel ── */}
          <div className="glass flex flex-col rounded-[2rem] shadow-luxe" style={{ minHeight: "600px" }}>
            {/* Messages */}
            <div className="flex-1 space-y-4 overflow-y-auto px-6 py-7">
              {messages.length === 0 && (
                <div className="flex h-full flex-col items-center justify-center gap-4 py-16 text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-forest/15">
                    <Sparkles className="h-6 w-6 text-forest" />
                  </div>
                  <div>
                    <p className="font-semibold text-foreground">Your personal AI stylist</p>
                    <p className="mt-1.5 max-w-xs text-sm text-muted-foreground">
                      Ask anything — outfit for a hot day, formal dinner, weekend hike. The stylist
                      retrieves your actual wardrobe items using semantic search.
                    </p>
                  </div>
                  <div className="flex flex-wrap justify-center gap-2 mt-2">
                    {[
                      "Suggest something casual for hot weather",
                      "I have a formal dinner tonight",
                      "Cozy weekend at home",
                    ].map((s) => (
                      <button
                        key={s}
                        onClick={() => send(s)}
                        className="rounded-full border border-border bg-card px-4 py-2 text-xs font-medium text-muted-foreground transition-colors hover:border-forest hover:text-forest"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <AnimatePresence initial={false}>
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
              </AnimatePresence>

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

              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void send(input);
              }}
              className="flex items-center gap-3 border-t border-border px-5 py-4 rounded-b-[2rem]"
            >
              <input
                id="stylist-chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask your stylist… e.g. 'Today is very hot, suggest something light'"
                className="w-full rounded-full border border-border bg-background px-5 py-3 text-sm outline-none transition-colors focus:border-forest"
              />
              <button
                type="submit"
                id="stylist-send-btn"
                aria-label="Send"
                disabled={thinking || !input.trim()}
                className="rounded-full bg-ink p-3 text-beige transition-transform hover:scale-105 disabled:opacity-40"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>

          {/* ── Outfit preview panel ── */}
          <div className="space-y-4">
            <p className="text-[0.62rem] font-bold uppercase tracking-[0.28em] text-muted-foreground">
              Suggested Outfit
            </p>

            {suggestedItems.length === 0 ? (
              <div className="glass flex min-h-[280px] flex-col items-center justify-center gap-3 rounded-[2rem] p-8 text-center">
                <Sparkles className="h-8 w-8 text-muted-foreground/40" />
                <p className="text-sm text-muted-foreground">
                  The stylist's picks will appear here after you chat.
                </p>
              </div>
            ) : (
              <AnimatePresence mode="popLayout">
                {suggestedItems.map((item, i) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ delay: i * 0.07 }}
                    className="glass flex items-center gap-4 rounded-2xl p-4 shadow-soft"
                  >
                    <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-xl bg-secondary">
                      <img
                        src={item.cutout_url}
                        alt={item.name}
                        width={128}
                        height={128}
                        className="h-12 w-12 object-contain drop-shadow-sm"
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-[0.58rem] font-bold uppercase tracking-[0.22em] text-muted-foreground">
                        {item.category}
                      </p>
                      <p className="mt-0.5 truncate text-sm font-bold">{item.name}</p>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {item.tags.slice(0, 2).map((tag) => (
                          <span
                            key={tag}
                            className="rounded-full bg-secondary px-2 py-0.5 text-[0.55rem] font-bold uppercase tracking-wider text-muted-foreground"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                    <button
                      id={`tryon-btn-${item.id}`}
                      onClick={() => navigate({ to: "/tryon" })}
                      title="Virtual Try-On"
                      className="shrink-0 rounded-full bg-ink p-2 text-beige transition-transform hover:scale-110"
                    >
                      <Wand2 className="h-3.5 w-3.5" />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
            )}

            {suggestedItems.length > 0 && (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                id="full-tryon-btn"
                onClick={() => navigate({ to: "/tryon" })}
                className="flex w-full items-center justify-center gap-2 rounded-full bg-ink px-6 py-4 text-[0.62rem] font-bold uppercase tracking-[0.2em] text-beige shadow-luxe transition-transform hover:scale-[1.02]"
              >
                <Zap className="h-4 w-4" /> Generate Full Try-On
              </motion.button>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
