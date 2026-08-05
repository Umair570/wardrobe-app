"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { ActivityEvent } from "@/types";
import { cn } from "@/lib/utils";
import { StaggerContainer, FadeIn } from "@/components/ui/motion-helpers";

const DOT_COLOR: Record<ActivityEvent["kind"], string> = {
  add: "bg-forest ring-4 ring-forest/15 dark:ring-forest/30",
  query: "bg-gold ring-4 ring-gold/15 dark:ring-gold/30",
  favorite: "bg-ink/50 dark:bg-cream/50 ring-4 ring-ink/10 dark:ring-cream/10",
};

function renderLabel(label: string) {
  const parts = label.split(/\*\*(.+?)\*\*/g);
  return parts.map((part, i) =>
    i % 2 === 1 ? (
      <b key={i} className="font-semibold text-ink dark:text-cream">
        {part}
      </b>
    ) : (
      <React.Fragment key={i}>{part}</React.Fragment>
    )
  );
}

export function ActivityTimeline({ events }: { events: ActivityEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="rounded-2xl bg-white/4 backdrop-blur-md border border-white/8 p-8 text-center text-xs text-ink/40 dark:text-cream/40">
        No activities found for this filter.
      </div>
    );
  }

  return (
    <StaggerContainer className="rounded-2xl bg-white/6 dark:bg-white/[0.03] backdrop-blur-xl border border-white/10 dark:border-white/8 p-2 shadow-[0_8px_32px_rgba(0,0,0,0.04)]">
      <AnimatePresence mode="popLayout">
        {events.map((event) => (
          <FadeIn key={event.id}>
            <motion.div
              layout
              whileHover={{ x: 4, backgroundColor: "rgba(255, 255, 255, 0.04)" }}
              transition={{ duration: 0.15 }}
              className="flex items-center justify-between gap-3 rounded-xl px-3.5 py-3 transition-colors"
            >
              <div className="flex items-center gap-3.5 min-w-0">
                <span
                  title={event.kind}
                  className={cn(
                    "h-2 w-2 flex-shrink-0 rounded-full transition-transform duration-200 group-hover:scale-125",
                    DOT_COLOR[event.kind]
                  )}
                />
                <p className="truncate text-xs text-ink/80 dark:text-cream/80">
                  {renderLabel(event.label)}
                </p>
              </div>
              <span className="shrink-0 text-[11px] font-mono text-ink/40 dark:text-cream/40">
                {event.timestamp}
              </span>
            </motion.div>
          </FadeIn>
        ))}
      </AnimatePresence>
    </StaggerContainer>
  );
}