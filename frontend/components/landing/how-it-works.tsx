"use client";

import * as React from "react";
import { motion, useInView } from "framer-motion";
import { Sparkles, Wand2, LayoutGrid } from "lucide-react";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

const STEPS = [
  { icon: Sparkles, title: "Scan your closet", copy: "Photograph what you own, once." },
  { icon: Wand2, title: "Ask your stylist", copy: "Describe the occasion. Get outfits from your own closet." },
  { icon: LayoutGrid, title: "See it on you", copy: "Instant visualization on your own body." },
];

export function HowItWorks() {
  const ref = React.useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const reduced = useReducedMotion();

  return (
    <section id="how" ref={ref} className="mx-auto max-w-6xl px-6 py-20 md:px-12">
      <div className="mb-14 text-center">
        <span className="font-sans text-xs font-semibold uppercase tracking-widest text-gold">How it works</span>
        <h2 className="mt-2.5 font-heading text-[clamp(28px,3vw,38px)] font-semibold text-ink dark:text-cream">
          Three steps to your next outfit
        </h2>
      </div>

      <div className="relative grid gap-10 md:grid-cols-3">
        {/* Animated connecting line (desktop) */}
        <svg
          aria-hidden
          className="pointer-events-none absolute left-[16.67%] right-[16.67%] top-[26px] hidden h-[2px] md:block"
          viewBox="0 0 800 2"
          preserveAspectRatio="none"
        >
          <motion.path
            d="M0,1 L800,1"
            stroke="url(#stepGradient)"
            strokeWidth="2"
            strokeDasharray="8 6"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={inView ? { pathLength: 1, opacity: 1 } : {}}
            transition={{ duration: reduced ? 0 : 1.2, ease: "easeInOut", delay: 0.3 }}
          />
          <defs>
            <linearGradient id="stepGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#2F4F3F" stopOpacity="0.3" />
              <stop offset="50%" stopColor="#C9A45C" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#2F4F3F" stopOpacity="0.3" />
            </linearGradient>
          </defs>
        </svg>

        {STEPS.map((step, i) => (
          <motion.div
            key={step.title}
            initial={{ opacity: 0, y: 22, scale: 0.96 }}
            whileInView={{ opacity: 1, y: 0, scale: 1 }}
            viewport={{ once: true }}
            transition={{ type: "spring", stiffness: 260, damping: 24, delay: i * 0.15 }}
            whileHover={{ y: -4 }}
            className="relative text-center"
          >
            <motion.div
              whileHover={{ scale: 1.08 }}
              transition={{ type: "spring", stiffness: 400, damping: 18 }}
              className="relative z-10 mx-auto mb-5 flex h-[52px] w-[52px] items-center justify-center rounded-full bg-card shadow-lg ring-1 ring-ink/5 dark:ring-cream/10"
            >
              <step.icon className="h-[22px] w-[22px] text-forest dark:text-[#8fbfa4]" strokeWidth={1.8} />
            </motion.div>
            <h3 className="mb-2 font-sans text-[17px] font-bold text-ink dark:text-cream">{step.title}</h3>
            <p className="mx-auto max-w-[26ch] font-sans text-sm leading-relaxed text-ink/60 dark:text-cream/60">
              {step.copy}
            </p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
