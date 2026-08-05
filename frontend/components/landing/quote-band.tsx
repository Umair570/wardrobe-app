"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";

const QUOTES = [
  { text: "It knows my closet better than I do.", author: "Priya, early user" },
  { text: "I stopped buying clothes I already own.", author: "Marcus, early user" },
  { text: "Dinner outfit, decided in ten seconds.", author: "Elena, early user" },
];

export function QuoteBand() {
  const [quoteIndex, setQuoteIndex] = React.useState(0);

  React.useEffect(() => {
    const t = setInterval(() => setQuoteIndex((i) => (i + 1) % QUOTES.length), 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <section className="relative overflow-hidden bg-ink px-6 py-24 dark:bg-black md:px-12">
      {/* Ambient gradient shift */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[length:200%_200%] animate-gradient-shift motion-reduce:animate-none"
        style={{
          backgroundImage:
            "radial-gradient(ellipse at 20% 50%, rgba(201,164,92,0.12) 0%, transparent 50%), radial-gradient(ellipse at 80% 50%, rgba(47,79,63,0.15) 0%, transparent 50%)",
        }}
      />

      {/* Particle texture */}
      <div aria-hidden className="pointer-events-none absolute inset-0 opacity-30">
        {Array.from({ length: 24 }).map((_, i) => (
          <motion.span
            key={i}
            className="absolute h-1 w-1 rounded-full bg-gold/40"
            style={{
              left: `${(i * 17 + 5) % 100}%`,
              top: `${(i * 23 + 10) % 100}%`,
            }}
            animate={{ opacity: [0.2, 0.7, 0.2], y: [0, -12, 0] }}
            transition={{ duration: 4 + (i % 3), repeat: Infinity, delay: i * 0.2, ease: "easeInOut" }}
          />
        ))}
      </div>

      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-[-100px] h-[500px] w-[500px] -translate-x-1/2 animate-drift-a rounded-full bg-gold/15 blur-3xl motion-reduce:animate-none"
      />

      <div className="relative mx-auto max-w-2xl text-center">
        <AnimatePresence mode="wait">
          <motion.blockquote
            key={quoteIndex}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.4 }}
            className="font-heading text-[clamp(22px,2.6vw,30px)] font-medium italic leading-relaxed text-cream"
          >
            &ldquo;{QUOTES[quoteIndex].text}&rdquo;
          </motion.blockquote>
        </AnimatePresence>
        <motion.p
          key={`author-${quoteIndex}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="mt-6 font-sans text-[13.5px] text-cream/55"
        >
          — {QUOTES[quoteIndex].author}
        </motion.p>
        <div className="mt-6 flex justify-center gap-2">
          {QUOTES.map((_, i) => (
            <button
              key={i}
              onClick={() => setQuoteIndex(i)}
              aria-label={`Quote ${i + 1}`}
              className="h-1.5 rounded-full transition-all duration-300"
              style={{
                width: i === quoteIndex ? 20 : 6,
                background: i === quoteIndex ? "#C9A45C" : "rgba(248,247,244,0.3)",
              }}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
