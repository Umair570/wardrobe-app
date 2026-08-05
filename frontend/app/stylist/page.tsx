"use client";

import * as React from "react";
import { AppNav } from "@/components/layout/app-nav";
import { ChatBubble } from "@/components/stylist/chat-bubble";
import { TypingIndicator } from "@/components/stylist/typing-indicator";
import { Button } from "@/components/ui/button";
import { askStylist } from "@/lib/api/stylist";
import type { ChatMessage } from "@/types";
import { motion } from "framer-motion";

const CHIPS = ["Rooftop dinner", "Client meeting", "Rainy commute", "Weekend brunch"];

export default function StylistPage() {
  const [query, setQuery] = React.useState("");
  const [thinking, setThinking] = React.useState(false);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [conversation, setConversation] = React.useState<ChatMessage[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const bottomRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation, thinking]);

  async function ask(text: string) {
    if (!text.trim() || thinking) return;
    setError(null);

    // Add user message
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", text };
    setConversation((c) => [...c, userMsg]);
    setQuery("");
    setThinking(true);

    try {
      const reply = await askStylist(text, sessionId);
      setSessionId(reply.sessionId ?? sessionId);
      setConversation((c) => [...c, reply]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      setError(message);
    } finally {
      setThinking(false);
    }
  }

  return (
    <div className="min-h-screen bg-cream dark:bg-[#161611]">
      <AppNav />
      <div className="mx-auto max-w-3xl px-6 pb-16 pt-11 md:px-12">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <span className="font-mono text-[11.5px] font-semibold tracking-wide text-gold">ASK YOUR STYLIST</span>
          <h1 className="mt-2 font-heading text-[clamp(30px,3.6vw,44px)] font-semibold text-ink dark:text-cream">
            AI Stylist
          </h1>
          <p className="mb-7 mt-2 font-sans text-[15px] text-ink/60 dark:text-cream/60">
            Describe an occasion. Get outfits pulled straight from your closet.
          </p>
        </motion.div>

        <div className="flex flex-col gap-5">
          {conversation.length === 0 && (
            <div className="flex flex-col items-center py-8 text-center">
              <p className="font-sans text-sm text-ink/40 dark:text-cream/40">
                Start by asking about an occasion — the stylist will search your wardrobe.
              </p>
            </div>
          )}
          {conversation.map((msg) => (
            <ChatBubble key={msg.id} message={msg} />
          ))}
          {thinking && <TypingIndicator />}
          {error && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center font-sans text-sm text-[#B5502F]"
            >
              {error}
            </motion.p>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {CHIPS.map((chip) => (
            <motion.button
              key={chip}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => ask(chip)}
              disabled={thinking}
              className="rounded-full bg-cream-muted px-4 py-2.5 font-sans text-[13px] text-ink transition-colors hover:bg-forest/10 disabled:opacity-50 dark:bg-white/10 dark:text-cream dark:hover:bg-white/15"
            >
              {chip}
            </motion.button>
          ))}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(query);
          }}
          className="mt-4 flex items-center gap-3 rounded-full border border-ink/6 bg-card px-5 py-3.5 shadow-[0_4px_16px_rgba(30,30,30,0.06)] transition-shadow focus-within:shadow-[0_0_0_3px_rgba(47,79,63,0.15)] dark:border-cream/10"
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask for an occasion…"
            className="flex-1 bg-transparent font-sans text-[14.5px] text-ink outline-none placeholder:text-ink/40 dark:text-cream dark:placeholder:text-cream/40"
          />
          <Button type="submit" size="sm" disabled={thinking || !query.trim()}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}
