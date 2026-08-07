"use client";

import * as React from "react";
import { AppNav } from "@/components/layout/app-nav";
import { ChatBubble } from "@/components/stylist/chat-bubble";
import { TypingIndicator } from "@/components/stylist/typing-indicator";
import { Button } from "@/components/ui/button";
import { askStylist, getChatSessions, getChatSessionHistory, deleteChatSession, type ChatSessionMeta } from "@/lib/api/stylist";
import type { ChatMessage } from "@/types";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Plus, Clock, ChevronDown, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSearchParams, useRouter } from "next/navigation";

const CHIPS = ["Rooftop dinner", "Client meeting", "Rainy commute", "Weekend brunch"];

function StylistContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [query, setQuery] = React.useState("");
  const [thinking, setThinking] = React.useState(false);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [conversation, setConversation] = React.useState<ChatMessage[]>([]);
  const [sessions, setSessions] = React.useState<ChatSessionMeta[]>([]);
  const [loadingHistory, setLoadingHistory] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [mobileHistoryOpen, setMobileHistoryOpen] = React.useState(false);
  const bottomRef = React.useRef<HTMLDivElement>(null);

  // Load chat sessions on mount
  React.useEffect(() => {
    getChatSessions()
      .then(setSessions)
      .catch((err) => console.warn("Failed to load sessions", err));
  }, []);

  const hasAsked = React.useRef(false);

  // Handle URL query parameter for initial search
  React.useEffect(() => {
    const q = searchParams.get("q");
    if (q && !thinking && conversation.length === 0 && !hasAsked.current) {
      hasAsked.current = true;
      ask(q);
      // Clean up the URL so it doesn't trigger again on reload
      router.replace("/stylist");
    }
  }, [searchParams, router]);

  // Auto-scroll to bottom on new messages
  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation, thinking]);

  async function loadSession(id: string) {
    if (thinking || loadingHistory) return;
    setLoadingHistory(true);
    setError(null);
    setMobileHistoryOpen(false);
    
    try {
      const history = await getChatSessionHistory(id);
      setSessionId(id);
      
      const mapped: ChatMessage[] = history.messages.map(m => ({
        id: m.id || crypto.randomUUID(),
        role: m.role,
        text: m.content,
        outfits: m.outfits,
        sessionId: id,
      }));
      setConversation(mapped);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load chat history";
      setError(message);
    } finally {
      setLoadingHistory(false);
    }
  }

  function startNewChat() {
    setSessionId(null);
    setConversation([]);
    setError(null);
    setMobileHistoryOpen(false);
  }

  async function handleDeleteSession(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this chat history?")) return;
    try {
      await deleteChatSession(id);
      setSessions((prev) => prev.filter((s) => s.session_id !== id));
      if (sessionId === id) {
        startNewChat();
      }
    } catch (err) {
      console.error("Failed to delete chat session", err);
    }
  }

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
      
      // If this was a new session, refresh the session list so it appears
      if (!sessionId && reply.sessionId) {
        setSessionId(reply.sessionId);
        getChatSessions().then(setSessions).catch(() => {});
      } else {
        setSessionId(reply.sessionId ?? sessionId);
      }
      
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
      <div className="mx-auto max-w-5xl px-6 pb-16 pt-11 md:px-12 flex flex-col md:flex-row gap-8 md:gap-12">
        
        {/* Sidebar for History */}
        <div className="w-full md:w-64 shrink-0 flex flex-col gap-4">
          <Button 
            onClick={startNewChat}
            variant="outline"
            className="w-full justify-start border-ink/10 dark:border-cream/10"
          >
            <Plus className="mr-2 h-4 w-4" /> New Chat
          </Button>

          {/* Mobile History Toggle */}
          <div className="md:hidden">
            <button
              onClick={() => setMobileHistoryOpen(!mobileHistoryOpen)}
              className="flex w-full items-center justify-between rounded-lg bg-card p-3 font-sans text-sm shadow-sm"
            >
              <span className="flex items-center gap-2 text-ink/70 dark:text-cream/70"><Clock className="h-4 w-4"/> Previous Chats</span>
              <ChevronDown className={cn("h-4 w-4 transition-transform", mobileHistoryOpen && "rotate-180")} />
            </button>
          </div>

          <div className={cn(
            "flex-col gap-1 overflow-y-auto max-h-[300px] md:max-h-[calc(100vh-200px)] scrollbar-none",
            mobileHistoryOpen ? "flex" : "hidden md:flex"
          )}>
            {sessions.length === 0 ? (
              <p className="p-2 font-sans text-[13px] text-ink/40 dark:text-cream/40">No previous chats.</p>
            ) : (
              sessions.map((s) => (
                  <button
                    key={s.session_id}
                    onClick={() => loadSession(s.session_id)}
                    className={cn(
                      "group flex items-center justify-between rounded-md px-3 py-2.5 text-left transition-colors",
                      s.session_id === sessionId
                        ? "bg-forest/10 dark:bg-[#8fbfa4]/10"
                        : "hover:bg-cream-muted dark:hover:bg-white/5"
                    )}
                  >
                    <div className="flex items-center gap-3 overflow-hidden">
                      <MessageSquare className={cn(
                        "h-4 w-4 shrink-0", 
                        s.session_id === sessionId ? "text-forest dark:text-[#8fbfa4]" : "text-ink/40 dark:text-cream/40"
                      )} />
                      <span className={cn(
                        "truncate font-sans text-[13px]",
                        s.session_id === sessionId ? "font-semibold text-forest dark:text-[#8fbfa4]" : "text-ink/70 dark:text-cream/70"
                      )}>
                        {s.title}
                      </span>
                    </div>
                    <div
                      role="button"
                      tabIndex={0}
                      onClick={(e) => handleDeleteSession(s.session_id, e)}
                      className="ml-2 hidden rounded-md p-1.5 text-ink/40 hover:bg-red-500/10 hover:text-red-500 group-hover:block dark:text-cream/40 dark:hover:bg-red-500/20"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </div>
                  </button>
              ))
            )}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 max-w-3xl flex flex-col">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
            <span className="font-mono text-[11.5px] font-semibold tracking-wide text-gold">ASK YOUR STYLIST</span>
            <h1 className="mt-2 font-heading text-[clamp(30px,3.6vw,44px)] font-semibold text-ink dark:text-cream">
              AI Stylist
            </h1>
            <p className="mb-7 mt-2 font-sans text-[15px] text-ink/60 dark:text-cream/60">
              Describe an occasion. Get outfits pulled straight from your closet.
            </p>
          </motion.div>

          <div className="flex flex-col gap-5 flex-1 min-h-[300px]">
            {loadingHistory ? (
              <div className="flex flex-col items-center py-8 text-center animate-pulse">
                <p className="font-sans text-sm text-gold">Loading history...</p>
              </div>
            ) : conversation.length === 0 ? (
              <div className="flex flex-col items-center py-8 text-center">
                <p className="font-sans text-sm text-ink/40 dark:text-cream/40">
                  Start by asking about an occasion — the stylist will search your wardrobe.
                </p>
              </div>
            ) : (
              conversation.map((msg) => (
                <ChatBubble key={msg.id} message={msg} />
              ))
            )}
            
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
    </div>
  );
}

export default function StylistPage() {
  return (
    <React.Suspense fallback={
      <div className="min-h-screen bg-cream dark:bg-[#161611] flex items-center justify-center">
        <div className="font-mono text-xs text-gold animate-pulse">Loading Stylist...</div>
      </div>
    }>
      <StylistContent />
    </React.Suspense>
  );
}
